import pytest
import os
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module under test
from code.analysis_summary import (
    load_feature_importance,
    load_correlation_results,
    get_top_features,
    summarize_feature_stats,
    generate_analysis_summary
)


class TestLoadFeatureImportance:
    def test_load_existing_csv(self, tmp_path):
        # Create a mock CSV
        csv_path = tmp_path / "feature_importance.csv"
        data = {
            'feature_name': ['f1', 'f2', 'f3'],
            'importance_score': [0.5, 0.3, 0.2],
            'rank': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        result = load_feature_importance(str(csv_path))
        assert len(result) == 3
        assert 'f1' in result['feature_name'].values

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_feature_importance(str(tmp_path / "nonexistent.csv"))


class TestLoadCorrelationResults:
    def test_load_existing_json(self, tmp_path):
        json_path = tmp_path / "correlation_results.json"
        data = {"correlations": [{"feature_name": "f1", "p_value": 0.01}]}
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        result = load_correlation_results(str(json_path))
        assert "correlations" in result
        assert len(result["correlations"]) == 1

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_correlation_results(str(tmp_path / "nonexistent.json"))


class TestGetTopFeatures:
    def test_get_top_n(self):
        data = {
            'feature_name': ['f1', 'f2', 'f3', 'f4'],
            'importance_score': [0.1, 0.9, 0.5, 0.3],
            'rank': [4, 1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        top = get_top_features(df, n=2)
        assert len(top) == 2
        assert top[0]['feature_name'] == 'f2'
        assert top[1]['feature_name'] == 'f3'

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['feature_name', 'importance_score', 'rank'])
        top = get_top_features(df, n=2)
        assert top == []


class TestSummarizeFeatureStats:
    def test_basic_stats(self):
        data = {
            'feature_name': ['f1', 'f2'],
            'importance_score': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        corr_results = {}
        
        stats = summarize_feature_stats(df, corr_results)
        assert stats['total_features'] == 2
        assert stats['mean_importance'] == 15.0
        assert stats['significant_features_count'] == 0

    def test_with_correlations(self):
        data = {
            'feature_name': ['f1', 'f2'],
            'importance_score': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        corr_results = {
            'correlations': [
                {'feature_name': 'f1', 'p_value': 0.01},
                {'feature_name': 'f2', 'p_value': 0.06}
            ]
        }
        
        stats = summarize_feature_stats(df, corr_results)
        assert stats['significant_features_count'] == 1


class TestGenerateAnalysisSummary:
    def test_full_generation(self, tmp_path):
        # Setup mock files
        importance_csv = tmp_path / "feature_importance.csv"
        corr_json = tmp_path / "correlation_results.json"
        output_json = tmp_path / "analysis_summary.json"
        
        # Create importance data
        imp_data = {
            'feature_name': ['f1', 'f2', 'f3'],
            'importance_score': [0.5, 0.3, 0.2],
            'rank': [1, 2, 3]
        }
        pd.DataFrame(imp_data).to_csv(importance_csv, index=False)
        
        # Create correlation data
        corr_data = {
            'correlations': [
                {'feature_name': 'f1', 'p_value': 0.01, 'adj_p_value': 0.02},
                {'feature_name': 'f2', 'p_value': 0.05, 'adj_p_value': 0.06}
            ]
        }
        with open(corr_json, 'w') as f:
            json.dump(corr_data, f)
        
        # Run generation
        result = generate_analysis_summary(
            importance_path=str(importance_csv),
            corr_path=str(corr_json),
            output_path=str(output_json)
        )
        
        # Verify output file exists
        assert os.path.exists(output_json)
        
        # Verify content
        with open(output_json, 'r') as f:
            saved = json.load(f)
        
        assert 'top_features' in saved
        assert len(saved['top_features']) == 3
        assert saved['top_features'][0]['feature_name'] == 'f1'
        assert 'adjusted_p_values' in saved
        assert len(saved['adjusted_p_values']) == 2