import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generator import main, FailureType, verify_pairing

def test_golden_subset_generation():
    """Test that generator creates the expected JSON file with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "golden_subset.json")
        seed = 42
        num_tasks = 5

        # Run the generator
        sys.argv = ["generator.py", "--seed", str(seed), "--num-tasks", str(num_tasks), "--output", output_path]
        main()

        # Verify file exists
        assert os.path.exists(output_path), f"Output file {output_path} was not created"

        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), "Output must be a list"
        assert len(data) == num_tasks, f"Expected {num_tasks} traces, got {len(data)}"

        # Verify schema
        for trace in data:
            assert "trace_id" in trace, "Missing trace_id"
            assert "ground_truth_label" in trace, "Missing ground_truth_label"
            assert "step_state" in trace, "Missing step_state"
            assert "task_description" in trace, "Missing task_description"

            # Verify label values
            assert trace["ground_truth_label"] in [FailureType.STATE_PERSISTENCE, FailureType.REASONING_DEFICIT]

            # Verify step_state structure
            assert "files" in trace["step_state"]
            assert "variables" in trace["step_state"]
            
            # Verify files structure
            for f_state in trace["step_state"]["files"]:
                assert "path" in f_state
                assert "content" in f_state
                assert "deleted" in f_state
                assert isinstance(f_state["deleted"], bool)

            # Verify variables structure
            for v_state in trace["step_state"]["variables"]:
                assert "name" in v_state
                assert "value" in v_state
                assert "type" in v_state

def test_verify_pairing_integration():
    """Test that verify_pairing is callable and doesn't crash during generation context."""
    # This is a sanity check that the dependency T004 is correctly integrated
    result = verify_pairing("test-id", 42)
    # The function might return True or False depending on internal state,
    # but it must not raise an exception.
    assert isinstance(result, bool)
