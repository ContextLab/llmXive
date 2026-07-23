"""
Test for Task T026: Generate metrics_summary.csv
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_metrics_summary import (
    load_cleaned_data,
    run_repeated_measures_anova,
    holm_bonferroni_correction,
    generate_metrics_summary
)

@pytest.fixture
def sample_cleaned_data():
    """Generate a small sample dataset for testing ANOVA."""
    # Create a dataset where Explainable is consistently faster
    n_participants = 20
    data = []
    
    for i in range(n_participants):
        # Traditional: higher completion time
        data.append({
            "participant_id": f"P{i:03d}",
            "interface_type": "traditional",
            "completion_time_seconds": 100.0 + np.random.normal(0, 5),
            "error_count": 5 + np.random.normal(0, 1),
            "sus_score": 50 + np.random.normal(0, 5),
            "explanation_engagement_time_seconds": 0.0
        })
        # Explainable: lower completion time (effect)
        data.append({
            "participant_id": f"P{i:03d}",
            "interface_type": "explainable",
            "completion_time_seconds": 80.0 + np.random.normal(0, 5), # 20s faster
            "error_count": 3 + np.random.normal(0, 1),
            "sus_score": 70 + np.random.normal(0, 5),
            "explanation_engagement_time_seconds": 15.0
        })
        
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_file(sample_cleaned_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_cleaned_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_cleaned_data(temp_input_file):
    """Test loading cleaned data."""
    df = load_cleaned_data(temp_input_file)
    assert len(df) == 40 # 20 participants * 2 conditions
    assert 'completion_time_seconds' in df.columns
    assert 'interface_type' in df.columns

def test_repeated_measures_anova(sample_cleaned_data):
    """Test the RM-ANOVA function."""
    result = run_repeated_measures_anova(sample_cleaned_data, 'completion_time_seconds')
    
    assert 'F_statistic' in result
    assert 'p_value' in result
    assert 'effect_size' in result
    
    # With the constructed data (20s difference), we expect a significant result
    assert result['F_statistic'] > 0
    assert result['p_value'] < 0.05 # Should be significant given the constructed effect
    assert result['n_subjects'] == 20

def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction."""
    p_values = [0.04, 0.02, 0.01, 0.005]
    adjusted = holm_bonferroni_correction(p_values)
    
    assert len(adjusted) == 4
    # Adjusted values should be >= original values
    assert all(adj >= orig for adj, orig in zip(adjusted, p_values))
    # Values should be <= 1.0
    assert all(adj <= 1.0 for adj in adjusted)

def test_generate_metrics_summary(temp_input_file):
    """Test the full generation of metrics summary."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "metrics_summary.csv")
        
        df = load_cleaned_data(temp_input_file)
        summary_df = generate_metrics_summary(df, output_path)
        
        assert os.path.exists(output_path)
        assert len(summary_df) == 3 # 3 metrics
        
        # Check columns
        required_cols = ['metric_name', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
        for col in required_cols:
            assert col in summary_df.columns
        
        # Check that at least one metric is significant (completion time)
        completion_row = summary_df[summary_df['metric_name'] == 'Completion Time']
        assert len(completion_row) == 1
        assert completion_row['p_value'].values[0] < 0.05