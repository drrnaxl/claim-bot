from pathlib import Path
from collections import defaultdict
from datetime import datetime

from modules.extractor import *
from modules.categorizer import *
from modules.excel_writer import *
from modules.receipt_db import *

CLAIMS = defaultdict(list)

for pdf in Path("receipts").glob(
        "**/*.pdf"):

    text = get_text(pdf)

    vendor = extract_vendor(text)

    amount = extract_amount(text)

    date = extract_date(text)

    if already_claimed(
            vendor,
            amount,
            date):

        print(
            f"Skipping duplicate: {vendor}"
        )

        continue

    category, purpose = (
        classify_expense(text)
    )

    month = date[:7]

    CLAIMS[month].append({

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

for month, receipts in CLAIMS.items():

    populate_claim(

        template_file=
        "template/claim_template.xlsx",

        output_file=
        f"output/Claim_{month}.xlsx",

        claim_data=
        receipts,

        project_name=
        "ReUp"
    )

    print(
        f"Generated Claim_{month}.xlsx"
    )