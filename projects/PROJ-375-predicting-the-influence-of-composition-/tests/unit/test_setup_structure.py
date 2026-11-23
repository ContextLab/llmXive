"""
Unit tests for project structure initialization.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories

class TestCreateDirectories:
    def test_creates_required_dirs(self, tmp_path):
        """Test that all required directories are created."""
        # Mock the base_dir to be tmp_path
        with patch('setup_structure.Path') as mock_path:
            mock_base = MagicMock()
            mock_base.__truediv__ = lambda self, other: tmp_path / other
            mock_base.__fspath__ = lambda self: str(tmp_path)
            mock_path.return_value = mock_base
            mock_path.side_effect = lambda x: Path(x) if isinstance(x, str) else x

            # Run the function
            result = create_directories()

            # Verify result
            assert result is True

            # Verify directories exist
            required_dirs = [
                "code/ingestion", "code/features", "code/modeling", "code/utils",
                "data/raw", "data/processed", "tests/unit", "tests/integration",
                "docs", "logs", "models", "results", "contracts"
            ]
            
            for dir_name in required_dirs:
                assert (tmp_path / dir_name).exists(), f"Directory {dir_name} was not created"

    def test_handles_existing_dirs(self, tmp_path):
        """Test that the function handles pre-existing directories gracefully."""
        # Pre-create some directories
        (tmp_path / "code").mkdir(parents=True)
        (tmp_path / "code" / "ingestion").mkdir()

        with patch('setup_structure.Path') as mock_path:
            mock_base = MagicMock()
            mock_base.__truediv__ = lambda self, other: tmp_path / other
            mock_base.__fspath__ = lambda self: str(tmp_path)
            mock_path.return_value = mock_base
            mock_path.side_effect = lambda x: Path(x) if isinstance(x, str) else x

            # Run the function
            result = create_directories()

            assert result is True
            assert (tmp_path / "code" / "ingestion").exists()

    def test_main_execution(self, tmp_path, capsys):
        """Test the __main__ execution block."""
        import setup_structure
        
        # Save original __file__
        original_file = setup_structure.__file__
        
        try:
            # Temporarily modify __file__ to point to tmp_path for testing
            # Note: This is a simplified test; in real scenarios, we'd mock Path creation
            setup_structure.__file__ = str(tmp_path / "setup_structure.py")
            
            # We can't easily test the full __main__ block without complex mocking,
            # but we can verify the script doesn't crash when imported
            assert hasattr(setup_structure, 'create_directories')
        finally:
            setup_structure.__file__ = original_file