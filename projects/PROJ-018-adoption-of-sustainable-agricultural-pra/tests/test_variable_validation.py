"""Simple test to ensure variable validation logs missing fields correctly.

The test runs ``code/01_download_data.py`` with the ``--synthetic`` flag,
then inspects the generated ``modeling_log.yaml`` for the ``variable_gaps``
section.
"""

import json
import os
import yaml
from pathlib import Path

import subprocess


def test_variable_validation_logs(tmp_path: Path):
    # Ensure a clean environment
    os.chdir(tmp_path)

    # Create a minimal config.yaml so the script can locate paths
    config = {
        "raw_data_path": "data/raw",
        "raw_data_filename": "survey_data.csv",
        "modeling_log_path": "modeling_log.yaml",
        "random_seed": 123,
        "synthetic_n": 10,
    }
    (tmp_path / "code").mkdir(parents=True, exist_ok=True)
    (tmp_path / "code" / "config.yaml").write_text(yaml.safe_dump(config))

    # Run the download script with synthetic flag
    subprocess.run(
        ["python", "code/01_download_data.py", "--synthetic"],
        check=True,
        cwd=tmp_path,
    )

    # Load the log and assert the variable_gaps section reports all_present
    log_path = tmp_path / "modeling_log.yaml"
    assert log_path.is_file(), "modeling_log.yaml was not created"
    log_content = yaml.safe_load(log_path.read_text())
    variable_gaps = log_content.get("variable_gaps", {})
    assert variable_gaps.get("status") == "all_present", f"Unexpected gaps: {variable_gaps}"