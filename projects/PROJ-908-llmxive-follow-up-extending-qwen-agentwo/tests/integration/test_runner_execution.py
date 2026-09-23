"""
Integration test for the inference runner execution.

This test verifies that the runner.py script can be executed and produces
the expected output file with valid CoT traces.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

# Ensure the code directory is in the path
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

@pytest.fixture
def output_file():
    """Fixture to provide the output file path."""
    return Path("data/raw/cot_traces.json")

@pytest.fixture
def representative_tasks_file():
    """Fixture to create a representative tasks file if it doesn't exist."""
    tasks_file = Path("data/raw/representative_tasks.json")
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not tasks_file.exists():
        # Create a minimal representative task set
        tasks = [
            {
                "id": "task_001",
                "input": {
                    "description": "Navigate from point A to point B",
                    "start": {"x": 0, "y": 0},
                    "goal": {"x": 10, "y": 10}
                }
            },
            {
                "id": "task_002",
                "input": {
                    "description": "Collect all items in the room",
                    "items": [{"id": "item1", "location": {"x": 2, "y": 2}}]
                }
            },
            {
                "id": "task_003",
                "input": {
                    "description": "Solve a simple puzzle",
                    "puzzle": {"type": "sliding", "size": 3}
                }
            }
        ]
        with open(tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    return tasks_file

def test_runner_execution(output_file, representative_tasks_file):
    """
    Test that the runner.py script executes successfully and produces valid output.
    
    This test:
    1. Runs the runner.py script with the representative set
    2. Verifies the output file is created
    3. Validates the structure of the generated traces
    """
    # Clean up any existing output
    if output_file.exists():
        output_file.unlink()
    
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/inference/runner.py", "--tasks=representative_set", "--output=data/raw/cot_traces.json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    # Check if the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Verify the output file exists
    assert output_file.exists(), f"Output file {output_file} was not created"
    
    # Load and validate the output
    with open(output_file, 'r') as f:
        traces = json.load(f)
    
    # Verify we have traces
    assert len(traces) > 0, "No traces were generated"
    
    # Validate the structure of each trace
    for trace in traces:
        assert "task_id" in trace, "Missing 'task_id' in trace"
        assert "input" in trace, "Missing 'input' in trace"
        assert "trace" in trace, "Missing 'trace' in trace"
        assert isinstance(trace["trace"], list), "'trace' should be a list"
        
        # Validate trace steps
        for step in trace["trace"]:
            assert "step" in step, "Missing 'step' in trace step"
            assert "thought" in step, "Missing 'thought' in trace step"
            assert "action" in step, "Missing 'action' in trace step"
            assert "state" in step, "Missing 'state' in trace step"

def test_runner_with_custom_output_path(output_file):
    """
    Test that the runner can write to a custom output path.
    """
    custom_output = Path("data/raw/custom_traces.json")
    
    # Clean up
    if custom_output.exists():
        custom_output.unlink()
    
    # Run with custom output
    result = subprocess.run(
        [sys.executable, "code/inference/runner.py", "--tasks=representative_set", f"--output={custom_output}"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert custom_output.exists(), f"Custom output file {custom_output} was not created"
    
    # Clean up
    custom_output.unlink()

def test_runner_fails_with_missing_tasks():
    """
    Test that the runner fails loudly when tasks are missing.
    """
    # Try to run with a non-existent tasks source
    result = subprocess.run(
        [sys.executable, "code/inference/runner.py", "--tasks=non_existent_tasks.json", "--output=data/raw/test_traces.json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    # The script should fail
    assert result.returncode != 0, "Script should fail when tasks are missing"
    assert "not found" in result.stderr.lower() or "no tasks loaded" in result.stderr.lower(), \
        f"Expected 'not found' or 'no tasks loaded' error, got: {result.stderr}"
