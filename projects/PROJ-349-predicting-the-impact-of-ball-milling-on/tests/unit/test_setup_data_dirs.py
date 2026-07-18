import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_data_dirs import setup_directories

class TestSetupDataDirs:
    """Tests for the setup_directories function."""

    def test_directories_created(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Mock the project root detection by patching __file__
            with patch('code.setup_data_dirs.Path') as mock_path:
                # Setup mock to return our temp directory structure
                mock_file = MagicMock()
                mock_file.resolve.return_value = tmp_path / 'code' / 'setup_data_dirs.py'
                mock_path.return_value = mock_file
                
                # We need to manually set up the directory structure in temp
                # because the function expects to run from a specific location
                (tmp_path / 'data').mkdir(parents=True, exist_ok=True)
                (tmp_path / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
                (tmp_path / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
                (tmp_path / 'data' / 'splits').mkdir(parents=True, exist_ok=True)
                (tmp_path / 'results').mkdir(parents=True, exist_ok=True)
                
                # Actually, let's test the real function by changing directory
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmp_path)
                    # Create the code directory structure
                    (tmp_path / 'code').mkdir()
                    os.chdir(tmp_path / 'code')
                    
                    # Now run the function
                    # We need to temporarily modify the function to use our temp dir
                    import code.setup_data_dirs as sd
                    original_resolve = Path.resolve
                    
                    def mock_resolve(self):
                        if self.name == 'setup_data_dirs.py':
                            return Path(tmp_path) / 'code' / 'setup_data_dirs.py'
                        return original_resolve(self)
                    
                    with patch.object(Path, 'resolve', mock_resolve):
                        result = sd.setup_directories()
                    
                    # Verify directories exist
                    assert 'data/raw' in result
                    assert 'data/processed' in result
                    assert 'data/splits' in result
                    assert 'results' in result
                    
                    for rel_path in result:
                        assert result[rel_path].exists()
                    
                finally:
                    os.chdir(original_cwd)

    def test_gitkeep_files_created(self):
        """Test that .gitkeep files are created in each directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Set up the directory structure
            (tmp_path / 'code').mkdir()
            (tmp_path / 'data').mkdir()
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path / 'code')
                
                import code.setup_data_dirs as sd
                original_resolve = Path.resolve
                
                def mock_resolve(self):
                    if self.name == 'setup_data_dirs.py':
                        return Path(tmp_path) / 'code' / 'setup_data_dirs.py'
                    return original_resolve(self)
                
                with patch.object(Path, 'resolve', mock_resolve):
                    sd.setup_directories()
                
                # Check that .gitkeep files exist
                for dir_name in ['data/raw', 'data/processed', 'data/splits', 'results', 'data/flagged']:
                    gitkeep_path = tmp_path / dir_name / '.gitkeep'
                    assert gitkeep_path.exists(), f".gitkeep not found in {dir_name}"
                    
            finally:
                os.chdir(original_cwd)

    def test_existing_directories_not_recreated(self):
        """Test that existing directories are not recreated but still returned."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Pre-create some directories
            (tmp_path / 'data').mkdir()
            (tmp_path / 'data' / 'raw').mkdir()
            (tmp_path / 'results').mkdir()
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path / 'code')
                (tmp_path / 'code').mkdir(exist_ok=True)
                
                import code.setup_data_dirs as sd
                original_resolve = Path.resolve
                
                def mock_resolve(self):
                    if self.name == 'setup_data_dirs.py':
                        return Path(tmp_path) / 'code' / 'setup_data_dirs.py'
                    return original_resolve(self)
                
                with patch.object(Path, 'resolve', mock_resolve):
                    result = sd.setup_directories()
                
                # Verify all directories are in result
                assert 'data/raw' in result
                assert 'results' in result
                assert result['data/raw'].exists()
                assert result['results'].exists()
                
            finally:
                os.chdir(original_cwd)

    def test_nested_directory_creation(self):
        """Test that nested directories are created when parent doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Only create the root data directory
            (tmp_path / 'data').mkdir()
            # Do NOT create data/processed, data/splits, etc.
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_path / 'code')
                (tmp_path / 'code').mkdir(exist_ok=True)
                
                import code.setup_data_dirs as sd
                original_resolve = Path.resolve
                
                def mock_resolve(self):
                    if self.name == 'setup_data_dirs.py':
                        return Path(tmp_path) / 'code' / 'setup_data_dirs.py'
                    return original_resolve(self)
                
                with patch.object(Path, 'resolve', mock_resolve):
                    result = sd.setup_directories()
                
                # Verify nested directories were created
                assert result['data/processed'].exists()
                assert result['data/splits'].exists()
                assert result['results'].exists()
                
            finally:
                os.chdir(original_cwd)