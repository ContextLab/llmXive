"""
Tests to verify that the models package is correctly initialized.
"""
import os
import sys
from pathlib import Path
import pytest

def test_models_directory_exists():
    """Verify the models directory exists."""
    models_dir = Path(__file__).parent.parent / "models"
    assert models_dir.exists(), f"Models directory {models_dir} does not exist"
    assert models_dir.is_dir(), f"{models_dir} is not a directory"

def test_models_init_exists():
    """Verify models/__init__.py exists."""
    init_file = Path(__file__).parent.parent / "models" / "__init__.py"
    assert init_file.exists(), f"models/__init__.py does not exist"

def test_models_package_importable():
    """Verify the models package can be imported."""
    code_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(code_dir))
    try:
        import models
        assert hasattr(models, '__path__'), "models is not a package"
    except ImportError as e:
        pytest.fail(f"Failed to import models package: {e}")
    finally:
        if str(code_dir) in sys.path:
            sys.path.remove(str(code_dir))
