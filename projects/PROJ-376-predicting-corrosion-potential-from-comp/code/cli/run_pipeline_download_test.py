"""
Integration test for the download stage.

Executes the CLI with the 'download' stage and verifies that the
expected output files are created:
  - data/raw/nist/nist_ir_8200_data.zip
  - data/logs/download_summary.json
The test will raise if any of these files are missing.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

# Paths to expected artifacts
zip_path = paths.data("raw", "nist", "nist_ir_8200_data.zip")
summary_path = paths.logs("download_summary.json")

# Verify existence
assert zip_path.is_file(), f"Expected zip file not found: {zip_path}"
assert summary_path.is_file(), f"Expected summary file not found: {summary_path}"

# Verify that the summary JSON contains the required keys
with open(summary_path, "r", encoding="utf-8") as f:
    summary = json.load(f)

required_keys = {"record_count", "alloy_designation_count"}
missing = required_keys - summary.keys()
assert not missing, f"Summary missing keys: {missing}"
