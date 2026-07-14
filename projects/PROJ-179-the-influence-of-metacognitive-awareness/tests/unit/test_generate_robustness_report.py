"""
Unit tests for the robustness report generation (T028).
The tests verify that the multiple‑comparison correction is applied correctly
and that the output file is created with the expected structure.
"""

import json
import os
from pathlib import Path

import pytest

from src.report.generate import generate_robustness_report

@pytest.fixture
def tmp_results_file(tmp_path: Path) -> Path:
    """
    Create a temporary robustness_analysis.json file with known p‑values.
    """
    data = [
        {"comparison": "visual", "p_value": 0.04},
        {"comparison": "auditory", "p_value": 0.06},
        {"comparison": "combined", "p_value": 0.01},
    ]
    file_path = tmp_path / "robustness_analysis.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path

def test_bonferroni_correction(tmp_results_file: Path):
    # Run the report generator using Bonferroni correction
    generate_robustness_report(results_path=tmp_results_file, method="bonferroni")

    # Load the file back and verify corrected values
    with tmp_results_file.open("r", encoding="utf-8") as f:
        corrected = json.load(f)

    assert len(corrected) == 3
    # Bonferroni multiplies each p by the number of tests (3)
    expected = [min(p * 3, 1.0) for p in [0.04, 0.06, 0.01]]
    for entry, exp in zip(corrected, expected):
        assert entry["correction_method"] == "bonferroni"
        assert pytest.approx(entry["p_value_corrected"], rel=1e-3) == exp

def test_fdr_bh_correction(tmp_results_file: Path):
    # Run the report generator using Benjamini‑Hochberg (fdr_bh)
    generate_robustness_report(results_path=tmp_results_file, method="fdr_bh")

    with tmp_results_file.open("r", encoding="utf-8") as f:
        corrected = json.load(f)

    # Verify that the corrected p‑values are monotonic and ≤ 1
    p_vals = [entry["p_value_corrected"] for entry in corrected]
    assert all(0.0 <= p <= 1.0 for p in p_vals)
    assert p_vals == sorted(p_vals)  # FDR ensures non‑decreasing order
    for entry in corrected:
        assert entry["correction_method"] == "fdr_bh"

def test_empty_input(tmp_path: Path):
    # Create an empty JSON list file
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]", encoding="utf-8")

    # Should not raise and should leave an empty list
    generate_robustness_report(results_path=empty_file, method="bonferroni")
    with empty_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == []