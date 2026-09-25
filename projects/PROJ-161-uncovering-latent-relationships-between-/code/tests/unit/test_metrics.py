import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from src.data.metrics import calculate_merge_metrics, save_merge_metrics, generate_merge_metrics_report


class TestCalculateMergeMetrics:
    def test_calculate_merge_metrics_basic(self):
        merged_df = pd.DataFrame({
            'inchi_key': ['A', 'B', 'C'],
            'mol_wt': [100, 200, 300],
            'resistance_score': [0.5, np.nan, 0.8]
        })
        metrics = calculate_merge_metrics(merged_df, 3)
        
        assert metrics['total_requested'] == 3
        assert metrics['matches'] == 2  # A and C
        assert metrics['fraction'] == 2/3
        assert metrics['total_merged_rows'] == 3

    def test_calculate_merge_metrics_empty(self):
        merged_df = pd.DataFrame()
        metrics = calculate_merge_metrics(merged_df, 10)
        assert metrics['total_requested'] == 0
        assert metrics['matches'] == 0
        assert metrics['fraction'] == 0.0

    def test_calculate_merge_metrics_no_matches(self):
        merged_df = pd.DataFrame({
            'inchi_key': ['A', 'B'],
            'mol_wt': [100, 200],
            'resistance_score': [np.nan, np.nan]
        })
        metrics = calculate_merge_metrics(merged_df, 2)
        assert metrics['matches'] == 0
        assert metrics['fraction'] == 0.0


class TestSaveMergeMetrics:
    def test_save_merge_metrics_creates_file(self):
        metrics = {'total_requested': 10, 'matches': 5, 'fraction': 0.5}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            result_path = save_merge_metrics(metrics, output_path)
            
            assert result_path.exists()
            with open(result_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == metrics


class TestGenerateMergeMetricsReport:
    def test_generate_report_format(self):
        metrics = {
            'total_requested': 100,
            'matches': 50,
            'fraction': 0.5,
            'total_merged_rows': 100
        }
        report = generate_merge_metrics_report(metrics)
        
        assert "100" in report
        assert "50" in report
        assert "50.00%" in report