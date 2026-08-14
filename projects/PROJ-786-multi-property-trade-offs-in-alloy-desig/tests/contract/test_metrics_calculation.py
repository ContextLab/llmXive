"""
Contract Test for T026: Metric Calculation.

Verifies:
1. The script calculates dominance correctly against the frontier.
2. The script calculates dominance against the Rule of Mixtures.
3. Output schema is correct.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from metrics_calculation import is_dominated, calculate_dominance_metrics, get_element_properties
from metrics_calculation import calculate_rule_of_mixtures


class TestDominanceLogic:
    """Test the core dominance logic (Maximization)."""

    def test_point_dominated_by_better(self):
        # (10, 10) is dominated by (11, 11)
        assert is_dominated((10, 10), (11, 11)) is True

    def test_point_not_dominated_by_equal(self):
        # (10, 10) is not dominated by (10, 10)
        assert is_dominated((10, 10), (10, 10)) is False

    def test_point_not_dominated_by_worse(self):
        # (10, 10) is not dominated by (9, 9)
        assert is_dominated((10, 10), (9, 9)) is False

    def test_point_dominated_by_mixed_better(self):
        # (10, 10) is dominated by (11, 9) -> NO, 9 < 10
        assert is_dominated((10, 10), (11, 9)) is False
        # (10, 10) is dominated by (9, 11) -> NO, 9 < 10
        assert is_dominated((10, 10), (9, 11)) is False
        # (10, 10) is dominated by (11, 10) -> YES (equal in one, better in other)
        assert is_dominated((10, 10), (11, 10)) is True


class TestRuleOfMixtures:
    """Test ROM calculation logic."""

    def test_rom_calculation(self):
        # Create a simple dataframe with two elements
        df = pd.DataFrame({
            'A_fraction': [0.5, 1.0],
            'B_fraction': [0.5, 0.0],
            'other_col': [1, 2]
        })
        
        props = {
            'A': 100.0,
            'B': 200.0
        }
        
        rom, _ = calculate_rule_of_mixtures(df, props, props)
        
        # Row 0: 0.5*100 + 0.5*200 = 150
        assert np.isclose(rom[0], 150.0)
        # Row 1: 1.0*100 + 0.0*200 = 100
        assert np.isclose(rom[1], 100.0)


class TestMetricsCalculation:
    """Test the full metric calculation flow."""

    def test_dominance_metrics_calculation(self):
        # Create mock frontier: High values
        frontier_df = pd.DataFrame({
            'predicted_bulk_modulus': [200.0, 210.0],
            'predicted_shear_modulus': [100.0, 105.0]
        })
        
        # Create mock empirical: Lower values (should be dominated)
        empirical_df = pd.DataFrame({
            'predicted_bulk_modulus': [100.0, 150.0],
            'predicted_shear_modulus': [50.0, 80.0],
            'A_fraction': [0.5, 0.5],
            'B_fraction': [0.5, 0.5]
        })
        
        # Mock ROM (should be lower than frontier, maybe lower than empirical)
        rom_bulk = np.array([80.0, 120.0])
        rom_shear = np.array([40.0, 70.0])
        
        metrics = calculate_dominance_metrics(
            frontier_df, empirical_df, 
            'predicted_bulk_modulus', 'predicted_shear_modulus',
            rom_bulk, rom_shear
        )
        
        # Check keys exist
        assert 'pct_empirical_dominated_by_frontier' in metrics
        assert 'pct_frontier_dominating_empirical' in metrics
        assert 'pct_empirical_beating_rom' in metrics
        
        # Empirical point 0 (100, 50) is dominated by frontier point 0 (200, 100)
        # Empirical point 1 (150, 80) is dominated by frontier point 1 (210, 105)
        # So 100% should be dominated
        assert metrics['pct_empirical_dominated_by_frontier'] == 100.0

    def test_rom_comparison_logic(self):
        # Frontier: (200, 100)
        frontier_df = pd.DataFrame({
            'predicted_bulk_modulus': [200.0],
            'predicted_shear_modulus': [100.0]
        })
        
        # Empirical: (150, 80)
        # ROM: (100, 50) -> Empirical beats ROM, Frontier beats ROM
        empirical_df = pd.DataFrame({
            'predicted_bulk_modulus': [150.0],
            'predicted_shear_modulus': [80.0],
            'A_fraction': [0.5],
            'B_fraction': [0.5]
        })
        
        rom_bulk = np.array([100.0])
        rom_shear = np.array([50.0])
        
        metrics = calculate_dominance_metrics(
            frontier_df, empirical_df,
            'predicted_bulk_modulus', 'predicted_shear_modulus',
            rom_bulk, rom_shear
        )
        
        # Empirical (150, 80) dominates ROM (100, 50)? Yes. -> 100%
        assert metrics['pct_empirical_beating_rom'] == 100.0
        
        # ROM (100, 50) dominated by Frontier (200, 100)? Yes. -> 100%
        assert metrics['pct_rom_dominated_by_frontier'] == 100.0