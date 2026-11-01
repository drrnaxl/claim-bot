# debug_pdf.py

import pdfplumber

with pdfplumber.open(
    "receipts/Bosagrape_Aug142026.pdf"
) as pdf:

    print("Pages:", len(pdf.pages))

    for i, page in enumerate(pdf.pages):

        text = page.extract_text()

        print("=" * 50)
        print("PAGE", i + 1)
        print("=" * 50)

        print(repr(text))