import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.setup_data_dirs import setup_directories

class TestSetupDataDirs:
    def test_setup_directories_creates_structure(self):
        """Verify that the function creates the expected directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the base directory to be inside our temp directory
            # We need to patch the resolve() or the path logic in setup_directories
            # Since setup_directories uses __file__, we can't easily mock it without 
            # moving the file. Instead, we will patch Path.mkdir to verify calls.
            
            # Create a fake file structure to test the logic
            # We will mock Path.mkdir to capture calls without actually creating files
            # and verify the paths passed to it.
            
            original_path = Path
            
            def mock_path(*args, **kwargs):
                if args and isinstance(args[0], str) and "setup_data_dirs.py" in args[0]:
                    # Return a mock path that points to our temp dir for the base
                    p = original_path(*args, **kwargs)
                    # We can't easily override __file__ inside the module execution context
                    # So we will test the logic by inspecting the source or by using a different approach.
                    # Let's just test that the function runs without error in a clean env.
                    return p
                return original_path(*args, **kwargs)

            # Simpler approach: Just run the function in a temp directory by changing cwd
            # and ensuring the relative structure is created relative to the script location.
            # Since the script is in code/code/, and we are running tests from code/tests/,
            # the relative path calculation is fixed.
            
            # To truly test, we rely on the fact that the script creates:
            # <project_root>/data/raw, etc.
            # We will create a temporary project root and verify.
            
            # Since we cannot easily change __file__, we will verify the logic by
            # checking that the directories exist after running in a controlled env.
            # However, for a unit test, we should mock the filesystem interactions.
            
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                with patch('pathlib.Path.exists', return_value=False):
                    # Mock Path to return a mock object that tracks calls
                    # This is tricky because setup_directories creates Path objects internally.
                    # We will instead verify the side effects by checking the actual file system
                    # in a temporary directory by moving the script there? No, too complex.
                    
                    # Let's just verify the function runs and returns the expected keys.
                    # We will patch the actual directory creation to not fail.
                    pass 
                    
            # Actual test: Run the function. If it doesn't crash, it likely worked
            # assuming the environment has write permissions to the project root.
            # Since we are in a test environment, we might not have permission to write to
            # the actual project root.
            
            # Better approach for this specific constraint:
            # We will verify the *logic* by checking the paths the function *would* create.
            # We can't easily do that without executing the function.
            # So we will execute it in a temp directory by temporarily moving the script?
            # No, that's too much.
            
            # Let's assume the project root is writable for the purpose of this test
            # or that the function is robust enough to handle existing dirs.
            # We will test that the returned dict has the correct keys.
            
            # Since we can't easily mock the __file__ based resolution in a unit test
            # without complex monkeypatching, we will rely on the integration test
            # or simply verify the keys returned.
            
            # To make this test pass in isolation, we will patch the base_dir resolution.
            # We can't do that easily. 
            
            # Let's try a different angle: The function returns a dict of paths.
            # We can verify the keys.
            
            # We will use a mock to simulate the path resolution.
            with patch('code.setup_data_dirs.Path') as MockPath:
                mock_base = MagicMock()
                mock_data_root = MagicMock()
                mock_raw = MagicMock()
                mock_processed = MagicMock()
                mock_splits = MagicMock()
                mock_results = MagicMock()
                
                # Chain the mocks
                MockPath.return_value = mock_base
                mock_base.__truediv__.return_value = mock_data_root # data_root = base / "data"
                
                # Setup the specific paths for data/raw, etc.
                mock_data_root.__truediv__.side_effect = lambda x: {
                    "raw": mock_raw,
                    "processed": mock_processed,
                    "splits": mock_splits
                }.get(x, MagicMock())
                
                # results is base / "results"
                mock_base.__truediv__.side_effect = lambda x: {
                    "data": mock_data_root,
                    "results": mock_results
                }.get(x, MagicMock())
                
                # Mock exists and mkdir
                mock_raw.exists.return_value = False
                mock_processed.exists.return_value = False
                mock_splits.exists.return_value = False
                mock_results.exists.return_value = False
                
                mock_raw.mkdir.return_value = None
                mock_processed.mkdir.return_value = None
                mock_splits.mkdir.return_value = None
                mock_results.mkdir.return_value = None

                result = setup_directories()
                
                assert "raw" in result
                assert "processed" in result
                assert "splits" in result
                assert "results" in result
                
                # Verify mkdir was called on each
                mock_raw.mkdir.assert_called_once()
                mock_processed.mkdir.assert_called_once()
                mock_splits.mkdir.assert_called_once()
                mock_results.mkdir.assert_called_once()

    def test_setup_directories_handles_existing_dirs(self):
        """Verify that existing directories are not recreated (exists returns True)."""
        with patch('code.setup_data_dirs.Path') as MockPath:
            mock_base = MagicMock()
            mock_data_root = MagicMock()
            mock_raw = MagicMock()
            mock_processed = MagicMock()
            mock_splits = MagicMock()
            mock_results = MagicMock()
            
            MockPath.return_value = mock_base
            mock_base.__truediv__.side_effect = lambda x: {
                "data": mock_data_root,
                "results": mock_results
            }.get(x, MagicMock())
            
            mock_data_root.__truediv__.side_effect = lambda x: {
                "raw": mock_raw,
                "processed": mock_processed,
                "splits": mock_splits
            }.get(x, MagicMock())
            
            # All exist
            mock_raw.exists.return_value = True
            mock_processed.exists.return_value = True
            mock_splits.exists.return_value = True
            mock_results.exists.return_value = True
            
            result = setup_directories()
            
            # mkdir should NOT be called if exists is True
            mock_raw.mkdir.assert_not_called()
            mock_processed.mkdir.assert_not_called()
            mock_splits.mkdir.assert_not_called()
            mock_results.mkdir.assert_not_called()