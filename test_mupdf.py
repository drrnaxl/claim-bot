# test_mupdf.py

import fitz

doc = fitz.open(
    "receipts/Bosagrape_Aug142026.pdf"
)

text = ""

for page in doc:
    text += page.get_text()

print("Length:", len(text))
print(text[:2000])