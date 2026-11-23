"""
Unit tests for rubric validation (T037).

Tests:
1. Load hold-out set with correct schema
2. Rubric scoring calculation
3. Correlation calculation
4. Validation threshold check
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.rubric_validation import (
    load_holdout_set,
    simulate_rubric_scoring,
    calculate_correlation,
    validate_correlation,
    CORRELATION_THRESHOLD,
    HOLDOUT_SIZE
)
from config import get_holdout_data_path


class TestLoadHoldoutSet:
    def test_load_holdout_set_success(self, tmp_path):
        """Test successful loading of hold-out set."""
        # Create a mock hold-out CSV
        mock_data = {
            'query': ['q1', 'q2', 'q3'],
            'ground_truth_intent': ['intent1', 'intent2', 'intent3'],
            'human_score': [0.8, 0.9, 0.7]
        }
        df = pd.DataFrame(mock_data)
        
        holdout_path = tmp_path / "holdout_set.csv"
        df.to_csv(holdout_path, index=False)
        
        # Mock get_holdout_data_path to return our temp file
        with patch('analysis.rubric_validation.get_holdout_data_path', return_value=holdout_path):
            result = load_holdout_set()
            
            assert len(result) == 3
            assert 'query' in result.columns
            assert 'ground_truth_intent' in result.columns
            assert 'human_score' in result.columns
            assert result['human_score'].iloc[0] == 0.8
    
    def test_load_holdout_set_missing_file(self, tmp_path):
        """Test error when hold-out file is missing."""
        non_existent_path = tmp_path / "non_existent.csv"
        
        with patch('analysis.rubric_validation.get_holdout_data_path', return_value=non_existent_path):
            with pytest.raises(FileNotFoundError):
                load_holdout_set()
    
    def test_load_holdout_set_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        mock_data = {
            'query': ['q1', 'q2'],
            'ground_truth_intent': ['intent1', 'intent2']
            # Missing 'human_score'
        }
        df = pd.DataFrame(mock_data)
        
        holdout_path = tmp_path / "holdout_set.csv"
        df.to_csv(holdout_path, index=False)
        
        with patch('analysis.rubric_validation.get_holdout_data_path', return_value=holdout_path):
            with pytest.raises(ValueError, match="missing required columns"):
                load_holdout_set()


class TestSimulateRubricScoring:
    def test_simulate_rubric_scoring(self):
        """Test that rubric scoring adds rubric_score column."""
        mock_data = {
            'query': ['q1', 'q2'],
            'ground_truth_intent': ['intent1', 'intent2'],
            'human_score': [0.8, 0.9],
            'complexity_score': [0.5, 0.7]
        }
        df = pd.DataFrame(mock_data)
        
        result = simulate_rubric_scoring(df)
        
        assert 'rubric_score' in result.columns
        assert len(result) == 2
        assert all(result['rubric_score'] >= 0)
        assert all(result['rubric_score'] <= 1.0)

class TestCalculateCorrelation:
    def test_calculate_correlation_perfect(self):
        """Test correlation with perfect linear relationship."""
        mock_data = {
            'human_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'rubric_score': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(mock_data)
        
        r, p_value = calculate_correlation(df)
        
        assert abs(r - 1.0) < 0.0001
        assert p_value < 0.05
    
    def test_calculate_correlation_negative(self):
        """Test correlation with inverse relationship."""
        mock_data = {
            'human_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'rubric_score': [5.0, 4.0, 3.0, 2.0, 1.0]
        }
        df = pd.DataFrame(mock_data)
        
        r, p_value = calculate_correlation(df)
        
        assert abs(r - (-1.0)) < 0.0001
        assert p_value < 0.05
    
    def test_calculate_correlation_insufficient_data(self):
        """Test error with less than 2 data points."""
        mock_data = {
            'human_score': [1.0],
            'rubric_score': [1.0]
        }
        df = pd.DataFrame(mock_data)
        
        with pytest.raises(ValueError, match="Need at least 2 data points"):
            calculate_correlation(df)

class TestValidateCorrelation:
    def test_validate_correlation_pass(self):
        """Test validation passes when r >= threshold."""
        result = validate_correlation(0.75, 0.01)
        
        assert result['is_valid'] is True
        assert result['correlation_coefficient'] == 0.75
        assert result['threshold'] == CORRELATION_THRESHOLD
    
    def test_validate_correlation_fail(self):
        """Test validation fails when r < threshold."""
        result = validate_correlation(0.65, 0.01)
        
        assert result['is_valid'] is False
        assert result['correlation_coefficient'] == 0.65
        assert result['threshold'] == CORRELATION_THRESHOLD
    
    def test_validate_correlation_exact_threshold(self):
        """Test validation passes exactly at threshold."""
        result = validate_correlation(CORRELATION_THRESHOLD, 0.01)
        
        assert result['is_valid'] is True