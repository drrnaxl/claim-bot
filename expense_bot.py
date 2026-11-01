from pathlib import Path
from collections import defaultdict
import yaml

from modules.extractor import *
from modules.categorizer import *
from modules.excel_writer import *
from modules.receipt_db import *

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

            "purpose": purpose
        })

        mark_claimed(
            vendor,
            amount,
            date
        )

        print(
            f"✅ {vendor} | "
            f"${amount:.2f} | "
            f"{date}"
        )

    for month, receipts in claims.items():

        populate_claim(

            template_file=
            "template/claim_template.xlsx",

            output_file=
            f"output/Claim_{month}.xlsx",

            claim_data=
            receipts,

            config=
            config
        )

        print(
            f"✅ Generated "
            f"Claim_{month}.xlsx"
        )

if __name__ == "__main__":
    main()