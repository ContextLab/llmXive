"""
Unit test that runs the configuration validation script.

The test simply executes the script as a subprocess and asserts that it exits
with a zero status code, indicating that both `species.yaml` and
`parameters.yaml` conform to the schema defined in `contracts/config.schema.yaml`.
"""

import os
import subprocess
import sys
from pathlib import Path

def test_config_schema_validation():
    # Resolve the path to the validation script relative to this test file
    script_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "src"
        / "pipeline"
        / "validate_config.py"
    )
    assert script_path.is_file(), f"Validation script not found at {script_path}"

    # Run the script using the same Python interpreter that runs the tests
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Debug output in case of failure
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    # The script must exit with code 0 for valid configurations
    assert result.returncode == 0, "Configuration validation failed"
