import os
import random
import numpy as np
import pytest
import torch

def pytest_configure(config):
    """Configure pytest with random seed pinning."""
    config.addinivalue_line(
        "markers", "cpu_only: mark test to run only on CPU"
    )

@pytest.fixture(autouse=True)
def set_seed():
    """Fix random seeds for reproducibility."""
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    yield
    # Cleanup if needed
