"""
Integration tests for linting CLI functionality.

These tests verify that the linting configuration
can be used in a command-line context.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.linting import main as linting_main


class TestLintingCLI:
    """Test cases for linting CLI functionality."""

    def test_main_executes_without_error(self):
        """Test that main() executes without raising exceptions."""
        # Capture stdout to prevent cluttering test output
        with patch("sys.stdout", new=io.StringIO()):
            # This should not raise any exceptions
            try:
                linting_main()
            except SystemExit:
                # SystemExit is expected if validation fails or succeeds with exit
                pass
            except Exception as e:
                # Any other exception is a failure
                pytest.fail(f"main() raised an unexpected exception: {e}")

    @patch("config.linting.validate_linting_setup")
    def test_main_with_valid_config(self, mock_validate):
        """Test main() when validation passes."""
        mock_validate.return_value = (True, "All good")
        
        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            try:
                linting_main()
            except SystemExit:
                pass
            
            output = mock_stdout.getvalue()
            assert "Validating linting and formatting setup" in output
            assert "All good" in output

    @patch("config.linting.validate_linting_setup")
    def test_main_with_invalid_config(self, mock_validate):
        """Test main() when validation fails."""
        mock_validate.return_value = (False, "Missing ruff")
        
        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                try:
                    linting_main()
                except SystemExit:
                    pass
                
                output = mock_stdout.getvalue()
                assert "Validating linting and formatting setup" in output
                assert "Missing ruff" in output
                mock_exit.assert_called_once_with(1)
