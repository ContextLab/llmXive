"""
Integration test for the pipeline watchdog (hard timeout) functionality.

The test defines a dummy function that deliberately sleeps longer than the
configured timeout.  The function is wrapped with the
``@enforce_pipeline_timeout`` decorator from ``orchestrator.runtime_tracker``.
The test asserts that:

* A ``RuntimeError`` is raised (non‑zero exit behaviour).
* ``data/runtime/pipeline_runtime.json`` exists and records
  ``"within_limit": false``.
* ``data/runtime/timeout_enforced.log`` exists and contains the timeout
  error message.
"""

import json
import time

import pytest

from orchestrator.runtime_tracker import enforce_pipeline_timeout
from llmxive_toolkit import paths


def test_watchdog_overrun():
    """Ensure that exceeding the timeout creates the required artefacts."""
    @enforce_pipeline_timeout(1)  # 1‑second hard limit
    def long_running_task():
        # Sleep longer than the limit to trigger the watchdog
        time.sleep(2)

    # The decorator should raise RuntimeError when the limit is exceeded
    with pytest.raises(RuntimeError):
        long_running_task()

    # Verify the runtime JSON was written and indicates an overrun
    runtime_path = paths.data("runtime", "pipeline_runtime.json")
    assert runtime_path.is_file(), "pipeline_runtime.json was not created"

    runtime_data = json.loads(runtime_path.read_text(encoding="utf-8"))
    assert runtime_data.get("within_limit") is False, "within_limit should be false"

    # Verify the timeout log was written
    log_path = paths.data("runtime", "timeout_enforced.log")
    assert log_path.is_file(), "timeout_enforced.log was not created"
    log_content = log_path.read_text(encoding="utf-8")
    assert "exceeded hard timeout" in log_content.lower()