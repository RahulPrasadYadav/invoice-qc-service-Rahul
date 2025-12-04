from __future__ import annotations
import re
from pathlib import Path
from typing import List

import pdfplumber

from .schema import Invoice, LineItem
from .utils import parse_date_maybe, parse_amount_maybe


# Some basic label patterns - you can expand these after seeing actual PDFs
INVOICE_NO_PATTERNS = [
    r"Invoice\s*(No\.?|Number|#)\s*[:\-]\s*(\S+)",
    r"Inv\s*#\s*[:\-]\s*(\S+)",
]

INVOICE_DATE_PATTERNS = [
    r"Invoice\s*Date\s*[:\-]\s*([A-Za-z0-9/\-\. ]+)",
    r"Date\s*[:\-]\s*([A-Za-z0-9/\-\. ]+)",
]

DUE_DATE_PATTERNS = [
    r"Due\s*Date\s*[:\-]\s*([A-Za-z0-9/\-\. ]+)",
]

SELLER_PATTERNS = [
    r"Seller\s*[:\-]\s*(.+)",
    r"Supplier\s*[:\-]\s*(.+)",
]

BUYER_PATTERNS = [
    r"Buyer\s*[:\-]\s*(.+)",
    r"Customer\s*[:\-]\s*(.+)",
]

CURRENCY_CODES = ["INR", "EUR", "USD", "GBP"]


def _extract_text_from_pdf(path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _search_first(patterns: list[str], text: str, group: int = 1) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(group).strip()
    return None


def _guess_currency(text: str) -> str:
    for code in CURRENCY_CODES:
        if re.search(rf"\b{code}\b", text):
            return code
    # very naive fallback: INR
    return "INR"


def _extract_totals(text: str) -> tuple[float, float, float]:
    """
    Very simple heuristic:
    - look for lines containing 'Net', 'Tax', 'Total'
    - parse last number on those lines
    """
    net = 0.0
    tax = 0.0
    gross = 0.0

    for line in text.splitlines():
        lower = line.lower()
        if "net" in lower and "total" in lower or "subtotal" in lower:
            amt = parse_amount_maybe(line)
            if amt is not None:
                net = amt
        elif "tax" in lower or "vat" in lower or "gst" in lower:
            amt = parse_amount_maybe(line)
            if amt is not None:
                tax = amt
        elif ("total" in lower or "grand total" in lower) and "net" not in lower:
            amt = parse_amount_maybe(line)
            if amt is not None:
                gross = amt

    # fallback: if gross is zero but net>0 and tax>=0, compute
    if gross == 0.0 and (net > 0 or tax > 0):
        gross = net + tax

    return net, tax, gross


def _extract_line_items(text: str) -> list[LineItem]:
    """
    For starter version, we keep this VERY simple:
    - If you don't have time to parse tables, return empty list.
    - Later you can extend this to detect table regions.
    """
    return []  # keeping line items optional for now


def parse_invoice_from_text(text: str, source_file: str) -> Invoice:
    """
    Convert raw text into an Invoice object using simple regex-based heuristics.
    Missing fields will raise validation error if required.
    """
    # invoice number
    invoice_number = _search_first(INVOICE_NO_PATTERNS, text) or "UNKNOWN"

    # invoice date
    raw_inv_date = _search_first(INVOICE_DATE_PATTERNS, text) or ""
    invoice_date = parse_date_maybe(raw_inv_date) or parse_date_maybe("2000-01-01")

    # due date (optional)
    raw_due_date = _search_first(DUE_DATE_PATTERNS, text) or ""
    due_date = parse_date_maybe(raw_due_date)

    # parties
    seller_name = _search_first(SELLER_PATTERNS, text) or "UNKNOWN_SELLER"
    buyer_name = _search_first(BUYER_PATTERNS, text) or "UNKNOWN_BUYER"

    # tax IDs - for now, naive detection of GST/VAT-like pattern
    seller_tax_id = None
    buyer_tax_id = None

    tax_id_match = re.search(r"(GSTIN|VAT|Tax\s*ID)\s*[:\-]\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
    if tax_id_match:
        seller_tax_id = tax_id_match.group(2).strip()

    # currency and totals
    currency = _guess_currency(text)
    net_total, tax_amount, gross_total = _extract_totals(text)

    # payment terms
    payment_terms_match = re.search(r"Payment\s*Terms\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    payment_terms = payment_terms_match.group(1).strip() if payment_terms_match else None

    line_items = _extract_line_items(text)

    return Invoice(
        source_file=source_file,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        seller_name=seller_name,
        seller_tax_id=seller_tax_id,
        buyer_name=buyer_name,
        buyer_tax_id=buyer_tax_id,
        currency=currency,
        net_total=net_total,
        tax_amount=tax_amount,
        gross_total=gross_total,
        payment_terms=payment_terms,
        line_items=line_items,
    )


def extract_from_dir(pdf_dir: str | Path) -> List[Invoice]:
    """
    Scan a folder, read all PDFs, and return a list of Invoice objects.
    """
    pdf_dir = Path(pdf_dir)
    invoices: list[Invoice] = []

    for pdf_path in pdf_dir.glob("*.pdf"):
        text = _extract_text_from_pdf(pdf_path)
        inv = parse_invoice_from_text(text, source_file=pdf_path.name)
        invoices.append(inv)

    return invoices
