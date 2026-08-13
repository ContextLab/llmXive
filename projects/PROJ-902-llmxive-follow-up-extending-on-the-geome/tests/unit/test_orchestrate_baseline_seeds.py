"""
Unit test for ``src.pipeline.orchestrate_baseline_seeds``.

The test verifies that the orchestrator can be imported and that calling
``orchestrate_seeds`` with an empty seed list completes without raising
any exception.  Running the full baseline training is intentionally **not**
performed here because it would be time‑consuming and would require GPU
resources.  The orchestrator is designed to be a thin wrapper around the
baseline script, so this lightweight sanity check is sufficient for CI
contract validation.
"""

import os
import tempfile

import pytest

# Import the module under test.
from src.pipeline import orchestrate_baseline_seeds


def test_orchestrate_with_no_seeds(monkeypatch):
    """
    Ensure that ``orchestrate_seeds`` handles an empty list gracefully.

    The function should simply initialise the logger and exit without
    invoking the baseline script.
    """
    # Patch the baseline main function so that we can detect accidental calls.
    called = {"count": 0}

    def fake_main():
        called["count"] += 1

    monkeypatch.setattr(
        orchestrate_baseline_seeds,
        "baseline_main",
        fake_main,
    )

    # Use a temporary directory for logs to avoid polluting the repository.
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "orchestrate_baseline_seeds.jsonl")
        # Patch the logger setup to write into the temporary directory.
        monkeypatch.setattr(
            orchestrate_baseline_seeds,
            "setup_logger",
            lambda path: orchestrate_baseline_seeds.setup_logger(log_path),
        )
        # Run orchestrator with an empty seed list.
        orchestrate_baseline_seeds.orchestrate_seeds(seeds=[])

    # No calls to the baseline script should have been made.
    assert called["count"] == 0