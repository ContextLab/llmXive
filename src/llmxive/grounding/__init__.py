"""Full-text claim-grounding service (spec 015 / #239 / F-19 v2)."""

from .full_text import RetrievedDoc, extract_pdf_text, html_to_text

__all__ = ["RetrievedDoc", "extract_pdf_text", "html_to_text"]
