import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
from scripts.setup_data_dirs import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project root."""
    # Create the expected path hierarchy
    code_data = tmp_path / "code" / "data"
    code_data.mkdir(parents=True)
    return tmp_path

def test_directories_created(temp_project_root):
    """Test that the setup_data_dirs script creates the required directories."""
    # Mock the Path resolution to point to our temp directory
    with patch('scripts.setup_data_dirs.Path') as mock_path:
        # Configure the mock to behave like the real Path but use our temp dir
        mock_instance = MagicMock()
        # The script does: script_dir = Path(__file__).resolve().parent
        # Then: project_root = script_dir.parent.parent
        # Then: data_base = project_root / "code" / "data"
        
        # We need to simulate the chain of parent calls returning our temp structure
        # The mock_path will be called with the script file path
        # We need to ensure that when the script constructs the paths, they land in temp_project_root
        
        # Simpler approach: patch the specific Path calls or just run the logic against the temp dir
        # Since the script uses relative paths from __file__, we can't easily mock the whole flow
        # without complex side_effect configuration.
        
        # Alternative: Patch the `mkdir` method to capture calls, or just verify existence after running
        # But we can't run it against the real FS easily in a unit test without side effects.
        
        # Let's use a different approach: Patch `Path.mkdir` to record calls, and patch `Path.__truediv__`
        # to return paths relative to temp_project_root.
        
        original_path = Path
        
        def mock_path_constructor(path_str=None, *args, **kwargs):
            if path_str is None:
                # This happens in Path(__file__) calls if mocked incorrectly, avoid
                return original_path(path_str, *args, **kwargs)
            
            # If it's the script file path, we need to simulate the hierarchy
            if isinstance(path_str, str) and "setup_data_dirs.py" in path_str:
                # Return a mock that has parent.parent pointing to temp_project_root
                mock_p = MagicMock()
                mock_p.parent.parent = temp_project_root
                return mock_p
            
            return original_path(path_str, *args, **kwargs)

        # Actually, the cleanest way for this specific script is to just verify the logic
        # by mocking the `Path` class to return our temp directory when the script builds the path.
        
        # Let's re-implement the test to be more direct about the script's logic
        # We will mock the `Path` class in the `setup_data_dirs` module
        
        with patch('scripts.setup_data_dirs.Path') as MockPath:
            # Mock the instance returned by Path(__file__)
            mock_file_path = MagicMock()
            mock_file_path.resolve.return_value.parent.parent = temp_project_root
            MockPath.return_value = mock_file_path
            
            # Mock the __truediv__ to return paths within temp_project_root
            # We need to ensure that `temp_project_root / "code" / "data" / ...` works
            # Since `temp_project_root` is a real Path, we can just let the real Path logic handle the concatenation
            # but we need to make sure `MockPath` doesn't interfere with the real Path operations on `temp_project_root`
            
            # Actually, the script does:
            # script_dir = Path(__file__).resolve().parent
            # project_root = script_dir.parent.parent
            # data_base = project_root / "code" / "data"
            
            # If we mock Path(__file__) to return a mock that has .parent.parent = temp_project_root,
            # then project_root is temp_project_root (a real Path).
            # Then data_base = temp_project_root / "code" / "data" -> real Path.
            # Then directories = [data_base / "raw", ...] -> real Paths.
            # Then directory.mkdir() is called on real Paths.
            
            # So we just need to ensure MockPath(__file__) returns our mock_file_path.
            # And we need to ensure that when Path is called with other strings (like "code"), it returns a real Path?
            # No, the script only calls Path(__file__).
            
            MockPath.side_effect = lambda x=None: mock_file_path if x is not None else mock_file_path
            
            # Run the main function
            main()
            
            # Verify that mkdir was called on the correct directories
            # We can't easily check the real FS if we mocked everything, but we can check the mock calls
            # However, since we used a real temp_project_root for the parent, the mkdir calls happen on real directories.
            
            # Let's verify the directories exist in the temp folder
            expected_dirs = [
                temp_project_root / "code" / "data" / "raw",
                temp_project_root / "code" / "data" / "interim",
                temp_project_root / "code" / "data" / "processed",
                temp_project_root / "code" / "data" / "final"
            ]
            
            for d in expected_dirs:
                assert d.exists(), f"Directory {d} was not created"
                assert d.is_dir(), f"{d} is not a directory"

def test_directories_are_empty_or_non_existent_before_run(temp_project_root):
    """Verify that the directories do not exist before the script runs."""
    expected_dirs = [
        temp_project_root / "code" / "data" / "raw",
        temp_project_root / "code" / "data" / "interim",
        temp_project_root / "code" / "data" / "processed",
        temp_project_root / "code" / "data" / "final"
    ]
    
    for d in expected_dirs:
        assert not d.exists(), f"Directory {d} should not exist before running the script"