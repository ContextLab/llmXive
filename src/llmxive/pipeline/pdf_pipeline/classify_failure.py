"""Classify a PDF audit failure into one of FR-018's four classes.

NO LLM CALLS (spec 010 FR-013).
"""

from __future__ import annotations


_KIND_TO_DEFAULT_CLASS = {
    "literal_command_text": "source_fixable",
    "non_square_bracket_cite": "source_fixable",
    "non_canonical_authorblock": "source_fixable",
    "off_spec_figure_width": "source_fixable",
    "section_number_gap": "unsupported_construct",
    "audit_tool_crash": "audit_tool_crash",
}


def classify(kind: str, evidence: str, *, source_available: bool) -> str:
    """Return one of {source_fixable, unsupported_construct, source_missing, audit_tool_crash}."""
    if kind == "audit_tool_crash":
        return "audit_tool_crash"
    if not source_available:
        return "source_missing"
    return _KIND_TO_DEFAULT_CLASS.get(kind, "unsupported_construct")


__all__ = ["classify"]
