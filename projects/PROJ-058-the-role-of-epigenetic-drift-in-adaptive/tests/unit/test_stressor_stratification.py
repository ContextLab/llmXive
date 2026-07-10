"""
Unit tests for stressor stratification logic (T024).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stressor_stratification import (
    get_stressor_column,
    get_env_type_column,
    stratify_by_stressor,
    run_stressor_stratification
)

class TestStressorStratification:
    """Tests for stressor stratification functions."""

    def test_get_stressor_column_found(self):
        """Test that stressor column is correctly identified."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2'],
            'var_methyl': [0.1, 0.2],
            'stressor_type': ['temp', 'nutrient'],
            'var_rna': [0.3, 0.4]
        })
        result = get_stressor_column(df)
        assert result == 'stressor_type'

    def test_get_stressor_column_not_found(self):
        """Test that None is returned when no stressor column exists."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2'],
            'var_methyl': [0.1, 0.2],
            'var_rna': [0.3, 0.4]
        })
        result = get_stressor_column(df)
        assert result is None

    def test_get_env_type_column_found(self):
        """Test that environment type column is correctly identified."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2'],
            'environment_type': ['cold', 'hot'],
            'var_methyl': [0.1, 0.2]
        })
        result = get_env_type_column(df)
        assert result == 'environment_type'

    def test_stratify_by_stressor_with_metadata(self):
        """Test stratification when metadata is present."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2', 'g3', 'g4'],
            'var_methyl': [0.1, 0.2, 0.3, 0.4],
            'stressor_type': ['temp', 'temp', 'nutrient', 'nutrient'],
            'var_rna': [0.1, 0.2, 0.3, 0.4]
        })
        correlation_results = {'rho': 0.5, 'p_value': 0.01}

        result = stratify_by_stressor(df, correlation_results)

        assert result['stratification_available'] is True
        assert len(result['stressor_types_found']) == 2
        assert 'temp' in result['stressor_types_found']
        assert 'nutrient' in result['stressor_types_found']
        assert 'temp' in result['stratification_details']
        assert result['stratification_details']['temp']['sample_count'] == 2

    def test_stratify_by_stressor_no_metadata(self):
        """Test stratification when no metadata is present."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2'],
            'var_methyl': [0.1, 0.2],
            'var_rna': [0.3, 0.4]
        })
        correlation_results = {}

        result = stratify_by_stressor(df, correlation_results)

        assert result['stratification_available'] is False
        assert len(result['notes']) > 0

    def test_stratify_by_stressor_insufficient_data(self):
        """Test stratification with insufficient data for a group."""
        df = pd.DataFrame({
            'gene_id': ['g1', 'g2', 'g3'],
            'var_methyl': [0.1, 0.2, 0.3],
            'stressor_type': ['temp', 'temp', 'nutrient'],  # Only 1 nutrient
            'var_rna': [0.1, 0.2, 0.3]
        })
        correlation_results = {}

        result = stratify_by_stressor(df, correlation_results)

        assert result['stratification_available'] is True
        assert 'temp' in result['stratification_details']
        # nutrient should be skipped due to insufficient data
        assert 'nutrient' not in result['stratification_details']

    @patch('code.analysis.stressor_stratification.load_variance_matrix')
    @patch('code.analysis.stressor_stratification.save_results')
    @patch('pathlib.Path.exists', return_value=True)
    def test_run_stressor_stratification_integration(
        self, mock_exists, mock_save, mock_load_matrix
    ):
        """Test the full run_stressor_stratification function."""
        # Mock variance matrix
        mock_df = pd.DataFrame({
            'gene_id': ['g1', 'g2', 'g3', 'g4'],
            'var_methyl': [0.1, 0.2, 0.3, 0.4],
            'stressor_type': ['temp', 'temp', 'nutrient', 'nutrient'],
            'var_rna': [0.1, 0.2, 0.3, 0.4]
        })
        mock_load_matrix.return_value = mock_df

        # Mock correlation results file
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"rho": 0.8}'
            mock_open.return_value.__enter__.return_value.__iter__ = lambda self: iter(['{"rho": 0.8}'])

            result = run_stressor_stratification()

            assert 'error' not in result
            assert result['stratification_available'] is True
            assert mock_save.called
