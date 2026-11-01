import re

import pdfplumber
from pdf2image import convert_from_path
import pytesseract


def extract_pdf_text(pdf_file):

    text = ""

    try:

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    except:

        pass

    return text


def extract_scanned_text(pdf_file):

    text = ""

    pages = convert_from_path(pdf_file)

    for page in pages:

        text += pytesseract.image_to_string(page)

    return text


def get_text(pdf_file):

    text = extract_pdf_text(pdf_file)

    if len(text.strip()) < 50:

        text = extract_scanned_text(pdf_file)

    return text


def extract_date(text):

    patterns = [
        r"(\d{1,2}/\d{1,2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2})"
    ]

    for p in patterns:

        m = re.search(p, text)

        if m:
            return m.group(1)

    return ""


def extract_amount(text):

    amounts = []

    patterns = [
        r"Total\s+\$?([0-9,]+\.[0-9]{2})",
        r"CAD\$([0-9,]+\.[0-9]{2})"
    ]

    for pattern in patterns:

        for m in re.finditer(
                pattern,
                text,
                re.IGNORECASE):

            try:

                amounts.append(
                    float(
                        m.group(1)
                        .replace(",", "")
                    )
                )

            except:
                pass

    if amounts:
        return max(amounts)

    return 0


def extract_vendor(text):

    lines = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    if lines:
        return lines[0]

    return "Unknown Vendor"