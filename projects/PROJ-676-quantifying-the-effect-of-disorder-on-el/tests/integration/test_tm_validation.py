import json
import os
import pytest
from pathlib import Path
from code.config import get_config

def test_tm_convergence_and_agreement():
    """
    Integration test for TM convergence and method agreement.
    """
    config = get_config()
    tm_path = Path(config.DATA_DIR) / "processed" / "lyapunov_exponents.json"
    pr_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    assert tm_path.exists(), "lyapunov_exponents.json not found"
    assert pr_path.exists(), "scaling_fits.json not found"
    
    with open(tm_path, 'r') as f:
        tm_data = json.load(f)
    with open(pr_path, 'r') as f:
        pr_data = json.load(f)
    
    assert len(tm_data) > 0, "TM results must not be empty"
    assert len(pr_data) > 0, "PR results must not be empty"
    
    # Check convergence trace existence
    tm_conv_path = Path(config.DATA_DIR) / "metadata" / "tm_convergence.json"
    assert tm_conv_path.exists(), "tm_convergence.json not found"
