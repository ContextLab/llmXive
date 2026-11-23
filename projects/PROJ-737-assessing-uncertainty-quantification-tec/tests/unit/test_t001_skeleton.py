"""Unit tests for task T001 – project skeleton verification.

The test runs the skeleton‑creation script and then the verification
script, asserting that all required directories exist and that the
contract schema contains the exact column order required by the spec.
"""

import subprocess
import sys
from pathlib import Path

import yaml

# Import the modules under test
from create_skeleton import main as create_main
from verify_t001 import main as verify_main

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "figures",
    "code/models",
    "code/metrics",
    "code/stats",
    "code/utils",
    "tests/unit",
    "tests/integration",
]

SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-assessing-uncertainty-quantification-tec"
    / "contracts"
    / "per_sample_errors.schema.yaml"
)

EXPECTED_COLUMNS = [
    "sample_id",
    "dataset",
    "method",
    "prediction",
    "lower_bound",
    "upper_bound",
    "ground_truth",
    "abs_error",
]

def test_create_and_verify_skeleton(tmp_path, monkeypatch):
    """
    Run the skeleton creation script, then the verification script,
    and finally assert that the required artefacts exist and are correct.
    """
    # Ensure the script works from the project root
    monkeypatch.chdir(PROJECT_ROOT)

    # 1. Run skeleton creation
    create_main()

    # 2. Verify that all required directories now exist
    for rel_dir in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / rel_dir
        assert dir_path.is_dir(), f"Missing required directory: {rel_dir}"

    # 3. Verify that the schema file exists
    assert SCHEMA_PATH.is_file(), f"Schema file not found at {SCHEMA_PATH}"

    # 4. Load the schema and check column order
    with SCHEMA_PATH.open() as f:
        schema = yaml.safe_load(f)

    cols = [c["name"] for c in schema.get("columns", [])]
    assert cols == EXPECTED_COLUMNS, (
        f"Schema columns mismatch. Expected {EXPECTED_COLUMNS}, got {cols}"
    )

    # 5. Run the verification script (it should exit with code 0)
    exit_code = verify_main()
    assert exit_code == 0, "verify_t001 script reported failures"
