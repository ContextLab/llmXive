import os
import json
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.importance_analyzer import (
    load_literature_baseline,
    load_user_baseline,
    calculate_permutation_importance,
    calculate_correlation_coefficient,
    run_correlation_analysis
)

class TestImportanceAnalyzer:
    def test_load_literature_baseline_success(self):
        """Test successful fetch of literature baseline."""
        # Mock requests.get
        with patch('utils.importance_analyzer.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response
            
            result = load_literature_baseline()
            assert result is not None
            assert "laser_power" in result
            assert result["laser_power"] == 0.85

    def test_load_literature_baseline_failure(self):
        """Test failure when DOI not found."""
        with patch('utils.importance_analyzer.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("404")
            mock_get.return_value = mock_response
            
            result = load_literature_baseline()
            assert result is None

    def test_load_user_baseline_success(self, tmp_path):
        """Test loading user baseline from JSON file."""
        data = {
            "parameters": [
                {"name": "laser_power", "rank": 1},
                {"name": "scan_speed", "rank": 2}
            ]
        }
        file_path = tmp_path / "baseline.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_user_baseline(str(file_path))
        assert result is not None
        assert result["laser_power"] == 1.0
        assert result["scan_speed"] == 2.0

    def test_load_user_baseline_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        result = load_user_baseline(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_user_baseline_invalid_schema(self, tmp_path):
        """Test loading invalid JSON schema."""
        data = {"wrong_key": []}
        file_path = tmp_path / "bad.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_user_baseline(str(file_path))
        assert result is None

    def test_calculate_permutation_importance(self):
        """Test permutation importance calculation."""
        # Create a simple mock model
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        X = np.random.rand(100, 3)
        y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.1, 100)
        model.fit(X, y)
        
        feature_names = ["f1", "f2", "f3"]
        result = calculate_permutation_importance(model, X, y, feature_names)
        
        assert isinstance(result, dict)
        assert len(result) == 3
        assert "f1" in result
        assert "f2" in result
        assert "f3" in result

    def test_calculate_correlation_coefficient(self):
        """Test Spearman correlation calculation."""
        model_rank = {"a": 0.9, "b": 0.5, "c": 0.1}
        base_rank = {"a": 0.8, "b": 0.6, "c": 0.2}
        
        corr, p_val = calculate_correlation_coefficient(model_rank, base_rank)
        
        assert -1.0 <= corr <= 1.0
        assert 0.0 <= p_val <= 1.0
        # High correlation expected
        assert corr > 0.9

    def test_run_correlation_analysis_halt_on_missing(self, tmp_path, monkeypatch):
        """Test that run_correlation_analysis halts if both sources missing."""
        # Mock model and data
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        X = np.random.rand(10, 2)
        y = X[:, 0]
        model.fit(X, y)
        
        # Mock load_literature_baseline to return None
        with patch('utils.importance_analyzer.load_literature_baseline', return_value=None):
            # Mock load_user_baseline to return None
            with patch('utils.importance_analyzer.load_user_baseline', return_value=None):
                with pytest.raises(FileNotFoundError, match="SC-004 requires a verified literature baseline"):
                    run_correlation_analysis(model, X, y, ["f1", "f2"])
    
    def test_run_correlation_analysis_uses_user_fallback(self, tmp_path, monkeypatch):
        """Test that user baseline is used if literature fails."""
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        X = np.random.rand(10, 2)
        y = X[:, 0]
        model.fit(X, y)
        
        # Create a user baseline file
        data = {"parameters": [{"name": "f1", "rank": 1}, {"name": "f2", "rank": 2}]}
        user_file = tmp_path / "baseline.json"
        with open(user_file, 'w') as f:
            json.dump(data, f)
        
        # Mock literature to fail
        with patch('utils.importance_analyzer.load_literature_baseline', return_value=None):
            # Mock user baseline to load from our temp file
            with patch('utils.importance_analyzer.load_user_baseline', return_value={"f1": 1.0, "f2": 2.0}):
                # Mock save to avoid file IO issues in test
                with patch('builtins.open', MagicMock()):
                    with patch('json.dump'):
                        result = run_correlation_analysis(model, X, y, ["f1", "f2"])
                        assert result is not None
                        assert result["baseline_source"] == "User Provided"