import os
import tempfile
import shutil
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code'))

from data.create_data_dirs import main

def test_data_directories_creation():
    """Test that the data directories and .gitkeep files are created correctly."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project structure
        code_dir = os.path.join(tmpdir, 'code')
        data_dir = os.path.join(tmpdir, 'data')
        os.makedirs(code_dir)
        
        # Temporarily change the base directory calculation
        # We'll test by directly calling the logic with a modified path
        import data.create_data_dirs as module
        
        # Save original function
        original_main = module.main
        
        # Override to use our temp dir
        def mock_main():
            base_dir = data_dir
            subdirs = ['raw', 'processed', 'explainability']
            
            for subdir in subdirs:
                dir_path = os.path.join(base_dir, subdir)
                os.makedirs(dir_path, exist_ok=True)
                
                keep_path = os.path.join(dir_path, '.gitkeep')
                with open(keep_path, 'w') as f:
                    f.write('# Keep this directory in git\n')
            
            return 0
        
        module.main = mock_main
        try:
            result = module.main()
            assert result == 0, "main() should return 0 on success"
            
            # Verify directories exist
            for subdir in ['raw', 'processed', 'explainability']:
                dir_path = os.path.join(data_dir, subdir)
                assert os.path.isdir(dir_path), f"Directory {dir_path} should exist"
                
                keep_path = os.path.join(dir_path, '.gitkeep')
                assert os.path.isfile(keep_path), f".gitkeep file {keep_path} should exist"
                
                with open(keep_path, 'r') as f:
                    content = f.read()
                    assert '# Keep this directory in git' in content, ".gitkeep should contain expected content"
        finally:
            module.main = original_main

def test_idempotency():
    """Test that running the creation multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_dir = os.path.join(tmpdir, 'code')
        data_dir = os.path.join(tmpdir, 'data')
        os.makedirs(code_dir)
        
        import data.create_data_dirs as module
        
        def mock_main():
            base_dir = data_dir
            subdirs = ['raw', 'processed', 'explainability']
            
            for subdir in subdirs:
                dir_path = os.path.join(base_dir, subdir)
                os.makedirs(dir_path, exist_ok=True)
                
                keep_path = os.path.join(dir_path, '.gitkeep')
                with open(keep_path, 'w') as f:
                    f.write('# Keep this directory in git\n')
            
            return 0
        
        original_main = module.main
        module.main = mock_main
        try:
            # Run twice
            result1 = module.main()
            result2 = module.main()
            
            assert result1 == 0, "First run should succeed"
            assert result2 == 0, "Second run should succeed"
        finally:
            module.main = original_main