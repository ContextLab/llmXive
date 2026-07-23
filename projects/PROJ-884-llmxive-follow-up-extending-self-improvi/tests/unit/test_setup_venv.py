"""
Unit tests for the virtual environment setup script.

These tests verify that the setup_venv.py script logic handles
path validation and Python detection correctly without actually
creating a venv (to avoid side effects in the test runner).
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add code directory to path to import the module if needed, 
# though we are testing logic primarily via mocking.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_venv import find_python311, main

class TestFindPython311:
    def test_returns_none_when_no_python_found(self):
        """Test that find_python311 returns None if no suitable interpreter is found."""
        with patch("setup_venv.subprocess.run") as mock_run:
            # Mock all calls to fail or return wrong version
            mock_run.side_effect = FileNotFoundError("Command not found")
            
            result = find_python311()
            assert result is None

    def test_returns_path_when_python311_found(self):
        """Test that find_python311 returns the command when 3.11 is detected."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.11.2"
        
        with patch("setup_venv.subprocess.run", return_value=mock_result) as mock_run:
            # Ensure the first candidate succeeds
            result = find_python311()
            assert result == "python3.11"
            mock_run.assert_called_once()

class TestMainLogic:
    def test_exits_if_project_root_missing(self, capsys):
        """Test that main() exits gracefully if the project directory does not exist."""
        with patch("setup_venv.Path.exists", return_value=False):
            with patch("setup_venv.sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_with(1)
                captured = capsys.readouterr()
                assert "Project root not found" in captured.out

    def test_skips_if_venv_exists(self, capsys):
        """Test that main() skips creation if venv already exists."""
        project_root = Path("fake_project")
        venv_path = project_root / "venv"
        
        with patch("setup_venv.Path.exists", return_value=True):
            with patch("setup_venv.Path", return_value=MagicMock(exists=MagicMock(side_effect=lambda x: x == str(venv_path)))):
                # Mock Path constructor to return a mock object where exists() checks path
                # This is a bit tricky, simpler to mock the specific check
                pass

        # Simpler approach: patch the specific Path checks
        with patch("setup_venv.Path") as MockPath:
            mock_root = MagicMock()
            mock_root.exists.return_value = True
            mock_venv = MagicMock()
            mock_venv.exists.return_value = True
            
            MockPath.side_effect = lambda path: mock_root if "PROJ-884" in path else mock_venv
            
            with patch("setup_venv.sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_with(0)
                captured = capsys.readouterr()
                assert "already exists" in captured.out

    def test_creates_venv_successfully(self, tmp_path):
        """Test that main() attempts to create venv when it doesn't exist."""
        # We can't easily test the actual subprocess.run in a unit test without
        # mocking the filesystem effects, so we mock the subprocess and verify the call.
        
        project_root = tmp_path / "projects" / "PROJ-884-llmxive-follow-up-extending-self-improvi"
        project_root.mkdir(parents=True)
        venv_path = project_root / "venv"
        
        mock_python = "python3.11"
        mock_activate = venv_path / "bin" / "activate"
        
        with patch("setup_venv.find_python311", return_value=mock_python):
            with patch("setup_venv.Path.exists", return_value=True) as mock_exists:
                # Make exists return True for project_root, False for venv initially, True after
                def exists_side_effect():
                    # This is tricky to mock perfectly without complex state
                    # Instead, we mock the specific calls in the flow
                    return True
                
                # We will mock the specific Path checks inside main
                original_path = Path
                
                def mock_path_init(path_str):
                    p = original_path(path_str)
                    if "venv" in str(path_str):
                        # Simulate venv not existing initially
                        p.exists = lambda: False
                    return p
                
                # Actually, simpler: just mock the subprocess and verify the call
                with patch("setup_venv.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock() # Success
                    
                    # Mock the existence check for venv to return False
                    with patch.object(venv_path, 'exists', return_value=False):
                        with patch.object(project_root, 'exists', return_value=True):
                            # Mock the post-run check for activate script
                            with patch.object(mock_activate, 'exists', return_value=True):
                                with patch("setup_venv.sys.exit") as mock_exit:
                                    # We need to patch Path inside the module to return our mock paths
                                    # But since we are passing absolute paths in the test, 
                                    # we can just verify the subprocess call arguments.
                                    
                                    # Re-run main with the mocked environment
                                    # Note: main() uses hardcoded relative path "projects/..."
                                    # We need to patch the Path constructor in setup_venv module
                                    
                                    with patch("setup_venv.Path") as MockPath:
                                        mock_root_obj = MagicMock()
                                        mock_root_obj.exists.return_value = True
                                        
                                        mock_venv_obj = MagicMock()
                                        mock_venv_obj.exists.return_value = False # Initially missing
                                        
                                        mock_activate_obj = MagicMock()
                                        mock_activate_obj.exists.return_value = True # After creation
                                        
                                        def path_side_effect(path_str):
                                            if "PROJ-884" in path_str:
                                                return mock_root_obj
                                            elif "venv" in path_str:
                                                return mock_venv_obj
                                            return original_path(path_str)
                                        
                                        MockPath.side_effect = path_side_effect
                                        
                                        main()
                                        
                                        # Verify subprocess was called with venv creation
                                        mock_run.assert_called_once()
                                        args, kwargs = mock_run.call_args
                                        assert "venv" in str(args[0])
                                        
                                        # Verify sys.exit(0) was called for success
                                        mock_exit.assert_called_with(0)