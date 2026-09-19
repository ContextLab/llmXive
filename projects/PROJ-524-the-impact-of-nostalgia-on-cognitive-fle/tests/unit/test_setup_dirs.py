import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_dirs import create_required_directories
from code.config import get_config

def test_create_required_directories_creates_all():
    """Test that all required directories are created."""
    # Use a temporary directory as root for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock config to use temp dir
        import code.config
        original_get_config = code.config.get_config
        
        def mock_get_config():
            return {'root_dir': tmp_dir}
        
        code.config.get_config = mock_get_config

        try:
            count = create_required_directories()
            
            # Verify all directories exist
            required_dirs = [
                'data/raw',
                'data/processed',
                'data/results',
                'data/stimuli',
                'contracts',
                'code',
                'tests',
                'paper'
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} should exist"
                assert dir_path.is_dir(), f"{dir_path} should be a directory"
            
            assert count == len(required_dirs), f"Expected {len(required_dirs)} directories created, got {count}"
        finally:
            # Restore original function
            code.config.get_config = original_get_config

def test_create_required_directories_handles_existing():
    """Test that existing directories are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create one directory beforehand
        pre_existing = Path(tmp_dir) / 'data' / 'raw'
        pre_existing.mkdir(parents=True, exist_ok=True)
        
        import code.config
        original_get_config = code.config.get_config
        
        def mock_get_config():
            return {'root_dir': tmp_dir}
        
        code.config.get_config = mock_get_config

        try:
            count = create_required_directories()
            # Should still report all directories as 'created/verified'
            # (the function counts existing ones too)
            assert count > 0
        finally:
            code.config.get_config = original_get_config
