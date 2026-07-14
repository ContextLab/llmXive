"""
Unit tests for the ``bug_detection`` module.

This file contains two tests:
1. ``test_bug_detection_handles_invalid_dataset`` – verifies that the
   ``main`` function returns a non‑zero exit code when the HumanEval dataset
   cannot be loaded (existing test from the original task).
2. ``test_compute_pass1_accuracy`` – validates the correctness of the
   ``compute_pass1_accuracy`` helper.
"""

from __future__ import annotations

import pytest

from bug_detection import compute_pass1_accuracy, main as bug_detection_main

# --------------------------------------------------------------------------- #
# Existing test (preserved from the original task)
# --------------------------------------------------------------------------- #
def test_bug_detection_handles_invalid_dataset(monkeypatch, caplog):
    """
    Force ``load_humaneval_dataset`` to raise a ``ValueError`` and ensure
    that ``main`` returns an error code and logs the failure.
    """
    def raise_error(*_args, **_kwargs):
        raise ValueError("Invalid HF URI")

    monkeypatch.setattr("bug_detection.load_humaneval_dataset", raise_error)

    exit_code = bug_detection_main()
    assert exit_code == 1
    assert any(
        "Failed to load HumanEval dataset" in rec.message for rec in caplog.records
    )

# --------------------------------------------------------------------------- #
# New test – pass@1 accuracy calculation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "results,expected",
    [
        ([], 0.0),                                 # empty input
        ([True], 1.0),                             # single correct
        ([False], 0.0),                            # single incorrect
        ([True, False, True, True], 0.75),        # mixed
        ([False, False, False], 0.0),             # all incorrect
        ([True, True, True, True], 1.0),          # all correct
    ],
)
def test_compute_pass1_accuracy(results, expected):
    """
    ``compute_pass1_accuracy`` should return the proportion of ``True`` values.
    """
    assert compute_pass1_accuracy(results) == pytest.approx(expected)