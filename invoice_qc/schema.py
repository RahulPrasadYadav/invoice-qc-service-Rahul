from __future__ import annotations
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """
    Represents one line in the invoice table.
    Example: "Product A, 2 units, 100 each, total 200"
    """
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., description="Quantity of the item")
    unit_price: float = Field(..., description="Price per unit")
    line_total: float = Field(..., description="Total amount for this line")


class Invoice(BaseModel):
    """
    Core invoice structure used across extractor, validator, API, CLI.
    """
    source_file: str = Field(..., description="Which PDF this came from")

    invoice_number: str = Field(..., description="Invoice identifier")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")

    seller_name: str = Field(..., description="Seller / supplier name")
    seller_tax_id: Optional[str] = Field(None, description="Seller tax ID or GST/VAT")

    buyer_name: str = Field(..., description="Buyer / customer name")
    buyer_tax_id: Optional[str] = Field(None, description="Buyer tax ID")

    currency: str = Field(..., description="Currency code, e.g. INR, EUR, USD")

    net_total: float = Field(..., description="Net amount before tax")
    tax_amount: float = Field(..., description="Total tax amount")
    gross_total: float = Field(..., description="Total payable amount")

    payment_terms: Optional[str] = Field(
        None, description="Payment terms, e.g. '30 days', '50% advance'"
    )

    line_items: List[LineItem] = Field(
        default_factory=list,
        description="List of invoice line items",
    )
