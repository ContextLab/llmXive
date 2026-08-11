"""
Unit tests for the data directory structure setup.

Tests verify that:
1. All required subdirectories are created
2. .gitkeep files exist in each subdirectory
3. .gitignore file is created with correct rules
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_config
from setup_data_structure import setup_data_structure


class TestDataDirectorySetup:
    """Test cases for data directory structure setup."""
    
    def test_setup_creates_all_directories(self, tmp_path):
        """Verify that all required subdirectories are created."""
        # Mock config to use temporary directory
        original_config = get_config()
        
        # Create a temporary config pointing to tmp_path
        import config as config_module
        original_get_config = config_module.get_config
        
        def mock_get_config():
            return {
                'paths': {
                    'data_dir': str(tmp_path / 'data')
                }
            }
        
        config_module.get_config = mock_get_config
        
        try:
            setup_data_structure()
            
            # Check that all required directories exist
            required_dirs = ['raw', 'derived', 'validation', 'logs']
            for subdir in required_dirs:
                dir_path = tmp_path / 'data' / subdir
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
        finally:
            # Restore original config
            config_module.get_config = original_get_config
    
    def test_setup_creates_gitkeep_files(self, tmp_path):
        """Verify that .gitkeep files are created in each subdirectory."""
        import config as config_module
        original_get_config = config_module.get_config
        
        def mock_get_config():
            return {
                'paths': {
                    'data_dir': str(tmp_path / 'data')
                }
            }
        
        config_module.get_config = mock_get_config
        
        try:
            setup_data_structure()
            
            # Check that .gitkeep exists in each subdirectory
            required_dirs = ['raw', 'derived', 'validation', 'logs']
            for subdir in required_dirs:
                gitkeep_path = tmp_path / 'data' / subdir / '.gitkeep'
                assert gitkeep_path.exists(), f".gitkeep file not found in {subdir}"
                assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"
        finally:
            config_module.get_config = original_get_config
    
    def test_setup_creates_gitignore(self, tmp_path):
        """Verify that .gitignore is created with correct rules."""
        import config as config_module
        original_get_config = config_module.get_config
        
        def mock_get_config():
            return {
                'paths': {
                    'data_dir': str(tmp_path / 'data')
                }
            }
        
        config_module.get_config = mock_get_config
        
        try:
            setup_data_structure()
            
            gitignore_path = tmp_path / 'data' / '.gitignore'
            assert gitignore_path.exists(), ".gitignore file was not created"
            
            content = gitignore_path.read_text()
            
            # Check for required rules
            assert 'raw/*' in content, "Missing rule for raw/*"
            assert '!raw/.gitkeep' in content, "Missing exception for raw/.gitkeep"
            assert 'derived/*' in content, "Missing rule for derived/*"
            assert '!derived/.gitkeep' in content, "Missing exception for derived/.gitkeep"
            assert 'validation/*' in content, "Missing rule for validation/*"
            assert '!validation/.gitkeep' in content, "Missing exception for validation/.gitkeep"
            assert 'logs/*' in content, "Missing rule for logs/*"
            assert '!logs/.gitkeep' in content, "Missing exception for logs/.gitkeep"
        finally:
            config_module.get_config = original_get_config
    
    def test_setup_idempotent(self, tmp_path):
        """Verify that running setup multiple times doesn't cause errors."""
        import config as config_module
        original_get_config = config_module.get_config
        
        def mock_get_config():
            return {
                'paths': {
                    'data_dir': str(tmp_path / 'data')
                }
            }
        
        config_module.get_config = mock_get_config
        
        try:
            # Run setup twice
            setup_data_structure()
            setup_data_structure()
            
            # Verify directories still exist
            required_dirs = ['raw', 'derived', 'validation', 'logs']
            for subdir in required_dirs:
                dir_path = tmp_path / 'data' / subdir
                assert dir_path.exists(), f"Directory {dir_path} missing after second run"
        finally:
            config_module.get_config = original_get_config