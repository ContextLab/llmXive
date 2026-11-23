"""
Tests for the environment setup and validation module.
"""
import sys
import importlib
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

def test_check_python_version_valid():
    """Test that valid Python versions pass the check."""
    from setup_environment import check_python_version

    # This should not raise an exception for the current running version
    # We can't easily mock sys.version_info in a way that breaks the check
    # without affecting the rest of the test, so we just ensure it doesn't crash
    # for the actual running version.
    try:
        check_python_version()
    except SystemExit:
        pytest.fail("check_python_version exited unexpectedly for valid version")

def test_check_python_version_invalid():
    """Test that invalid Python versions raise an error."""
    from setup_environment import check_python_version

    # Mock sys.version_info to simulate an invalid version
    with patch('setup_environment.sys.version_info', (3, 9, 0)):
        with patch('setup_environment.sys.exit') as mock_exit:
            with patch('setup_environment.print'):
                check_python_version()
                mock_exit.assert_called_once_with(1)

def test_check_dependencies_all_present(tmp_path):
    """Test dependency check when all packages are present."""
    # Create a fake requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("numpy>=1.26.0\npytest>=7.4.0\n")

    with patch('setup_environment.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        # Mock the open function to return our temp file content
        import builtins
        original_open = builtins.open
        def mock_open(*args, **kwargs):
            if args[0] == req_file:
                return original_open(req_file, *args[1:], **kwargs)
            return original_open(*args, **kwargs)

        with patch('builtins.open', mock_open):
            with patch('importlib.import_module') as mock_import:
                mock_import.return_value = MagicMock()
                from setup_environment import check_dependencies
                # Should not raise
                check_dependencies()

def test_check_dependencies_missing(tmp_path):
    """Test dependency check when some packages are missing."""
    # Create a fake requirements.txt with a missing package
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("numpy>=1.26.0\nnonexistent_package_xyz>=1.0.0\n")

    with patch('setup_environment.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        import builtins
        original_open = builtins.open
        def mock_open(*args, **kwargs):
            if args[0] == req_file:
                return original_open(req_file, *args[1:], **kwargs)
            return original_open(*args, **kwargs)

        with patch('builtins.open', mock_open):
            with patch('importlib.import_module') as mock_import:
                # numpy imports successfully, but nonexistent_package_xyz fails
                def import_side_effect(name):
                    if name == "nonexistent_package_xyz":
                        raise ImportError(f"No module named '{name}'")
                    return MagicMock()

                mock_import.side_effect = import_side_effect

                with patch('setup_environment.sys.exit') as mock_exit:
                    with patch('setup_environment.print'):
                        from setup_environment import check_dependencies
                        check_dependencies()
                        mock_exit.assert_called_once_with(1)