"""
Test suite for the reference calendar generation (T007).

Verifies that the `reference_calendar.json` file exists, is valid JSON,
and contains a non‑empty list of events.
"""

import json
from pathlib import Path

# Import the llmxive toolkit path helper
from llmxive_toolkit import paths

def test_reference_calendar_exists_and_valid():
    """
    Ensure the generated reference calendar file exists, can be parsed as JSON,
    and contains an 'events' list with at least one entry.
    """
    calendar_path: Path = paths.data("events", "reference_calendar.json")
    assert calendar_path.is_file(), f"{calendar_path} does not exist"

    with open(calendar_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic schema checks
    assert isinstance(data, dict), "Root of JSON should be a dict"
    assert "events" in data, "'events' key missing in reference calendar"
    events = data["events"]
    assert isinstance(events, list), "'events' should be a list"
    assert len(events) > 0, "Reference calendar contains no events"