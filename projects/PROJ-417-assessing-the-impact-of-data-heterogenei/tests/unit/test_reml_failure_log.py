"""
Unit tests for the REML failure JSON logging helper (FR-006).
"""

import json

from code.simulation.estimators import log_reml_failure


def test_log_reml_failure_appends_events(tmp_path):
    log_file = tmp_path / "reml_failures.json"
    log_reml_failure({"estimator": "reml", "reason": "test failure"}, str(log_file))
    log_reml_failure({"estimator": "reml", "reason": "another failure"}, str(log_file))

    with open(log_file) as f:
        events = json.load(f)
    assert len(events) == 2
    assert events[0]["reason"] == "test failure"
    assert events[1]["reason"] == "another failure"
    assert "timestamp" in events[0]
    assert "timestamp" in events[1]
