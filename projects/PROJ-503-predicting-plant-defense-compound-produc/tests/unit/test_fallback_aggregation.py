"""
Unit tests for T016b: Fallback to condition-level aggregation.
"""
import pytest
import json
import csv
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from exceptions import E_PAIRING
from run_fallback_aggregation import (
    calculate_sample_level_pairing_rate,
    aggregate_by_condition,
    run_fallback_aggregation
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestFallbackAggregation:
    
    def test_sample_level_pairing_rate_100(self):
        """Test pairing rate calculation with 100% match."""
        expr = {'s1': {'condition': 'A'}, 's2': {'condition': 'B'}}
        metab = {'s1': {'condition': 'A'}, 's2': {'condition': 'B'}}
        
        rate, unmatched_expr, unmatched_metab = calculate_sample_level_pairing_rate(expr, metab)
        
        assert rate == 1.0
        assert len(unmatched_expr) == 0
        assert len(unmatched_metab) == 0
    
    def test_sample_level_pairing_rate_partial(self):
        """Test pairing rate calculation with partial match."""
        expr = {'s1': {'condition': 'A'}, 's2': {'condition': 'B'}, 's3': {'condition': 'C'}}
        metab = {'s1': {'condition': 'A'}, 's2': {'condition': 'B'}}
        
        rate, unmatched_expr, unmatched_metab = calculate_sample_level_pairing_rate(expr, metab)
        
        assert rate == 2/3
        assert 's3' in unmatched_expr
        assert len(unmatched_metab) == 0
    
    def test_sample_level_pairing_rate_low(self):
        """Test pairing rate calculation with low match rate."""
        expr = {'s1': {'condition': 'A'}, 's2': {'condition': 'B'}, 's3': {'condition': 'C'}, 's4': {'condition': 'D'}}
        metab = {'s1': {'condition': 'A'}}
        
        rate, unmatched_expr, unmatched_metab = calculate_sample_level_pairing_rate(expr, metab)
        
        assert rate == 0.25
        assert len(unmatched_expr) == 3
    
    def test_aggregate_by_condition(self):
        """Test condition-level aggregation."""
        expr = {
            's1': {'condition': 'Treatment_A'},
            's2': {'condition': 'Treatment_A'},
            's3': {'condition': 'Control'}
        }
        metab = {
            's1': {'condition': 'Treatment_A'},
            's4': {'condition': 'Control'},
            's5': {'condition': 'Control'}
        }
        
        expr_counts, metab_counts, total_pairs = aggregate_by_condition(expr, metab)
        
        assert expr_counts == {'Treatment_A': 2, 'Control': 1}
        assert metab_counts == {'Treatment_A': 1, 'Control': 2}
        # min(2,1) + min(1,2) = 1 + 1 = 2
        assert total_pairs == 2
    
    def test_aggregate_by_condition_single_condition(self):
        """Test aggregation with single condition."""
        expr = {
            f's{i}': {'condition': 'Stress'} for i in range(30)
        }
        metab = {
            f's{i}': {'condition': 'Stress'} for i in range(25)
        }
        
        _, _, total_pairs = aggregate_by_condition(expr, metab)
        
        # min(30, 25) = 25
        assert total_pairs == 25
    
    @patch('run_fallback_aggregation.load_expression_metadata')
    @patch('run_fallback_aggregation.load_metabolite_metadata')
    @patch('run_fallback_aggregation.log_data_pairing_mismatch')
    @patch('run_fallback_aggregation.save_pairing_log')
    @patch('run_fallback_aggregation.LOGS_DIR')
    def test_fallback_proceeds_with_sufficient_aggregation(
        self, mock_logs_dir, mock_save_log, mock_log_mismatch, mock_load_metab, mock_load_expr
    ):
        """Test that fallback proceeds when aggregated n >= 28."""
        # Setup: Low sample-level pairing, but sufficient condition-level
        mock_load_expr.return_value = {
            f's_expr_{i}': {'condition': 'Stress'} for i in range(30)
        }
        mock_load_metab.return_value = {
            f's_metab_{i}': {'condition': 'Stress'} for i in range(28)
        }
        
        # Mock directory
        mock_logs_dir.__truediv__.return_value = Path('/tmp/test_logs')
        
        # This should not raise
        result = run_fallback_aggregation()
        
        assert result is True
        mock_log_mismatch.assert_called()  # Should log mismatches
    
    @patch('run_fallback_aggregation.load_expression_metadata')
    @patch('run_fallback_aggregation.load_metabolite_metadata')
    def test_fallback_aborts_with_insufficient_aggregation(
        self, mock_load_metab, mock_load_expr
    ):
        """Test that fallback aborts with E-PAIRING when aggregated n < 28."""
        # Setup: Low sample-level pairing, insufficient condition-level
        mock_load_expr.return_value = {
            f's_expr_{i}': {'condition': 'Stress'} for i in range(10)
        }
        mock_load_metab.return_value = {
            f's_metab_{i}': {'condition': 'Stress'} for i in range(5)
        }
        
        with pytest.raises(E_PAIRING):
            run_fallback_aggregation()
    
    @patch('run_fallback_aggregation.load_expression_metadata')
    @patch('run_fallback_aggregation.load_metabolite_metadata')
    def test_fallback_proceeds_no_fallback_needed(
        self, mock_load_metab, mock_load_expr
    ):
        """Test that function proceeds normally if sample-level pairing is sufficient."""
        # Setup: High sample-level pairing (>= 95%)
        mock_load_expr.return_value = {f's_{i}': {'condition': 'A'} for i in range(20)}
        mock_load_metab.return_value = {f's_{i}': {'condition': 'A'} for i in range(20)}
        
        result = run_fallback_aggregation()
        
        assert result is True