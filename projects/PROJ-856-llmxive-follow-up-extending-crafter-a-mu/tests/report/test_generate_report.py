"""
Test suite for the ``src.report.generate_report`` module.

The test runs the report generator on a minimal synthetic validation
dataset and checks that the expected markdown sections appear in the
produced ``outputs/report.md`` file.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.report.generate_report import main as generate_report_main

@pytest.fixture
def synthetic_validation(tmp_path: Path):
    """Create a tiny validation file with both interfaces represented."""
    validation_dir = tmp_path / "validation"
    validation_dir.mkdir(parents=True)
    records = [
        {
            "participant_id": "p1",
            "interface": "structured",
            "time_to_success_ms": 1200,
            "iteration_count": 3,
            "vector_match": True,
            "semantic_pass": True,
        },
        {
            "participant_id": "p1",
            "interface": "chat",
            "time_to_success_ms": 1500,
            "iteration_count": 4,
            "vector_match": True,
            "semantic_pass": True,
        },
        {
            "participant_id": "p2",
            "interface": "structured",
            "time_to_success_ms": 1100,
            "iteration_count": 2,
            "vector_match": False,
            "semantic_pass": True,
        },
        {
            "participant_id": "p2",
            "interface": "chat",
            "time_to_success_ms": 1400,
            "iteration_count": 5,
            "vector_match": True,
            "semantic_pass": False,
        },
    ]
    validation_file = validation_dir / "semantic_validation.jsonl"
    with validation_file.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    return validation_dir

@pytest.fixture
def empty_analysis_dir(tmp_path: Path):
    """Create an empty analysis directory (no analysis results)."""
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir(parents=True)
    return analysis_dir

def test_generate_report_creates_markdown(tmp_path, synthetic_validation, empty_analysis_dir):
    # Override the default paths to point at the temporary locations
    output_path = tmp_path / "outputs" / "report.md"
    output_path.parent.mkdir(parents=True)

    # Run the generator with our temporary dirs
    import sys
    sys.argv = [
        "generate_report.py",
        "--validation-dir",
        str(synthetic_validation),
        "--analysis-dir",
        str(empty_analysis_dir),
        "--output-path",
        str(output_path),
    ]
    exit_code = generate_report_main()
    assert exit_code == 0

    # Verify the file exists
    assert output_path.is_file()

    content = output_path.read_text(encoding="utf-8")

    # Required sections (regex‑style checks)
    for keyword in ["Mean", "Median", "Wilcoxon statistic", "p‑value",
                    "vector‑match success", "semantic‑similarity success"]:
        assert keyword.lower() in content.lower()

    # Ensure the success‑rate table contains both interfaces
    assert "| Structured |" in content
    assert "| Chat |" in content