"""
Unit tests for the budget check logic (T033).
"""
import pytest
import sys
from pathlib import Path
import json
import os
import tempfile
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.pipeline.budget_check import (
    calculate_max_realizations,
    run_budget_check,
    calculate_per_unit_time
)

def test_calculate_max_realizations():
    """Test the core calculation of max realizations."""
    budget = 3600  # 1 hour
    per_unit = 10  # 10 seconds per unit
    n_frac = 2
    n_algo = 2
    
    # Total operations per realization = 2 * 2 = 4
    # Time per realization = 40 seconds
    # Max N = 3600 / 40 = 90
    expected = 90
    result = calculate_max_realizations(budget, per_unit, n_frac, n_algo)
    assert result == expected

def test_calculate_max_realizations_zero():
    """Test that zero budget or zero time returns 0."""
    assert calculate_max_realizations(0, 10, 1, 1) == 0
    assert calculate_max_realizations(100, 0, 1, 1) == 0
    assert calculate_max_realizations(100, 10, 0, 1) == 0

def test_reduction_logic_fractions():
    """Test that N_fractions are reduced first when N < 30."""
    budget = 1000  # Small budget
    per_unit = 10  # 10s per unit
    requested_n_frac = 10
    requested_n_algo = 5
    
    # With 10*5=50 ops, time per real = 500s.
    # Max N = 1000/500 = 2. (Less than 30)
    # Should reduce fractions first.
    
    final_config = run_budget_check(
        budget_seconds=budget,
        per_unit_time=per_unit,
        requested_n_fractions=requested_n_frac,
        requested_n_algos=requested_n_algo,
        gap_fractions=list(range(requested_n_frac)),
        algo_names=list(range(requested_n_algo)),
        min_realizations=30
    )
    
    # We expect fractions to be reduced significantly to increase N
    # 1000s budget. Target N >= 30.
    # Max ops per real = 1000 / 30 = 33.3
    # So we need N_frac * N_algo <= 33
    # If we start with 5 algos, max fractions = 33/5 = 6.
    # So fractions should be reduced from 10 to 6.
    
    assert final_config['n_fractions'] < requested_n_frac
    assert final_config['n_algos'] == requested_n_algo  # Algos shouldn't be reduced yet
    assert final_config['n_realizations'] >= 30 or final_config['status'] == 'insufficient_budget'

def test_reduction_logic_algos():
    """Test that N_algos are reduced if fractions cannot be reduced enough."""
    # Setup: Budget allows for very few operations per realization.
    # If we have only 1 fraction, and still N < 30, we must reduce algos.
    budget = 100
    per_unit = 10
    requested_n_frac = 1
    requested_n_algo = 10
    
    # Ops per real = 1 * 10 = 10. Time = 100s.
    # Max N = 100 / 100 = 1. (Less than 30)
    # Reduce fractions? Already 1.
    # Reduce algos? Yes.
    # Target N >= 30. Max ops = 100/30 = 3.3.
    # With 1 fraction, max algos = 3.
    
    final_config = run_budget_check(
        budget_seconds=budget,
        per_unit_time=per_unit,
        requested_n_fractions=requested_n_frac,
        requested_n_algos=requested_n_algo,
        gap_fractions=[0.1],
        algo_names=list(range(requested_n_algo)),
        min_realizations=30
    )
    
    assert final_config['n_algos'] < requested_n_algo
    assert final_config['n_fractions'] == requested_n_frac

def test_reduction_logic_halt():
    """Test that if N < 30 even with 1 frac and 1 algo, status is insufficient."""
    budget = 100
    per_unit = 200  # 200s per unit
    requested_n_frac = 1
    requested_n_algo = 1
    
    # Ops = 1. Time = 200s. Max N = 0.
    final_config = run_budget_check(
        budget_seconds=budget,
        per_unit_time=per_unit,
        requested_n_fractions=requested_n_frac,
        requested_n_algos=requested_n_algo,
        gap_fractions=[0.1],
        algo_names=["algo1"],
        min_realizations=30
    )
    
    assert final_config['status'] == 'insufficient_budget'
    assert final_config['n_realizations'] == 0
