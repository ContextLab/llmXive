"""
Integration test for the quickstart validation script.

This test verifies that the quickstart validation script can be executed
and produces the expected output structure.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.integration
def test_quickstart_script_syntax():
    """Test that the quickstart script has valid Python syntax."""
    script_path = Path("code/quickstart_validator.py")
    assert script_path.exists(), "quickstart_validator.py must exist"
    
    # Try compiling the script
    try:
        with open(script_path, 'r') as f:
            compile(f.read(), script_path, 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in quickstart_validator.py: {e}")

@pytest.mark.integration
def test_quickstart_script_imports():
    """Test that all required imports in quickstart script are available."""
    try:
        from quickstart_validator import (
            check_dependencies,
            run_download,
            run_preprocessing,
            run_metrics,
            run_analysis,
            run_report_generation,
            verify_outputs,
            main
        )
    except ImportError as e:
        pytest.fail(f"Failed to import from quickstart_validator: {e}")

@pytest.mark.integration
def test_quickstart_main_function_exists():
    """Test that the main function exists and is callable."""
    from quickstart_validator import main
    assert callable(main), "main function must be callable"

@pytest.mark.integration
def test_quickstart_logging_setup():
    """Test that logging is properly configured."""
    from quickstart_validator import logger
    assert logger is not None, "Logger must be configured"
    assert logger.name == "quickstart_validator", "Logger name must be correct"

@pytest.mark.integration
def test_quickstart_expected_files_list():
    """Test that the expected files list contains the required outputs."""
    from quickstart_validator import verify_outputs
    
    # We can't easily call verify_outputs without running the full pipeline,
    # but we can check that the function exists and has the right signature
    import inspect
    sig = inspect.signature(verify_outputs)
    assert len(sig.parameters) == 0, "verify_outputs should take no arguments"
    
    # Check return type annotation
    assert sig.return_annotation == tuple, "verify_outputs should return a tuple"

@pytest.mark.integration
def test_quickstart_script_executable():
    """Test that the script can be executed as a module."""
    # This is a lightweight test that doesn't run the full pipeline
    # We just verify the script can be imported and run without immediate errors
    result = subprocess.run(
        [sys.executable, "-c", "from quickstart_validator import main; print('Import successful')"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Script import failed: {result.stderr}"
    assert "Import successful" in result.stdout

@pytest.mark.integration
def test_quickstart_dependency_check_function():
    """Test that check_dependencies function exists and returns boolean."""
    from quickstart_validator import check_dependencies
    
    result = check_dependencies()
    assert isinstance(result, bool), "check_dependencies should return a boolean"

@pytest.mark.integration
def test_quickstart_verify_outputs_function():
    """Test that verify_outputs function exists and returns tuple."""
    from quickstart_validator import verify_outputs
    
    success, missing = verify_outputs()
    assert isinstance(success, bool), "First return value should be boolean"
    assert isinstance(missing, list), "Second return value should be a list"
    assert all(isinstance(f, str) for f in missing), "All items in missing list should be strings"
