"""
Contract test for T047: Degenerate Dataset Handling.

This test verifies that `preprocess.py` correctly handles a dataset with
zero porosity variance (degenerate dataset).

Expected Behavior:
1. `preprocess.py` detects zero variance in the target column ('porosity').
2. It writes a status file `data/processed/degenerate_flag.json` with specific content.
3. It updates `state.yaml` to mark the dataset as degenerate.
4. It exits with code 0 (graceful failure) rather than crashing with an exception.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path

# Add the project root to the path to allow imports if running directly
# Note: In the actual pipeline, the script is run as a subprocess.
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "state.yaml"

# Ensure the paths match the project structure defined in tasks.md
assert CODE_DIR.exists(), f"Code directory not found at {CODE_DIR}"
assert DATA_DIR.exists(), f"Data directory not found at {DATA_DIR}"

def setup_degenerate_environment():
    """
    Creates a temporary CSV file with zero porosity variance and ensures
    necessary directories exist for the test.
    """
    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary CSV with zero porosity variance
    # We use a fixed set of parameters but constant porosity
    degenerate_csv_content = """laser_power,scan_speed,hatch_spacing,layer_thickness,porosity
    200.0,500.0,0.1,0.03,0.05
    250.0,600.0,0.12,0.03,0.05
    300.0,700.0,0.11,0.03,0.05
    220.0,550.0,0.1,0.03,0.05
    """
    
    temp_input_path = PROCESSED_DIR / "degenerate_input.csv"
    with open(temp_input_path, "w") as f:
        f.write(degenerate_csv_content)
    
    return temp_input_path

def cleanup_test_artifacts():
    """Removes test-specific artifacts to ensure a clean state for other tests."""
    flag_file = PROCESSED_DIR / "degenerate_flag.json"
    if flag_file.exists():
        flag_file.unlink()
    
    # We do not delete state.yaml as it is a critical project file,
    # but we might need to restore it if the test modifies it.
    # For this test, we will verify the update by reading the file.
    
def test_degenerate_dataset_handling():
    """
    Test that preprocess.py handles a degenerate dataset correctly.
    """
    # 1. Setup
    input_file = setup_degenerate_environment()
    cleanup_test_artifacts() # Ensure clean state before run
    
    flag_file = PROCESSED_DIR / "degenerate_flag.json"
    assert not flag_file.exists(), "Degenerate flag file should not exist before test run."

    # 2. Execute preprocess.py with the degenerate input
    # We construct the command to run the specific script with arguments if needed,
    # or rely on the script's default behavior if it expects a specific input location.
    # Based on T014/T015 description, the script likely takes input/output paths or
    # uses defaults. We will assume it can be invoked with an input argument or
    # we modify the input path in a config.
    # However, to strictly follow the "inject a CSV" requirement, we will pass it as an argument
    # if the script supports it, or rename the file to the expected input.
    # Looking at T014, it loads raw data. Let's assume the script expects `data/raw/input.csv`
    # or accepts `--input`. Since we don't have the exact CLI signature of the current
    # `preprocess.py` implementation in the prompt, we will assume a standard pattern:
    # python code/preprocess.py --input <path> --output <path>
    
    # To be safe and robust, we will create a symlink or copy the file to the expected
    # raw location if the script looks there, OR we pass it as an argument.
    # Given the task description "inject a CSV", passing it as an argument is the cleanest.
    # If the script doesn't support args, we might need to mock the input path.
    # Let's assume the script has a standard CLI: `python code/preprocess.py --input <file>`
    
    cmd = [
        sys.executable,
        str(CODE_DIR / "preprocess.py"),
        "--input", str(input_file),
        "--output", str(PROCESSED_DIR / "cleaned_316L.csv")
    ]
    
    # Run the script
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    
    # 3. Verify Exit Code
    # T015 says: "exit with code 0 (graceful failure)"
    assert result.returncode == 0, (
        f"preprocess.py should exit with code 0 for degenerate dataset. "
        f"Got {result.returncode}. Stderr: {result.stderr}, Stdout: {result.stdout}"
    )

    # 4. Verify Flag File Content
    assert flag_file.exists(), "degenerate_flag.json was not created."
    
    with open(flag_file, "r") as f:
        flag_data = json.load(f)
    
    assert flag_data.get("reason") == "Zero porosity variance", (
        f"Expected reason 'Zero porosity variance', got {flag_data.get('reason')}"
    )
    assert flag_data.get("status") == "degenerate", (
        f"Expected status 'degenerate', got {flag_data.get('status')}"
    )

    # 5. Verify State Update
    # The script should update state.yaml with degenerate: true
    assert STATE_FILE.exists(), "state.yaml was not found."
    
    # Read and parse state.yaml (simple parsing for this test)
    with open(STATE_FILE, "r") as f:
        state_content = f.read()
    
    assert "degenerate: true" in state_content, (
        f"state.yaml should contain 'degenerate: true'. Content: {state_content}"
    )

    # 6. Cleanup
    if input_file.exists():
        input_file.unlink()
    # Note: We leave the flag file and state update as evidence of the test run,
    # but in a real CI pipeline, we would reset state.yaml.
    
if __name__ == "__main__":
    pytest.main([__file__, "-v"])