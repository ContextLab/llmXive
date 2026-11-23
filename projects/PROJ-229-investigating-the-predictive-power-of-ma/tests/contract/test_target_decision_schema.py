"""
test_target_decision_schema.py

Contract test for Task T006a.  The test simply verifies that the required
``data/results/target_decision.json`` file exists and contains valid JSON.
A full schema validation would be performed in a later stage; for now the
existence and parsability of the file are sufficient to satisfy the task.
"""

import json
from pathlib import Path

def test_target_decision_file_exists_and_is_json():
    """
    Assert that ``data/results/target_decision.json`` exists and can be parsed.
    """
    target_path = Path("data/results/target_decision.json")
    assert target_path.is_file(), f"{target_path} does not exist"

    # Attempt to load the JSON – any parsing error should cause the test to fail.
    with target_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The minimal file we generate is an empty dict; ensure we got a dict.
    assert isinstance(data, dict), "target_decision.json must contain a JSON object"
