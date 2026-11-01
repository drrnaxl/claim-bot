from pathlib import Path
from collections import defaultdict
from datetime import datetime
import yaml
import os

from modules.extractor import *
from modules.categorizer import *
from modules.excel_writer import *
from modules.receipt_db import *

os.chdir(
    Path(__file__).resolve().parent
)


def main():

    Path("output").mkdir(
        exist_ok=True
    )

    with open(
        "config.yaml",
        "r"
    ) as f:

        config = yaml.safe_load(f)
        print(config)

    claims = defaultdict(list)

    for pdf in Path(
        "receipts"
    ).glob("**/*.pdf"):

        print(
            f"Processing: {pdf.name}"
        )

        text = get_text(pdf)

        vendor = extract_vendor(text)

        amount = extract_amount(text)

        date = extract_date(text)

        currency = extract_currency(text)

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
                    f"Missing {currency} exchange rate "
                    f"for {pdf.name}. "
                    "Add it to config.yaml."
                )

            exchange_rate = float(
                exchange_rate
            )

            import math

            if (
                not math.isfinite(exchange_rate)
                or exchange_rate <= 0
            ):

                raise ValueError(
                    "Exchange rate must be "
                    "a positive finite number."
                )

        if already_claimed(
            vendor,
            amount,
            date
        ):

            print(
                f"Skipping duplicate: {vendor}"
            )

            continue

        category, purpose = (
            classify_expense(text)
        )

        month = date[:7]

        claims[month].append({

            "vendor": vendor,

            "date": date,

            "amount": amount,

            "category": category,

            "purpose": purpose,

            "currency": currency,

            "exchange_rate": exchange_rate,
        })

        print(
            f"✅ {vendor} | "
            f"${amount:.2f} | "
            f"{date}"
        )

    receipts = [
        receipt
        for monthly_receipts in claims.values()
        for receipt in monthly_receipts
    ]

    receipts.sort(
        key=lambda receipt: receipt["date"]
    )

    if not receipts:

        print("No new receipts to process.")

        return

    output_file = (
        "output/Claim_All_"
        f"{datetime.now():%Y%m%d_%H%M%S_%f}.xlsx"
    )

    populate_claim(
        template_file=
        "template/claim_template.xlsx",

        output_file=
        output_file,

        claim_data=
        receipts,

        config=
        config
    )

    for receipt in receipts:

        mark_claimed(
            receipt["vendor"],
            receipt["amount"],
            receipt["date"]
        )

    print(
        f"Generated {output_file}"
    )


if __name__ == "__main__":
    main()