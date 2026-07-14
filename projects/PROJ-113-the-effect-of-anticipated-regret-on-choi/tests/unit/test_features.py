import pandas as pd
import numpy as np
import pytest

from features import (
    calculate_min_max_regret,
    calculate_potential_loss_magnitude,
    calculate_price_variance_proxy,
    add_perceived_risk_covariate,
    validate_regret_proxy_single_option
)


def test_calculate_min_max_regret_multi_option():
    """Test regret calculation with multiple options."""
    df = pd.DataFrame({
        'context_id': [1, 1, 2, 2],
        'option_id': ['A', 'B', 'A', 'B'],
        'utility': [0.8, 0.5, 0.9, 0.2]
    })
    result = calculate_min_max_regret(df)
    
    # Context 1: Max=0.8. Regret for A=0, B=0.3
    # Context 2: Max=0.9. Regret for A=0, B=0.7
    assert result.loc[0, 'regret_proxy'] == 0.0
    assert result.loc[1, 'regret_proxy'] == 0.3
    assert result.loc[2, 'regret_proxy'] == 0.0
    assert result.loc[3, 'regret_proxy'] == 0.7


def test_calculate_min_max_regret_single_option():
    """Test regret calculation with single option (should be 0)."""
    df = pd.DataFrame({
        'context_id': [1],
        'option_id': ['A'],
        'utility': [0.5]
    })
    result = calculate_min_max_regret(df)
    assert result.loc[0, 'regret_proxy'] == 0.0


def test_calculate_price_variance_proxy():
    """Test price variance calculation."""
    df = pd.DataFrame({
        'context_id': [1, 1, 2, 2],
        'price': [10.0, 12.0, 5.0, 5.0]
    })
    result = calculate_price_variance_proxy(df)
    
    # Context 1: Var([10, 12]) = 2.0
    # Context 2: Var([5, 5]) = 0.0
    assert result.loc[0, 'price_variance'] == 2.0
    assert result.loc[1, 'price_variance'] == 2.0
    assert result.loc[2, 'price_variance'] == 0.0
    assert result.loc[3, 'price_variance'] == 0.0


def test_add_perceived_risk_covariate_missing():
    """Test fallback logic when perceived_risk is missing."""
    df = pd.DataFrame({
        'context_id': [1, 1],
        'price': [10.0, 12.0]
    })
    result = add_perceived_risk_covariate(df)
    
    assert 'perceived_risk' in result.columns
    assert result.loc[0, 'perceived_risk'] == 2.0
    assert result.loc[1, 'perceived_risk'] == 2.0


def test_add_perceived_risk_covariate_exists():
    """Test that existing perceived_risk is preserved."""
    df = pd.DataFrame({
        'context_id': [1, 1],
        'price': [10.0, 12.0],
        'perceived_risk': [1.0, 1.0]
    })
    result = add_perceived_risk_covariate(df)
    
    assert result.loc[0, 'perceived_risk'] == 1.0
    assert result.loc[1, 'perceived_risk'] == 1.0


def test_validate_regret_proxy_single_option():
    """Test validation of single option regret."""
    df = pd.DataFrame({
        'context_id': [1, 2, 2],
        'option_id': ['A', 'A', 'B'],
        'utility': [0.5, 0.8, 0.2]
    })
    # First, calculate regret normally
    df = calculate_min_max_regret(df)
    # Then validate (context 1 has 1 option, context 2 has 2)
    result = validate_regret_proxy_single_option(df)
    
    assert result.loc[0, 'regret_proxy'] == 0.0
    # Context 2 should remain as calculated (0 and 0.6)
    assert result.loc[1, 'regret_proxy'] == 0.0
    assert result.loc[2, 'regret_proxy'] == 0.6
