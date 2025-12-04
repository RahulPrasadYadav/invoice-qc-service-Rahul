from __future__ import annotations
from collections import Counter
from typing import List, Dict, Any

from .schema import Invoice


EPSILON = 0.05  # tolerance for float comparisons
ALLOWED_CURRENCIES = {"INR", "EUR", "USD", "GBP"}


def _check_completeness(invoice: Invoice) -> list[str]:
    errors: list[str] = []

    if not invoice.invoice_number.strip():
        errors.append("missing_field: invoice_number")

    if not invoice.seller_name.strip():
        errors.append("missing_field: seller_name")

    if not invoice.buyer_name.strip():
        errors.append("missing_field: buyer_name")

    if invoice.currency not in ALLOWED_CURRENCIES:
        errors.append(f"invalid_currency: {invoice.currency}")

    # basic date sanity check
    if invoice.invoice_date.year < 2000:
        errors.append("invalid_date: invoice_date_too_old")

    if invoice.due_date and invoice.due_date < invoice.invoice_date:
        errors.append("business_rule_failed: due_date_before_invoice_date")

    return errors


def _check_business_rules(invoice: Invoice) -> list[str]:
    errors: list[str] = []

    # gross ≈ net + tax
    if abs((invoice.net_total + invoice.tax_amount) - invoice.gross_total) > EPSILON:
        errors.append("business_rule_failed: totals_mismatch_net_plus_tax_ne_gross")

    # totals non-negative
    if invoice.net_total < 0 or invoice.tax_amount < 0 or invoice.gross_total < 0:
        errors.append("anomaly: negative_totals")

    # if line items exist, check their sum vs net_total
    if invoice.line_items:
        lines_sum = sum(li.line_total for li in invoice.line_items)
        if abs(lines_sum - invoice.net_total) > EPSILON:
            errors.append("business_rule_failed: line_items_sum_ne_net_total")

    return errors


def _check_duplicates(invoices: List[Invoice]) -> Dict[str, List[int]]:
    """
    Return dict: key = invoice key string,
                 value = list of indices (positions in original list) that are duplicates.
    """
    key_to_indices: dict[str, list[int]] = {}
    for idx, inv in enumerate(invoices):
        key = f"{inv.invoice_number}::{inv.seller_name}::{inv.invoice_date.isoformat()}"
        key_to_indices.setdefault(key, []).append(idx)

    # only return those with more than 1 index
    return {k: v for k, v in key_to_indices.items() if len(v) > 1}


def validate_invoices(invoices: List[Invoice]) -> Dict[str, Any]:
    """
    Main validation entrypoint.

    Returns:
    {
      "summary": {...},
      "results": [
        {
          "invoice_id": "...",
          "source_file": "...",
          "is_valid": bool,
          "errors": [...]
        },
        ...
      ]
    }
    """
    results: list[dict[str, Any]] = []
    error_counter: Counter[str] = Counter()

    # per-invoice checks
    for inv in invoices:
        inv_errors: list[str] = []
        inv_errors.extend(_check_completeness(inv))
        inv_errors.extend(_check_business_rules(inv))

        for e in inv_errors:
            error_counter[e] += 1

        results.append(
            {
                "invoice_id": inv.invoice_number,
                "source_file": inv.source_file,
                "is_valid": len(inv_errors) == 0,
                "errors": inv_errors,
            }
        )

    # duplicate detection
    duplicates = _check_duplicates(invoices)
    for key, indices in duplicates.items():
        for idx in indices:
            results[idx]["errors"].append("anomaly: duplicate_invoice")
            error_counter["anomaly: duplicate_invoice"] += 1

    total_invoices = len(invoices)
    invalid_invoices = sum(1 for r in results if not r["is_valid"])
    valid_invoices = total_invoices - invalid_invoices

    summary = {
        "total_invoices": total_invoices,
        "valid_invoices": valid_invoices,
        "invalid_invoices": invalid_invoices,
        "error_counts": dict(error_counter),
    }

    return {
        "summary": summary,
        "results": results,
    }
