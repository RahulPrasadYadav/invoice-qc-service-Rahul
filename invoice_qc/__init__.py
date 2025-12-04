"""
Invoice QC Service package.

Modules:
- schema: Pydantic models for Invoice & LineItem
- extractor: PDF -> Invoice objects
- validator: Validation rules and summary
- cli: CLI interface (extract/validate/full-run)
- api: FastAPI app
"""
__all__ = ["schema", "extractor", "validator"]
