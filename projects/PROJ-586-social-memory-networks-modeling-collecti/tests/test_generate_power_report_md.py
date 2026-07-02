"""Integration test for the power‑analysis markdown generator.

The test runs the generator on a tiny synthetic dataset (created on‑the‑fly)
to verify that:
  1. The script executes without error.
  2. The expected markdown file is created.
  3. The file contains the required sections.
"""
import csv
import os
import tempfile
from pathlib import Path

import pandas as pd

from generate_power_report_md import main as generate_report

def _write_dummy_results(path: Path, condition: str, n: int = 10) -> None:
    """Write a minimal but valid results CSV."""
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "game_id",
                "specialization_index",
                "retrieval_efficiency",
                "context_condition",
                "agent_count",
            ],
        )
        writer.writeheader()
        for i in range(n):
            writer.writerow(
                {
                    "game_id": i,
                    "specialization_index": 0.5 + 0.1 * (i % 3),
                    "retrieval_efficiency": 0.6 + 0.05 * (i % 2),
                    "context_condition": condition,
                    "agent_count": 5,
                }
            )

def test_generate_power_report_creates_markdown(tmp_path: Path) -> None:
    # Create temporary result CSVs.
    full_csv = tmp_path / "results_full.csv"
    limited_csv = tmp_path / "results_limited.csv"
    _write_dummy_results(full_csv, "full", n=30)
    _write_dummy_results(limited_csv, "limited", n=30)

    # Destination markdown file.
    output_md = tmp_path / "power_analysis_report.md"

    # Run the generator.
    exit_code = generate_report(
        [
            "--full-csv",
            str(full_csv),
            "--limited-csv",
            str(limited_csv),
            "--output",
            str(output_md),
        ]
    )
    assert exit_code == 0
    assert output_md.is_file()

    # Basic sanity checks on content.
    content = output_md.read_text(encoding="utf-8")
    assert "# Power Analysis Report" in content
    assert "## Two‑Way ANOVA" in content
    assert "## Power Analysis" in content
    # Ensure at least one metric table appears.
    assert "Metric: Specialization Index" in content or "Metric: Retrieval Efficiency" in content