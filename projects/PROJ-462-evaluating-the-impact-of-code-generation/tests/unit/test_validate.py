"""
Unit tests for dataset validation module (T017a).

Tests validate that datasets contain required variables before ingestion.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest.validate import (
    check_csv_variables,
    REQUIRED_VARIABLES,
    generate_validation_report
)

class TestDatasetValidation(TestCase):
    """Test cases for dataset validation functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_check_csv_variables_all_present(self):
        """Test validation when all required variables are present."""
        # Create CSV with all required variables
        csv_path = self.temp_path / 'complete.csv'
        with open(csv_path, 'w') as f:
            f.write(','.join(REQUIRED_VARIABLES) + '\n')
            f.write('value1,value2,value3,value4,value5,value6,value7\n')
        
        result = check_csv_variables(csv_path)
        
        self.assertTrue(result['all_present'])
        self.assertEqual(len(result['missing_variables']), 0)
        self.assertEqual(result['variable_count'], 7)
    
    def test_check_csv_variables_missing_some(self):
        """Test validation when some required variables are missing."""
        # Create CSV with only some required variables
        csv_path = self.temp_path / 'incomplete.csv'
        with open(csv_path, 'w') as f:
            f.write('tool_usage,task_time,defect_rate\n')
            f.write('value1,value2,value3\n')
        
        result = check_csv_variables(csv_path)
        
        self.assertFalse(result['all_present'])
        self.assertEqual(len(result['missing_variables']), 4)
        self.assertIn('experience_years', result['missing_variables'])
        self.assertIn('task_complexity', result['missing_variables'])
        self.assertIn('project_type', result['missing_variables'])
        self.assertIn('team_size', result['missing_variables'])
    
    def test_check_csv_variables_file_not_found(self):
        """Test validation when file does not exist."""
        csv_path = self.temp_path / 'nonexistent.csv'
        
        result = check_csv_variables(csv_path)
        
        self.assertIn('error', result)
        self.assertFalse(result['all_present'])
    
    def test_check_csv_variables_empty_file(self):
        """Test validation when file is empty."""
        csv_path = self.temp_path / 'empty.csv'
        csv_path.touch()
        
        result = check_csv_variables(csv_path)
        
        self.assertIn('error', result)
        self.assertFalse(result['all_present'])
    
    def test_required_variables_list(self):
        """Test that required variables list contains all expected fields."""
        expected_vars = [
            'tool_usage',
            'task_time',
            'defect_rate',
            'experience_years',
            'task_complexity',
            'project_type',
            'team_size'
        ]
        
        self.assertEqual(len(REQUIRED_VARIABLES), len(expected_vars))
        for var in expected_vars:
            self.assertIn(var, REQUIRED_VARIABLES)
    
    def test_generate_validation_report(self):
        """Test validation report generation."""
        output_dir = self.temp_path / 'output'
        output_dir.mkdir()
        
        # Temporarily override OUTPUT_DIR
        import ingest.validate
        original_output_dir = ingest.validate.OUTPUT_DIR
        ingest.validate.OUTPUT_DIR = output_dir
        
        report = {
            'validation_timestamp': '2024-01-15T10:30:00',
            'total_datasets': 1,
            'datasets_passed': 1,
            'datasets_failed': 0,
            'datasets_with_errors': 0,
            'results': []
        }
        
        report_path = generate_validation_report(report)
        
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            saved_report = json.load(f)
        
        self.assertIn('summary', saved_report)
        self.assertEqual(saved_report['summary']['required_variable_count'], 7)
        
        # Restore original
        ingest.validate.OUTPUT_DIR = original_output_dir

if __name__ == '__main__':
    main()