"""
Unit tests for the Repeated Measures ANOVA implementation in stats_engine.py.

Tests verify:
1. Correct calculation of F-statistic and p-value using known datasets.
2. The function runs regardless of normality (ignoring Shapiro-Wilk).
3. Proper error handling for missing columns and insufficient data.
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.stats_engine import run_anova_rm, generate_metrics_summary
import tempfile
import os

class TestRepeatedMeasuresANOVA:
    
    def test_known_dataset_f_statistic(self):
        """
        Test ANOVA calculation against a known dataset.
        We construct a simple dataset where we can manually verify the F-stat.
        
        Scenario: 3 participants, 2 conditions.
        Data:
          P1: CondA=10, CondB=12 -> diff=2
          P2: CondA=14, CondB=16 -> diff=2
          P3: CondA=12, CondB=14 -> diff=2
        
        Since the difference is constant, the variance between conditions 
        should be significant relative to error.
        
        Actually, let's use a standard example:
        P1: 2, 4
        P2: 4, 6
        P3: 3, 5
        
        Means: A=3, B=5. Grand Mean = 4.
        SS_between = 3 * ((3-4)^2 + (5-4)^2) = 3 * (1 + 1) = 6.
        SS_subjects = 2 * ((3-4)^2 + (5-4)^2 + (4-4)^2) -> Wait, subject means:
        P1 mean=3, P2 mean=5, P3 mean=4.
        SS_subjects = 2 * ((3-4)^2 + (5-4)^2 + (4-4)^2) = 2 * (1 + 1 + 0) = 4.
        SS_total: values [2,4, 4,6, 3,5]. Grand mean 4.
        (2-4)^2=4, (4-4)^2=0, (4-4)^2=0, (6-4)^2=4, (3-4)^2=1, (5-4)^2=1.
        SS_total = 10.
        SS_error = 10 - 6 - 4 = 0.
        If SS_error is 0, F is infinite. Let's add noise.
        
        Modified:
        P1: 2, 5
        P2: 4, 7
        P3: 3, 6
        
        Means: A=3, B=6. Grand=4.5.
        SS_between = 3 * ((3-4.5)^2 + (6-4.5)^2) = 3 * (2.25 + 2.25) = 13.5.
        Subject means: P1=3.5, P2=5.5, P3=4.5.
        SS_subjects = 2 * ((3.5-4.5)^2 + (5.5-4.5)^2 + (4.5-4.5)^2) = 2 * (1 + 1 + 0) = 4.
        SS_total: 
          2: (2-4.5)^2 = 6.25
          5: (5-4.5)^2 = 0.25
          4: (4-4.5)^2 = 0.25
          7: (7-4.5)^2 = 6.25
          3: (3-4.5)^2 = 2.25
          6: (6-4.5)^2 = 2.25
          Sum = 17.5
        SS_error = 17.5 - 13.5 - 4 = 0. Still zero? 
        Let's try a standard scipy example.
        
        Using scipy.stats.f_oneway for independent samples is not RM ANOVA.
        We will verify our manual calculation logic against a known result from a library
        like pingouin if available, or just verify the code runs and produces a finite number.
        
        Let's create a dataset that we know yields a specific F-stat via manual calc.
        P1: 10, 20 (diff 10)
        P2: 10, 20 (diff 10)
        P3: 10, 20 (diff 10)
        This is perfect correlation, F should be huge.
        
        Let's use:
        P1: 1, 3
        P2: 2, 4
        P3: 3, 5
        
        Means: A=2, B=4. Grand=3.
        SS_between = 3 * ((2-3)^2 + (4-3)^2) = 3 * 2 = 6.
        Subject means: 2, 3, 4.
        SS_subjects = 2 * ((2-3)^2 + (3-3)^2 + (4-3)^2) = 2 * 2 = 4.
        SS_total: 
          1: 4
          3: 0
          2: 1
          4: 1
          3: 0
          5: 4
          Sum = 10.
        SS_error = 10 - 6 - 4 = 0.
        
        Okay, let's add noise to make SS_error > 0.
        P1: 1, 4
        P2: 2, 5
        P3: 3, 6
        
        Means: A=2, B=5. Grand=3.5.
        SS_between = 3 * ((2-3.5)^2 + (5-3.5)^2) = 3 * (2.25 + 2.25) = 13.5.
        Subject means: 2.5, 3.5, 4.5.
        SS_subjects = 2 * ((2.5-3.5)^2 + (3.5-3.5)^2 + (4.5-3.5)^2) = 2 * (1+0+1) = 4.
        SS_total:
          1: (1-3.5)^2 = 6.25
          4: (4-3.5)^2 = 0.25
          2: (2-3.5)^2 = 2.25
          5: (5-3.5)^2 = 2.25
          3: (3-3.5)^2 = 0.25
          6: (6-3.5)^2 = 6.25
          Sum = 17.5.
        SS_error = 17.5 - 13.5 - 4 = 0.
        
        Why is SS_error always 0? Because the difference is constant (3).
        Let's vary the difference.
        P1: 1, 4 (diff 3)
        P2: 2, 6 (diff 4)
        P3: 3, 5 (diff 2)
        
        Means: A=2, B=5. Grand=3.5.
        SS_between = 13.5 (same as above).
        Subject means: 2.5, 4.0, 4.0.
        SS_subjects = 2 * ((2.5-3.5)^2 + (4.0-3.5)^2 + (4.0-3.5)^2) = 2 * (1 + 0.25 + 0.25) = 3.0.
        SS_total:
          1: 6.25
          4: 0.25
          2: 2.25
          6: 6.25
          3: 0.25
          5: 2.25
          Sum = 17.5.
        SS_error = 17.5 - 13.5 - 3.0 = 1.0.
        
        df_between = 2-1 = 1.
        df_error = (2-1)*(3-1) = 2.
        MS_between = 13.5 / 1 = 13.5.
        MS_error = 1.0 / 2 = 0.5.
        F = 13.5 / 0.5 = 27.0.
        
        p_val = 1 - F.cdf(27, 1, 2).
        """
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2', 'P3', 'P3'],
            'interface_type': ['A', 'B', 'A', 'B', 'A', 'B'],
            'metric': [1, 4, 2, 6, 3, 5]
        }
        df = pd.DataFrame(data)
        
        result = run_anova_rm(df, 'metric')
        
        assert abs(result['F_stat'] - 27.0) < 1e-6, f"Expected F=27.0, got {result['F_stat']}"
        assert result['p_val'] > 0 and result['p_val'] < 1, "p-value must be between 0 and 1"
        assert result['n_participants'] == 3
        assert result['n_observations'] == 6

    def test_runs_ignoring_normality(self):
        """
        Verify that run_anova_rm executes successfully even if the data
        is non-normal (which would fail a Shapiro-Wilk based check).
        We use a highly skewed distribution.
        """
        # Create non-normal data (exponential)
        np.random.seed(42)
        n_subjects = 10
        n_conditions = 2
        
        data = []
        for i in range(n_subjects):
            # Subject effect
            subj_base = np.random.uniform(10, 20)
            # Condition A
            val_a = subj_base + np.random.exponential(2)
            # Condition B (shifted)
            val_b = subj_base + np.random.exponential(2) + 5
            
            data.append({'participant_id': f'S{i}', 'interface_type': 'A', 'metric': val_a})
            data.append({'participant_id': f'S{i}', 'interface_type': 'B', 'metric': val_b})
        
        df = pd.DataFrame(data)
        
        # This should not raise an error even if data is non-normal
        result = run_anova_rm(df, 'metric')
        
        assert 'F_stat' in result
        assert 'p_val' in result
        assert result['n_participants'] == 10

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise ValueError."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'interface_type': ['A', 'B']
            # Missing 'metric' column
        })
        
        with pytest.raises(ValueError, match="missing required columns"):
            run_anova_rm(df, 'metric')

    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises ValueError."""
        df = pd.DataFrame({
            'participant_id': ['P1'],
            'interface_type': ['A', 'B'],
            'metric': [10, 20]
        })
        
        # Only 1 participant, need at least 2 for ANOVA
        with pytest.raises(ValueError, match="At least 2 subjects"):
            run_anova_rm(df, 'metric')

    def test_generate_metrics_summary_writes_file(self):
        """Test that generate_metrics_summary writes the correct CSV file."""
        # Create sample data
        data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'interface_type': ['A', 'B', 'A', 'B'],
            'completion_time': [10, 12, 11, 13],
            'error_count': [1, 0, 2, 1]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            generate_metrics_summary(df, ['completion_time'], output_path)
            
            assert os.path.exists(output_path)
            
            result_df = pd.read_csv(output_path)
            assert 'metric' in result_df.columns
            assert 'F_stat' in result_df.columns
            assert 'p_val' in result_df.columns
            assert len(result_df) == 1
            assert result_df.iloc[0]['metric'] == 'completion_time'
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)