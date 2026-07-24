import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.metrics import (
    calculate_aggregate_metrics,
    calculate_confidence_interval,
    load_simulation_results
)

class TestClopperPearsonVerification:
    def test_ci_zero_successes(self):
        """Test CI when successes = 0"""
        lower, upper = calculate_confidence_interval(0, 100, alpha=0.05)
        assert lower == 0.0
        assert upper > 0.0
        assert upper < 0.1  # Should be small

    def test_ci_full_successes(self):
        """Test CI when successes = n"""
        lower, upper = calculate_confidence_interval(100, 100, alpha=0.05)
        assert lower > 0.9
        assert upper == 1.0

    def test_ci_typical(self):
        """Test CI for typical binomial proportion"""
        # 50 successes out of 100, 95% CI
        lower, upper = calculate_confidence_interval(50, 100, alpha=0.05)
        assert 0.4 < lower < 0.5
        assert 0.5 < upper < 0.6

class TestEmpiricalErrorRate:
    @pytest.fixture
    def sample_null_data(self):
        """Create a mock DataFrame with null hypothesis results"""
        data = {
            'config_id': ['cfg1'] * 100,
            'scaling_method': ['standard'] * 100,
            'test_type': ['t_test'] * 100,
            'p_value': np.random.uniform(0, 1, 100),
            'ground_truth': ['null'] * 100
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_alt_data(self):
        """Create a mock DataFrame with alternative hypothesis results"""
        # Generate p-values skewed towards 0 (high power)
        p_vals = np.concatenate([np.random.uniform(0, 0.1, 80), np.random.uniform(0.1, 1, 20)])
        data = {
            'config_id': ['cfg1'] * 100,
            'scaling_method': ['standard'] * 100,
            'test_type': ['t_test'] * 100,
            'p_value': p_vals,
            'ground_truth': ['alternative'] * 100
        }
        return pd.DataFrame(data)

    def test_aggregate_null(self, sample_null_data, tmp_path):
        """Test aggregation for null hypothesis (Type I error)"""
        output_path = str(tmp_path / "aggregate_null.csv")
        result_df = calculate_aggregate_metrics(
            df=sample_null_data,
            output_path=output_path,
            alpha=0.05
        )

        assert len(result_df) == 1
        assert result_df['config_id'].iloc[0] == 'cfg1'
        assert pd.notna(result_df['error_rate'].iloc[0])
        assert pd.isna(result_df['power'].iloc[0]) # Power should be NaN for null
        assert 0.0 <= result_df['error_rate'].iloc[0] <= 1.0
        
        # Check file exists
        assert Path(output_path).exists()

    def test_aggregate_alternative(self, sample_alt_data, tmp_path):
        """Test aggregation for alternative hypothesis (Power)"""
        output_path = str(tmp_path / "aggregate_alt.csv")
        result_df = calculate_aggregate_metrics(
            df=sample_alt_data,
            output_path=output_path,
            alpha=0.05
        )

        assert len(result_df) == 1
        assert result_df['config_id'].iloc[0] == 'cfg1'
        assert pd.isna(result_df['error_rate'].iloc[0]) # Error rate NaN for alt
        assert pd.notna(result_df['power'].iloc[0])
        assert result_df['power'].iloc[0] > 0.5 # Should be high power
        
        # Check file exists
        assert Path(output_path).exists()

    def test_combined_data(self, sample_null_data, sample_alt_data, tmp_path):
        """Test aggregation with both null and alternative data"""
        combined = pd.concat([sample_null_data, sample_alt_data], ignore_index=True)
        output_path = str(tmp_path / "aggregate_combined.csv")
        result_df = calculate_aggregate_metrics(
            df=combined,
            output_path=output_path,
            alpha=0.05
        )

        # Should have 2 rows: one for null, one for alternative
        assert len(result_df) == 2
        
        null_row = result_df[result_df['ground_truth'] == 'null'] if 'ground_truth' in result_df.columns else result_df[result_df['error_rate'].notna()]
        alt_row = result_df[result_df['power'].notna()]
        
        assert len(null_row) == 1
        assert len(alt_row) == 1

class TestFullPipeline:
    def test_run_full_analysis_pipeline_with_data(self, tmp_path):
        """Test the run_full_analysis_pipeline function"""
        # Create dummy data
        data = {
            'config_id': ['c1'] * 50,
            'scaling_method': ['s1'] * 50,
            'test_type': ['t1'] * 50,
            'p_value': np.random.uniform(0, 1, 50),
            'ground_truth': ['null'] * 50
        }
        df = pd.DataFrame(data)
        
        # Save to temp file to simulate load
        input_path = str(tmp_path / "sim_results.csv")
        df.to_csv(input_path, index=False)
        
        result = run_full_analysis_pipeline(input_path=input_path)
        
        assert 'metrics' in result
        assert 'status' in result
        assert result['status'] == 'success'
        assert len(result['metrics']) > 0
