import re

import pdfplumber
from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def extract_pdf_text(pdf_file):

    text = ""

    try:

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    except Exception as e:
        print("PDF extraction error:", e)

    return text


def extract_scanned_text(pdf_file):

    text = ""

    try:

        pages = convert_from_path(
            pdf_file,
            poppler_path=r"C:\tools\poppler\Library\bin"
        )
    
    except Exception as e:

        print(
            f"OCR failed: {pdf_file}"
        )

        print(e)

        return ""

    for page in pages:

        text += pytesseract.image_to_string(page)

    return text


def get_text(pdf_file):

    text = extract_pdf_text(pdf_file)

    if len(text.strip()) > 200:
        return text

    print(f"OCR fallback: {pdf_file}")

    text = extract_scanned_text(pdf_file)

    return text


from dateutil import parser


def extract_date(text):

    # DigiKey places the dates below the headings.
    lines = text.splitlines()

    for index, line in enumerate(lines):

        if (
            "Order Date:" in line
            and "Invoice Date:" in line
        ):

            following = " ".join(
                lines[index + 1:index + 3]
            )

            dates = re.findall(
                r"\d{1,2}-[A-Za-z]{3}-\d{4}",
                following
            )

            if len(dates) >= 2:

                return parser.parse(
                    dates[1]
                ).strftime("%Y-%m-%d")

    patterns = [
        r"Invoice Date:\s*(\d{1,2}-[A-Za-z]{3}-\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}/\d{1,2}/\d{4})",
        r"(\d{1,2}-[A-Za-z]{3}-\d{4})"
    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if m:

            try:

                return parser.parse(
                    m.group(1)
                ).strftime("%Y-%m-%d")

            except ValueError:
                continue

    raise ValueError(
        "Receipt date not found."
    )


def extract_amount(text):

    patterns = [
        r"Total charged to credit card\s*:?\s*\$?\s*([\d,]+\.\d{2})",
        r"Order Total\s*(?:\([A-Z]{3}\))?\s*:?\s*\$?\s*([\d,]+\.\d{2})",
        r"Grand Total\s*:?\s*\$?\s*([\d,]+\.\d{2})",
        r"^\s*Total\s*:?\s*\$?\s*([\d,]+\.\d{2})\s*$"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE
        )

        if matches:

            amounts = {
                float(value.replace(",", ""))
                for value in matches
            }

            if len(amounts) != 1:

                raise ValueError(
                    "Multiple receipt totals found."
                )

            return amounts.pop()

    raise ValueError(
        "Receipt total not found."
    )

def extract_currency(text):

    currencies = set(
        re.findall(
            r"\b(CAD|USD|EUR|GBP|AUD)\b",
            text.upper()
        )
    )

    if len(currencies) == 1:
        return currencies.pop()

    raise ValueError(
        "Receipt currency missing or ambiguous."
    )

KNOWN_VENDORS = [
    "American Institute of Chemical Engineers",
    "Amazon",
    "DigiKey",
    "Mouser",
    "Home Depot",
    "BosaGrape",
    "McMaster",
    "AliExpress"
]


def extract_vendor(text):

    lower = text.lower()

    for vendor in KNOWN_VENDORS:

        if vendor.lower() in lower:
            return vendor

    lines = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    if lines:
        return lines[0][:100]

    return "Unknown Vendor"