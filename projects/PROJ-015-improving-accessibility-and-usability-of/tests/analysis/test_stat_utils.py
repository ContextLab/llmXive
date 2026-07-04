import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
import tempfile
from analysis.stat_utils import StatUtils

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'participant_id': [1, 1, 2, 2, 3, 3],
        'interface_type': ['Traditional', 'Explainable', 'Traditional', 'Explainable', 'Traditional', 'Explainable'],
        'completion_time': [10.5, 9.2, 11.0, 8.5, 10.0, 9.8],
        'explanation_engagement_time': [0.0, 5.2, 0.0, 4.8, 0.0, 6.1]
    })

@pytest.fixture
def temp_raw_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock session files
        sessions = [
            {
                "session_id": "s1",
                "participant_id": 1,
                "interface_type": "Traditional",
                "metrics": {
                    "completion_time": 10.5,
                    "error_count": 2,
                    "explanation_engagement_time": 0.0
                }
            },
            {
                "session_id": "s2",
                "participant_id": 1,
                "interface_type": "Explainable",
                "metrics": {
                    "completion_time": 9.2,
                    "error_count": 1,
                    "explanation_engagement_time": 5.2
                }
            },
            {
                "session_id": "s3",
                "participant_id": 2,
                "interface_type": "Traditional",
                "metrics": {
                    "completion_time": 11.0,
                    "error_count": 3,
                    "explanation_engagement_time": 0.0
                }
            },
            {
                "session_id": "s4",
                "participant_id": 2,
                "interface_type": "Explainable",
                "metrics": {
                    "completion_time": 8.5,
                    "error_count": 0,
                    "explanation_engagement_time": 4.8
                }
            }
        ]
        
        for i, session in enumerate(sessions):
            with open(os.path.join(tmpdir, f"session_{i}.json"), 'w') as f:
                json.dump(session, f)
        
        yield tmpdir

def test_run_shapiro_wilk(sample_data):
    # Test with completion_time
    result = StatUtils.run_shapiro_wilk(sample_data['completion_time'])
    assert 'statistic' in result
    assert 'pvalue' in result
    assert isinstance(result['statistic'], float)
    assert isinstance(result['pvalue'], float)

def test_run_repeated_measures_anova(sample_data):
    # Test with completion_time, 2 conditions
    result = StatUtils.run_repeated_measures_anova(
        sample_data, 
        within_subject_col='interface_type', 
        dependent_col='completion_time'
    )
    assert 'F_statistic' in result
    assert 'p_value' in result
    assert result['method'] == "Paired t-test (equivalent to RM-ANOVA for 2 conditions)"

def test_generate_descriptive_stats_report(temp_raw_data_dir, tmp_path):
    output_file = tmp_path / "descriptive_stats.csv"
    success = StatUtils.generate_descriptive_stats_report(temp_raw_data_dir, str(output_file))
    
    assert success
    assert output_file.exists()
    
    df = pd.read_csv(output_file)
    assert 'interface_type' in df.columns
    assert 'metric_name' in df.columns
    assert 'mean' in df.columns
    assert 'std' in df.columns
    assert 'count' in df.columns
    
    # Check that we have rows for both interface types
    assert len(df) == 2
    assert set(df['interface_type']) == {'Traditional', 'Explainable'}
    assert all(df['metric_name'] == 'explanation_engagement_time')
    
    # Check specific values (manual calculation from sample data)
    # Traditional: 0.0, 0.0 -> mean=0.0, std=0.0 (or NaN depending on ddof)
    # Explainable: 5.2, 4.8 -> mean=5.0, std=0.2828...
    trad_row = df[df['interface_type'] == 'Traditional'].iloc[0]
    expl_row = df[df['interface_type'] == 'Explainable'].iloc[0]
    
    assert trad_row['mean'] == 0.0
    assert expl_row['mean'] == 5.0
    # std for [5.2, 4.8] with ddof=1 is 0.282842712474619
    assert np.isclose(expl_row['std'], 0.282842712474619, rtol=1e-4)
