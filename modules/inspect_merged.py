# inspect_merged.py

from openpyxl import load_workbook

wb = load_workbook(
    "template/claim_template.xlsx"
)

ws = wb["Claim Form"]

for merged in ws.merged_cells.ranges:
    print(merged)