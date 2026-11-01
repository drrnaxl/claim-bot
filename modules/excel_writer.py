from openpyxl import load_workbook


def populate_claim(
        template_file,
        output_file,
        claim_data,
        project_name):

    wb = load_workbook(
        template_file
    )

    ws = wb["Claim Form"]

    START_ROW = 24

    total = 0

    for idx, item in enumerate(claim_data):

        row = START_ROW + idx

        ws[f"A{row}"] = idx + 1

        ws[f"B{row}"] = item["date"]

        ws[f"C{row}"] = item["vendor"]

        ws[f"D{row}"] = item["amount"]

        ws[f"E{row}"] = "CAD"

        ws[f"F{row}"] = item["amount"]

        ws[f"G{row}"] = item["category"]

        ws[f"H{row}"] = project_name

        ws[f"J{row}"] = item["purpose"]

        total += item["amount"]

    wb.save(output_file)

    return total