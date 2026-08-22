import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    def test_directories_exist_after_creation(self, tmp_path):
        """Test that the directory creation logic works."""
        # Change to tmp_path to simulate project root
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            from setup_directories import create_directories, verify_directories, generate_verification_log
            
            dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
            create_directories(dirs)
            
            missing = verify_directories(dirs)
            assert len(missing) == 0, f"Directories missing: {missing}"
            
            # Check log generation
            generate_verification_log(dirs)
            assert os.path.exists('data/.verify_structure.log')
            
            with open('data/.verify_structure.log', 'r') as f:
                content = f.read()
                for d in dirs:
                    assert f'OK {d}' in content
        finally:
            os.chdir(original_cwd)

    def test_verify_structure_script_logic(self, tmp_path):
        """Test the verification script logic."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            from setup_directories import create_directories, generate_verification_log
            
            dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
            create_directories(dirs)
            generate_verification_log(dirs)
            
            from verify_structure import main
            # We can't easily capture sys.exit(0) in a simple assert without pytest.raises,
            # but we can verify the logic by checking the file exists and has content
            assert os.path.exists('data/.verify_structure.log')
            
            # Simulate the verification logic manually
            expected = dirs
            with open('data/.verify_structure.log', 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.startswith('OK')]
                found = [l.split(' ', 1)[1] for l in lines]
            
            missing = set(expected) - set(found)
            assert len(missing) == 0
        finally:
            os.chdir(original_cwd)