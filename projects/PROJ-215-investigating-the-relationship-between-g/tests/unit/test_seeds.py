"""
Unit test for ``code/seeds.py``.
The test executes the script, then verifies that ``state/seeds.yaml``
exists and contains integer entries for the required seeds.
"""

import os
from pathlib import Path

import yaml

import subprocess
import sys

# Import the project's paths helper to resolve the expected location.
from llmxive_toolkit import paths


def test_seeds_file_creation(tmp_path, monkeypatch):
    """
    Run ``code/seeds.py`` and assert that the output file exists and
    contains the correct integer fields.
    """
    # Ensure the working directory is the project root for relative paths.
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # Execute the script
    result = subprocess.run(
        [sys.executable, "code/seeds.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Resolve the generated seeds.yaml path using the toolkit helper.
    seeds_path = paths.path("state", "seeds.yaml")
    assert seeds_path.is_file(), f"Expected seeds file at {seeds_path}"

    # Load and validate contents.
    with seeds_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Required keys must be present and be integers.
    required_keys = ["random_seed", "numpy_seed"]
    for key in required_keys:
        assert key in data, f"Missing key {key}"
        assert isinstance(data[key], int), f"{key} is not an integer"

    # ``torch_seed`` is optional – if present it must also be an integer.
    if "torch_seed" in data:
        assert isinstance(data["torch_seed"], int), "torch_seed is not an integer"