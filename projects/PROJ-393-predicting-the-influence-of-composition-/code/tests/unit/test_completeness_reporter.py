import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.preprocessing.completeness_reporter import (
    calculate_source_proportions,
    generate_completeness_report,
    run_completeness_report_pipeline
)


class TestCompletenessReporter:
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe with source_type column."""
        data = {
            'alloy': ['Co2MnGa', 'Co2MnAl', 'Fe3Ga', 'NiMnSb', 'Co2FeAl'],
            'source_type': ['NIST', 'NIST', 'Journal', 'Manual', 'NIST'],
            'coercivity': [100.0, 200.0, 150.0, 300.0, 120.0],
            'saturation': [100.0, 100.0, 100.0, 100.0, 100.0]
        }
        return pd.DataFrame(data)

    def test_calculate_source_proportions(self, sample_df):
        """Test that proportions are calculated correctly."""
        proportions = calculate_source_proportions(sample_df)
        
        # NIST: 3/5 = 0.6
        # Journal: 1/5 = 0.2
        # Manual: 1/5 = 0.2
        assert abs(proportions['NIST'] - 0.6) < 1e-6
        assert abs(proportions['Journal'] - 0.2) < 1e-6
        assert abs(proportions['Manual'] - 0.2) < 1e-6
        assert len(proportions) == 3

    def test_calculate_source_proportions_empty_df(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['source_type'])
        proportions = calculate_source_proportions(df)
        assert proportions == {}

    def test_calculate_source_proportions_missing_column(self, sample_df):
        """Test handling when source_type is missing."""
        df = sample_df.drop(columns=['source_type'])
        # Should not raise, should warn and use 'unknown' or fallback
        proportions = calculate_source_proportions(df)
        # Since target_source is also missing, it should default to 'unknown'
        assert 'unknown' in proportions

    def test_generate_completeness_report(self, sample_df):
        """Test full report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            
            report = generate_completeness_report(sample_df, output_path)
            
            assert output_path.exists()
            assert report['report_type'] == 'data_completeness'
            assert report['spec_id'] == 'SC-004'
            assert report['total_records'] == 5
            assert 'source_proportions' in report
            assert 'columns_present' in report
            assert 'missing_column_counts' in report

            # Verify JSON content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['total_records'] == 5
            assert abs(loaded['source_proportions']['NIST'] - 0.6) < 1e-6

    def test_run_completeness_report_pipeline(self, sample_df):
        """Test the full pipeline function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.json"
            
            sample_df.to_csv(input_path, index=False)
            
            report = run_completeness_report_pipeline(input_path, output_path)
            
            assert output_path.exists()
            assert report['total_records'] == 5