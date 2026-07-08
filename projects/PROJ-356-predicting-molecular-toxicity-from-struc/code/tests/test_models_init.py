"""
Test for models package initialization.
Verifies that the models directory and package are correctly set up.
"""
import os
import sys
from pathlib import Path

import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

def test_models_directory_exists():
    """Test that the models directory exists."""
    models_dir = code_dir / "models"
    assert models_dir.exists(), f"Models directory does not exist at {models_dir}"
    assert models_dir.is_dir(), f"{models_dir} is not a directory"

def test_models_init_exists():
    """Test that the __init__.py file exists in the models directory."""
    init_file = code_dir / "models" / "__init__.py"
    assert init_file.exists(), f"__init__.py does not exist at {init_file}"

def test_models_package_importable():
    """Test that the models package can be imported."""
    try:
        import models
        assert models is not None, "Models package is None"
    except ImportError as e:
        pytest.fail(f"Failed to import models package: {e}")