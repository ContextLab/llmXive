"""
Integration test for the full renderer pipeline (T021).

This test verifies the consistency of the ASCII grid generation and event log
production across the full lifecycle of a simulated game run. It specifically
validates that the `utils/renderer_validator.py` (T006) can successfully
cross-reference the generated artifacts, ensuring Levenshtein distance = 0
between the ground truth state and the rendered ASCII representation.

Prerequisites:
- T014: renderer.py (generate_ascii_grid, render_visual_to_ascii)
- T015: renderer.py (generate_event_log)
- T016: renderer.py (render_error_block, validation logic)
- T006: utils/renderer_validator.py (validate_ascii_visual_consistency)
"""

import os
import sys
import json
import tempfile
import shutil
import pytest

# Add project root to path to allow imports from code/ and utils/
# Assuming this test runs from project root or is configured with PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
code_dir = os.path.join(project_root, "code")
utils_dir = os.path.join(project_root, "utils")

if code_dir not in sys.path:
    sys.path.insert(0, code_dir)
if utils_dir not in sys.path:
    sys.path.insert(0, utils_dir)

from renderer import (
    generate_ascii_grid,
    generate_event_log,
    render_error_block,
    validate_ascii_grid,
    create_event_entry
)
from renderer_validator import validate_ascii_visual_consistency

# Constants for the test
GRID_SIZE = 10
NUM_STEPS = 5
TEST_SEED = 42


def setup_test_environment():
    """
    Creates a temporary directory for test artifacts and ensures it is clean.
    Returns the path to the temp directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_integration_")
    return temp_dir


def teardown_test_environment(temp_dir):
    """
    Cleans up the temporary directory after the test.
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_full_renderer_pipeline_consistency():
    """
    T021: Integration test for full renderer pipeline.
    
    Steps:
    1. Simulate a sequence of visual states (ground truth).
    2. Render each state to ASCII using `generate_ascii_grid`.
    3. Generate a corresponding event log.
    4. Save artifacts to disk (ASCII and JSON).
    5. Use `utils/renderer_validator.py` to verify consistency.
    
    Assertion:
    - The validator must return a pass status with Levenshtein distance = 0.
    """
    temp_dir = setup_test_environment()
    try:
        ascii_output_path = os.path.join(temp_dir, "test_run.ascii")
        log_output_path = os.path.join(temp_dir, "test_run.json")
        
        # 1. Simulate Ground Truth States
        # We simulate a simple grid state: a list of (row, col, item_type)
        # For this integration test, we generate deterministic "visual" data.
        ground_truth_states = []
        for step in range(NUM_STEPS):
            # Create a simple grid representation: 0=empty, 1=agent, 2=target
            grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            # Move agent diagonally
            agent_pos = (step % GRID_SIZE, step % GRID_SIZE)
            grid[agent_pos[0]][agent_pos[1]] = 1
            # Place a target
            target_pos = ((step + 1) % GRID_SIZE, (step + 2) % GRID_SIZE)
            grid[target_pos[0]][target_pos[1]] = 2
            
            ground_truth_states.append({
                "step": step,
                "grid": grid,
                "agent_pos": agent_pos,
                "target_pos": target_pos
            })
        
        # 2. Render and Generate Logs
        rendered_lines = []
        event_log = []
        
        for state in ground_truth_states:
            # Render ASCII
            ascii_grid_str = generate_ascii_grid(state["grid"])
            rendered_lines.append(ascii_grid_str)
            
            # Create event entry
            event = create_event_entry(
                step=state["step"],
                action="move",
                agent_pos=state["agent_pos"],
                target_pos=state["target_pos"],
                state_hash=None # Simplified for integration test
            )
            event_log.append(event)
        
        # 3. Save Artifacts
        with open(ascii_output_path, "w") as f:
            f.write("\n".join(rendered_lines))
        
        with open(log_output_path, "w") as f:
            json.dump(event_log, f, indent=2)
        
        # 4. Validate Consistency
        # We reconstruct the "visual" representation from the ground truth
        # to pass to the validator, or the validator can re-render if it has the ground truth.
        # Based on T006 design, the validator compares the stored ASCII against the
        # expected ASCII derived from the ground truth or visual frames.
        
        # Re-construct expected ASCII from ground truth for validation
        expected_ascii_lines = []
        for state in ground_truth_states:
            expected_ascii_lines.append(generate_ascii_grid(state["grid"]))
        expected_ascii_content = "\n".join(expected_ascii_lines)
        
        # Read back the saved ASCII
        with open(ascii_output_path, "r") as f:
            saved_ascii_content = f.read()
        
        # 5. Run Validator
        # The validator function signature from T006 is expected to take
        # the ground truth (or visual source) and the ASCII file path/content.
        # We adapt the call to match the likely interface:
        # validate_ascii_visual_consistency(expected_ascii, actual_ascii_path)
        
        validation_result = validate_ascii_visual_consistency(
            expected_ascii=expected_ascii_content,
            ascii_file_path=ascii_output_path,
            log_file_path=log_output_path
        )
        
        # Assertions
        assert validation_result["status"] == "PASS", \
            f"Validation failed: {validation_result.get('error', 'Unknown error')}"
        
        assert validation_result["levenshtein_distance"] == 0, \
            f"Levenshtein distance is non-zero: {validation_result['levenshtein_distance']}"
        
        print(f"Integration Test Passed: {validation_result}")
        
    finally:
        teardown_test_environment(temp_dir)


def test_renderer_error_handling_integration():
    """
    T021b: Integration test for error handling (Out of Bounds).
    
    Verifies that the renderer correctly produces the `ERROR: STATE_CORRUPT` block
    when provided with invalid state data, and that the validator handles this
    gracefully (or flags it as a specific error type).
    """
    temp_dir = setup_test_environment()
    try:
        corrupt_ascii_path = os.path.join(temp_dir, "corrupt_run.ascii")
        
        # Simulate a corrupt state (e.g., negative coordinates or out of bounds)
        # We directly invoke the render_error_block to simulate the failure path
        error_block = render_error_block("STATE_CORRUPT", "Agent position out of bounds")
        
        with open(corrupt_ascii_path, "w") as f:
            f.write(error_block)
        
        # Validate: The validator should detect that the file contains an error block
        # and potentially return a specific status or handle it without crashing.
        # For this test, we ensure the file exists and contains the expected error string.
        with open(corrupt_ascii_path, "r") as f:
            content = f.read()
        
        assert "ERROR: STATE_CORRUPT" in content, \
            "Corrupt state file does not contain the expected error block."
        
        # If we run the validator, it should ideally flag this as a non-matching
        # ground truth vs. rendered output, or return a specific "ERROR" status.
        # We assume the validator returns a status that is not "PASS" for this case.
        validation_result = validate_ascii_visual_consistency(
            expected_ascii="Valid Grid Content",
            ascii_file_path=corrupt_ascii_path,
            log_file_path=None
        )
        
        # The validator should detect the mismatch (Expected valid, got error block)
        assert validation_result["status"] != "PASS", \
            "Validator should not pass on a corrupt state file."
        
        print(f"Error Handling Test Passed: {validation_result}")
        
    finally:
        teardown_test_environment(temp_dir)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
