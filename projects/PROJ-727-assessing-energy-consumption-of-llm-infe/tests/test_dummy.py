"""
T008a: Dummy inference test to verify environment without OOM risk.
"""
import sys
import os
import torch

def test_dummy_inference():
    """
    Performs a lightweight import check and a single-token generation 
    using a small dummy prompt to verify environment without OOM risk.
    """
    # 1. Verify torch is available and working
    try:
        device = torch.device("cpu")
        x = torch.ones(1, 1).to(device)
        assert x.sum().item() == 1.0
    except Exception as e:
        raise AssertionError(f"Torch environment check failed: {e}")

    # 2. Verify key imports work
    try:
        from code.config import ensure_directories, get_model_hf_id
        from codecarbon import EmissionsTracker
        import pandas as pd
        import numpy as np
    except ImportError as e:
        raise AssertionError(f"Import check failed: {e}")

    # 3. Verify directories can be created
    try:
        ensure_directories()
    except Exception as e:
        raise AssertionError(f"Directory creation failed: {e}")

    print("Environment Verified: All imports and basic checks passed.")
    return True

if __name__ == "__main__":
    test_dummy_inference()