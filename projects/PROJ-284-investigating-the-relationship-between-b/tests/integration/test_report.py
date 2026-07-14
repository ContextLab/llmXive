import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.report.generate import generate_report, generate_conclusion, LIMITATION_TEXT

class TestReportGeneration:
    """Integration tests for the report generator."""

    def test_report_generates_markdown_with_all_sections(self):
        """
        Verify that generate_report creates a markdown file with all required sections
        and specific text constraints.
        """
        # Prepare dummy data
        corr_data = pd.DataFrame({
            "metric_name": ["Modularity", "Global Efficiency", "Participation Coeff"],
            "r": [0.35, 0.12, 0.45],
            "p": [0.02, 0.45, 0.01],
            "q": [0.04, 0.60, 0.03],
            "significant": [True, False, True]
        })

        power_data = pd.DataFrame({
            "metric_name": ["Modularity", "Global Efficiency"],
            "detectable_r": [0.25, 0.30]
        })

        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            template_path = Path(tmpdir) / "template.md"

            # Create a simple template
            template_content = """
            # Test Report
            {{correlation_table}}
            {{power_analysis}}
            {{plots}}
            {{limitations}}
            {{conclusion}}
            """
            template_path.write_text(template_content)

            # Run generator
            result = generate_report(
                correlation_results=corr_data,
                power_results=power_data,
                plots_dir=str(Path(tmpdir) / "figures"), # Empty dir
                output_path=str(output_path),
                template_path=str(template_path)
            )

            # Verify file exists
            assert result.exists(), "Report file was not created."

            # Read content
            content = result.read_text()

            # Check for required sections
            assert "Correlation Results" in content or "## Correlation Results" in content, \
                "Missing Correlation Results section"
            assert "Power Analysis" in content or "## Power Analysis" in content, \
                "Missing Power Analysis section"
            assert "Limitations" in content or "## Limitations" in content, \
                "Missing Limitations section"
            assert "Conclusion" in content or "## Conclusion" in content, \
                "Missing Conclusion section"

            # Check for required limitation text
            assert LIMITATION_TEXT in content, \
                f"Missing required limitation text: '{LIMITATION_TEXT}'"

            # Check for required associational phrase
            has_assoc = "associational relationship" in content or "correlational evidence" in content
            assert has_assoc, \
                "Conclusion must contain 'associational relationship' or 'correlational evidence'"

    def test_conclusion_logic_significant_results(self):
        """
        Verify that the conclusion uses the correct phrasing when significant results exist.
        """
        corr_data = pd.DataFrame({
            "metric_name": ["Metric A"],
            "r": [0.5],
            "p": [0.01],
            "q": [0.02],
            "significant": [True]
        })

        conclusion = generate_conclusion(corr_data, None)
        assert "associational relationship" in conclusion.lower(), \
            "Conclusion should mention 'associational relationship' for significant results."

    def test_conclusion_logic_no_significant_results(self):
        """
        Verify that the conclusion handles non-significant results correctly.
        """
        corr_data = pd.DataFrame({
            "metric_name": ["Metric A"],
            "r": [0.1],
            "p": [0.5],
            "q": [0.6],
            "significant": [False]
        })

        conclusion = generate_conclusion(corr_data, None)
        # Should still mention the phrase but in a negative context
        assert "associational relationship" in conclusion.lower() or "correlational evidence" in conclusion.lower(), \
            "Conclusion should still reference the relationship type even if not significant."