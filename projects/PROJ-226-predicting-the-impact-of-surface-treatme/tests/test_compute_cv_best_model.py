"""
Test suite for ``code/compute_cv_best_model.py``.
It simply runs the script and checks that the expected JSON file exists
and contains the required keys.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

def test_best_model_json_exists_and_valid():
    # Execute the script – the test runner will have already executed the
    # artifact because it is marked with ``execute: true`` in the task
    # definition.  Here we only validate the output.
    best_path = paths.models("best_model.json")
    assert best_path.is_file(), f"{best_path} was not created"

    with best_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Required top‑level keys as per the task description.
    required_keys = {
        "best_model_type",
        "hyperparameters",
        "validation_r2",
        "validation_rmse",
        "cv_r2_mean",
        "cv_r2_std",
        "null_result",
        "timestamp",
    }
    assert required_keys.issubset(data.keys()), "Missing required fields"

    # Types – a few sanity checks.
    assert isinstance(data["best_model_type"], (str, type(None)))
    assert isinstance(data["hyperparameters"], dict)
    assert isinstance(data["null_result"], bool)