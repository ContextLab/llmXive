"""
Unit tests for src/pipeline/compute_complexity.py

The tests verify that:
  * The script creates the expected CSV file.
  * The CSV contains the same clip_ids as the descriptor file.
  * The correlation file is produced and contains numeric values.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.compute_complexity import compute_complexity, _derive_subgoal_count

@pytest.fixture
def descriptors_path(tmp_path):
    # Re‑use the real descriptors file shipped with the repository.
    # Copy it into the temporary directory to avoid side‑effects.
    src = Path(__file__).resolve().parents[2] / "data" / "descriptors_subset.csv"
    dst = tmp_path / "descriptors_subset.csv"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dst

def test_derive_subgoal_count():
    # Basic sanity checks for the deterministic mapping.
    assert _derive_subgoal_count(0.0) == 1
    assert _derive_subgoal_count(0.1) == 2
    assert _derive_subgoal_count(0.9) == 10  # capped at 10

def test_compute_complexity_creates_files(tmp_path, descriptors_path):
    csv_out = tmp_path / "complexity.csv"
    corr_out = tmp_path / "correlation.txt"

    compute_complexity(descriptors_path, csv_out, corr_out)

    # Verify CSV exists and has expected columns.
    assert csv_out.is_file()
    df_c = pd.read_csv(csv_out)
    assert list(df_c.columns) == ["clip_id", "subgoal_count"]
    assert len(df_c) == 50  # matches the descriptor file

    # Verify clip_id alignment with descriptor file.
    df_desc = pd.read_csv(descriptors_path)
    assert set(df_c["clip_id"]) == set(df_desc["clip_id"])

    # Verify correlation file format.
    assert corr_out.is_file()
    content = corr_out.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    assert any(line.startswith("r =") for line in lines)
    assert any(line.startswith("p =") for line in lines)

# Run the test with a realistic timeout to ensure the script finishes
# quickly on the CI runner.
@pytest.mark.timeout(30)
def test_full_pipeline_execution(tmp_path, descriptors_path):
    # Run the full pipeline and check that it exits without error.
    csv_out = tmp_path / "complexity.csv"
    corr_out = tmp_path / "correlation.txt"
    compute_complexity(descriptors_path, csv_out, corr_out)
    # Ensure the correlation meets the verification thresholds.
    r_line = next(l for l in corr_out.read_text().splitlines() if l.startswith("r ="))
    p_line = next(l for l in corr_out.read_text().splitlines() if l.startswith("p ="))
    r = float(r_line.split("=")[1])
    p = float(p_line.split("=")[1])
    assert r > 0.5
    assert p < 0.05