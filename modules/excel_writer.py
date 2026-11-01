from openpyxl import load_workbook


def find_expense_table(ws):
    """
    Find the first expense entry row.

    On the current UBC template:
    Row 13 = headers
    Row 14 = first receipt line
    """

    for row in range(1, 50):

        no_header = ws.cell(row=row, column=1).value
        date_header = ws.cell(row=row, column=2).value

        if (
            str(no_header).strip().upper() == "NO."
            and
            "PURCHASED" in str(date_header).upper()
        ):
            return row + 1

    raise RuntimeError(
        "Expense table header not found."
    )


def populate_claim(
        template_file,
        output_file,
        claim_data,
        project_name):

    wb = load_workbook(template_file)

    ws = wb["Claim Form"]

    start_row = find_expense_table(ws)

    max_receipts = 10

    if len(claim_data) > max_receipts:

        raise ValueError(
            f"Template only supports "
            f"{max_receipts} receipts."
        )

    total = 0

    for index, item in enumerate(claim_data):

        row = start_row + index

        amount = float(
            item.get("amount", 0)
        )

        # A = No.
        ws[f"A{row}"] = index + 1

        # B = Purchased Date
        ws[f"B{row}"] = item.get(
            "date",
            ""
        )

        # D = Vendor/Supplier
        ws[f"D{row}"] = item.get(
            "vendor",
            ""
        )

        # E = Receipt Amount
        ws[f"E{row}"] = amount

        # F = Exchange Rate
        ws[f"F{row}"] = 1

        # G = Amount in Canadian
        ws[f"G{row}"] = amount

        # H = Expense Category
        ws[f"H{row}"] = item.get(
            "category",
            ""
        )

        # I = Project Name
        ws[f"I{row}"] = project_name

        # J = Missing Receipt
        ws[f"J{row}"] = ""

        # K = Purpose & Note
        ws[f"K{row}"] = item.get(
            "purpose",
            ""
        )

        total += amount

    wb.save(output_file)

    return total