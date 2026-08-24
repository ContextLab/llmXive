"""Tests for the dynamic sample size reporting added in T074."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the functions from the module under test
from code.report.generate import (
    format_sample_info,
    generate_report,
    load_qc_summary,
    load_validation_status,
)


@pytest.fixture
def tmp_files(tmp_path: Path):
    """Create temporary QC summary and validation status files."""
    # Create a minimal QC summary CSV
    qc_csv_path = tmp_path / "qc_summary.csv"
    df = pd.DataFrame(
        {
            "subject_id": ["sub-01", "sub-02", "sub-03", "sub-04"],
            "included": [True, False, True, False],
        }
    )
    df.to_csv(qc_csv_path, index=False)

    # Create a matching validation_status.json
    validation_path = tmp_path / "validation_status.json"
    validation_content = {
        "status": "passed",
        "subjects_processed": 2,
        "subjects_excluded": 2,
    }
    validation_path.write_text(json.dumps(validation_content), encoding="utf-8")

    # Simple Markdown template with the placeholder
    template_path = tmp_path / "template.md"
    template_path.write_text(
        "# Study Report\\n\\n{{SAMPLE_INFO}}\\n\\nOther sections...", encoding="utf-8"
    )

    # Output path for the generated report
    output_path = tmp_path / "summary.md"

    return {
        "qc_csv": qc_csv_path,
        "validation_json": validation_path,
        "template": template_path,
        "output": output_path,
    }


def test_load_validation_status(tmp_files):
    data = load_validation_status(tmp_files["validation_json"])
    assert data["status"] == "passed"
    assert data["subjects_processed"] == 2
    assert data["subjects_excluded"] == 2


def test_load_qc_summary(tmp_files):
    df = load_qc_summary(tmp_files["qc_csv"])
    assert len(df) == 4
    assert list(df["included"]) == [True, False, True, False]


def test_format_sample_info(tmp_files):
    info = format_sample_info(
        validation_path=tmp_files["validation_json"],
        qc_summary_path=tmp_files["qc_csv"],
    )
    # The CSV says 2 processed, 2 excluded
    assert "Number of subjects processed:** 2" in info
    assert "Number of subjects excluded:** 2" in info


def test_generate_report_writes_file(tmp_files):
    generate_report(
        template_path=tmp_files["template"],
        output_path=tmp_files["output"],
        validation_path=tmp_files["validation_json"],
        qc_summary_path=tmp_files["qc_csv"],
    )
    assert tmp_files["output"].is_file()
    content = tmp_files["output"].read_text(encoding="utf-8")
    # Verify that the placeholder was replaced
    assert "{{SAMPLE_INFO}}" not in content
    assert "Number of subjects processed:** 2" in content
    assert "Number of subjects excluded:** 2" in content


def test_cli_invocation(tmp_path: Path, monkeypatch):
    """Run the module as a script with CLI arguments."""
    # Prepare files
    qc_csv = tmp_path / "qc_summary.csv"
    pd.DataFrame(
        {"subject_id": ["s1"], "included": [True]}
    ).to_csv(qc_csv, index=False)

    validation_json = tmp_path / "validation_status.json"
    validation_json.write_text(
        json.dumps({"status": "passed", "subjects_processed": 1, "subjects_excluded": 0}),
        encoding="utf-8",
    )

    template_md = tmp_path / "template.md"
    template_md.write_text(
        "# Report\\n\\n{{SAMPLE_INFO}}\\n", encoding="utf-8"
    )

    output_md = tmp_path / "summary.md"

    # Build argv list
    argv = [
        "--template",
        str(template_md),
        "--output",
        str(output_md),
        "--validation",
        str(validation_json),
        "--qc-summary",
        str(qc_csv),
    ]

    # Import the main function and run it
    from code.report.generate import main

    exit_code = main(argv)
    assert exit_code == 0
    assert output_md.is_file()
    rendered = output_md.read_text(encoding="utf-8")
    assert "Number of subjects processed:** 1" in rendered
    assert "Number of subjects excluded:** 0" in rendered