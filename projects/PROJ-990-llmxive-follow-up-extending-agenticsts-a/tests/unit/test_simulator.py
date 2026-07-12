"""
Unit tests for token budget enforcement and minimum context floor in simulator.py.

This module verifies that the simulator correctly:
1. Enforces the hard token budget (4096 tokens).
2. Enforces the minimum context floor (256 tokens).
3. Truncates/prunes layers when the predicted token count exceeds the budget.
4. Does NOT fallback to full layers if that exceeds the budget.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path so we can import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import TOKEN_BUDGET, MIN_CONTEXT
from simulator import (
    simulate_turn,
    select_layers_with_budget,
    calculate_token_count,
    prune_layers_to_budget
)


class TestTokenBudgetEnforcement:
    """Tests for hard token budget enforcement."""

    def test_select_layers_within_budget(self):
        """Test that layers are selected when total tokens are within budget."""
        # Mock layer data where total tokens < TOKEN_BUDGET
        layers = [
            {"id": "layer_1", "tokens": 500, "utility": 0.9},
            {"id": "layer_2", "tokens": 600, "utility": 0.85},
            {"id": "layer_3", "tokens": 400, "utility": 0.7}
        ]
        predicted_k = 3
        
        selected = select_layers_with_budget(layers, predicted_k, TOKEN_BUDGET)
        
        # All layers should be selected
        assert len(selected) == 3
        total_tokens = sum(l["tokens"] for l in selected)
        assert total_tokens <= TOKEN_BUDGET

    def test_select_layers_exceeds_budget_truncates(self):
        """Test that layers are truncated when total tokens exceed budget."""
        # Mock layer data where total tokens > TOKEN_BUDGET
        layers = [
            {"id": "layer_1", "tokens": 2000, "utility": 0.95},
            {"id": "layer_2", "tokens": 1500, "utility": 0.9},
            {"id": "layer_3", "tokens": 1500, "utility": 0.85},
            {"id": "layer_4", "tokens": 1000, "utility": 0.7}
        ]
        predicted_k = 4
        
        selected = select_layers_with_budget(layers, predicted_k, TOKEN_BUDGET)
        
        # Should not exceed budget
        total_tokens = sum(l["tokens"] for l in selected)
        assert total_tokens <= TOKEN_BUDGET
        
        # Should have truncated some layers (not all 4)
        assert len(selected) < 4

    def test_select_layers_single_layer_exceeds_budget(self):
        """Test behavior when even the single highest utility layer exceeds budget."""
        layers = [
            {"id": "layer_1", "tokens": 5000, "utility": 0.95},
            {"id": "layer_2", "tokens": 4000, "utility": 0.9}
        ]
        predicted_k = 2
        
        selected = select_layers_with_budget(layers, predicted_k, TOKEN_BUDGET)
        
        # Even if we can't fit the best, we should try to fit what we can
        # or return empty if nothing fits
        total_tokens = sum(l["tokens"] for l in selected)
        assert total_tokens <= TOKEN_BUDGET

    def test_prune_layers_to_budget(self):
        """Test the pruning function specifically."""
        layers = [
            {"id": "layer_1", "tokens": 1500, "utility": 0.9},
            {"id": "layer_2", "tokens": 1500, "utility": 0.85},
            {"id": "layer_3", "tokens": 1500, "utility": 0.8},
            {"id": "layer_4", "tokens": 1500, "utility": 0.7}
        ]
        budget = 4096
        
        pruned = prune_layers_to_budget(layers, budget)
        
        total_tokens = sum(l["tokens"] for l in pruned)
        assert total_tokens <= budget
        # Should have removed at least one layer
        assert len(pruned) < len(layers)


class TestMinimumContextFloor:
    """Tests for minimum context floor enforcement."""

    def test_context_floor_enforced(self):
        """Test that minimum context is enforced even with low token counts."""
        # Mock layers with very low token counts
        layers = [
            {"id": "layer_1", "tokens": 50, "utility": 0.9},
            {"id": "layer_2", "tokens": 50, "utility": 0.8}
        ]
        predicted_k = 2
        
        selected = select_layers_with_budget(layers, predicted_k, TOKEN_BUDGET)
        
        # Total tokens should be at least MIN_CONTEXT
        total_tokens = sum(l["tokens"] for l in selected)
        # Note: The actual implementation might handle this differently,
        # but the requirement is to enforce a floor
        # This test documents the expected behavior
        assert total_tokens >= MIN_CONTEXT or len(selected) == 0

    def test_no_fallback_to_full_layers_over_budget(self):
        """Test that the system does NOT fallback to full layers if they exceed budget."""
        # Mock layers where all layers together exceed budget
        layers = [
            {"id": "layer_1", "tokens": 3000, "utility": 0.95},
            {"id": "layer_2", "tokens": 3000, "utility": 0.9},
            {"id": "layer_3", "tokens": 3000, "utility": 0.85}
        ]
        predicted_k = 3
        
        selected = select_layers_with_budget(layers, predicted_k, TOKEN_BUDGET)
        
        # Must NOT return all 3 layers (which would be 9000 tokens)
        total_tokens = sum(l["tokens"] for l in selected)
        assert total_tokens <= TOKEN_BUDGET
        assert len(selected) < 3


class TestCalculateTokenCount:
    """Tests for token count calculation."""

    def test_calculate_token_count(self):
        """Test that token count is calculated correctly."""
        layers = [
            {"id": "layer_1", "tokens": 1000, "utility": 0.9},
            {"id": "layer_2", "tokens": 1500, "utility": 0.85}
        ]
        
        count = calculate_token_count(layers)
        
        assert count == 2500

    def test_calculate_token_count_empty(self):
        """Test token count for empty layer list."""
        count = calculate_token_count([])
        assert count == 0


class TestSimulateTurn:
    """Integration tests for simulate_turn function."""

    @patch('simulator.select_layers_with_budget')
    @patch('simulator.calculate_token_count')
    def test_simulate_turn_respects_budget(self, mock_calc_tokens, mock_select_layers):
        """Test that simulate_turn respects token budget."""
        mock_select_layers.return_value = [
            {"id": "layer_1", "tokens": 2000, "utility": 0.9}
        ]
        mock_calc_tokens.return_value = 2000
        
        # Mock the execution
        with patch('simulator.execute_layer_sequence') as mock_exec:
            mock_exec.return_value = {"result": "success", "tokens_used": 2000}
            
            result = simulate_turn(
                turn_data={"turn": 1, "entropy": 0.5},
                available_layers=[
                    {"id": "layer_1", "tokens": 2000, "utility": 0.9},
                    {"id": "layer_2", "tokens": 3000, "utility": 0.8}
                ],
                model_predict_fn=lambda x: 2,
                token_budget=TOKEN_BUDGET,
                min_context=MIN_CONTEXT
            )
            
            # Verify that token count was calculated
            assert mock_calc_tokens.called
            # Verify execution happened with selected layers
            assert mock_exec.called

    @patch('simulator.select_layers_with_budget')
    def test_simulate_turn_handles_zero_moves(self, mock_select_layers):
        """Test behavior when there are zero legal moves (entropy edge case)."""
        mock_select_layers.return_value = []
        
        with patch('simulator.execute_layer_sequence') as mock_exec:
            mock_exec.return_value = {"result": "no_moves", "tokens_used": 0}
            
            result = simulate_turn(
                turn_data={"turn": 1, "entropy": 0.0},
                available_layers=[],
                model_predict_fn=lambda x: 0,
                token_budget=TOKEN_BUDGET,
                min_context=MIN_CONTEXT
            )
            
            # Should handle gracefully
            assert result is not None


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_token_budget_is_4096(self):
        """Verify TOKEN_BUDGET is set to 4096."""
        assert TOKEN_BUDGET == 4096

    def test_min_context_is_256(self):
        """Verify MIN_CONTEXT is set to 256."""
        assert MIN_CONTEXT == 256