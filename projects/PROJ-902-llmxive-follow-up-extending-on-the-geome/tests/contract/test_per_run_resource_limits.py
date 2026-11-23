"""
Contract test: Verify each experimental run's resource-monitor log
respects the 7 GB RAM and 360 min wall-clock limits.

This test reads JSON-line logs produced by `src/utils/resource_monitor.py`,
parses them, and asserts that every log entry adheres to the project's
resource constraints (SC-003 and SC-004).
"""
import json
import os
from pathlib import Path

import pytest

# Constants defined in the project spec (FR-007, SC-003, SC-004)
MAX_RAM_GB = 7.0
MAX_WALL_CLOCK_MIN = 360.0

# Path to the logs directory (relative to project root)
LOGS_DIR = Path("data/logs")

def _load_log_entries(log_path: Path):
    """
    Load all JSON-line entries from a log file.
    Raises FileNotFoundError if the file doesn't exist.
    Raises json.JSONDecodeError if a line is invalid JSON.
    """
    entries = []
    with log_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at {log_path}:{line_num}") from e
    return entries

def _find_all_log_files():
    """
    Recursively find all .jsonl (or .log) files under data/logs.
    Returns a list of Path objects.
    """
    if not LOGS_DIR.exists():
        return []
    return list(LOGS_DIR.glob("**/*.jsonl")) + list(LOGS_DIR.glob("**/*.log"))

def test_resource_limits_per_run():
    """
    Contract test: Iterate over all resource monitor logs in data/logs/.
    For each log entry, verify:
      - peak_ram_gb <= MAX_RAM_GB
      - wall_clock_min <= MAX_WALL_CLOCK_MIN

    If any entry violates these limits, the test fails with a descriptive message.
    """
    log_files = _find_all_log_files()

    if not log_files:
        # If no logs exist yet, we skip the assertion but note that logs are expected
        # in a real run. For strict contract testing, we might fail here if logs
        # are mandatory for CI. For now, we assume logs may not exist in unit test env.
        pytest.skip("No resource monitor logs found in data/logs/.")

    violations = []

    for log_path in log_files:
        entries = _load_log_entries(log_path)
        if not entries:
            continue

        for idx, entry in enumerate(entries):
            # Validate expected keys exist
            if "peak_ram_gb" not in entry:
                violations.append(
                    f"{log_path} (entry {idx}): missing 'peak_ram_gb'"
                )
                continue
            if "wall_clock_min" not in entry:
                violations.append(
                    f"{log_path} (entry {idx}): missing 'wall_clock_min'"
                )
                continue

            peak_ram = entry["peak_ram_gb"]
            wall_clock = entry["wall_clock_min"]

            if peak_ram > MAX_RAM_GB:
                violations.append(
                    f"{log_path} (entry {idx}): peak_ram_gb={peak_ram} exceeds limit {MAX_RAM_GB}"
                )

            if wall_clock > MAX_WALL_CLOCK_MIN:
                violations.append(
                    f"{log_path} (entry {idx}): wall_clock_min={wall_clock} exceeds limit {MAX_WALL_CLOCK_MIN}"
                )

    assert not violations, (
        "Resource limit violations detected in logs:\n" + "\n".join(violations)
    )

def test_resource_limits_schema_compliance():
    """
    Additional contract check: Ensure every log entry has the correct schema
    for resource monitoring fields (numeric types).
    """
    log_files = _find_all_log_files()

    if not log_files:
        pytest.skip("No resource monitor logs found in data/logs/.")

    schema_errors = []

    for log_path in log_files:
        entries = _load_log_entries(log_path)
        for idx, entry in enumerate(entries):
            if "peak_ram_gb" not in entry or not isinstance(entry["peak_ram_gb"], (int, float)):
                schema_errors.append(
                    f"{log_path} (entry {idx}): 'peak_ram_gb' must be numeric"
                )
            if "wall_clock_min" not in entry or not isinstance(entry["wall_clock_min"], (int, float)):
                schema_errors.append(
                    f"{log_path} (entry {idx}): 'wall_clock_min' must be numeric"
                )

    assert not schema_errors, (
        "Schema compliance errors in resource logs:\n" + "\n".join(schema_errors)
    )