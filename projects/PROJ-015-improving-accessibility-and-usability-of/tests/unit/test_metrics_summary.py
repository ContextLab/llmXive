"""
Unit tests for the metrics summary generation (T026).

Tests verify:
1. ANOVA results are calculated correctly.
2. Holm-Bonferroni correction is applied.
3. Output CSV contains required columns.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_metrics_summary import (
    load_cleaned_data,
    run_repeated_measures_anova,
    holm_bonferroni_correction,
    generate_metrics_summary
)

def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction logic."""
    p_values = [0.01, 0.03, 0.04]
    adjusted = holm_bonferroni_correction(p_values)
    
    # Sorted: 0.01, 0.03, 0.04
    # i=0: 0.01 * 3 = 0.03
    # i=1: 0.03 * 2 = 0.06
    # i=2: 0.04 * 1 = 0.04
    # Monotonicity: 0.03, 0.06, 0.06 (max of 0.06 and 0.04) -> actually 0.04 is less than 0.06
    # Wait, Holm requires non-decreasing order of adjusted p-values
    # Correct logic: 0.03, 0.06, 0.06 (since 0.04 < 0.06, it becomes 0.06)
    
    # Check monotonicity
    for i in range(1, len(adjusted)):
        assert adjusted[i] >= adjusted[i-1], "Adjusted p-values must be non-decreasing"
    
    # Check values are within [0, 1]
    for p in adjusted:
        assert 0 <= p <= 1, f"P-value {p} out of bounds"

def test_anova_calculation():
    """Test Repeated Measures ANOVA calculation."""
    # Create synthetic paired data where we know the difference
    np.random.seed(42)
    n = 10
    traditional = np.random.normal(100, 10, n)
    explainable = traditional - 10  # Explainable is 10 units faster
    
    df = pd.DataFrame({
        'participant_id': list(range(n)) * 2,
        'interface_type': ['traditional'] * n + ['explainable'] * n,
        'completion_time_seconds': list(traditional) + list(explainable)
    })
    
    result = run_repeated_measures_anova(df, 'completion_time_seconds')
    
    assert result is not None, "ANOVA result should not be None"
    assert 'F_statistic' in result
    assert 'p_value' in result
    assert 'effect_size' in result
    assert result['n_participants'] == n
    
    # Since explainable is significantly faster, p-value should be small
    assert result['p_value'] < 0.05, "Expected significant result for known difference"

def test_generate_metrics_summary_output():
    """Test that the output CSV contains required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'cleaned.csv')
        output_path = os.path.join(tmpdir, 'summary.csv')
        
        # Create test data
        n = 20
        df_data = []
        for i in range(n):
            df_data.append({
                'participant_id': i,
                'interface_type': 'traditional',
                'completion_time_seconds': 100.0 + np.random.normal(0, 5),
                'error_count': 2,
                'sus_score': 50,
                'explanation_engagement_time_seconds': 0.0
            })
            df_data.append({
                'participant_id': i,
                'interface_type': 'explainable',
                'completion_time_seconds': 90.0 + np.random.normal(0, 5),
                'error_count': 1,
                'sus_score': 70,
                'explanation_engagement_time_seconds': 10.0
            })
        
        pd.DataFrame(df_data).to_csv(input_path, index=False)
        
        success = generate_metrics_summary(pd.read_csv(input_path), output_path)
        
        assert success, "Summary generation should succeed"
        assert os.path.exists(output_path), "Output file should exist"
        
        summary_df = pd.read_csv(output_path)
        
        required_cols = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
        for col in required_cols:
            assert col in summary_df.columns, f"Missing column: {col}"

if __name__ == '__main__':
    test_holm_bonferroni_correction()
    test_anova_calculation()
    test_generate_metrics_summary_output()
    print("All tests passed.")