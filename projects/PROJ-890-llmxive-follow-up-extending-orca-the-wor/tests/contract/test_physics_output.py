"""
Contract test for physics engine simulation output format.

This test verifies that the physics engine simulation output adheres to the
expected data structure and field definitions required by downstream tasks
(T020b, T023, T024, T026a).

It ensures that the `code/data/physics_verify.py` module produces output
compatible with the `data/validation/physics_ground_truth_subset.csv` schema.
"""
import pytest
import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the config to ensure we are testing against the correct paths
from config import get_config, ensure_directories
from data.models import PhysicalScenarioPydantic, LatentVectorPydantic

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"
PHYSICS_OUTPUT_FILE = DATA_VALIDATION_DIR / "physics_ground_truth_subset.csv"


class TestPhysicsOutputContract:
    """
    Contract tests for the physics simulation output format.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure required directories exist before running tests."""
        ensure_directories()
        # Note: We do not create the file here; the test should fail if the
        # file is missing, indicating the simulation task (T020b) hasn't run
        # or failed to write output.

    def test_output_file_exists(self):
        """
        Contract: The physics verification script MUST produce
        data/validation/physics_ground_truth_subset.csv.
        """
        assert PHYSICS_OUTPUT_FILE.exists(), (
            f"Contract failed: Physics output file {PHYSICS_OUTPUT_FILE} does not exist. "
            "Ensure code/data/physics_verify.py has been executed successfully."
        )

    def test_required_columns_present(self):
        """
        Contract: The output CSV must contain the exact required columns:
        - scenario_id
        - counterfactual_prompt
        - simulated_outcome
        """
        required_columns = {"scenario_id", "counterfactual_prompt", "simulated_outcome"}
        
        with open(PHYSICS_OUTPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actual_columns = set(reader.fieldnames) if reader.fieldnames else set()

            missing = required_columns - actual_columns
            extra = actual_columns - required_columns

            assert not missing, (
                f"Contract failed: Missing required columns in {PHYSICS_OUTPUT_FILE}: {missing}"
            )
            # Optional: Warn if extra columns exist, but don't fail unless strict schema is enforced
            # assert not extra, f"Contract warning: Unexpected columns found: {extra}"

    def test_data_types_and_format(self):
        """
        Contract: Verify data types and formats for each column.
        - scenario_id: string, non-empty
        - counterfactual_prompt: string, non-empty
        - simulated_outcome: string, non-empty (e.g., "object_fell", "no_collision")
        """
        errors = []
        row_count = 0

        with open(PHYSICS_OUTPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                
                # Check scenario_id
                if not row.get("scenario_id") or not isinstance(row["scenario_id"], str):
                    errors.append(f"Row {row_count}: 'scenario_id' is missing or not a string.")
                
                # Check counterfactual_prompt
                if not row.get("counterfactual_prompt") or not isinstance(row["counterfactual_prompt"], str):
                    errors.append(f"Row {row_count}: 'counterfactual_prompt' is missing or not a string.")
                
                # Check simulated_outcome
                if not row.get("simulated_outcome") or not isinstance(row["simulated_outcome"], str):
                    errors.append(f"Row {row_count}: 'simulated_outcome' is missing or not a string.")

        assert not errors, (
            f"Contract failed: Data type/format errors found in {PHYSICS_OUTPUT_FILE}:\n"
            + "\n".join(errors[:5])  # Show first 5 errors
        )
        assert row_count > 0, (
            f"Contract failed: {PHYSICS_OUTPUT_FILE} exists but contains no data rows. "
            "Ensure physics simulation was executed for the N=50 subset."
        )

    def test_no_null_values(self):
        """
        Contract: Ensure no null or empty string values in critical fields.
        """
        critical_fields = ["scenario_id", "counterfactual_prompt", "simulated_outcome"]
        null_count = 0

        with open(PHYSICS_OUTPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for field in critical_fields:
                    value = row.get(field)
                    if value is None or value.strip() == "":
                        null_count += 1

        assert null_count == 0, (
            f"Contract failed: Found {null_count} null/empty values in critical fields "
            f"({', '.join(critical_fields)}) in {PHYSICS_OUTPUT_FILE}."
        )

    def test_outcome_values_are_valid_enum(self):
        """
        Contract: Verify that 'simulated_outcome' contains only expected outcome strings.
        This prevents typos or unhandled simulation states from propagating.
        """
        # Define a set of valid outcomes based on the project's physical simulation logic.
        # These should match the possible return values from the physics engine.
        # If the simulation logic changes, this list must be updated.
        valid_outcomes = {
            "object_fell",
            "object_stayed_put",
            "object_moved_horizontally",
            "collision_detected",
            "no_collision",
            "simulation_error"
        }

        invalid_outcomes = set()

        with open(PHYSICS_OUTPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                outcome = row.get("simulated_outcome", "").strip()
                if outcome and outcome not in valid_outcomes:
                    invalid_outcomes.add(outcome)

        assert not invalid_outcomes, (
            f"Contract failed: Found unexpected 'simulated_outcome' values in {PHYSICS_OUTPUT_FILE}: "
            f"{invalid_outcomes}. "
            "Please ensure the physics simulation script uses standardized outcome strings."
        )

    def test_scenario_id_uniqueness(self):
        """
        Contract: Ensure each scenario_id is unique in the output file.
        """
        scenario_ids = []
        duplicates = set()

        with open(PHYSICS_OUTPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("scenario_id")
                if sid in scenario_ids:
                    duplicates.add(sid)
                scenario_ids.append(sid)

        assert not duplicates, (
            f"Contract failed: Duplicate scenario_ids found in {PHYSICS_OUTPUT_FILE}: {duplicates}"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
