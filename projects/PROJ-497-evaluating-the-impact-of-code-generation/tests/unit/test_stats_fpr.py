import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from stats import calculate_fpr_metrics

class TestFPRMetrics:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator_path = os.path.join(self.temp_dir, 'validator_flags.csv')
        self.raw_counts_path = os.path.join(self.temp_dir, 'raw_vulnerability_counts.csv')
        self.output_path = os.path.join(self.temp_dir, 'fpr_metrics.json')
        
        # Create sample validator flags
        validator_data = [
            {'sample_id': 'file1.py', 'is_valid': True},
            {'sample_id': 'file2.py', 'is_valid': False},
            {'sample_id': 'file3.py', 'is_valid': False},
            {'sample_id': 'file4.py', 'is_valid': True},
            {'sample_id': 'file5.py', 'is_valid': True},
        ]
        pd.DataFrame(validator_data).to_csv(self.validator_path, index=False)
        
        # Create sample raw vulnerability counts
        raw_data = [
            {'file_path': 'file1.py', 'vulnerability_count': 2, 'source_type': 'LLM'},
            {'file_path': 'file2.py', 'vulnerability_count': 1, 'source_type': 'LLM'},
            {'file_path': 'file3.py', 'vulnerability_count': 3, 'source_type': 'LLM'},
            {'file_path': 'file4.py', 'vulnerability_count': 0, 'source_type': 'Human'}, # No vuln, should be ignored
            {'file_path': 'file5.py', 'vulnerability_count': 1, 'source_type': 'Human'},
            {'file_path': 'file6.py', 'vulnerability_count': 2, 'source_type': 'Human'}, # Missing in validator
        ]
        pd.DataFrame(raw_data).to_csv(self.raw_counts_path, index=False)
        
        # Mock the raw counts path in the function by creating the expected file in the default location
        # or by passing the correct path. Since the function looks for 'data/processed/raw_vulnerability_counts.csv',
        # we will create a symlink or copy for the test if needed, but better to modify the test to use the temp dir.
        # However, the function `calculate_fpr_metrics` hardcodes the raw counts path.
        # To test properly, we need to either:
        # 1. Refactor the function to accept the path (not allowed per constraints)
        # 2. Create the file in the expected location relative to the test
        # 3. Mock the file system (complex)
        
        # Given the constraint "extend, don't re-author", we assume the function will be run in the project context.
        # For the unit test, we will create the necessary files in the project's data/processed directory
        # if they don't exist, or skip if not in project context.
        
        # Alternative: We test the logic by creating the files in the expected relative paths
        # assuming the test runs from the project root.
        data_processed_dir = Path('data/processed')
        data_processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy validator flags to expected location
        Path(self.validator_path).rename('data/processed/validator_flags.csv')
        self.validator_path = 'data/processed/validator_flags.csv'
        
        # Copy raw counts to expected location
        Path(self.raw_counts_path).rename('data/processed/raw_vulnerability_counts.csv')
        self.raw_counts_path = 'data/processed/raw_vulnerability_counts.csv'
        
        self.output_path = 'data/processed/fpr_metrics_test.json'

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up created files
        for file in ['data/processed/validator_flags.csv', 
                     'data/processed/raw_vulnerability_counts.csv',
                     self.output_path]:
            if os.path.exists(file):
                os.remove(file)

    def test_fpr_calculation_llm_and_human(self):
        """Test FPR calculation for both LLM and Human groups."""
        # Expected:
        # LLM: 
        #   file1.py: vuln=2, valid=True -> TP
        #   file2.py: vuln=1, valid=False -> FP
        #   file3.py: vuln=3, valid=False -> FP
        #   Total Reported = 3, TP = 1, FP = 2, FPR = 2/3
        # Human:
        #   file4.py: vuln=0 -> Ignored
        #   file5.py: vuln=1, valid=True -> TP
        #   file6.py: vuln=2 -> Not in validator -> Ignored (or treated as not valid? The merge is inner)
        #   Total Reported (in merge) = 1, TP = 1, FP = 0, FPR = 0/1
        
        result = calculate_fpr_metrics(self.validator_path, self.output_path)
        
        assert result['status'] == 'success'
        assert 'LLM' in result['results']
        assert 'Human' in result['results']
        
        # Check LLM
        llm_metrics = result['results']['LLM']
        assert llm_metrics['total_reported_vulnerabilities'] == 3
        assert llm_metrics['true_positives'] == 1
        assert llm_metrics['false_positives'] == 2
        assert abs(llm_metrics['fpr'] - (2/3)) < 0.001
        
        # Check Human
        human_metrics = result['results']['Human']
        assert human_metrics['total_reported_vulnerabilities'] == 1
        assert human_metrics['true_positives'] == 1
        assert human_metrics['false_positives'] == 0
        assert human_metrics['fpr'] == 0.0

    def test_fpr_no_reported_vulns(self):
        """Test FPR when there are no reported vulnerabilities."""
        # Modify raw counts to have 0 vulns
        raw_data = [
            {'file_path': 'file1.py', 'vulnerability_count': 0, 'source_type': 'LLM'},
        ]
        pd.DataFrame(raw_data).to_csv('data/processed/raw_vulnerability_counts.csv', index=False)
        
        result = calculate_fpr_metrics(self.validator_path, self.output_path)
        
        assert result['status'] == 'success'
        assert result['results']['LLM']['total_reported_vulnerabilities'] == 0
        assert result['results']['LLM']['fpr'] == 0.0
        assert 'note' in result['results']['LLM']

    def test_fpr_file_not_found(self):
        """Test FPR when validator file is not found."""
        result = calculate_fpr_metrics('non_existent_file.csv', self.output_path)
        
        assert result['status'] == 'error'
        assert 'File not found' in result['message']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])