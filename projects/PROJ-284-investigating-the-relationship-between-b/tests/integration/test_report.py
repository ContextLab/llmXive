"""Integration test for report generation (T030).

Verifies that the report generator produces a Markdown file with all required
sections and correct template injection, using dummy/synthetic results.
"""
import os
import tempfile
from pathlib import Path

import pytest

from code.report.generate import generate_report, load_template
from code.logging_config import get_logger

logger = get_logger(__name__)


def test_report_generates_markdown_with_all_sections():
    """Test that the report generator creates a valid Markdown file with all sections.

    This test uses dummy data to verify:
    1. The template loads correctly.
    2. All required sections are present in the output.
    3. Template variables are correctly injected.
    4. The output file is written to the correct location.
    """
    # Arrange: Prepare dummy data
    dummy_correlation_table = (
        "| Metric | r | p | q | Significant |\n"
        "|---|---|---|---|---|\n"
        "| Modularity | 0.35 | 0.02 | 0.04 | Yes |\n"
        "| Global Efficiency | 0.28 | 0.08 | 0.12 | No |\n"
        "| Participation Coeff | 0.41 | 0.01 | 0.03 | Yes |\n"
    )

    dummy_power_analysis = (
        "Power Analysis (80%% power, α=0.05, FDR-corrected):\n"
        "- Detectable effect size (r): 0.32\n"
        "- Sample size achieved: N=50\n"
    )

    dummy_plots = [
        "figures/scatter_modularity.png",
        "figures/scatter_participation.png",
    ]

    dummy_limitations = (
        "Motor Task Performance is a proxy for proprioceptive accuracy.\n"
        "Cross-sectional design limits causal inference.\n"
    )

    context = {
        "correlation_table": dummy_correlation_table,
        "power_analysis": dummy_power_analysis,
        "plots": dummy_plots,
        "limitations": dummy_limitations,
        "analysis_date": "2024-01-15",
    }

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "report.md"

        # Act: Generate the report
        generate_report(context, output_path=str(output_path))

        # Assert 1: File exists
        assert output_path.exists(), "Report file was not created."

        # Assert 2: Read content
        content = output_path.read_text(encoding="utf-8")

        # Assert 3: Verify required sections exist
        required_sections = [
            "# Brain Network Dynamics and Sensorimotor Performance Report",
            "## Correlation Results",
            "## Power Analysis",
            "## Visualizations",
            "## Limitations",
            "## Conclusion",
        ]

        for section in required_sections:
            self.assertIn(
                section, content,
                f"Required section/phrase '{section}' not found in report"
            )

        # Assert 4: Verify template injection
        assert "Modularity" in content, "Correlation table not injected."
        assert "0.35" in content, "Specific values not injected."
        assert "0.32" in content, "Power analysis not injected."

        # Assert 5: Verify specific phrasing requirements from spec (T033)
        # "Motor Task Performance is a proxy for proprioceptive accuracy."
        assert "Motor Task Performance is a proxy for proprioceptive accuracy" in content, (
            "Missing limitation statement about motor task proxy."
        )

        # "associational relationship" OR "correlational evidence"
        has_assoc = "associational relationship" in content.lower()
        has_corr = "correlational evidence" in content.lower()
        assert has_assoc or has_corr, (
            "Conclusion missing required phrasing: 'associational relationship' or "
            "'correlational evidence'."
        )

        # Assert 6: Verify plots section lists the dummy files
        for plot in dummy_plots:
            assert plot in content, f"Plot {plot} not listed in report."

        logger.log(
            "test_report_generates_markdown_with_all_sections",
            status="passed",
            output_file=str(output_path),
            content_length=len(content),
        )