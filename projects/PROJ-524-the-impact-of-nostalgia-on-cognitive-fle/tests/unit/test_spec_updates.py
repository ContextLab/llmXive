"""
Unit tests for specification updates (Task T001).

These tests verify that the specification file has been updated to:
1. Use Hedges' g for effect size calculation (FR‑004).
2. Use the corrected borderline p‑value band [0.020, 0.030] (FR‑005).
3. Include a rationale paragraph that references the plan's "kick‑back notes".
"""

import pathlib

SPEC_PATH = pathlib.Path(__file__).resolve().parents[2] / "specs" / "001-nostalgia-cognitive-flexibility" / "spec.md"

def test_hedges_g_present():
    """Check that Hedges' g wording appears in the spec."""
    content = SPEC_PATH.read_text(encoding="utf-8")
    assert "Hedges' g" in content, "Hedges' g not found in spec.md"

def test_borderline_band_present():
    """Check that the corrected p‑value band [0.020, 0.030] appears in the spec."""
    content = SPEC_PATH.read_text(encoding="utf-8")
    assert "[0.020, 0.030]" in content, "Corrected borderline band not found in spec.md"

def test_kickback_rationale_present():
    """Check that the rationale paragraph referencing 'kick‑back notes' is present."""
    content = SPEC_PATH.read_text(encoding="utf-8")
    assert "kick‑back notes" in content, "Rationale referencing 'kick‑back notes' not found in spec.md"