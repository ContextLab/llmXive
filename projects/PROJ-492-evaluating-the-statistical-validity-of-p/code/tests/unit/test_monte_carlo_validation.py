"""
Unit tests for Monte-Carlo validation module.
"""
import pytest
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    DIFFERENCE_THRESHOLD
)

def test_validate_z_test():
    passed, result = validate_z_test()
    assert result['test'] == 'z_test'
    assert 'theoretical_p' in result
    assert 'empirical_p' in result
    assert 'difference' in result
    assert result['passed'] is True
    assert result['difference'] <= DIFFERENCE_THRESHOLD

def test_validate_fisher_exact():
    passed, result = validate_fisher_exact()
    assert result['test'] == 'fisher_exact'
    assert 'theoretical_p' in result
    assert 'empirical_p' in result
    assert 'difference' in result
    assert result['passed'] is True
    assert result['difference'] <= DIFFERENCE_THRESHOLD

def test_validate_welch_t_test():
    passed, result = validate_welch_t_test()
    assert result['test'] == 'welch_t_test'
    assert 'theoretical_p' in result
    assert 'empirical_p' in result
    assert 'difference' in result
    assert result['passed'] is True
    assert result['difference'] <= DIFFERENCE_THRESHOLD

def test_validate_binomial_test():
    passed, result = validate_binomial_test()
    assert result['test'] == 'binomial'
    assert 'theoretical_p' in result
    assert 'empirical_p' in result
    assert 'difference' in result
    assert result['passed'] is True
    assert result['difference'] <= DIFFERENCE_THRESHOLD