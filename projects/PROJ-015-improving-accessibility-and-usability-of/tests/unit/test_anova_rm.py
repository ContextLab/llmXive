"""
Unit tests for Repeated Measures ANOVA implementation in stats_engine.

Verifies:
1. Correct F-statistic and p-value calculation on a known dataset.
2. Execution regardless of normality log content (ignoring Shapiro-Wilk).
3. Correct Holm-Bonferroni correction.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.stats_engine import run_anova_rm, holm_bonferroni_correction, generate_metrics_summary

def test_run_anova_rm_known_dataset():
    """
    Test ANOVA calculation with a small, manually verifiable dataset.
    
    Dataset:
    Participant | Condition | Score
    P1          | A         | 10
    P1          | B         | 12
    P2          | A         | 11
    P2          | B         | 13
    P3          | A         | 9
    P3          | B         | 11
    
    This is a perfect linear relationship.
    Mean A = 10, Mean B = 12.
    Grand Mean = 11.
    
    SS_condition = n * sum((mean_cond - grand_mean)^2) = 3 * ((10-11)^2 + (12-11)^2) = 3 * (1 + 1) = 6
    SS_subject = k * sum((mean_subj - grand_mean)^2) = 2 * ((11-11)^2 + (12-11)^2 + (10-11)^2) = 2 * (0 + 1 + 1) = 4
    SS_total = sum((x - grand_mean)^2)
       P1: (10-11)^2 + (12-11)^2 = 1 + 1 = 2
       P2: (11-11)^2 + (13-11)^2 = 0 + 4 = 4
       P3: (9-11)^2 + (11-11)^2 = 4 + 0 = 4
       Total = 10
    SS_error = SS_total - SS_condition - SS_subject = 10 - 6 - 4 = 0
    
    Since SS_error is 0, the F-stat should be infinite (or very large) and p-value 0.
    """
    data = {
        'participant_id': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3'],
        'interface_type': ['A', 'B', 'A', 'B', 'A', 'B'],
        'score': [10, 12, 11, 13, 9, 11]
    }
    df = pd.DataFrame(data)
    
    result = run_anova_rm(df, 'score')
    
    assert result['metric'] == 'score'
    assert result['n_participants'] == 3
    assert result['n_conditions'] == 2
    assert result['F_stat'] == float('inf') or result['F_stat'] > 1000.0 # Allow for float precision
    assert result['p_val'] == 0.0

def test_run_anova_rm_with_noise():
    """
    Test ANOVA with a dataset that has some variance.
    """
    # Create a dataset with known variance structure
    np.random.seed(42)
    n_subjects = 10
    n_conditions = 2
    
    participants = []
    conditions = []
    scores = []
    
    for i in range(n_subjects):
        # Base subject effect
        subj_effect = np.random.normal(0, 2)
        
        for j in range(n_conditions):
            # Condition effect (B is higher than A by 5)
            cond_effect = 5 if j == 1 else 0
            noise = np.random.normal(0, 1)
            
            participants.append(f'S{i}')
            conditions.append(['A', 'B'][j])
            scores.append(10 + subj_effect + cond_effect + noise)
    
    df = pd.DataFrame({
        'participant_id': participants,
        'interface_type': conditions,
        'score': scores
    })
    
    result = run_anova_rm(df, 'score')
    
    assert result['metric'] == 'score'
    assert result['n_participants'] == n_subjects
    assert result['n_conditions'] == n_conditions
    assert result['F_stat'] > 0
    assert 0.0 <= result['p_val'] <= 1.0
    # With a strong effect size (5 units vs noise 1), p-value should be small
    assert result['p_val'] < 0.05, f"Expected significant p-value, got {result['p_val']}"

def test_holm_bonferroni_correction():
    """
    Test Holm-Bonferroni correction on known p-values.
    """
    p_values = [0.01, 0.04, 0.03, 0.005]
    corrected = holm_bonferroni_correction(p_values)
    
    assert len(corrected) == 4
    # Sorted p: 0.005, 0.01, 0.03, 0.04
    # Corrected:
    # 0.005 * 4 = 0.02
    # 0.01 * 3 = 0.03
    # 0.03 * 2 = 0.06
    # 0.04 * 1 = 0.04 -> max(0.04, 0.06) = 0.06
    
    # Reorder back:
    # 0.01 -> 0.03
    # 0.04 -> 0.06
    # 0.03 -> 0.06
    # 0.005 -> 0.02
    
    expected_map = {
        0.01: 0.03,
        0.04: 0.06,
        0.03: 0.06,
        0.005: 0.02
    }
    
    for p, corr in zip(p_values, corrected):
        assert abs(corr - expected_map[p]) < 1e-6, f"Expected {expected_map[p]} for {p}, got {corr}"

def test_anova_runs_regardless_of_normality():
    """
    Verify that run_anova_rm does not check for normality or raise errors
    based on normality assumptions (as per spec FR-002 amendment).
    
    We simulate a non-normal distribution and ensure the function still runs.
    """
    # Create a highly skewed distribution (exponential)
    np.random.seed(42)
    n_subjects = 20
    n_conditions = 2
    
    participants = []
    conditions = []
    scores = []
    
    for i in range(n_subjects):
        subj_effect = np.random.exponential(2)
        for j in range(n_conditions):
            cond_effect = 1 if j == 1 else 0
            noise = np.random.exponential(0.5)
            participants.append(f'S{i}')
            conditions.append(['A', 'B'][j])
            scores.append(subj_effect + cond_effect + noise)
    
    df = pd.DataFrame({
        'participant_id': participants,
        'interface_type': conditions,
        'score': scores
    })
    
    # This should NOT raise an error about normality
    try:
        result = run_anova_rm(df, 'score')
        assert result['F_stat'] is not None
        assert result['p_val'] is not None
    except Exception as e:
        pytest.fail(f"run_anova_rm raised an error on non-normal data: {e}")

def test_generate_metrics_summary_writes_file(tmp_path):
    """
    Test that generate_metrics_summary writes the output file correctly.
    """
    data = {
        'participant_id': ['P1', 'P1', 'P2', 'P2'],
        'interface_type': ['A', 'B', 'A', 'B'],
        'metric1': [10, 12, 11, 13],
        'metric2': [5, 6, 4, 5]
    }
    df = pd.DataFrame(data)
    
    output_file = tmp_path / "metrics_summary.csv"
    
    result_df = generate_metrics_summary(df, ['metric1', 'metric2'], str(output_file))
    
    assert output_file.exists()
    assert result_df is not None
    assert 'metric' in result_df.columns
    assert 'F_stat' in result_df.columns
    assert 'p_val' in result_df.columns
    assert 'corrected_p' in result_df.columns
    assert len(result_df) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])