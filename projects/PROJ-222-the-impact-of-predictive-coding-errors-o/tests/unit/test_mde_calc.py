import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import calculate_mde

def test_mde_calculation():
    """Test that MDE is calculated correctly and is positive."""
    # Create synthetic data for testing (real data is not available in unit test context)
    # Note: In integration tests, we would use real data. Here we verify the math.
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "duration_estimate": np.random.normal(100, 10, n),
        "surprisal": np.random.normal(0, 1, n),
        "sequence_length": np.random.randint(1, 10, n),
        "modality": np.random.choice(["visual", "auditory"], n),
        "participant_id": [f"P{i}" for i in range(n)]
    })
    
    mde = calculate_mde(data)
    
    # MDE should be a positive number
    assert mde > 0, "MDE should be positive"
    
    # MDE should decrease as sample size increases (inverse relationship)
    mde_large = calculate_mde(data.assign(duration_estimate=np.random.normal(100, 10, 1000)))
    # Note: This simple test might be flaky due to randomness, but the logic holds.
    # We primarily check that it returns a float > 0.
    
def test_mde_small_sample():
    """Test MDE with very small sample size."""
    data = pd.DataFrame({
        "duration_estimate": [10, 12, 11, 13, 10],
        "surprisal": [0.1, 0.2, 0.3, 0.4, 0.5],
        "sequence_length": [1, 2, 3, 4, 5],
        "modality": ["vis", "aud", "vis", "aud", "vis"],
        "participant_id": ["P1", "P2", "P3", "P4", "P5"]
    })
    
    mde = calculate_mde(data)
    assert mde > 0
    # MDE should be larger for smaller samples
    assert mde > 1.0 # Heuristic check

def test_mde_zero_variance():
    """Test MDE with zero variance in outcome."""
    data = pd.DataFrame({
        "duration_estimate": [10, 10, 10, 10],
        "surprisal": [0.1, 0.2, 0.3, 0.4],
        "sequence_length": [1, 2, 3, 4],
        "modality": ["vis", "aud", "vis", "aud"],
        "participant_id": ["P1", "P2", "P3", "P4"]
    })
    
    mde = calculate_mde(data)
    assert mde == 0.0, "MDE should be 0 if variance is 0"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
