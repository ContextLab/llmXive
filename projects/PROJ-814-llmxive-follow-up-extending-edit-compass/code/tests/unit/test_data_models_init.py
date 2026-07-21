"""
Tests for the data-models package initialization.
"""

import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

class TestDataModelsInit:
    """Test that the data-models package initializes correctly."""
    
    def test_package_exists(self):
        """Assert that the data-models directory exists."""
        package_path = code_dir / "src" / "data-models"
        assert package_path.exists(), f"Directory {package_path} does not exist"
        assert package_path.is_dir(), f"{package_path} is not a directory"
    
    def test_init_file_exists(self):
        """Assert that __init__.py exists in the package."""
        init_path = code_dir / "src" / "data-models" / "__init__.py"
        assert init_path.exists(), f"File {init_path} does not exist"
    
    def test_import_models(self):
        """Assert that EditInstance and ScoreRecord can be imported from the package."""
        try:
            from src.data_models import EditInstance, ScoreRecord
            assert EditInstance is not None
            assert ScoreRecord is not None
        except ImportError as e:
            pytest.fail(f"Failed to import models from src.data_models: {e}")
    
    def test_package_exports(self):
        """Assert that the package exports the expected names."""
        import src.data_models as dm
        assert "EditInstance" in dir(dm)
        assert "ScoreRecord" in dir(dm)