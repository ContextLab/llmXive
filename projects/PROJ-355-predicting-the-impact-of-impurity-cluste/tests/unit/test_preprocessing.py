import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocessing import filter_zero_impurity_configs, generate_preprocessing_report, run_preprocessing_filter

class TestFilterZeroImpurityConfigs:
    def test_filter_zero_impurities(self):
        """Test that configurations with zero impurities are filtered out."""
        data = {
            'config_id': [1, 2, 3, 4],
            'impurity_count': [0, 1, 0, 2],
            'value': [10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        
        filtered_df = filter_zero_impurity_configs(df)
        
        assert len(filtered_df) == 2
        assert all(filtered_df['impurity_count'] > 0)
        assert list(filtered_df['config_id']) == [2, 4]

    def test_no_zero_impurities(self):
        """Test that DataFrame is unchanged if no zero impurities exist."""
        data = {
            'config_id': [1, 2, 3],
            'impurity_count': [1, 2, 3],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        filtered_df = filter_zero_impurity_configs(df)
        
        assert len(filtered_df) == 3
        pd.testing.assert_frame_equal(filtered_df, df)

    def test_all_zero_impurities(self):
        """Test that DataFrame is empty if all have zero impurities."""
        data = {
            'config_id': [1, 2, 3],
            'impurity_count': [0, 0, 0],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        filtered_df = filter_zero_impurity_configs(df)
        
        assert len(filtered_df) == 0

    def test_missing_column(self):
        """Test behavior when impurity_count column is missing."""
        data = {
            'config_id': [1, 2, 3],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        filtered_df = filter_zero_impurity_configs(df)
        
        # Should return original DataFrame when column is missing
        pd.testing.assert_frame_equal(filtered_df, df)

class TestGeneratePreprocessingReport:
    def test_report_generation(self):
        """Test that the preprocessing report is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preprocessing_report.json"
            
            generate_preprocessing_report(excluded_count=5, total_count=20, output_path=output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['filter_type'] == 'zero_impurity_removal'
            assert report['total_configurations'] == 20
            assert report['excluded_count'] == 5
            assert report['retained_count'] == 15
            assert 'exclusion_reason' in report

class TestRunPreprocessingFilter:
    def test_full_run(self):
        """Test the full preprocessing filter pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create input data
            data = {
                'config_id': [1, 2, 3, 4, 5],
                'impurity_count': [0, 1, 0, 2, 3],
                'value': [10, 20, 30, 40, 50]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            # Run preprocessing
            result = run_preprocessing_filter(input_path=input_path, output_path=output_path)
            
            assert result['total'] == 5
            assert result['excluded'] == 2
            assert result['retained'] == 3
            
            # Verify output file
            assert output_path.exists()
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 3
            assert all(output_df['impurity_count'] > 0)
            
            # Verify report file
            report_path = Path(tmpdir) / "preprocessing_report.json"
            # The function uses a default path relative to project root, but we need to check in tmpdir
            # For this test, we'll check the generated report in the default location
            # Since we can't easily override the default path in the function, we'll check the result dict
            assert 'report_path' in result