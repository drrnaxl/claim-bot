from modules.excel_writer import populate_claim

populate_claim(
    template_file=
    "template/claim_template.xlsx",

    output_file=
    "output/test_claim.xlsx",

    claim_data=[
        {
            "date": "2026-08-14",
            "vendor": "BosaGrape Winery Supplies Ltd.",
            "amount": 229.56,
            "category": "Prototype Project",
            "purpose": (
                "Fermentation supplies "
                "and cleaning materials"
            ),
        }
    ],

    project_name="ReUp"
)

print("Done")