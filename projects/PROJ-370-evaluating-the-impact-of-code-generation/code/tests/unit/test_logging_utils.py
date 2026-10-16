"""
Unit tests for the pipeline JSON‑lines logger.

The test verifies that ``log_event`` creates ``logs/pipeline.jsonl``,
that the file contains valid JSON, and that the payload matches the
dictionary passed to the function.
"""
import json
from pathlib import Path

from src.pipeline.logging_utils import log_event

def test_log_event_writes_valid_json(tmp_path, monkeypatch):
    # Redirect the internal log path to a temporary location.
    temp_log = tmp_path / "pipeline.jsonl"
    monkeypatch.setattr(
        "src.pipeline.logging_utils._PIPELINE_LOG_PATH", temp_log, raising=False
    )

    event = {"event": "test_event", "value": 42}
    log_event(event)

    # The file must exist and contain exactly one line.
    assert temp_log.is_file()
    lines = temp_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    # The line must be valid JSON and equal to the original dict.
    loaded = json.loads(lines[0])
    assert loaded == event
