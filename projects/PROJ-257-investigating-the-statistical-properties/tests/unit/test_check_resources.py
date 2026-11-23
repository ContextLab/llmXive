"""
Unit tests for the resource‑limit enforcement script (T002 part 3).

The test creates a temporary ``resource_usage.json`` with values that are
within the limits and ensures that the script exits without error. It then
overwrites the file with a violating value and checks that the script
raises a ``SystemExit``.
"""

import json
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from code.src.analysis.check_resources import main as check_main

@pytest.fixture
def usage_path(tmp_path):
    # Override the default results directory for the duration of the test.
    original = paths.results
    paths.results = lambda *parts: Path(tmp_path, *parts)
    yield Path(tmp_path, "resource_usage.json")
    # Restore original function after test.
    paths.results = original

def test_resources_within_limits(usage_path):
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(
        json.dumps(
            {
                "wall_time_seconds": 1000,
                "peak_memory_gb": 2.5,
                "peak_disk_gb": 5.0,
            }
        )
    )
    # Should not raise; exit code 0.
    check_main()

def test_resources_exceed_limits(usage_path):
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(
        json.dumps(
            {
                "wall_time_seconds": 30000,  # > 6 h
                "peak_memory_gb": 8.0,       # > 7 GB
                "peak_disk_gb": 25.0,        # > 20 GB
            }
        )
    )
    with pytest.raises(SystemExit) as excinfo:
        check_main()
    assert excinfo.value.code == 1
