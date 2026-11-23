"""
Test suite for verifying that the generated `output/report.md` contains all
required sections as specified by task T118.

Required sections (case‑insensitive search):
  * Dataset statistics / dataset stats
  * VIF summary
  * Model performance (R², |r|, p‑value)
  * Permutation importance with corrected p‑values
  * Bootstrap confidence intervals (CI)
  * Disclaimers (e.g., data limitation warning, usage disclaimer)

The test reads the markdown file, checks that it exists, is non‑empty, and
that each required keyword pattern appears at least once.
"""

import pathlib
import re

import pytest


@pytest.fixture(scope="module")
def report_path():
    """Path to the generated report markdown."""
    return pathlib.Path("output/report.md")


def test_report_exists_and_not_empty(report_path):
    """The report file must exist and contain content."""
    assert report_path.is_file(), f"Report file not found at {report_path}"
    content = report_path.read_text(encoding="utf-8")
    assert content.strip(), "Report file is empty"


@pytest.mark.parametrize(
    "section_name, patterns",
    [
        (
            "dataset statistics",
            [
                r"dataset\s+statistics",
                r"dataset\s+stats",
                r"sample\s+size",
                r"number\s+of\s+records",
            ],
        ),
        (
            "VIF summary",
            [
                r"VIF\s+summary",
                r"variance\s+inflation\s+factor",
                r"VIF\s*[:\-]",
            ],
        ),
        (
            "model performance",
            [
                r"R\s*²",
                r"R\^2",
                r"R2",
                r"\|r\|",
                r"pearson\s+r",
                r"p[-\s]?value",
            ],
        ),
        (
            "permutation importance with corrected p-values",
            [
                r"permutation\s+importance",
                r"corrected\s+p[-\s]?values?",
                r"holm[-\s]?bonferroni",
                r"multiple\s+comparison\s+correction",
            ],
        ),
        (
            "bootstrap confidence intervals",
            [
                r"bootstrap\s+confidence\s+interval",
                r"bootstrap\s+CI",
                r"confidence\s+intervals?",
            ],
        ),
        (
            "disclaimers",
            [
                r"disclaimer",
                r"data\s+limitation\s+warning",
                r"usage\s+disclaimer",
            ],
        ),
    ],
)
def test_report_contains_required_section(report_path, section_name, patterns):
    """
    Verify that each required section appears in the report.

    The check is performed by searching for at least one of the provided
    regular‑expression patterns (case‑insensitive) within the file content.
    """
    content = report_path.read_text(encoding="utf-8")
    # Normalise line endings for consistent regex matching
    content = content.replace("\r\n", "\n")

    matches = any(re.search(pat, content, flags=re.IGNORECASE) for pat in patterns)
    assert (
        matches
    ), f"Required section '{section_name}' not found in report. Expected one of patterns: {patterns}"