"""
Integration test for User Story 1: Validate end-to-end generation of 500 failures.

This test verifies that the baseline failure generation pipeline:
1. Loads the task bank and configuration correctly.
2. Invokes the trajectory generator with valid parameters.
3. Produces a `data/raw/baseline_failures.json` file containing >= 500 validated entries.
4. Ensures each entry has valid IDs, failure steps, and linked ground-truth transitions.
5. Validates schema compliance using the contract test definitions.

Note: This test is marked as an integration test and requires the implementation
of `src/sim/trajectory_generator.py` to be present and functional.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.trajectory_generator import generate_baseline_failures
from src.config.config import SEED, DATA_PATH
from tests.contract.test_trajectory_schema import validate_trajectory_schema


# Constants for the integration test
TARGET_COUNT = 500
OUTPUT_FILE = DATA_PATH / "raw" / "baseline_failures.json"
MAX_RETRIES = 10  # Max retries for the generation loop to prevent hanging in tests


@pytest.mark.integration
def test_baseline_generation_end_to_end():
    """
    End-to-end integration test for generating 500 baseline failure trajectories.

    This test ensures that:
    - The output file is created.
    - The file contains at least 500 entries.
    - Each entry passes the schema validation contract.
    - Entries have non-empty failure reasons and valid ground-truth links.
    """
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing output file to ensure fresh generation
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    # Generate the baseline failures
    # Note: In a real execution environment, this might take a significant amount of time.
    # For the purpose of this test, we assume the implementation is efficient enough
    # or that the test environment has the necessary resources.
    try:
        generated_count = generate_baseline_failures(
            target_count=TARGET_COUNT,
            seed=SEED,
            max_retries=MAX_RETRIES,
            output_path=OUTPUT_FILE
        )
    except Exception as e:
        pytest.fail(f"Generation process failed with error: {e}")

    # Assert that the expected number of failures was generated
    assert generated_count >= TARGET_COUNT, (
        f"Expected at least {TARGET_COUNT} failures, but only generated {generated_count}"
    )

    # Assert that the output file exists
    assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} was not created"

    # Load and validate the generated data
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        failures_data = json.load(f)

    assert isinstance(failures_data, list), "Output data must be a list of trajectories"
    assert len(failures_data) >= TARGET_COUNT, (
        f"Loaded file contains {len(failures_data)} entries, expected >= {TARGET_COUNT}"
    )

    # Validate each entry against the schema contract
    errors = []
    for idx, entry in enumerate(failures_data):
        schema_valid, error_msg = validate_trajectory_schema(entry)
        if not schema_valid:
            errors.append(f"Entry {idx}: {error_msg}")
            continue

        # Additional integration-specific checks
        if "failure_reason" not in entry or not entry["failure_reason"]:
            errors.append(f"Entry {idx}: Missing or empty 'failure_reason'")
        
        if "ground_truth_link" not in entry or not entry["ground_truth_link"]:
            errors.append(f"Entry {idx}: Missing or empty 'ground_truth_link'")

        if "trajectory_id" not in entry or not entry["trajectory_id"]:
            errors.append(f"Entry {idx}: Missing or empty 'trajectory_id'")

    if errors:
        pytest.fail(
            f"Schema validation or integration checks failed for {len(errors)} entries:\n"
            + "\n".join(errors[:10])  # Limit error output to first 10
        )

    # If we reach here, all checks passed
    print(f"Successfully validated {len(failures_data)} baseline failure trajectories.")