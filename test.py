from openpyxl import load_workbook

wb = load_workbook(
    "template/claim_template.xlsx"
)

ws = wb["Claim Form"]

for row in range(1,50):
    for col in range(1,15):
        value = ws.cell(row,col).value

        if value:
            print(row,col,value)
