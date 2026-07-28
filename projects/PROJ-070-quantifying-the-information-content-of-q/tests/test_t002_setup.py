import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Verify that all modules initialized in T002 can be imported."""
    try:
        from code.config import Config
        from code.logging_config import setup_logging, logger
        from code.data_loader import validate_external_datasets, generate_internal_wavefunction, E_DATASET_MISSING
        from code.metrics import check_numerical_stability, calculate_entanglement_entropy, quantize_wavefunction, calculate_ncd
        from code.statistics import calculate_correlation, calculate_partial_correlation, bootstrap_correlation
        from code.viz import plot_scatter_with_regression
        assert True
    except ImportError as e:
        raise AssertionError(f"Import failed: {e}")

def test_config_seed():
    """Test Config seed initialization."""
    from code.config import Config
    cfg = Config(seed=42)
    assert cfg.seed == 42
    assert cfg.random_state is not None

def test_logging_setup():
    """Test logging setup."""
    from code.logging_config import logger
    assert logger is not None
    assert logger.level is not None

def test_data_loader_structure():
    """Test data loader basic structure."""
    from code.data_loader import validate_external_datasets
    # Should not raise, just log
    result = validate_external_datasets()
    assert result is True

def test_metrics_stability():
    """Test numerical stability check."""
    from code.metrics import check_numerical_stability
    import numpy as np
    good_data = np.array([1.0, 2.0, 3.0])
    bad_data = np.array([1.0, np.nan, 3.0])
    
    assert check_numerical_stability(good_data) is True
    assert check_numerical_stability(bad_data) is False