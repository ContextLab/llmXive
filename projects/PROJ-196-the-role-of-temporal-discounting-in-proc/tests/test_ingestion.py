import pytest
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingestion import validate_dgp_config, calculate_cronbach_alpha
from code.config import get_random_state

# Mock DGP configurations for testing
VALID_DGP_CONFIG = {
    "n_participants": 500,
    "delay_discounting": {
        "k_mean": 0.05,
        "k_std": 0.02,
        "reliability_alpha": 0.85
    },
    "procrastination": {
        "mean_score": 3.5,
        "std_score": 1.2,
        "reliability_alpha": 0.80
    },
    "working_memory": {
        "accuracy_mean": 0.75,
        "accuracy_std": 0.10,
        "reliability_alpha": 0.90
    }
}

INVALID_DGP_CONFIG_MISSING_KEY = {
    "n_participants": 500,
    "delay_discounting": {
        "k_mean": 0.05,
        "k_std": 0.02,
        # Missing reliability_alpha
    },
    "procrastination": {
        "mean_score": 3.5,
        "std_score": 1.2,
        "reliability_alpha": 0.80
    },
    "working_memory": {
        "accuracy_mean": 0.75,
        "accuracy_std": 0.10,
        "reliability_alpha": 0.90
    }
}

INVALID_DGP_CONFIG_NEGATIVE = {
    "n_participants": -10,
    "delay_discounting": {
        "k_mean": 0.05,
        "k_std": 0.02,
        "reliability_alpha": 0.85
    },
    "procrastination": {
        "mean_score": 3.5,
        "std_score": 1.2,
        "reliability_alpha": 0.80
    },
    "working_memory": {
        "accuracy_mean": 0.75,
        "accuracy_std": 0.10,
        "reliability_alpha": 0.90
    }
}

def test_validate_dgp_config_valid():
    """Test that a valid DGP configuration passes validation."""
    result = validate_dgp_config(VALID_DGP_CONFIG)
    assert result is True

def test_validate_dgp_config_missing_key():
    """Test that a DGP configuration missing required keys fails validation."""
    with pytest.raises(ValueError) as excinfo:
        validate_dgp_config(INVALID_DGP_CONFIG_MISSING_KEY)
    assert "reliability_alpha" in str(excinfo.value)

def test_validate_dgp_config_negative_participants():
    """Test that a DGP configuration with negative participants fails validation."""
    with pytest.raises(ValueError) as excinfo:
        validate_dgp_config(INVALID_DGP_CONFIG_NEGATIVE)
    assert "n_participants" in str(excinfo.value)
    assert "positive" in str(excinfo.value)

def test_validate_dgp_config_invalid_alpha():
    """Test that a DGP configuration with invalid alpha values fails validation."""
    invalid_config = VALID_DGP_CONFIG.copy()
    invalid_config["delay_discounting"]["reliability_alpha"] = 1.5
    with pytest.raises(ValueError) as excinfo:
        validate_dgp_config(invalid_config)
    assert "reliability_alpha" in str(excinfo.value)
    assert "between 0 and 1" in str(excinfo.value)

def test_cronbach_alpha_calculation():
    """Test Cronbach's alpha calculation with known data."""
    # Create a simple dataset with known reliability
    np.random.seed(42)
    n_items = 5
    n_participants = 100
    # Generate correlated items
    latent = np.random.normal(0, 1, n_participants)
    items = latent[:, np.newaxis] + np.random.normal(0, 0.5, (n_participants, n_items))
    df = pd.DataFrame(items, columns=[f"item_{i}" for i in range(n_items)])
    
    alpha = calculate_cronbach_alpha(df)
    assert 0.5 < alpha < 0.95  # Should be reasonably high due to construction

def test_cronbach_alpha_single_item():
    """Test Cronbach's alpha with single item (should return 0 or handle gracefully)."""
    df = pd.DataFrame({"item_1": [1, 2, 3, 4, 5]})
    alpha = calculate_cronbach_alpha(df)
    assert alpha == 0.0 or alpha < 0.01  # Single item has no internal consistency

def test_cronbach_alpha_no_variance():
    """Test Cronbach's alpha with no variance in items."""
    df = pd.DataFrame({"item_1": [1, 1, 1, 1], "item_2": [2, 2, 2, 2]})
    alpha = calculate_cronbach_alpha(df)
    # Should handle division by zero or return 0
    assert alpha == 0.0 or np.isnan(alpha)

def test_random_state_consistency():
    """Test that DGP generation uses the provided random state."""
    # This is a basic check that the random state is being used
    # In a full implementation, we would verify the exact outputs
    rng1 = get_random_state(42)
    rng2 = get_random_state(42)
    
    # Both should produce the same sequence
    val1 = rng1.random()
    val2 = rng2.random()
    assert val1 == val2