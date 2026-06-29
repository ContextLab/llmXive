"""
Unit tests for citation report generation (T051).

Tests the generate_citation_report.py module to ensure it:
1. Correctly parses verified datasets from spec.md
2. Generates valid JSON reports
3. Handles edge cases (no datasets, invalid URLs, etc.)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
import unittest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from validate.generate_citation_report import (
    load_verified_datasets_from_spec,
    generate_citation_validation_report
)

class TestCitationReportGeneration(unittest.TestCase):
    """Test citation report generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_spec_path = Path(self.temp_dir) / "spec.md"
        self.temp_output_path = Path(self.temp_dir) / "output" / "citation_validation.json"
        
        # Mock spec.md with verified datasets
        self.mock_spec_content = """# 001-code-generation-performance-outcomes Spec

## Verified datasets

- URL: https://example.com/dataset1.csv
  SHA-256: abc123def456
  Required variables: tool_usage, task_time, defect_rate
  Citation: Example Dataset 1 (2023)

- URL: https://example.com/dataset2.csv
  SHA-256: xyz789uvw012
  Required variables: experience_years, task_complexity
  Citation: Example Dataset 2 (2024)
"""
        
        with open(self.temp_spec_path, 'w', encoding='utf-8') as f:
            f.write(self.mock_spec_content)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_verified_datasets_from_spec(self):
        """Test parsing verified datasets from spec.md."""
        # Temporarily override SPEC_PATH for testing
        import validate.generate_citation_report as module
        original_spec_path = module.SPEC_PATH
        module.SPEC_PATH = self.temp_spec_path
        
        try:
            datasets = load_verified_datasets_from_spec()
            
            self.assertEqual(len(datasets), 2)
            self.assertEqual(datasets[0]['url'], 'https://example.com/dataset1.csv')
            self.assertEqual(datasets[0]['checksum'], 'abc123def456')
            self.assertEqual(datasets[0]['required_variables'], 'tool_usage, task_time, defect_rate')
            self.assertEqual(datasets[0]['citation'], 'Example Dataset 1 (2023)')
        finally:
            module.SPEC_PATH = original_spec_path
    
    def test_load_verified_datasets_from_empty_spec(self):
        """Test parsing when spec.md has no verified datasets."""
        import validate.generate_citation_report as module
        
        empty_spec_path = Path(self.temp_dir) / "empty_spec.md"
        with open(empty_spec_path, 'w', encoding='utf-8') as f:
            f.write("# Empty spec\nNo datasets here")
        
        original_spec_path = module.SPEC_PATH
        module.SPEC_PATH = empty_spec_path
        
        try:
            datasets = load_verified_datasets_from_spec()
            self.assertEqual(len(datasets), 0)
        finally:
            module.SPEC_PATH = original_spec_path
    
    def test_generate_citation_validation_report(self):
        """Test generating citation validation report."""
        datasets = [
            {
                'url': 'https://example.com/dataset.csv',
                'checksum': 'abc123',
                'required_variables': 'var1, var2',
                'citation': 'Test Citation'
            }
        ]
        
        report = generate_citation_validation_report(datasets, self.temp_output_path)
        
        # Verify report structure
        self.assertIn('report_type', report)
        self.assertIn('timestamp', report)
        self.assertIn('all_passed', report)
        self.assertIn('total_citations', report)
        self.assertIn('citations', report)
        
        # Verify file was written
        self.assertTrue(self.temp_output_path.exists())
        
        # Verify JSON is valid
        with open(self.temp_output_path, 'r', encoding='utf-8') as f:
            loaded_report = json.load(f)
        self.assertEqual(loaded_report['total_citations'], 1)
    
    def test_report_contains_required_fields(self):
        """Test that report contains all Constitution Principle II required fields."""
        datasets = [
            {
                'url': 'https://example.com/dataset.csv',
                'checksum': 'abc123',
                'required_variables': 'var1',
                'citation': 'Test'
            }
        ]
        
        report = generate_citation_validation_report(datasets, self.temp_output_path)
        
        required_fields = [
            'report_type',
            'timestamp',
            'all_passed',
            'total_citations',
            'verified_citations',
            'failed_citations',
            'citations',
            'status'
        ]
        
        for field in required_fields:
            self.assertIn(field, report, f"Missing required field: {field}")
    
    def test_report_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        datasets = [
            {
                'url': 'https://example.com/dataset.csv',
                'checksum': 'abc123',
                'required_variables': 'var1',
                'citation': 'Test'
            }
        ]
        
        report = generate_citation_validation_report(datasets, self.temp_output_path)
        
        # Should be parseable as ISO format
        datetime.fromisoformat(report['timestamp'])
    
    def test_output_directory_created(self):
        """Test that output directory is created if it doesn't exist."""
        datasets = [
            {
                'url': 'https://example.com/dataset.csv',
                'checksum': 'abc123',
                'required_variables': 'var1',
                'citation': 'Test'
            }
        ]
        
        deep_path = Path(self.temp_dir) / "deep" / "nested" / "output" / "citation_validation.json"
        
        report = generate_citation_validation_report(datasets, deep_path)
        
        self.assertTrue(deep_path.exists())
    
    def test_multiple_datasets_in_report(self):
        """Test that multiple datasets are all included in report."""
        datasets = [
            {'url': 'https://example.com/ds1.csv', 'checksum': 'abc', 'required_variables': 'var1', 'citation': 'C1'},
            {'url': 'https://example.com/ds2.csv', 'checksum': 'def', 'required_variables': 'var2', 'citation': 'C2'},
            {'url': 'https://example.com/ds3.csv', 'checksum': 'ghi', 'required_variables': 'var3', 'citation': 'C3'},
        ]
        
        report = generate_citation_validation_report(datasets, self.temp_output_path)
        
        self.assertEqual(report['total_citations'], 3)
        self.assertEqual(len(report['citations']), 3)


if __name__ == '__main__':
    unittest.main()
