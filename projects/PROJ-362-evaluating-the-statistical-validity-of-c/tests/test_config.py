import os
import sys

# Add project root to path if necessary
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DATA_RAW_DIR,
    RESULTS_DIR,
    NULL_DISTRIBUTIONS_DIR,
    P_VALUES_DIR,
    MDES_DIR,
    SENSITIVITY_DIR,
    PLOTS_DIR,
    ensure_dirs,
)

def test_directory_paths():
    """Test that directory paths are correctly constructed."""
    assert os.path.basename(DATA_DIR) == "data"
    assert os.path.basename(DATA_RAW_DIR) == "raw"
    assert os.path.basename(RESULTS_DIR) == "results"
    assert os.path.basename(NULL_DISTRIBUTIONS_DIR) == "null_distributions"
    assert os.path.basename(P_VALUES_DIR) == "p_values"
    assert os.path.basename(MDES_DIR) == "mdes"
    assert os.path.basename(SENSITIVITY_DIR) == "sensitivity"
    assert os.path.basename(PLOTS_DIR) == "plots"

def test_ensure_dirs():
    """Test that ensure_dirs creates the required directories."""
    # Run ensure_dirs
    result = ensure_dirs()
    assert result is True

    # Check that directories exist
    assert os.path.isdir(DATA_DIR)
    assert os.path.isdir(DATA_RAW_DIR)
    assert os.path.isdir(RESULTS_DIR)
    assert os.path.isdir(NULL_DISTRIBUTIONS_DIR)
    assert os.path.isdir(P_VALUES_DIR)
    assert os.path.isdir(MDES_DIR)
    assert os.path.isdir(SENSITIVITY_DIR)
    assert os.path.isdir(PLOTS_DIR)