from __future__ import annotations
from typing import List, Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from .schema import Invoice
from .validator import validate_invoices

app = FastAPI(
    title="Invoice QC Service",
    version="0.1.0",
    description="Simple Invoice Extraction & Quality Control API",
)


class ValidationResponse(BaseModel):
    summary: Dict[str, Any]
    results: List[Dict[str, Any]]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate-json", response_model=ValidationResponse)
def validate_json(invoices: List[Invoice]):
    """
    Accepts a list of invoice JSON objects and returns validation summary + per-invoice results.
    """
    result = validate_invoices(invoices)
    return ValidationResponse(**result)
