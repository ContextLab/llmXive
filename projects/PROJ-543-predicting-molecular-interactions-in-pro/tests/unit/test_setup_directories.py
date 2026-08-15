"""
Unit tests for T009: Directory structure setup.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the utils.io logging to avoid file writing during tests if needed,
# though standard logging is usually fine.
import sys
from unittest.mock import patch, MagicMock

# Add code to path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_directories import main

class TestSetupDirectories:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def setup_code_dir(self, temp_project_root):
        """Ensure the code/ directory exists so the script can find the root."""
        code_dir = temp_project_root / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        return code_dir

    def test_creates_directories(self, temp_project_root, setup_code_dir):
        """Verify that the script creates the required data directories."""
        # Change to the code directory to simulate execution
        original_cwd = os.getcwd()
        try:
            os.chdir(setup_code_dir)

            # Mock sys.exit to capture the return code
            exit_code = None
            def mock_exit(code):
                nonlocal exit_code
                exit_code = code

            with patch("sys.exit", side_effect=mock_exit):
                # We need to call main() directly, but it uses __file__
                # Since we are mocking the environment, we can run main()
                # However, main() relies on __file__ being code/setup_directories.py
                # To make this robust, we can temporarily patch the working directory
                # and ensure the script logic works relative to the temp root.

                # Actually, the script determines root as parent of __file__.
                # If we run this test from the temp_project_root/code directory,
                # and the script is copied there or we mock __file__, it works.
                # Simpler approach: Just verify the logic by checking the paths
                # constructed in a controlled way, or run the script if we copy it.

                # Let's run the script by executing it as a module or script file.
                # Since we can't easily copy the file in a fixture without complexity,
                # let's test the logic directly by importing the function and
                # patching the path resolution.

                # Re-implementing the logic test:
                data_root = temp_project_root / "data"
                dirs_to_check = [
                    data_root / "raw",
                    data_root / "processed",
                    data_root / "results"
                ]

                # Execute main
                # We need to ensure the script sees the temp root as the parent of code/
                # The script uses Path(__file__).resolve().parent (code/) -> parent (root)
                # So if we put the script in temp_project_root/code, it works.
                pass

            # Let's just run the script by creating a temporary script file
            script_content = (code_path / "setup_directories.py").read_text()
            temp_script = setup_code_dir / "setup_directories.py"
            temp_script.write_text(script_content)

            # Now run the script logic by importing it fresh or executing
            # Since we modified sys.path, we can import if we are in the right dir
            # But __file__ will point to the temp script.
            # Let's just execute the code block manually to test the side effects.

            # Clean up any existing data dir first
            if data_root.exists():
                shutil.rmtree(data_root)

            # Run main
            result = main()

            assert result == 0, "main() should return 0 on success"

            for d in dirs_to_check:
                assert d.exists(), f"Directory {d} should exist after running main()"
                assert d.is_dir(), f"{d} should be a directory"

        finally:
            os.chdir(original_cwd)

    def test_directories_already_exist(self, temp_project_root, setup_code_dir):
        """Verify the script handles existing directories gracefully."""
        data_root = temp_project_root / "data"
        data_root.mkdir(parents=True)
        (data_root / "raw").mkdir()
        (data_root / "processed").mkdir()
        (data_root / "results").mkdir()

        script_content = (code_path / "setup_directories.py").read_text()
        temp_script = setup_code_dir / "setup_directories.py"
        temp_script.write_text(script_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(setup_code_dir)
            result = main()
            assert result == 0
        finally:
            os.chdir(original_cwd)