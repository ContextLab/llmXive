import os
import json
import tempfile
import numpy as np
import pandas as pd
from simulation.verify_us1 import compute_run_id, verify_mnar_correlation, run_verification_and_save

def test_compute_run_id():
    """Test run ID computation."""
    run_id = compute_run_id(42, 0.5)
    assert isinstance(run_id, str)
    assert len(run_id) == 64  # SHA-256 hash length
    assert run_id == compute_run_id(42, 0.5)  # Deterministic

def test_verify_mnar_correlation():
    """Test MNAR correlation verification."""
    # Create data with known correlation
    np.random.seed(42)
    y = np.random.normal(0, 1, 1000)
    # Create mask correlated with y
    mask = (y > 0).astype(int)
    
    df = pd.DataFrame({'mask': mask, 'y': y})
    rho, p_value = verify_mnar_correlation(df, 'mask', 'y')
    
    assert rho > 0.5  # Should have strong positive correlation
    assert p_value < 0.01  # Should be statistically significant

def test_verify_mnar_correlation_no_correlation():
    """Test MNAR correlation with no correlation."""
    np.random.seed(42)
    y = np.random.normal(0, 1, 1000)
    mask = np.random.randint(0, 2, 1000)  # Random mask
    
    df = pd.DataFrame({'mask': mask, 'y': y})
    rho, p_value = verify_mnar_correlation(df, 'mask', 'y')
    
    assert abs(rho) < 0.1  # Should have near-zero correlation
    assert p_value > 0.05  # Should not be statistically significant

def test_run_verification_and_save():
    """Test verification and saving results."""
    np.random.seed(42)
    mask_data = np.random.randint(0, 2, 100)
    complete_y = np.random.normal(0, 1, 100)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        result = run_verification_and_save(
            seed=42,
            beta=0.5,
            mask_data=mask_data,
            complete_y=complete_y,
            output_path=temp_path
        )
        
        assert 'run_id' in result
        assert 'correlation' in result
        assert 'p_value' in result
        assert 'status' in result
        
        # Verify file was written
        assert os.path.exists(temp_path)
        
        # Verify JSON is valid
        with open(temp_path, 'r') as f:
            loaded = json.load(f)
        assert isinstance(loaded, list)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)