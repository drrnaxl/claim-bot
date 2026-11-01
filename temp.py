from modules.extractor import *

text = get_text(
    "receipts/Bosagrape_Aug142026.pdf"
)

print(
    "Vendor:",
    extract_vendor(text)
)

print(
    "Amount:",
    extract_amount(text)
)

print(
    "Date:",
    extract_date(text)
)