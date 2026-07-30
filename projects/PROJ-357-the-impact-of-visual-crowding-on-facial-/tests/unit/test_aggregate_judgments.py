"""
Unit tests for T029: Aggregate Judgments logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.aggregate_judgments import compute_accuracy, aggregate_judgments

class TestComputeAccuracy:
    def test_accuracy_computation_correct(self):
        data = {
            'true_label': ['happy', 'sad', 'neutral'],
            'response_label': ['happy', 'sad', 'angry']
        }
        df = pd.DataFrame(data)
        result = compute_accuracy(df)
        
        assert result['accuracy'].iloc[0] == 1.0
        assert result['accuracy'].iloc[1] == 1.0
        assert result['accuracy'].iloc[2] == 0.0
    
    def test_accuracy_computation_missing_columns(self):
        data = {'wrong_col': ['happy']}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            compute_accuracy(df)
    
    def test_accuracy_type_consistency(self):
        data = {
            'true_label': [1, 2, 3],
            'response_label': [1, 2, 4]
        }
        df = pd.DataFrame(data)
        result = compute_accuracy(df)
        assert result['accuracy'].dtype in [np.float64, np.float32, 'float64', 'float32']

class TestAggregateJudgments:
    def test_aggregation_logic(self):
        data = {
            'stimulus_id': ['s1', 's1', 's1', 's2'],
            'emotion_label': ['happy', 'happy', 'happy', 'sad'],
            'flanker_count': [3, 3, 3, 5],
            'accuracy': [1.0, 0.0, 1.0, 1.0],
            'participant_id': ['p1', 'p2', 'p1', 'p1']
        }
        df = pd.DataFrame(data)
        result = aggregate_judgments(df)
        
        # Check s1 aggregation: 3 trials, 2 correct -> mean 0.666...
        s1_row = result[result['stimulus_id'] == 's1'].iloc[0]
        assert s1_row['total_trials'] == 3
        assert np.isclose(s1_row['mean_accuracy'], 2/3)
        assert s1_row['num_participants'] == 2
        
        # Check s2 aggregation: 1 trial, 1 correct -> mean 1.0
        s2_row = result[result['stimulus_id'] == 's2'].iloc[0]
        assert s2_row['total_trials'] == 1
        assert s2_row['mean_accuracy'] == 1.0
        assert s2_row['std_accuracy'] == 0.0  # Filled NaN
    
    def test_missing_columns(self):
        data = {'stimulus_id': ['s1']}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            aggregate_judgments(df)
    
    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['stimulus_id', 'emotion_label', 'flanker_count', 'accuracy', 'participant_id'])
        result = aggregate_judgments(df)
        assert len(result) == 0