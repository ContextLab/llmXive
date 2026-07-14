"""Integration test for report generation (US3).

This test verifies that the report generator produces a valid Markdown file
containing all required sections, template injections, and specific phrasing
mandated by the specification (FR-004, FR-007).
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Import the report generator
from code.report.generate import (
    load_template,
    format_correlation_table,
    format_power_analysis,
    generate_conclusion,
    generate_report,
    main as report_main
)
from code.logging_config import get_logger

logger = get_logger(__name__)


class TestReportGeneration:
    """Integration tests for the report generation pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_path = Path(self.test_dir) / "test_report.md"
        
        # Create dummy data that mimics real analysis output
        # to ensure the report generator has real data to process
        self.correlation_data = pd.DataFrame({
            'metric_name': ['Modularity', 'Global_Efficiency', 'Participation_Coeff'],
            'r': [0.45, -0.12, 0.38],
            'p': [0.002, 0.45, 0.01],
            'q': [0.006, 0.60, 0.03],
            'significant': [True, False, True]
        })
        
        self.power_data = {
            'detectable_r': 0.25,
            'n': 100,
            'power': 0.80,
            'alpha': 0.05
        }

    def teardown_method(self):
        """Clean up test files."""
        if self.output_path.exists():
            self.output_path.unlink()
        if Path(self.test_dir).exists():
            import shutil
            shutil.rmtree(self.test_dir)

    def test_report_generates_markdown_with_all_sections(self):
        """
        Integration test: test_report_generates_markdown_with_all_sections.
        
        Verifies that:
        1. The report file is generated at the specified path.
        2. All required sections are present (Introduction, Methods, Results, Discussion, Limitations).
        3. Template variables are correctly injected (correlation table, power analysis).
        4. Mandatory phrasing is present:
           - "Limitation Statement": "Motor Task Performance is a proxy for proprioceptive accuracy."
           - Conclusion: Contains "associational relationship" OR "correlational evidence".
        """
        # Generate the report using the real generator logic
        # We pass dummy data directly to the generate_report function
        # to ensure it runs without needing the full pipeline to have run first.
        
        report_content = generate_report(
            correlation_results=self.correlation_data,
            power_analysis=self.power_data,
            output_path=self.output_path
        )

        # Assert file was written to disk
        assert self.output_path.exists(), f"Report file not created at {self.output_path}"

        # Read the content for assertions
        with open(self.output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Verify file is not empty
        assert len(content) > 100, "Report content is too short; likely missing sections."

        # 2. Verify required sections exist
        required_sections = [
            "# Introduction",
            "# Methods",
            "# Results",
            "# Discussion",
            "## Limitations"
        ]
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

        # 3. Verify correlation table is formatted and present
        # The generator should format the dataframe into a markdown table
        assert "| metric_name | r | p | q | significant |" in content or \
               "Modularity" in content, "Correlation table not found or malformed."

        # 4. Verify Power Analysis is present
        assert "0.25" in content, "Detectable effect size (0.25) not found in report."
        assert "80" in content, "Power value (80%) not found in report."

        # 5. CRITICAL: Verify mandatory "Limitation Statement" text
        limitation_text = "Motor Task Performance is a proxy for proprioceptive accuracy."
        assert limitation_text in content, \
            f"Missing mandatory limitation statement: '{limitation_text}'"

        # 6. CRITICAL: Verify "Associational Relationship" phrasing in conclusion
        conclusion_present = (
            "associational relationship" in content.lower() or
            "correlational evidence" in content.lower()
        )
        assert conclusion_present, \
            "Missing mandatory conclusion phrasing ('associational relationship' or 'correlational evidence')."

        # 7. Verify the file is valid markdown (basic check)
        # (We already checked for headers and tables, which are key MD elements)
        assert content.count("#") >= 4, "Report appears to lack proper Markdown structure."

    def test_report_with_empty_correlations(self):
        """
        Test that the report handles cases with no significant correlations gracefully.
        """
        empty_corr = pd.DataFrame(columns=['metric_name', 'r', 'p', 'q', 'significant'])
        
        report_content = generate_report(
            correlation_results=empty_corr,
            power_analysis=self.power_data,
            output_path=Path(self.test_dir) / "empty_report.md"
        )
        
        assert (Path(self.test_dir) / "empty_report.md").exists()
        with open(Path(self.test_dir) / "empty_report.md", 'r') as f:
            content = f.read()
        
        # Should still have sections and limitation
        assert "Motor Task Performance is a proxy for proprioceptive accuracy." in content
        assert "# Results" in content

    def test_main_entry_point(self):
        """
        Test that the CLI main entry point works and writes to the default path.
        """
        # Create a temporary output path for the main entry point test
        test_output = Path(self.test_dir) / "cli_report.md"
        
        # Mock the sys.argv to simulate CLI call
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ['report_generate', '--output', str(test_output)]
            
            # Run the main function
            report_main()
            
            # Verify output
            assert test_output.exists(), "CLI main did not create output file."
            
            with open(test_output, 'r') as f:
                content = f.read()
            
            # Verify content integrity
            assert "Motor Task Performance is a proxy for proprioceptive accuracy." in content
            
        finally:
            sys.argv = original_argv