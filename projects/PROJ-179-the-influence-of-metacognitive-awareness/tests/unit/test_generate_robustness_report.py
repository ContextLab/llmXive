"""
Unit tests for the robustness report generation (T028).

The tests create a minimal mock robustness JSON file, invoke the
``generate_robustness_report`` function with both correction methods, and
verify that the output JSON contains the expected corrected p‑values.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the function from the module we just created
from src.report.generate import generate_robustness_report

@pytest.fixture
def raw_robustness_file(tmp_path: Path):
    """Create a temporary robustness JSON with known p‑values."""
    data = {
        "visual": {"r": 0.25, "p": 0.04},
        "auditory": {"r": -0.10, "p": 0.20},
    }
    file_path = tmp_path / "robustness_analysis.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return file_path

def test_bonferroni_correction(raw_robustness_file: Path):
    """Bonferroni should multiply p‑values by 2 (capped at 1)."""
    output_path = raw_robustness_file.parent / "out_bonf.json"
    generate_robustness_report(
        correction_method="bonferroni",
        input_path=str(raw_robustness_file),
        output_path=str(output_path),
    )
    with output_path.open() as f:
        result = json.load(f)

    assert result["visual"]["p_corrected"] == pytest.approx(min(0.04 * 2, 1.0))
    assert result["auditory"]["p_corrected"] == pytest.approx(min(0.20 * 2, 1.0))
    assert result["correction_method"] == "bonferroni"
    assert result["num_comparisons"] == 2

def test_bh_correction(raw_robustness_file: Path):
    """Benjamini‑Hochberg should order p‑values and adjust accordingly."""
    output_path = raw_robustness_file.parent / "out_bh.json"
    generate_robustness_report(
        correction_method="benjamini-hochberg",
        input_path=str(raw_robustness_file),
        output_path=str(output_path),
    )
    with output_path.open() as f:
        result = json.load(f)

    # For two tests, BH correction yields the same as Bonferroni when sorted
    # because rank=1 for smallest (0.04) and rank=2 for larger (0.20)
    # => corrected p = p * m / rank
    # visual (0.04) -> 0.04 * 2 / 1 = 0.08
    # auditory (0.20) -> max(prev, 0.20 * 2 / 2) = max(0.08, 0.20) = 0.20
    assert result["visual"]["p_corrected"] == pytest.approx(0.08)
    assert result["auditory"]["p_corrected"] == pytest.approx(0.20)
    assert result["correction_method"] == "benjamini-hochberg"
    assert result["num_comparisons"] == 2