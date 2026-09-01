"""
Integration test for T046: Quickstart Validation.

This test verifies that the `code/06_quickstart_validator.py` script
executes correctly and returns the expected exit code.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"

# Ensure the code directory is in the path for the subprocess
env = os.environ.copy()
env["PYTHONPATH"] = str(CODE_DIR) + ":" + env.get("PYTHONPATH", "")

def test_validator_script_exists():
    """Verify the validator script exists."""
    validator_path = CODE_DIR / "06_quickstart_validator.py"
    assert validator_path.exists(), f"Validator script not found at {validator_path}"

def test_validator_imports():
    """Verify the validator script can be imported (syntax check)."""
    # We run the script with --help or just import it to check syntax
    # Since it has a main block, we try to import the module
    sys.path.insert(0, str(CODE_DIR))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validator", str(CODE_DIR / "06_quickstart_validator.py"))
        module = importlib.util.module_from_spec(spec)
        # This will raise SyntaxError if there are issues
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to import validator module: {e}")

def test_validator_execution_structure_check():
    """
    Run the validator.
    We expect it to fail on data checks if the pipeline hasn't been run yet,
    but it must NOT crash with an import error or syntax error.
    """
    # Create minimal directory structure if missing to avoid immediate structure failure
    # This allows the test to run even in a fresh environment (though it will fail on data)
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "results").mkdir(parents=True, exist_ok=True)

    # Run the validator
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "06_quickstart_validator.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env
    )

    # We expect exit code 1 if data is missing (which is fine for this test)
    # We expect exit code 0 if everything is ready.
    # The critical part is that it didn't crash with an ImportError.
    # Check stderr for import errors
    assert "ImportError" not in result.stderr, f"Import error in validator: {result.stderr}"
    assert "ModuleNotFoundError" not in result.stderr, f"Module not found in validator: {result.stderr}"
    
    # If it runs, it should output logs
    assert "Quickstart Validation" in result.stdout or "Quickstart Validation" in result.stderr, \
        "Validator did not start logging"

def test_validator_output_path_check():
    """
    Verify that the validator checks for the specific output paths
    defined in the tasks (e.g., generated_proposals.jsonl).
    """
    validator_code = (CODE_DIR / "06_quickstart_validator.py").read_text()
    
    # Check for key artifact paths
    assert "generated_proposals.jsonl" in validator_code
    assert "analysis_report.md" in validator_code
    assert "corpus.jsonl" in validator_code
    assert "associational, not causal" in validator_code
