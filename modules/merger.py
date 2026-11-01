from pypdf import PdfMerger


def merge_receipts(
        receipt_files,
        output_file):

    merger = PdfMerger()

    for receipt in receipt_files:

        merger.append(receipt)

    merger.write(output_file)

    merger.close()