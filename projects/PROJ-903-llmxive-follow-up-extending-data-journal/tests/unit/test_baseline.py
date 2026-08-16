"""
Unit tests for baseline correlation detection in code/narrative/baseline.py.

This module verifies the core logic of the baseline narrative generation,
specifically the identification of the strongest statistically significant
relationship and the formatting of the output JSON.
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
from scipy import stats

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from narrative.baseline import (
    compute_pairwise_correlations,
    identify_strongest_relationship,
    generate_narrative_claim,
    BaselineResult,
    CORRELATION_SCHEMA_KEYS
)


class TestComputePairwiseCorrelations:
    """Tests for the compute_pairwise_correlations function."""

    def test_returns_dataframe_with_required_columns(self):
        """Test that the output is a DataFrame with r, p, and column pairs."""
        # Create a simple synthetic dataset
        np.random.seed(42)
        data = {
            'A': np.random.rand(100),
            'B': np.random.rand(100),
            'C': np.random.rand(100)
        }
        df = pd.DataFrame(data)

        result = compute_pairwise_correlations(df)

        assert isinstance(result, pd.DataFrame)
        assert 'var_x' in result.columns
        assert 'var_y' in result.columns
        assert 'r_value' in result.columns
        assert 'p_value' in result.columns

    def test_only_computes_for_numeric_columns(self):
        """Test that non-numeric columns are excluded."""
        data = {
            'A': np.random.rand(100),
            'B': np.random.rand(100),
            'Categorical': ['x', 'y'] * 50
        }
        df = pd.DataFrame(data)

        result = compute_pairwise_correlations(df)

        # 'Categorical' should not appear in var_x or var_y
        assert not result['var_x'].isin(['Categorical']).any()
        assert not result['var_y'].isin(['Categorical']).any()

    def test_correctly_calculates_correlation_for_perfect_correlation(self):
        """Test calculation on a known perfect correlation."""
        data = {
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10]  # Perfect linear relationship
        }
        df = pd.DataFrame(data)

        result = compute_pairwise_correlations(df)
        
        # Find the row for A-B
        row = result[(result['var_x'] == 'A') & (result['var_y'] == 'B')]
        
        assert len(row) == 1
        assert np.isclose(row['r_value'].iloc[0], 1.0)
        assert row['p_value'].iloc[0] < 0.05  # Should be significant


class TestIdentifyStrongestRelationship:
    """Tests for the identify_strongest_relationship function."""

    def test_returns_top_correlation(self):
        """Test that the function returns the strongest correlation."""
        correlations = pd.DataFrame([
            {'var_x': 'A', 'var_y': 'B', 'r_value': 0.1, 'p_value': 0.5},
            {'var_x': 'A', 'var_y': 'C', 'r_value': 0.9, 'p_value': 0.001},
            {'var_x': 'B', 'var_y': 'C', 'r_value': 0.5, 'p_value': 0.1}
        ])

        result = identify_strongest_relationship(correlations)

        assert result['var_x'] == 'A'
        assert result['var_y'] == 'C'
        assert result['r_value'] == 0.9

    def test_handles_negative_correlations(self):
        """Test that strong negative correlations are prioritized by magnitude."""
        correlations = pd.DataFrame([
            {'var_x': 'A', 'var_y': 'B', 'r_value': 0.1, 'p_value': 0.5},
            {'var_x': 'A', 'var_y': 'C', 'r_value': -0.9, 'p_value': 0.001},
            {'var_x': 'B', 'var_y': 'C', 'r_value': 0.5, 'p_value': 0.1}
        ])

        result = identify_strongest_relationship(correlations)

        # Should pick the one with |r| = 0.9
        assert abs(result['r_value']) == 0.9

    def test_filters_by_significance(self):
        """Test that non-significant correlations are ignored if significant ones exist."""
        correlations = pd.DataFrame([
            {'var_x': 'A', 'var_y': 'B', 'r_value': 0.8, 'p_value': 0.001},
            {'var_x': 'A', 'var_y': 'C', 'r_value': 0.9, 'p_value': 0.5}, # High r, not sig
            {'var_x': 'B', 'var_y': 'C', 'r_value': 0.1, 'p_value': 0.9}
        ])

        result = identify_strongest_relationship(correlations, p_threshold=0.05)

        # Should pick A-B because A-C is not significant
        assert result['var_x'] == 'A'
        assert result['var_y'] == 'B'

    def test_returns_none_when_no_significant_correlations(self):
        """Test behavior when no correlations meet the threshold."""
        correlations = pd.DataFrame([
            {'var_x': 'A', 'var_y': 'B', 'r_value': 0.1, 'p_value': 0.9},
            {'var_x': 'A', 'var_y': 'C', 'r_value': 0.2, 'p_value': 0.8}
        ])

        result = identify_strongest_relationship(correlations, p_threshold=0.05)

        assert result is None


class TestGenerateNarrativeClaim:
    """Tests for the narrative generation logic."""

    def test_produces_valid_json_schema(self):
        """Test that the output contains all required schema keys."""
        top_rel = {
            'var_x': 'median_income',
            'var_y': 'house_value',
            'r_value': 0.65,
            'p_value': 0.0001,
            'significance': 'highly_significant'
        }

        result = generate_narrative_claim(top_rel)

        for key in CORRELATION_SCHEMA_KEYS:
            assert key in result, f"Missing key: {key}"

    def test_primary_narrative_is_string(self):
        """Test that the primary_narrative field is a non-empty string."""
        top_rel = {
            'var_x': 'A',
            'var_y': 'B',
            'r_value': 0.8,
            'p_value': 0.001,
            'significance': 'significant'
        }

        result = generate_narrative_claim(top_rel)

        assert isinstance(result['primary_narrative'], str)
        assert len(result['primary_narrative']) > 0
        assert 'A' in result['primary_narrative']
        assert 'B' in result['primary_narrative']

    def test_handles_negative_correlation_in_narrative(self):
        """Test that negative correlations are described correctly."""
        top_rel = {
            'var_x': 'pollution',
            'var_y': 'health_index',
            'r_value': -0.7,
            'p_value': 0.001,
            'significance': 'significant'
        }

        result = generate_narrative_claim(top_rel)

        # The narrative should indicate a negative relationship
        narrative = result['primary_narrative'].lower()
        assert any(word in narrative for word in ['negative', 'decrease', 'inverse', 'decline'])


class TestBaselineResult:
    """Tests for the BaselineResult dataclass."""

    def test_serialization(self):
        """Test that the result can be serialized to JSON."""
        result = BaselineResult(
            primary_narrative="Test narrative",
            r_value=0.5,
            p_value=0.01,
            var_x="A",
            var_y="B",
            significance="significant"
        )

        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert parsed['primary_narrative'] == "Test narrative"
        assert parsed['r_value'] == 0.5
        assert parsed['var_x'] == "A"

    def test_deserialization(self):
        """Test that the result can be deserialized from JSON."""
        json_str = json.dumps({
            'primary_narrative': "Test",
            'r_value': 0.5,
            'p_value': 0.01,
            'var_x': "A",
            'var_y': "B",
            'significance': "significant"
        })

        result = BaselineResult.from_json(json_str)

        assert result.primary_narrative == "Test"
        assert result.r_value == 0.5
        assert result.var_x == "A"