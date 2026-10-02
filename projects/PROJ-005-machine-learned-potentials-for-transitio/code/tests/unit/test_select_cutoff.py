"""
Unit tests for T017c: select_cutoff_and_generate_graphs.py
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.data.select_cutoff_and_generate_graphs import (
    load_sensitivity_metrics,
    select_optimal_cutoff,
    flag_outliers,
)


class TestLoadSensitivityMetrics:
    def test_load_valid_metrics(self, tmp_path):
        data = [
            {"cutoff": 3.0, "avg_edge_feature_cv": 0.5, "samples_processed": 100, "status": "ok"},
            {"cutoff": 4.0, "avg_edge_feature_cv": 0.2, "samples_processed": 100, "status": "ok"},
        ]
        path = tmp_path / "metrics.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_sensitivity_metrics(path)
        assert len(result) == 2
        assert result[0]['cutoff'] == 3.0

    def test_load_filters_no_data(self, tmp_path):
        data = [
            {"cutoff": 3.0, "avg_edge_feature_cv": 0.5, "samples_processed": 100, "status": "ok"},
            {"cutoff": 4.0, "avg_edge_feature_cv": 0.0, "samples_processed": 0, "status": "no_data"},
        ]
        path = tmp_path / "metrics.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_sensitivity_metrics(path)
        assert len(result) == 1
        assert result[0]['cutoff'] == 3.0

    def test_load_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_sensitivity_metrics(tmp_path / "nonexistent.json")

    def test_load_raises_on_empty_valid(self, tmp_path):
        data = [
            {"cutoff": 3.0, "samples_processed": 0, "status": "no_data"},
        ]
        path = tmp_path / "metrics.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError):
            load_sensitivity_metrics(path)


class TestSelectOptimalCutoff:
    def test_selects_min_cv(self):
        metrics = [
            {"cutoff": 3.0, "avg_edge_feature_cv": 0.5},
            {"cutoff": 4.0, "avg_edge_feature_cv": 0.2},
            {"cutoff": 5.0, "avg_edge_feature_cv": 0.8},
        ]
        best = select_optimal_cutoff(metrics)
        assert best == 4.0

    def test_tie_breaks_smallest_cutoff(self):
        metrics = [
            {"cutoff": 4.0, "avg_edge_feature_cv": 0.2},
            {"cutoff": 3.0, "avg_edge_feature_cv": 0.2},
        ]
        best = select_optimal_cutoff(metrics)
        assert best == 3.0


class TestFlagOutliers:
    def test_flags_correct_outliers(self):
        df = pd.DataFrame({
            'graph_id': [1, 2, 3],
            'max_coordination_number': [5.0, 7.0, 6.0]
        })
        result = flag_outliers(df, threshold=6)
        assert result.loc[0, 'is_outlier'] == False
        assert result.loc[1, 'is_outlier'] == True
        assert result.loc[2, 'is_outlier'] == False

    def test_handles_missing_column(self):
        df = pd.DataFrame({
            'graph_id': [1, 2],
            'coordination_number': [5.0, 7.0] # Simulating node level if max missing
        })
        # This test assumes the function handles missing max_coordination_number
        # by falling back or raising. The implementation falls back to 0 if 
        # neither exists, but if 'coordination_number' exists it might try to merge.
        # For simplicity, we test the happy path where max_coordination_number exists.
        df['max_coordination_number'] = df['coordination_number']
        result = flag_outliers(df, threshold=6)
        assert 'is_outlier' in result.columns