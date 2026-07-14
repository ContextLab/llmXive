"""
Integration test for report generation (US3).
Verifies that the report generator produces a valid Markdown file with all required sections
and correct template injection, using dummy results.
"""
import os
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.report.generate import generate_report, load_template, format_correlation_table, format_power_analysis
from code.logging_config import get_logger

logger = get_logger(__name__)

# Import the actual implementation
from code.report.generate import (
    load_template,
    format_correlation_table,
    format_power_analysis,
    generate_conclusion,
    generate_report,
    main
)
from code.logging_config import get_logger

class TestReportGeneration(unittest.TestCase):
    """Integration tests for the report generation module."""

    def setUp(self):
        """Set up temporary directories and dummy data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create dummy data files that the report generator expects
        self.correlations_file = self.output_dir / "correlations.csv"
        self.power_file = self.output_dir / "power_analysis.csv"
        
        # Create minimal dummy correlation data
        self.correlations_data = """metric_name,r,p,q,significant,covariate_controlled
        Modularity,0.35,0.012,0.048,True,False
        Global_Efficiency,0.28,0.045,0.089,True,False
        Participation_Coeff,0.15,0.230,0.420,False,False
        Within_Module_Degree,0.31,0.021,0.063,True,False
        """
        
        # Create minimal dummy power analysis data
        self.power_data = """metric_name,detectable_effect_size,n_subjects,power,alpha
        Modularity,0.35,50,0.80,0.05
        Global_Efficiency,0.28,50,0.80,0.05
        Participation_Coeff,0.15,50,0.80,0.05
        Within_Module_Degree,0.31,50,0.80,0.05
        """
        
        # Write dummy files
        with open(self.correlations_file, "w") as f:
            f.write(self.correlations_data)
        
        with open(self.power_file, "w") as f:
            f.write(self.power_data)

        # Ensure templates directory exists
        self.templates_dir = PROJECT_ROOT / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Create a minimal report template if it doesn't exist
        template_file = self.templates_dir / "report_template.md"
        if not template_file.exists():
            template_content = """# Brain Network Dynamics and Sensorimotor Performance Report

## Executive Summary
{{summary}}

## Methods
{{methods}}

## Results

### Correlation Analysis
{{correlation_table}}

### Power Analysis
{{power_analysis}}

### Visualizations
{{plots}}

## Discussion
{{discussion}}

## Limitations
{{limitations}}

## Conclusion
{{conclusion}}
"""
            with open(template_file, "w") as f:
                f.write(template_content)

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()

    def test_report_generates_markdown_with_all_sections(self):
        """
        Integration test: Verify that generate_report produces a valid Markdown file
        containing all required sections with properly injected template variables.
        """
        # Define paths for report generation
        report_output = self.output_dir / "final_report.md"
        
        # Prepare dummy data dictionaries
        correlation_df = None
        power_df = None
        
        # Load data manually for the test (mimicking what generate_report does internally)
        import pandas as pd
        correlation_df = pd.read_csv(self.correlations_file)
        power_df = pd.read_csv(self.power_file)
        
        # Generate the report
        try:
            generate_report(
                correlation_results=correlation_df,
                power_analysis_results=power_df,
                output_path=str(report_output),
                template_path=str(self.templates_dir / "report_template.md")
            )
        except Exception as e:
            self.fail(f"Report generation failed with error: {str(e)}")

        # Verify the output file exists
        self.assertTrue(report_output.exists(), "Report file was not created")
        
        # Read the generated report
        with open(report_output, "r") as f:
            report_content = f.read()

        # Verify all required sections exist
        required_sections = [
            "## Executive Summary",
            "## Methods",
            "## Results",
            "### Correlation Analysis",
            "### Power Analysis",
            "### Visualizations",
            "## Discussion",
            "## Limitations",
            "## Conclusion"
        ]
        
        for section in required_sections:
            self.assertIn(section, report_content, f"Required section '{section}' missing from report")

        # Verify template injection worked (check for actual data content)
        self.assertIn("Modularity", report_content, "Correlation data not properly injected")
        self.assertIn("0.35", report_content, "Correlation values not properly injected")
        self.assertIn("detectable_effect_size", report_content, "Power analysis data not properly injected")

        # Verify specific requirement from T033 (referenced by T030 context):
        # The report must include "Limitation Statement" text
        self.assertIn("Motor Task Performance is a proxy for proprioceptive accuracy", report_content, 
                     "Required limitation statement missing")
        
        # Verify specific requirement: "Associational Relationship" phrase
        self.assertTrue(
            "associational relationship" in report_content.lower() or 
            "correlational evidence" in report_content.lower(),
            "Required 'associational relationship' or 'correlational evidence' phrase missing from conclusion"
        )

    def test_format_correlation_table(self):
        """Test that correlation table formatting produces valid Markdown."""
        import pandas as pd
        df = pd.read_csv(self.correlations_file)
        
        formatted = format_correlation_table(df)
        
        self.assertIsInstance(formatted, str, "format_correlation_table should return a string")
        self.assertIn("metric_name", formatted, "Table should contain column headers")
        self.assertIn("Modularity", formatted, "Table should contain data rows")

    def test_format_power_analysis(self):
        """Test that power analysis formatting produces valid Markdown."""
        import pandas as pd
        df = pd.read_csv(self.power_file)
        
        formatted = format_power_analysis(df)
        
        self.assertIsInstance(formatted, str, "format_power_analysis should return a string")
        self.assertIn("detectable_effect_size", formatted, "Table should contain column headers")
        self.assertIn("Modularity", formatted, "Table should contain data rows")

    def test_load_template(self):
        """Test that template loading works correctly."""
        template_path = self.templates_dir / "report_template.md"
        
        template = load_template(str(template_path))
        
        self.assertIsInstance(template, str, "load_template should return a string")
        self.assertIn("{{correlation_table}}", template, "Template should contain placeholders")
        self.assertIn("{{power_analysis}}", template, "Template should contain placeholders")


if __name__ == "__main__":
    unittest.main()