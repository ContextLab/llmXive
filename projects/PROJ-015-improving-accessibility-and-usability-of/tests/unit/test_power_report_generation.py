"""
Unit tests for the Power Analysis Report Generation (T036b).

These tests verify that the report generator correctly reads input files,
generates the Markdown content, and updates the main report.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.generate_power_report import (
    load_power_flags,
    load_metrics_summary,
    generate_power_report_md,
    update_main_report,
    main
)

class TestPowerReportGeneration(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.data_processed_dir = Path(self.test_dir) / "data" / "processed"
        self.data_processed_dir.mkdir(parents=True)

        # Mock file paths
        self.power_flags_file = self.data_processed_dir / "power_flags.json"
        self.metrics_summary_file = self.data_processed_dir / "metrics_summary.csv"
        self.report_summary_file = self.data_processed_dir / "report_summary.txt"
        self.power_report_file = self.data_processed_dir / "power_report.md"

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_load_power_flags_success(self):
        """Test loading power flags from a valid JSON file."""
        test_data = [
            {"subgroup": "Visual", "N": 35, "power": 0.85, "flag": "OK"},
            {"subgroup": "Motor", "N": 20, "power": 0.45, "flag": "UNDERPOWERED"}
        ]
        with open(self.power_flags_file, 'w') as f:
            json.dump(test_data, f)

        # Temporarily patch the global constant
        import code.analysis.generate_power_report as module
        original_path = module.POWER_FLAGS_FILE
        module.POWER_FLAGS_FILE = self.power_flags_file

        try:
            result = load_power_flags()
            self.assertEqual(result, test_data)
        finally:
            module.POWER_FLAGS_FILE = original_path

    def test_load_power_flags_missing_file(self):
        """Test that load_power_flags raises FileNotFoundError if file is missing."""
        import code.analysis.generate_power_report as module
        original_path = module.POWER_FLAGS_FILE
        module.POWER_FLAGS_FILE = Path("/nonexistent/path.json")

        try:
            with self.assertRaises(FileNotFoundError):
                load_power_flags()
        finally:
            module.POWER_FLAGS_FILE = original_path

    def test_generate_power_report_md(self):
        """Test the Markdown generation logic."""
        power_flags = [
            {"subgroup": "Visual", "N": 35, "power": 0.85, "flag": "OK"},
            {"subgroup": "Motor", "N": 20, "power": 0.45, "flag": "UNDERPOWERED"}
        ]
        metrics_df = None  # Not used in this specific function's logic for basic structure

        md_content = generate_power_report_md(power_flags, metrics_df)

        # Check for key sections
        self.assertIn("# Power Analysis Report", md_content)
        self.assertIn("## Power Analysis Results", md_content)
        self.assertIn("Visual", md_content)
        self.assertIn("Motor", md_content)
        self.assertIn("UNDERPOWERED", md_content)
        self.assertIn("OK", md_content)
        self.assertIn("Warning: Underpowered Study", md_content)

    def test_generate_power_report_md_all_ok(self):
        """Test Markdown generation when all groups are OK."""
        power_flags = [
            {"subgroup": "Visual", "N": 50, "power": 0.95, "flag": "OK"}
        ]
        md_content = generate_power_report_md(power_flags, None)

        self.assertIn("✅ Study Power Status", md_content)
        self.assertNotIn("Warning: Underpowered Study", md_content)

    def test_update_main_report_creates_new(self):
        """Test updating main report when it doesn't exist."""
        power_report = "# Power Report Content"
        
        # Ensure file doesn't exist
        if self.report_summary_file.exists():
            self.report_summary_file.unlink()

        # Patch the global constant
        import code.analysis.generate_power_report as module
        original_path = module.REPORT_SUMMARY_FILE
        module.REPORT_SUMMARY_FILE = self.report_summary_file

        try:
            update_main_report(power_report)
            self.assertTrue(self.report_summary_file.exists())
            with open(self.report_summary_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, power_report)
        finally:
            module.REPORT_SUMMARY_FILE = original_path

    def test_update_main_report_appends(self):
        """Test updating main report when it exists."""
        existing_content = "# Existing Report\n"
        power_report = "\n# Power Report Content"
        
        with open(self.report_summary_file, 'w') as f:
            f.write(existing_content)

        # Patch the global constant
        import code.analysis.generate_power_report as module
        original_path = module.REPORT_SUMMARY_FILE
        module.REPORT_SUMMARY_FILE = self.report_summary_file

        try:
            update_main_report(power_report)
            with open(self.report_summary_file, 'r') as f:
                content = f.read()
            self.assertIn(existing_content, content)
            self.assertIn(power_report, content)
        finally:
            module.REPORT_SUMMARY_FILE = original_path

if __name__ == '__main__':
    unittest.main()