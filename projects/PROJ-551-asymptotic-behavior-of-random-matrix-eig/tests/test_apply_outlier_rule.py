"""
Unit test for ``code/analysis/apply_outlier_rule.py``.

The test creates a tiny ``mc_results.csv`` in a temporary directory,
runs the ``apply_outlier_rule`` function and checks that the produced
``validated_sweep_results.csv`` contains the correct boolean flag according
to the FR‑004 rule (value > bulk_edge + 0.05).
"""

import csv
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from analysis.apply_outlier_rule import apply_outlier_rule


@pytest.fixture
def small_mc_results(tmp_path: Path) -> Path:
    """
    Write a minimal ``mc_results.csv`` with three rows covering the three
    possible cases (outlier, non‑outlier, edge‑case).
    """
    csv_path = tmp_path / "mc_results.csv"
    rows = [
        {
            "run_id": "r1",
            "N": 100,
            "k": 1,
            "pattern_type": "diagonal",
            "theta": 2.5,
            "seed": 42,
            "eigenvalue_top": 2.60,
            "empirical_bulk_edge": 2.50,
            "computation_time_ms": 10.0,
        },
        {
            "run_id": "r2",
            "N": 100,
            "k": 1,
            "pattern_type": "diagonal",
            "theta": 1.0,
            "seed": 43,
            "eigenvalue_top": 2.04,
            "empirical_bulk_edge": 2.00,
            "computation_time_ms": 12.0,
        },
        {
            "run_id": "r3",
            "N": 100,
            "k": 1,
            "pattern_type": "diagonal",
            "theta": 0.9,
            "seed": 44,
            "eigenvalue_top": 2.04,
            "empirical_bulk_edge": 2.00,
            "computation_time_ms": 11.0,
        },
    ]
    # Write CSV header + rows
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


def test_apply_outlier_rule_correctness(tmp_path: Path, small_mc_results: Path):
    """
    Verify that the outlier flag follows the strict‑tolerance rule:
    eigenvalue_top > empirical_bulk_edge + 0.05
    """
    output_path = tmp_path / "validated_sweep_results.csv"

    # Run the core function (no CLI needed)
    apply_outlier_rule(small_mc_results, output_path)

    # Load the result and check flags
    df = pd.read_csv(output_path)

    # Expected flags based on the rule
    expected_flags = [
        # 2.60 > 2.50 + 0.05  → True
        True,
        # 2.04 > 2.00 + 0.05  → False (2.04 ≤ 2.05)
        False,
        # Same values as previous row → False
        False,
    ]

    assert list(df["outlier_flag"]) == expected_flags
    # Ensure all original columns are preserved
    for col in [
        "run_id",
        "N",
        "k",
        "pattern_type",
        "theta",
        "seed",
        "eigenvalue_top",
        "empirical_bulk_edge",
        "computation_time_ms",
    ]:
        assert col in df.columns