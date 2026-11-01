import json
import hashlib
from pathlib import Path

DB_FILE = "expense_db.json"


def load_db():

    if not Path(DB_FILE).exists():

        return {
            "claimed_receipts": []
        }

    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def receipt_hash(vendor, amount, date):

    key = f"{vendor}|{amount}|{date}"

    return hashlib.sha256(
        key.encode()
    ).hexdigest()


def already_claimed(vendor, amount, date):

    db = load_db()

    h = receipt_hash(
        vendor,
        amount,
        date
    )

    return h in db["claimed_receipts"]


def mark_claimed(vendor, amount, date):

    db = load_db()

    h = receipt_hash(
        vendor,
        amount,
        date
    )

    if h not in db["claimed_receipts"]:
        db["claimed_receipts"].append(h)

    save_db(db)