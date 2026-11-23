import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.stability_check import load_robustness_report, analyze_stability, write_results

@pytest.fixture
def sample_robustness_report():
    return pd.DataFrame({
        'threshold': [50, 100, 150],
        'interaction_coefficient': [0.1, 0.12, 0.09],
        'interaction_pvalue': [0.03, 0.02, 0.04],
        'interaction_p_adj': [0.06, 0.04, 0.08],
        'mean_belief_rating': [4.2, 4.1, 4.3],
        'std_dev_belief': [0.5, 0.6, 0.4]
    })

def test_load_robustness_report_basic(sample_robustness_report, tmp_path):
    # Save the report to a temporary file
    report_path = tmp_path / "robustness_report.csv"
    sample_robustness_report.to_csv(report_path, index=False)
    
    loaded = load_robustness_report(str(report_path))
    assert len(loaded) == 3
    assert 'threshold' in loaded.columns
    assert 'interaction_coefficient' in loaded.columns

def test_analyze_stability_consistent(sample_robustness_report):
    stability = analyze_stability(sample_robustness_report)
    assert 'consistent_direction' in stability
    assert 'consistent_significance' in stability
    assert stability['consistent_direction'] is True  # All coefficients are positive
    # Check significance based on adjusted p-values
    assert stability['consistent_significance'] is True  # All adjusted p-values < 0.1

def test_analyze_stability_inconsistent_direction():
    inconsistent_data = pd.DataFrame({
        'threshold': [50, 100, 150],
        'interaction_coefficient': [0.1, -0.1, 0.05],
        'interaction_pvalue': [0.03, 0.02, 0.04],
        'interaction_p_adj': [0.06, 0.04, 0.08]
    })
    stability = analyze_stability(inconsistent_data)
    assert stability['consistent_direction'] is False

def test_analyze_stability_inconsistent_significance():
    inconsistent_data = pd.DataFrame({
        'threshold': [50, 100, 150],
        'interaction_coefficient': [0.1, 0.12, 0.09],
        'interaction_pvalue': [0.03, 0.02, 0.04],
        'interaction_p_adj': [0.06, 0.15, 0.08]  # One is not significant
    })
    stability = analyze_stability(inconsistent_data)
    assert stability['consistent_significance'] is False

def test_write_results(tmp_path):
    stability_results = {
        'consistent_direction': True,
        'consistent_significance': True,
        'ci_overlap_summary': 'High overlap'
    }
    output_path = tmp_path / "stability_check.json"
    write_results(stability_results, str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0