RULES = {

    "yeast": (
        "Prototype Project",
        "Fermentation consumables for prototype testing"
    ),

    "star san": (
        "Prototype Project",
        "Sanitation supplies for fermentation development"
    ),

    "pbw": (
        "Prototype Project",
        "Cleaning supplies for prototype maintenance"
    ),

    "sensor": (
        "Prototype Project",
        "Electronic sensing components for prototype development"
    ),

    "arduino": (
        "Prototype Project",
        "Embedded control hardware"
    ),

    "tubing": (
        "Prototype Project",
        "Fabrication materials and plumbing components"
    ),
}


def classify_expense(text):

    lower = text.lower()

    category = "Prototype Project"

    purposes = []

    for keyword, result in RULES.items():

        if keyword in lower:

            purposes.append(
                result[1]
            )

    if not purposes:

        purposes.append(
            "Prototype materials and consumables for project development"
        )

    return (
        category,
        "; ".join(
            sorted(
                set(purposes)
            )
        )
    )