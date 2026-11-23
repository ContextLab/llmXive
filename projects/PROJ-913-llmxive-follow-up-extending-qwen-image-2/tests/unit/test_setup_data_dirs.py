import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from utils.setup_data_dirs import setup_data_directories
from config import PROJECT_ROOT

class TestSetupDataDirs:
    @patch('utils.setup_data_dirs.get_logger')
    def test_creates_required_directories(self, mock_logger):
        """Test that the function creates all required directories."""
        # Mock the logger to avoid side effects
        mock_logger.return_value = MagicMock()

        # We will check existence manually after call
        # Since we can't easily mock mkdir in a way that persists for checking in a unit test 
        # without patching the actual Path, we rely on the logic check here.
        # However, to be safe in a real environment, we'd run this in a temp dir.
        # For this unit test context, we assert the logic path.
        
        # Let's patch Path.mkdir to track calls
        original_mkdir = Path.mkdir
        created_dirs = []

        def mock_mkdir(self, parents=False, exist_ok=False):
            created_dirs.append(str(self))
            # Don't actually create on disk for this unit test
            return True

        with patch.object(Path, 'mkdir', mock_mkdir):
            with patch.object(Path, 'touch', return_value=True):
                setup_data_directories()

        # Verify expected directories were attempted to be created
        expected_suffixes = [
            "prompts",
            "models",
            "outputs/base",
            "outputs/rl_unified",
            "raw",
            "processed",
            "logs"
        ]
        
        for suffix in expected_suffixes:
            # Check if any created dir ends with the suffix (handling root path variance)
            found = any(str(d).endswith(suffix) for d in created_dirs)
            assert found, f"Directory {suffix} was not created/attempted"

    @patch('utils.setup_data_dirs.get_logger')
    def test_creates_gitkeep_files(self, mock_logger):
        """Test that .gitkeep files are created in the directories."""
        mock_logger.return_value = MagicMock()
        
        touch_calls = []
        
        def mock_touch(self):
            touch_calls.append(str(self))
            return True

        with patch.object(Path, 'mkdir', return_value=True):
            with patch.object(Path, 'touch', mock_touch):
                setup_data_directories()
        
        # Verify .gitkeep was touched for each directory
        # We expect one .gitkeep per directory created
        assert len(touch_calls) > 0, "No .gitkeep files were created"
        for call_path in touch_calls:
            assert call_path.endswith(".gitkeep"), f"File {call_path} is not a .gitkeep file"
