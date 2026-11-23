"""
Unit tests for deterministic workflow generation (US1).
Verifies that running the generator twice with the same seed produces
byte-for-byte identical output and valid JSON structure.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Import the generator implementation.
# We assume the generator module will be created in T012.
# To allow this test to run in isolation, we mock the import if the module
# is not yet present, or we import it directly if it exists.
try:
    from code.generators.workflow_generator import generate_workflow
except ImportError:
    # Fallback for early testing if the module isn't created yet.
    # In a real scenario, T012 must be completed before T010 runs.
    pytest.skip("code.generators.workflow_generator not yet implemented", allow_module_level=True)

from code.config import SEED, WORKFLOW_COUNT


class TestDeterministicGeneration:
    """Tests for seed consistency in workflow generation."""

    def test_seed_consistency_produces_identical_output(self):
        """
        Verify that running the generator twice with the same seed
        produces byte-for-byte identical JSON output.
        """
        # Create a temporary directory for test outputs
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path_1 = Path(tmpdir) / "workflow_seed_42_run1.json"
            output_path_2 = Path(tmpdir) / "workflow_seed_42_run2.json"

            # Run generation twice with the same seed
            generate_workflow(seed=SEED, workflow_id=1, output_path=str(output_path_1))
            generate_workflow(seed=SEED, workflow_id=1, output_path=str(output_path_2))

            # Read and compare file contents
            with open(output_path_1, "r", encoding="utf-8") as f1:
                content1 = f1.read()
            with open(output_path_2, "r", encoding="utf-8") as f2:
                content2 = f2.read()

            # Assert byte-for-byte identity
            assert content1 == content2, "Generated workflows with same seed are not identical"

            # Also verify valid JSON structure
            try:
                json.loads(content1)
                json.loads(content2)
            except json.JSONDecodeError as e:
                pytest.fail(f"Generated content is not valid JSON: {e}")

    def test_different_seeds_produce_different_output(self):
        """
        Verify that running the generator with different seeds
        produces different output.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path_1 = Path(tmpdir) / "workflow_seed_42.json"
            output_path_2 = Path(tmpdir) / "workflow_seed_123.json"

            # Run generation with different seeds
            generate_workflow(seed=SEED, workflow_id=2, output_path=str(output_path_1))
            generate_workflow(seed=SEED + 1, workflow_id=2, output_path=str(output_path_2))

            # Read contents
            with open(output_path_1, "r", encoding="utf-8") as f1:
                content1 = f1.read()
            with open(output_path_2, "r", encoding="utf-8") as f2:
                content2 = f2.read()

            # Assert they are different (highly probable)
            assert content1 != content2, "Generated workflows with different seeds are identical"

    def test_workflow_structure_contains_required_fields(self):
        """
        Verify that generated workflows contain all necessary variables
        as per SC-005 (tool outputs, state snapshots).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "workflow_structure_test.json"

            generate_workflow(seed=SEED, workflow_id=3, output_path=str(output_path))

            with open(output_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Check for required top-level fields
            required_fields = ["workflow_id", "seed", "steps", "final_state", "decision_tree"]
            for field in required_fields:
                assert field in workflow_data, f"Missing required field: {field}"

            # Check for tool outputs in steps
            assert "steps" in workflow_data
            for step in workflow_data["steps"]:
                assert "tool_name" in step, "Step missing tool_name"
                assert "tool_output" in step, "Step missing tool_output"

            # Check for state snapshots
            assert "final_state" in workflow_data
            assert "state_snapshot" in workflow_data["final_state"]

    def test_reproducibility_across_multiple_workflows(self):
        """
        Verify that generating multiple workflows with the same seed
        produces the same set of workflows each time.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate first batch
            batch1_paths = []
            for i in range(1, 4):  # Generate 3 workflows
                path = Path(tmpdir) / f"batch1_workflow_{i}.json"
                generate_workflow(seed=SEED, workflow_id=i, output_path=str(path))
                batch1_paths.append(path)

            # Generate second batch
            batch2_paths = []
            for i in range(1, 4):
                path = Path(tmpdir) / f"batch2_workflow_{i}.json"
                generate_workflow(seed=SEED, workflow_id=i, output_path=str(path))
                batch2_paths.append(path)

            # Compare corresponding files
            for path1, path2 in zip(batch1_paths, batch2_paths):
                with open(path1, "r", encoding="utf-8") as f1:
                    content1 = f1.read()
                with open(path2, "r", encoding="utf-8") as f2:
                    content2 = f2.read()

                assert content1 == content2, f"Workflows {path1.name} and {path2.name} differ between batches"