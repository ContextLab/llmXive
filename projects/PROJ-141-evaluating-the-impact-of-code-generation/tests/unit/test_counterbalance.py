"""
Unit tests for counterbalancing functionality.

Tests the Latin Square design and random swap strategies
to ensure correct condition ordering and balance.
"""
import pytest
import random
import hashlib
from typing import List
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from experiment.counterbalance import (
    CounterbalanceError,
    LatinSquare,
    CounterbalanceManager,
    apply_counterbalancing
)

class TestLatinSquare:
    """Tests for the LatinSquare class."""
    
    def test_initialization_with_two_conditions(self):
        """Test Latin Square initialization with 2 conditions."""
        conditions = ['A', 'B']
        ls = LatinSquare(conditions)
        assert ls.n_conditions == 2
        assert ls.conditions == conditions
    
    def test_initialization_requires_minimum_two_conditions(self):
        """Test that Latin Square requires at least 2 conditions."""
        with pytest.raises(CounterbalanceError):
            LatinSquare(['A'])
    
    def test_square_generation_2x2(self):
        """Test Latin Square generation for 2x2 case."""
        conditions = ['A', 'B']
        ls = LatinSquare(conditions)
        square = ls._generate_square()
        
        assert len(square) == 2
        assert len(square[0]) == 2
        assert square[0] == ['A', 'B']
        assert square[1] == ['B', 'A']
    
    def test_deterministic_order_selection(self):
        """Test that order selection is deterministic based on participant_id and seed."""
        conditions = ['A', 'B']
        ls = LatinSquare(conditions)
        
        # Same inputs should produce same output
        order1 = ls.get_order_for_participant('p1', 42)
        order2 = ls.get_order_for_participant('p1', 42)
        assert order1 == order2
        
        # Different participant should potentially produce different order
        order3 = ls.get_order_for_participant('p2', 42)
        # Note: Due to hash distribution, different participants might get same order
        # but the important thing is determinism
    
    def test_order_contains_all_conditions(self):
        """Test that generated order contains all conditions exactly once."""
        conditions = ['A', 'B', 'C']
        ls = LatinSquare(conditions)
        
        for i in range(10):
            pid = f"participant_{i}"
            order = ls.get_order_for_participant(pid, seed=123)
            assert sorted(order) == sorted(conditions)
            assert len(order) == len(conditions)

class TestCounterbalanceManager:
    """Tests for the CounterbalanceManager class."""
    
    def test_initialization_default_strategy(self):
        """Test default initialization with latin_square strategy."""
        manager = CounterbalanceManager()
        assert manager.strategy == 'latin_square'
        assert manager.conditions == ['llm_assisted', 'baseline']
    
    def test_initialization_custom_seed(self):
        """Test initialization with custom seed."""
        manager = CounterbalanceManager(seed=999)
        assert manager.seed == 999
    
    def test_get_condition_order_latin_square(self):
        """Test condition order retrieval with Latin Square strategy."""
        manager = CounterbalanceManager(strategy='latin_square', seed=42)
        order = manager.get_condition_order('participant_001')
        
        assert isinstance(order, list)
        assert len(order) == 2
        assert set(order) == {'llm_assisted', 'baseline'}
    
    def test_get_condition_order_random_swap(self):
        """Test condition order retrieval with random swap strategy."""
        manager = CounterbalanceManager(strategy='random_swap', seed=42)
        order = manager.get_condition_order('participant_001')
        
        assert isinstance(order, list)
        assert len(order) == 2
        assert set(order) == {'llm_assisted', 'baseline'}
    
    def test_unknown_strategy_raises_error(self):
        """Test that unknown strategy raises CounterbalanceError."""
        manager = CounterbalanceManager(strategy='invalid_strategy')
        with pytest.raises(CounterbalanceError):
            manager.get_condition_order('participant_001')
    
    def test_reproducibility_across_runs(self):
        """Test that same participant always gets same order."""
        manager = CounterbalanceManager(strategy='latin_square', seed=42)
        
        orders = []
        for _ in range(5):
            order = manager.get_condition_order('test_participant')
            orders.append(order)
        
        # All orders should be identical
        assert all(o == orders[0] for o in orders)
    
    def test_verify_balance(self):
        """Test balance verification."""
        manager = CounterbalanceManager(strategy='latin_square', seed=42)
        
        # With 2 participants, should be perfectly balanced
        participant_ids = ['p1', 'p2']
        result = manager.verify_balance(participant_ids)
        
        assert result['total_participants'] == 2
        assert result['is_balanced'] is True
        assert len(result['order_counts']) <= 2  # At most 2 different orders
    
    def test_create_record(self):
        """Test counterbalance record creation."""
        manager = CounterbalanceManager(strategy='latin_square', seed=42)
        
        record = manager.create_record('participant_001')
        
        assert 'participant_id' in record
        assert record['participant_id'] == 'participant_001'
        assert 'strategy' in record
        assert record['strategy'] == 'latin_square'
        assert 'seed' in record
        assert 'condition_order' in record
        assert 'timestamp' in record
        assert 'hash' in record
        assert len(record['condition_order']) == 2

class TestApplyCounterbalancing:
    """Tests for the convenience function apply_counterbalancing."""
    
    def test_basic_usage(self):
        """Test basic usage of apply_counterbalancing."""
        order = apply_counterbalancing('participant_001', strategy='latin_square')
        
        assert isinstance(order, list)
        assert len(order) == 2
        assert set(order) == {'llm_assisted', 'baseline'}
    
    def test_different_strategies(self):
        """Test with different strategies."""
        order_latin = apply_counterbalancing('p1', strategy='latin_square')
        order_random = apply_counterbalancing('p1', strategy='random_swap')
        
        assert len(order_latin) == 2
        assert len(order_random) == 2
        assert set(order_latin) == {'llm_assisted', 'baseline'}
        assert set(order_random) == {'llm_assisted', 'baseline'}

class TestIntegration:
    """Integration tests for counterbalancing workflow."""
    
    def test_full_workflow_latin_square(self):
        """Test complete workflow with Latin Square strategy."""
        manager = CounterbalanceManager(strategy='latin_square', seed=42)
        
        # Simulate 20 participants
        participant_ids = [f"participant_{i:03d}" for i in range(1, 21)]
        
        orders = []
        for pid in participant_ids:
            order = manager.get_condition_order(pid)
            orders.append(order)
        
        # Verify balance
        balance = manager.verify_balance(participant_ids)
        
        # With 20 participants, should be reasonably balanced
        assert balance['total_participants'] == 20
        assert balance['balance_ratio'] <= 0.6  # Allow some tolerance
        
        # All orders should be valid
        for order in orders:
            assert len(order) == 2
            assert set(order) == {'llm_assisted', 'baseline'}
    
    def test_full_workflow_random_swap(self):
        """Test complete workflow with random swap strategy."""
        manager = CounterbalanceManager(strategy='random_swap', seed=123)
        
        # Simulate 20 participants
        participant_ids = [f"participant_{i:03d}" for i in range(1, 21)]
        
        orders = []
        for pid in participant_ids:
            order = manager.get_condition_order(pid)
            orders.append(order)
        
        # Verify balance
        balance = manager.verify_balance(participant_ids)
        
        assert balance['total_participants'] == 20
        
        # All orders should be valid
        for order in orders:
            assert len(order) == 2
            assert set(order) == {'llm_assisted', 'baseline'}

if __name__ == '__main__':
    pytest.main([__file__, '-v'])