import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'projects' / 'PROJ-924-llmxive-follow-up-extending-agentdog-1-5' / 'code'))

from drift_scoring import compute_cosine_distance, batch_process_logs, export_results
from utils import load_json_file, save_json_file

class TestEmptyLogHandling:
    """Tests for T014: Empty/whitespace log handling with Drift Score 2.0"""
    
    def test_empty_log_returns_drift_score_2_0(self):
        """Test that empty logs get drift_score=2.0 and review_flag='true'"""
        # Mock centroids
        centroids = np.array([[1.0, 0.0], [0.0, 1.0]])
        
        # Mock model that returns random embeddings
        class MockModel:
            def encode(self, texts, **kwargs):
                return np.random.rand(len(texts), 2)
        
        mock_model = MockModel()
        
        # Test with empty log
        logs = [
            {'log_id': 'empty_1', 'text': ''},
            {'log_id': 'whitespace_1', 'text': '   '},
            {'log_id': 'whitespace_2', 'text': '\t\n'},
            {'log_id': 'normal_1', 'text': 'This is a normal log entry'}
        ]
        
        results = batch_process_logs(logs, centroids, mock_model)
        
        # Check empty log
        empty_result = next(r for r in results if r['log_id'] == 'empty_1')
        assert empty_result['drift_score'] == 2.0
        assert empty_result['review_flag'] == 'true'
        
        # Check whitespace logs
        ws_result = next(r for r in results if r['log_id'] == 'whitespace_1')
        assert ws_result['drift_score'] == 2.0
        assert ws_result['review_flag'] == 'true'
        
        ws_result2 = next(r for r in results if r['log_id'] == 'whitespace_2')
        assert ws_result2['drift_score'] == 2.0
        assert ws_result2['review_flag'] == 'true'
        
        # Check normal log (should not be 2.0 and not flagged)
        normal_result = next(r for r in results if r['log_id'] == 'normal_1')
        assert normal_result['drift_score'] != 2.0
        assert normal_result['review_flag'] == 'false'
    
    def test_all_empty_logs(self):
        """Test batch of all empty logs"""
        centroids = np.array([[1.0, 0.0]])
        
        class MockModel:
            def encode(self, texts, **kwargs):
                return np.random.rand(len(texts), 1)
        
        logs = [
            {'log_id': 'e1', 'text': ''},
            {'log_id': 'e2', 'text': '   '}
        ]
        
        results = batch_process_logs(logs, centroids, MockModel())
        
        assert len(results) == 2
        for r in results:
            assert r['drift_score'] == 2.0
            assert r['review_flag'] == 'true'
    
    def test_export_results_includes_review_flag(self, tmp_path):
        """Test that export_results includes review_flag column"""
        results = [
            {'log_id': 'e1', 'drift_score': 2.0, 'review_flag': 'true'},
            {'log_id': 'n1', 'drift_score': 0.5, 'review_flag': 'false'}
        ]
        
        output_file = tmp_path / 'test_drift_scores.csv'
        export_results(results, str(output_file))
        
        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        assert 'log_id' in df.columns
        assert 'drift_score' in df.columns
        assert 'review_flag' in df.columns
        
        # Check values
        assert df.loc[df['log_id'] == 'e1', 'review_flag'].iloc[0] == 'true'
        assert df.loc[df['log_id'] == 'n1', 'review_flag'].iloc[0] == 'false'
        
        assert df.loc[df['log_id'] == 'e1', 'drift_score'].iloc[0] == 2.0
        assert df.loc[df['log_id'] == 'n1', 'drift_score'].iloc[0] == 0.5