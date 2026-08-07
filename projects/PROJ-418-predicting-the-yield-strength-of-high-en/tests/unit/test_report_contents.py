"""
Test suite for verifying that the generated ``output/report.md`` file
contains all required sections as specified in task T118.

Required sections (case‑insensitive search):
  * Dataset statistics
  * VIF summary
  * Model performance (R², |r|, p‑value)
  * Permutation importance with corrected p‑values
  * Bootstrap confidence intervals
  * Disclaimer (the mandatory associational disclaimer)

The test reads the markdown file produced by the pipeline (``output/report.md``)
and asserts that each of the above headings or key phrases is present.
"""

import pathlib
import re

import pytest


# Path to the generated report – this is the location used by the
# ``code/models/report_generator`` module when it writes the final markdown.
REPORT_PATH = pathlib.Path("output/report.md")


@pytest.fixture(scope="module")
def report_text():
    """Load the report markdown as a single string."""
    if not REPORT_PATH.is_file():
        pytest.fail(f"Report file not found at expected location: {REPORT_PATH}")
    return REPORT_PATH.read_text(encoding="utf-8")


def _assert_section_present(text: str, pattern: str, description: str):
    """
    Helper that asserts a regex pattern is found in ``text``.
    ``pattern`` is compiled with ``re.IGNORECASE`` to make the check
    case‑insensitive.
    """
    if not re.search(pattern, text, flags=re.IGNORECASE):
        pytest.fail(f"Missing required section: {description}")



def test_dataset_statistics_section(report_text):
    """The report must contain a dataset statistics section."""
    _assert_section_present(
        report_text,
        r"##\s*Dataset\s*Statistics",
        "Dataset Statistics (e.g., a heading like '## Dataset Statistics')",
    )


def test_vif_summary_section(report_text):
    """The report must contain a VIF summary section."""
    _assert_section_present(
        report_text,
        r"##\s*VIF\s*Summary",
        "VIF Summary (e.g., a heading like '## VIF Summary')",
    )


def test_model_performance_section(report_text):
    """The report must contain a model performance section including R², |r|, and p‑value."""
    _assert_section_present(
        report_text,
        r"##\s*Model\s*Performance",
        "Model Performance (e.g., a heading like '## Model Performance')",
    )
    # Also check that the three key metrics appear somewhere in the section.
    for metric in ["R²", r"\|r\|", "p‑value", "p-value"]:
        _assert_section_present(
            report_text,
            metric,
            f"Model Performance metric '{metric}' not found in report",
        )


def test_permutation_importance_section(report_text):
    """The report must contain a permutation‑importance section with corrected p‑values."""
    _assert_section_present(
        report_text,
        r"##\s*Permutation\s*Importance",
        "Permutation Importance (e.g., a heading like '## Permutation Importance')",
    )
    _assert_section_present(
        report_text,
        r"corrected\s*p-?values?",
        "Corrected p‑values for permutation importance not found",
    )


def test_bootstrap_confidence_intervals_section(report_text):
    """The report must contain a bootstrap confidence‑intervals section."""
    _assert_section_present(
        report_text,
        r"##\s*Bootstrap\s*Confidence\s*Intervals",
        "Bootstrap Confidence Intervals (e.g., a heading like '## Bootstrap Confidence Intervals')",
    )


def test_disclaimer_present(report_text):
    """The mandatory disclaimer must be present in the report."""
    disclaimer_phrase = (
        "Associational analysis only; no causal inference"
    )
    _assert_section_present(
        report_text,
        re.escape(disclaimer_phrase),
        "Mandatory disclaimer not found in report",
    )