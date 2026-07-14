import os
import pytest
import shutil
import tempfile
import sys

# Add parent directory to path to import setup_directories
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.setup_directories import main

class TestSetupDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Create a temporary directory and change to it
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        yield
        # Restore original directory and clean up temp
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_main_creates_directories(self):
        """Test that main() creates the required directories."""
        expected_dirs = [
            "code",
            "artifacts",
            "tests",
            "artifacts/logs",
            "artifacts/metrics",
            "artifacts/figures",
            "tests/unit",
            "tests/integration",
            "tests/contract",
        ]

        # Verify directories do not exist before
        for d in expected_dirs:
            assert not os.path.exists(d), f"Directory {d} should not exist before test"

        # Run the main function
        result = main()

        # Verify return code is 0
        assert result == 0, "main() should return 0 on success"

        # Verify directories exist after
        for d in expected_dirs:
            assert os.path.exists(d), f"Directory {d} should exist after main() execution"
            assert os.path.isdir(d), f"{d} should be a directory"

    def test_main_idempotent(self):
        """Test that running main() twice does not fail."""
        # Run once
        main()
        # Run again
        result = main()
        assert result == 0, "main() should be idempotent and return 0 on second run"