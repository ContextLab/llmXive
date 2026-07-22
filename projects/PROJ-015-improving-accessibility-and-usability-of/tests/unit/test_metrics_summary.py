"""
Unit tests for the metrics summary generation (T026).
Verifies that the ANOVA and Holm-Bonferroni logic produces real, non-fabricated results.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.generate_metrics_summary import run_repeated_measures_anova, holm_bonferroni_correction, generate_metrics_summary

def test_anova_deterministic():
    """
    Test that ANOVA produces deterministic results on a known dataset.
    We create a small dataset where we know the effect.
    """
    # Create a small dataset: 10 participants, 2 conditions
    # Traditional: 100, 105, 110... (mean ~105)
    # Explainable: 90, 95, 100... (mean ~95) -> Should show significant difference
    data = []
    for i in range(10):
        data.append({
            'participant_id': f'P{i}',
            'interface_type': 'traditional',
            'completion_time_seconds': 100 + i * 2 + np.random.normal(0, 1),
            'error_count': 5,
            'sus_score': 80,
            'explanation_engagement_time_seconds': 0.0
        })
        data.append({
            'participant_id': f'P{i}',
            'interface_type': 'explainable',
            'completion_time_seconds': 90 + i * 2 + np.random.normal(0, 1),
            'error_count': 3,
            'sus_score': 85,
            'explanation_engagement_time_seconds': 5.0
        })
    
    # Fix seed for reproducibility in test
    np.random.seed(42)
    # Regenerate with fixed seed
    data = []
    for i in range(10):
        data.append({
            'participant_id': f'P{i}',
            'interface_type': 'traditional',
            'completion_time_seconds': 100 + i * 2 + np.random.normal(0, 1),
            'error_count': 5,
            'sus_score': 80,
            'explanation_engagement_time_seconds': 0.0
        })
        data.append({
            'participant_id': f'P{i}',
            'interface_type': 'explainable',
            'completion_time_seconds': 90 + i * 2 + np.random.normal(0, 1),
            'error_count': 3,
            'sus_score': 85,
            'explanation_engagement_time_seconds': 5.0
        })
    
    df = pd.DataFrame(data)
    
    result = run_repeated_measures_anova(df, 'completion_time_seconds')
    
    assert result['metric_name'] == 'completion_time_seconds'
    assert not np.isnan(result['F_statistic']), "F-statistic should be calculated"
    assert not np.isnan(result['p_value']), "P-value should be calculated"
    assert result['n_participants'] == 10
    
    # Since Explainable is faster (lower time), we expect a significant difference
    # The mean difference is 10, noise is 1. Should be significant.
    assert result['p_value'] < 0.05, f"Expected p < 0.05, got {result['p_value']}"

def test_holm_bonferroni():
    """
    Test Holm-Bonferroni correction logic.
    """
    p_values = [0.01, 0.04, 0.03, 0.005]
    corrected = holm_bonferroni_correction(p_values)
    
    assert len(corrected) == 4
    # Corrected p-values should be >= original p-values
    for orig, adj in zip(p_values, corrected):
        assert adj >= orig, f"Corrected p-value {adj} should be >= original {orig}"
    
    # Check monotonicity in the sorted order
    sorted_indices = sorted(range(len(p_values)), key=lambda k: p_values[k])
    sorted_adj = [corrected[i] for i in sorted_indices]
    for i in range(1, len(sorted_adj)):
        assert sorted_adj[i] >= sorted_adj[i-1], "Corrected p-values must be monotonic"

def test_generate_metrics_summary_writes_file(tmp_path):
    """
    Test that generate_metrics_summary actually writes the CSV file.
    """
    # Create dummy data
    data = []
    for i in range(5):
        data.append({'participant_id': f'P{i}', 'interface_type': 'traditional', 
                     'completion_time_seconds': 100.0, 'error_count': 5, 'sus_score': 80,
                     'explanation_engagement_time_seconds': 0.0})
        data.append({'participant_id': f'P{i}', 'interface_type': 'explainable', 
                     'completion_time_seconds': 90.0, 'error_count': 3, 'sus_score': 85,
                     'explanation_engagement_time_seconds': 5.0})
    
    df = pd.DataFrame(data)
    output_path = tmp_path / "metrics_summary.csv"
    
    generate_metrics_summary(df, str(output_path))
    
    assert output_path.exists(), "metrics_summary.csv should be created"
    
    df_out = pd.read_csv(output_path)
    assert 'metric_name' in df_out.columns
    assert 'F_statistic' in df_out.columns
    assert 'p_value' in df_out.columns
    assert 'adjusted_p_value' in df_out.columns
    assert len(df_out) == 3 # 3 metrics

if __name__ == "__main__":
    pytest.main([__file__, "-v"])