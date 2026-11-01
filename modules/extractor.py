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

    patterns = [
        r"(\d{1,2}/\d{1,2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2})"
    ]

    for pattern in patterns:

        m = re.search(pattern, text)

        if m:

            try:

                dt = parser.parse(
                    m.group(1)
                )

                return dt.strftime(
                    "%Y-%m-%d"
                )

            except Exception:
                pass

    return ""


def extract_amount(text):

    import re

    numbers = re.findall(
        r"([0-9]+\.[0-9]{2})",
        text
    )

    values = []

    for n in numbers:

        try:
            values.append(float(n))
        except:
            pass

    if not values:
        return 0.0

    # total is usually the largest value
    return max(values)


KNOWN_VENDORS = [
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