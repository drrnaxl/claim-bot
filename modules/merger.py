from pypdf import PdfWriter


def merge_receipts(
        receipt_files,
        output_file):

    merger = PdfWriter()

    try:

        for receipt in receipt_files:

            merger.append(receipt)

        merger.write(output_file)

    finally:

        merger.close()