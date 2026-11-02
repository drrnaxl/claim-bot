import asyncio
import hashlib
import json
import math
import os
import tempfile

from datetime import datetime
from pathlib import Path

import discord
import yaml

from discord import app_commands

from modules.extractor import (
    get_text,
    extract_vendor,
    extract_amount,
    extract_date,
    extract_currency
)

from modules.categorizer import classify_expense
from modules.excel_writer import populate_claim


ROOT = Path(__file__).resolve().parent

DATA = ROOT / "discord_data"
DATA.mkdir(exist_ok=True)

GUILD = discord.Object(
    id=int(os.environ["DISCORD_GUILD_ID"])
)

# Prevent commands from changing a queue simultaneously.
queue_lock = asyncio.Lock()


def queue_file(interaction):

    return DATA / (
        f"{interaction.guild_id}_"
        f"{interaction.user.id}.json"
    )


def load_queue(interaction):

    path = queue_file(interaction)

    if not path.exists():
        return []

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_queue(interaction, receipts):

    path = queue_file(interaction)

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(receipts, indent=2),
        encoding="utf-8"
    )

    temporary.replace(path)


def load_config():

    with open(
        ROOT / "config.yaml",
        "r",
        encoding="utf-8"
    ) as f:

        return yaml.safe_load(f)

def profile_file(interaction):

    return DATA / (
        f"profile_{interaction.guild_id}_"
        f"{interaction.user.id}.json"
    )


def load_profile(interaction):

    path = profile_file(interaction)

    if not path.exists():
        return None

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_profile(interaction, profile):

    path = profile_file(interaction)

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(profile, indent=2),
        encoding="utf-8"
    )

    temporary.replace(path)

def process_pdf(path, config):

    text = get_text(path)

    vendor = extract_vendor(text)
    amount = float(extract_amount(text))
    date = extract_date(text)
    currency = extract_currency(text)

    # Check the date before adding it to the queue.
    datetime.strptime(
        date,
        "%Y-%m-%d"
    )

    if currency == "CAD":

        exchange_rate = 1.0

    else:

        exchange_rate = (
            config
            .get("exchange_rates", {})
            .get(currency)
        )

        if exchange_rate is None:

            raise ValueError(
                f"Add the actual {currency} "
                "exchange rate to config.yaml."
            )

        exchange_rate = float(
            exchange_rate
        )

    if not all(
        math.isfinite(value) and value > 0
        for value in (amount, exchange_rate)
    ):

        raise ValueError(
            "Amount and exchange rate must "
            "be positive finite numbers."
        )

    category, purpose = classify_expense(text)

    return {
        "vendor": vendor,
        "date": date,
        "amount": amount,
        "currency": currency,
        "exchange_rate": exchange_rate,
        "category": category,
        "purpose": purpose
    }


class ClaimBot(discord.Client):

    def __init__(self):

        super().__init__(
            intents=discord.Intents.default()
        )

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):

        self.tree.copy_global_to(
            guild=GUILD
        )

        await self.tree.sync(
            guild=GUILD
        )

    async def on_ready(self):

        print(
            f"Connected as {self.user}"
        )


bot = ClaimBot()

receipt_group = app_commands.Group(
    name="receipt",
    description="Manage your receipt queue."
)

profile_group = app_commands.Group(
    name="profile",
    description="Manage your claimant information."
)

claim_group = app_commands.Group(
    name="claim",
    description="Generate reimbursement claims."
)


@bot.tree.command(
    name="ping",
    description="Check whether Claim Bot is online."
)
async def ping(
        interaction: discord.Interaction):

    await interaction.response.send_message(
        "Claim Bot is connected!",
        ephemeral=True
    )


@receipt_group.command(
    name="add",
    description="Upload up to five PDF receipts."
)
async def receipt_add(
        interaction: discord.Interaction,
        file1: discord.Attachment,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
        file4: discord.Attachment = None,
        file5: discord.Attachment = None):

    await interaction.response.defer(
        ephemeral=True,
        thinking=True
    )

    attachments = [
        file
        for file in (
            file1,
            file2,
            file3,
            file4,
            file5
        )
        if file is not None
    ]

    results = []

    async with queue_lock:

        receipts = load_queue(interaction)
        config = load_config()

        for attachment in attachments:

            name = attachment.filename[:80]

            try:

                if not name.lower().endswith(".pdf"):

                    raise ValueError(
                        "Only PDF files are supported."
                    )

                # Application limit, independent of Discord's limit.
                if attachment.size > 10 * 1024 * 1024:

                    raise ValueError(
                        "PDF must be 10 MB or smaller."
                    )

                if len(receipts) >= 10:

                    raise ValueError(
                        "Your queue already has 10 receipts."
                    )

                content = await attachment.read()

                if b"%PDF-" not in content[:1024]:

                    raise ValueError(
                        "This file does not appear to be a PDF."
                    )

                digest = hashlib.sha256(
                    content
                ).hexdigest()

                if any(
                    item.get("hash") == digest
                    for item in receipts
                ):

                    results.append(
                        f"Skipped {name}: already queued."
                    )

                    continue

                with tempfile.TemporaryDirectory() as folder:

                    path = Path(folder) / "receipt.pdf"

                    path.write_bytes(content)

                    item = await asyncio.to_thread(
                        process_pdf,
                        path,
                        config
                    )

                item["hash"] = digest
                item["filename"] = attachment.filename

                # Persist before confirming that this receipt was added.
                updated = receipts + [item]

                save_queue(
                    interaction,
                    updated
                )

                receipts = updated

                results.append(
                    f"Added {name}: "
                    f"{item['date']} | "
                    f"{item['currency']} "
                    f"{item['amount']:,.2f}"
                )

            except Exception as error:

                print(
                    f"Receipt error: {error}"
                )

                results.append(
                    f"Failed {name}: {str(error)[:180]}"
                )

    message = (
        "\n".join(results)
        + f"\n\nQueued: {len(receipts)}/10."
        + "\nUse /receipt list to review."
    )

    await interaction.followup.send(
        message,
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions.none()
    )


@receipt_group.command(
    name="list",
    description="Show your queued receipt details."
)
async def receipt_list(
        interaction: discord.Interaction):

    async with queue_lock:

        receipts = load_queue(interaction)

    if not receipts:

        await interaction.response.send_message(
            "Your queue is empty.",
            ephemeral=True
        )

        return

    lines = []

    for index, item in enumerate(
        receipts,
        start=1
    ):

        lines.append(
            f"{index}. {item['vendor'][:70]}\n"
            f"{item['date']} | "
            f"{item['currency']} "
            f"{item['amount']:,.2f} | "
            f"CAD rate: {item['exchange_rate']}"
        )

    await interaction.response.send_message(
        "\n\n".join(lines),
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions.none()
    )


@receipt_group.command(
    name="clear",
    description="Empty your queue. Original PDFs are unaffected."
)
async def receipt_clear(
        interaction: discord.Interaction,
        confirm: bool):

    if not confirm:

        await interaction.response.send_message(
            "Nothing cleared. Set confirm to True to empty your queue.",
            ephemeral=True
        )

        return

    async with queue_lock:

        save_queue(
            interaction,
            []
        )

    await interaction.response.send_message(
        "Your receipt queue is now empty.",
        ephemeral=True
    )


@claim_group.command(
    name="generate",
    description="Generate one Excel using the claimant in config.yaml."
)
async def claim_generate(
        interaction: discord.Interaction):

    await interaction.response.defer(
        ephemeral=True,
        thinking=True
    )

    async with queue_lock:

        receipts = load_queue(interaction)

    if not receipts:

        await interaction.followup.send(
            "Your queue is empty. Use /receipt add first.",
            ephemeral=True
        )

        return

    receipts.sort(
        key=lambda item: item["date"]
    )

    try:

        config = load_config()

        async with queue_lock:

            profile = load_profile(
                interaction
            )

        if profile is None:

            await interaction.followup.send(
                "Use /profile set to save your "
                "claimant details first.",
                ephemeral=True
            )

            return

        config["claimant"] = profile

        filename = (
            "Claim_All_"
            f"{datetime.now():%Y%m%d_%H%M%S_%f}.xlsx"
        )

        with tempfile.TemporaryDirectory() as folder:

            output = Path(folder) / filename

            await asyncio.to_thread(
                populate_claim,
                template_file=(
                    ROOT / "template" / "claim_template.xlsx"
                ),
                output_file=output,
                claim_data=receipts,
                config=config
            )

            with discord.File(
                output,
                filename=filename
            ) as workbook:

                await interaction.followup.send(
                    f"Draft for {config['claimant']['name']} "
                    f"with {len(receipts)} receipts.\n"
                    "Review the workbook before submitting. "
                    "Your queue has been kept.",
                    file=workbook,
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none()
                )

    except Exception as error:

        print(
            f"Claim generation error: {error}"
        )

        await interaction.followup.send(
            f"Could not generate the claim: {str(error)[:300]}\n"
            "Your queue has been kept.",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none()
        )


bot.tree.add_command(
    receipt_group
)

bot.tree.add_command(
    claim_group
)

@profile_group.command(
    name="set",
    description="Save your reimbursement claimant details."
)
async def profile_set(
        interaction: discord.Interaction,
        name: str,
        student_id: str,
        email: str,
        phone: str,
        mailing_address: str):

    profile = {
        "name": name.strip(),
        "student_id": student_id.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "mailing_address": mailing_address.strip()
    }

    if not all(profile.values()):

        await interaction.response.send_message(
            "Please fill in every field.",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    async with queue_lock:

        save_profile(
            interaction,
            profile
        )

    await interaction.followup.send(
        "Your claimant details have been saved. "
        "Future claims will use this profile.",
        ephemeral=True
    )
    
bot.tree.add_command(
    profile_group
)

bot.run(
    os.environ["DISCORD_TOKEN"]
)