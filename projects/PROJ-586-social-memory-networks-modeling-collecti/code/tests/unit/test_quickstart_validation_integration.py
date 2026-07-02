"""
Integration test for quickstart validation.

This test verifies that the validate_quickstart.py script:
1. Successfully parses quickstart.md
2. Executes all commands
3. Generates a valid report
4. Returns appropriate exit codes
"""

import pytest
import tempfile
from pathlib import Path
import subprocess
import sys
import json


class TestQuickstartValidationIntegration:
    def test_script_exists(self):
        """Verify the validation script exists."""
        script_path = Path(__file__).parent.parent.parent / "validate_quickstart.py"
        assert script_path.exists(), f"Script not found: {script_path}"
    
    def test_script_syntax_valid(self):
        """Verify the script has valid Python syntax."""
        script_path = Path(__file__).parent.parent.parent / "validate_quickstart.py"
        
        # Try to compile the script
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        try:
            compile(code, script_path.name, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in validate_quickstart.py: {e}")
    
    def test_extract_bash_commands(self):
        """Test the command extraction logic."""
        from validate_quickstart import extract_bash_commands
        
        markdown = """
        # Test
        
        ```bash
        echo "hello"
        python test.py
        ```
        
        ```bash
        ls -la
        ```
        """
        
        commands = extract_bash_commands(markdown)
        
        assert len(commands) == 3
        assert "echo \"hello\"" in commands
        assert "python test.py" in commands
        assert "ls -la" in commands
    
    def test_run_command_success(self):
        """Test running a simple successful command."""
        from validate_quickstart import run_command
        from pathlib import Path
        
        exit_code, stdout, stderr = run_command("echo 'test'", Path("."))
        
        assert exit_code == 0
        assert "test" in stdout
    
    def test_run_command_failure(self):
        """Test running a failing command."""
        from validate_quickstart import run_command
        from pathlib import Path
        
        exit_code, stdout, stderr = run_command("false", Path("."))
        
        assert exit_code == 1
    
    def test_full_validation_flow(self):
        """Test the complete validation flow with a mock quickstart.md."""
        from validate_quickstart import validate_quickstart
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a mock quickstart.md
            quickstart_content = """
            # Quickstart Test
            
            ```bash
            echo "Setup complete"
            ```
            
            ```bash
            echo "Running experiment"
            ```
            """
            
            (tmpdir / "quickstart.md").write_text(quickstart_content)
            
            # Run validation
            report = validate_quickstart(tmpdir)
            
            # Verify results
            assert report["success"] is True
            assert report["commands_tested"] == 2
            assert report["commands_passed"] == 2
            assert report["commands_failed"] == 0
            assert len(report["results"]) == 2
            assert all(r["success"] for r in report["results"])
    
    def test_missing_quickstart_file(self):
        """Test validation when quickstart.md is missing."""
        from validate_quickstart import validate_quickstart
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            report = validate_quickstart(tmpdir)
            
            assert report["success"] is False
            assert "not found" in report["error"]
            assert report["commands_tested"] == 0
    
    def test_no_commands_in_quickstart(self):
        """Test validation when quickstart.md has no commands."""
        from validate_quickstart import validate_quickstart
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create quickstart.md with no bash blocks
            quickstart_content = """
            # Quickstart
            
            This is just text with no commands.
            """
            
            (tmpdir / "quickstart.md").write_text(quickstart_content)
            
            report = validate_quickstart(tmpdir)
            
            assert report["success"] is False
            assert "No commands found" in report["error"]
            assert report["commands_tested"] == 0
    
    def test_failed_command_in_quickstart(self):
        """Test validation when a command fails."""
        from validate_quickstart import validate_quickstart
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            quickstart_content = """
            # Quickstart
            
            ```bash
            echo "success"
            ```
            
            ```bash
            false
            ```
            """
            
            (tmpdir / "quickstart.md").write_text(quickstart_content)
            
            report = validate_quickstart(tmpdir)
            
            assert report["success"] is False
            assert report["commands_tested"] == 2
            assert report["commands_passed"] == 1
            assert report["commands_failed"] == 1
    
    def test_report_generation(self):
        """Test that the report is generated correctly."""
        from validate_quickstart import validate_quickstart, save_report
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            quickstart_content = """
            ```bash
            echo "test"
            ```
            """
            
            (tmpdir / "quickstart.md").write_text(quickstart_content)
            
            report = validate_quickstart(tmpdir)
            
            # Save and reload
            report_path = tmpdir / "test_report.json"
            save_report(report, report_path)
            
            assert report_path.exists()
            
            with open(report_path, 'r') as f:
                loaded_report = json.load(f)
            
            assert loaded_report["commands_tested"] == 1
            assert loaded_report["success"] is True
            assert "timestamp" in loaded_report
            assert "quickstart_path" in loaded_report