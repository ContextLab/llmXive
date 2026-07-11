"""
Basic smoke test to verify configuration loading and directory structure.
"""
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_imports():
    """Verify core dependencies are importable."""
    import pandas as pd
    import numpy as np
    import scipy
    import statsmodels
    import sklearn
    import yaml
    import jsonschema
    assert pd is not None
    assert np is not None

def test_config_loads():
    """Verify code.config imports successfully."""
    from code import config
    assert hasattr(config, 'PROJECT_ROOT')
    assert hasattr(config, 'DATA_RAW_DIR')
    assert hasattr(config, 'logger')

def test_directories_exist():
    """Verify required data directories exist."""
    from code import config
    assert config.DATA_RAW_DIR.exists()
    assert config.DATA_PROCESSED_DIR.exists()
    assert config.DATA_MODELS_DIR.exists()