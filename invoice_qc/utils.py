from __future__ import annotations
import re
from datetime import date
from typing import Optional

from dateutil import parser as date_parser


def parse_date_maybe(value: str) -> Optional[date]:
    """
    Try to parse a date string. Return None if it fails.
    Accepts many formats: 2024-01-10, 10/01/2024, etc.
    """
    value = value.strip()
    if not value:
        return None
    try:
        dt = date_parser.parse(value, dayfirst=True)
        return dt.date()
    except Exception:
        return None


def parse_amount_maybe(value: str) -> Optional[float]:
    """
    Clean and parse an amount like '₹ 1,234.50' or '1 234,50'.
    Returns None if parsing fails.
    """
    if value is None:
        return None
    # remove currency symbols and spaces
    cleaned = re.sub(r"[^\d,.\-]", "", value).strip()
    if not cleaned:
        return None

    # handle formats like "1.234,50" or "1,234.50"
    # naive approach: if both ',' and '.' exist, assume ',' is thousand or decimal
    if "," in cleaned and "." in cleaned:
        # assume comma is thousand separator, remove commas
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        # assume comma as decimal separator
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None
