"""
Unit tests for the HeuristicSelector base class.

These tests verify that the abstract base class is properly defined
and that the interface contracts are enforced.
"""

import pytest
import numpy as np
from abc import ABC
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.heuristics.base import HeuristicSelector
from code.heuristics import (
    BlockEntropyHeuristic,
    GradientMagnitudeHeuristic,
    RecencyBiasHeuristic
)

class TestHeuristicSelectorBase:
    """Tests for the HeuristicSelector abstract base class."""
    
    def test_instantiate_abstract_class_fails(self):
        """Test that we cannot instantiate the abstract base class directly."""
        with pytest.raises(TypeError):
            HeuristicSelector(name="test")
    
    def test_subclass_must_implement_compute_scores(self):
        """Test that subclasses must implement compute_scores."""
        class IncompleteHeuristic(HeuristicSelector):
            def __init__(self):
                super().__init__(name="incomplete")
            
            def select_blocks(self, scores, k, **kwargs):
                return np.array([])
        
        with pytest.raises(TypeError):
            IncompleteHeuristic()
    
    def test_subclass_must_implement_select_blocks(self):
        """Test that subclasses must implement select_blocks."""
        class IncompleteHeuristic(HeuristicSelector):
            def __init__(self):
                super().__init__(name="incomplete")
            
            def compute_scores(self, attention_logits, **kwargs):
                return np.array([0.5])
        
        with pytest.raises(TypeError):
            IncompleteHeuristic()
    
    def test_concrete_classes_can_be_instantiated(self):
        """Test that concrete heuristic classes can be instantiated."""
        entropy = BlockEntropyHeuristic()
        assert entropy.name == "block_entropy"
        
        gradient = GradientMagnitudeHeuristic()
        assert gradient.name == "gradient_magnitude"
        
        recency = RecencyBiasHeuristic()
        assert recency.name == "recency_bias"
    
    def test_concrete_classes_implement_abstract_methods(self):
        """Test that concrete classes implement all abstract methods."""
        entropy = BlockEntropyHeuristic()
        assert hasattr(entropy, 'compute_scores')
        assert hasattr(entropy, 'select_blocks')
        
        gradient = GradientMagnitudeHeuristic()
        assert hasattr(gradient, 'compute_scores')
        assert hasattr(gradient, 'select_blocks')
        
        recency = RecencyBiasHeuristic()
        assert hasattr(recency, 'compute_scores')
        assert hasattr(recency, 'select_blocks')
    
    def test_config_management(self):
        """Test configuration get and update methods."""
        heuristic = BlockEntropyHeuristic(config={'block_size': 64})
        
        # Test get_config
        config = heuristic.get_config()
        assert 'block_size' in config
        assert config['block_size'] == 64
        
        # Test update_config
        heuristic.update_config(block_size=128, threshold=0.5)
        config = heuristic.get_config()
        assert config['block_size'] == 128
        assert config['threshold'] == 0.5
    
    def test_validate_input(self):
        """Test input validation method."""
        heuristic = BlockEntropyHeuristic()
        
        # Valid inputs
        assert heuristic.validate_input(np.random.rand(2, 4, 64, 64)) is True
        assert heuristic.validate_input(np.random.rand(4, 64, 64)) is True
        
        # Invalid inputs
        assert heuristic.validate_input(None) is False
        assert heuristic.validate_input("not an array") is False
        assert heuristic.validate_input(np.array([1, 2, 3])) is False  # ndim < 3
    
    def test_str_and_repr(self):
        """Test string representation methods."""
        heuristic = BlockEntropyHeuristic(config={'test': 123})
        
        str_repr = str(heuristic)
        assert "BlockEntropyHeuristic" in str_repr
        assert "block_entropy" in str_repr
        
        repr_repr = repr(heuristic)
        assert "BlockEntropyHeuristic" in repr_repr
        assert "test=123" in repr_repr
    
    def test_set_logger(self):
        """Test logger setting functionality."""
        heuristic = BlockEntropyHeuristic()
        
        # Mock logger
        class MockLogger:
            pass
        
        mock_logger = MockLogger()
        heuristic.set_logger(mock_logger)
        assert heuristic.logger is mock_logger
    
    def test_is_subclass_of_abc(self):
        """Test that the base class is properly defined as an ABC."""
        assert issubclass(HeuristicSelector, ABC)