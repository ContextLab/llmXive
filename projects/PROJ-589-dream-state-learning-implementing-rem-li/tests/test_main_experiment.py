"""
Basic integration test for the ``code/main.py`` orchestrator.

The test checks that, after invoking the script, the expected result
JSON files exist for each seed and that they conform to the JSON schema
defined in ``specs/001-dream-state-learning-implementing-rem-li/contracts/experiment_result_schema.schema.yaml``.
"""

import json
from pathlib import Path
import subprocess
import sys

import jsonschema

# Load the JSON schema once
SCHEMA_PATH = Path(
    "specs/001-dream-state-learning-implementing-rem-li/contracts/experiment_result_schema.schema.yaml"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = json.load(f)

def test_multi_seed_experiment(tmp_path: Path):
    # Run the orchestrator script (uses default seeds 0‑4)
    result = subprocess.run(
        [sys.executable, "code/main.py"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that result files exist and validate against the schema
    for seed in range(5):
        for run_type in ("wake_dream", "baseline"):
            json_path = Path("data/results") / f"experiment_result_seed{seed}_{run_type}.json"
            assert json_path.is_file(), f"Missing {json_path}"
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate against the schema
            jsonschema.validate(instance=data, schema=schema)

# The test will be discovered and run by ``pytest -v`` automatically.