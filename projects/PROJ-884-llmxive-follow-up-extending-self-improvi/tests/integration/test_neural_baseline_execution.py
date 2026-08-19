"""
Integration test for T030d: Neural Subset Baseline Execution.

Verifies that the neural baseline script runs end-to-end and produces
the expected output artifact.
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_config(temp_output_dir):
    """Create a minimal config for testing."""
    config_path = temp_output_dir / "config.yaml"
    config_content = """
    experiment_id: test_neural_baseline
    mode: neural_subset
    n_puzzles: 5
    population_size: 10
    generations: 5
    seed: 42
    device: cpu
    """
    config_path.write_text(config_content)
    return config_path

def test_neural_baseline_script_exists():
    """Verify the script file exists."""
    script_path = project_root / "code" / "run_neural_baseline.py"
    assert script_path.exists(), "run_neural_baseline.py must exist"

def test_neural_baseline_execution_produces_output(temp_output_dir, sample_config):
    """Test that running the neural baseline script produces the expected output."""
    output_file = temp_output_dir / "neural_baseline_results.json"

    # Run the script with a small subset
    cmd = [
        sys.executable,
        str(project_root / "code" / "run_neural_baseline.py"),
        "--n", "5",
        "--output", str(output_file),
        "--seed", "42"
    ]

    # Execute the script
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    # Check if execution was successful
    if result.returncode != 0:
        pytest.fail(f"Script execution failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

    # Verify output file exists
    assert output_file.exists(), f"Output file {output_file} was not created"

    # Verify output file is valid JSON
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output file is not valid JSON: {e}")

    # Verify required fields are present
    required_fields = [
        "experiment_id",
        "mode",
        "n_puzzles_processed",
        "successful_solutions",
        "failed_solutions",
        "success_rate",
        "total_time_seconds"
    ]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from output"

    # Verify mode is correct
    assert data["mode"] == "neural_subset", "Mode should be 'neural_subset'"

    # Verify puzzle count matches
    assert data["n_puzzles_processed"] == 5, "Should have processed 5 puzzles"

def test_neural_baseline_output_structure(temp_output_dir, sample_config):
    """Test that the output JSON has the correct structure."""
    output_file = temp_output_dir / "neural_baseline_results.json"

    # Run the script
    cmd = [
        sys.executable,
        str(project_root / "code" / "run_neural_baseline.py"),
        "--n", "3",
        "--output", str(output_file),
        "--seed", "42"
    ]

    subprocess.run(cmd, cwd=project_root, capture_output=True, timeout=300)

    # Load and validate structure
    with open(output_file, 'r') as f:
        data = json.load(f)

    # Check puzzle_details structure
    if "puzzle_details" in data and data["puzzle_details"]:
        detail = data["puzzle_details"][0]
        assert "puzzle_id" in detail, "puzzle_detail must have puzzle_id"
        assert "solved" in detail, "puzzle_detail must have solved"
        assert "time_seconds" in detail, "puzzle_detail must have time_seconds"
        assert "complexity_n" in detail, "puzzle_detail must have complexity_n"
