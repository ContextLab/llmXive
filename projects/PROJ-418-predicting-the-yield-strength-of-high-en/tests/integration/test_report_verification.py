"""
Integration test for Task T041: Verify final report generation.
Confirms output/report.md exists, contains mandatory disclaimer,
and includes Data Limitation Warning if count_warning is true.
"""
import os
import json
import unittest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

class TestReportVerification(unittest.TestCase):
    
    def setUp(self):
        self.project_root = project_root
        self.output_dir = self.project_root / "output"
        self.report_path = self.output_dir / "report.md"
        self.status_path = self.output_dir / "data_status.json"

    def test_report_file_exists(self):
        """Verify that output/report.md exists."""
        self.assertTrue(
            self.report_path.exists(), 
            f"Report file not found at {self.report_path}"
        )

    def test_mandatory_disclaimer_present(self):
        """Verify the mandatory disclaimer string exists in the report."""
        if not self.report_path.exists():
            self.skipTest("Report file does not exist")
        
        content = self.report_path.read_text()
        mandatory_disclaimer = "Associational analysis only; no causal inference"
        
        self.assertIn(
            mandatory_disclaimer, 
            content, 
            f"Mandatory disclaimer '{mandatory_disclaimer}' not found in report"
        )

    def test_data_limitation_warning_logic(self):
        """
        Verify that if data_status.json indicates count_warning is true,
        the report contains the 'Data Limitation Warning' section.
        """
        if not self.status_path.exists():
            self.skipTest("data_status.json not found")
        
        if not self.report_path.exists():
            self.skipTest("Report file does not exist")

        with open(self.status_path, 'r') as f:
            status_data = json.load(f)

        count_warning = status_data.get("count_warning", False)
        report_content = self.report_path.read_text()

        if count_warning:
            self.assertIn(
                "Data Limitation Warning",
                report_content,
                "Report must include 'Data Limitation Warning' section when count_warning is true"
            )
        else:
            # If count_warning is false, the section is optional but shouldn't be misleading
            # We just ensure the logic holds: if warning is true -> section exists.
            pass

if __name__ == "__main__":
    unittest.main()