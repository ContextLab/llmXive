"""
tests/logger/test_interaction_logger.py
---------------------------------------

Unit tests for the interaction logger ensuring that records conform to the
``interaction_log`` schema and that deterministic logging produces reproducible
output.
"""

import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from src.logger.interaction_logger import clear_logs, log_interaction, set_deterministic, LOG_PATH

# Load the contract schema (assumed to be present in the repository)
SCHEMA_PATH = Path(__file__).parents[2] / "specs" / "001-llmxive-follow-up-extending-crafter-a-mu" / "contracts" / "interaction_log.schema.yaml"
with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    INTERACTION_SCHEMA = json.load(f)

@pytest.fixture(autouse=True)
def clean_log():
    # Ensure a fresh log before each test
    clear_logs()
    yield
    clear_logs()

def test_basic_logging():
    log_interaction(
        participant_id="test_user",
        figure_id="figure_0",
        interface="structured",
        payload={"action": "set_color", "target": "axis", "color": "red"},
        iteration=1,
    )
    # Verify a single line was written
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    # Required fields
    for field in [
        "log_id",
        "session_id",
        "task_id",
        "timestamp_ms",
        "iteration",
        "mode",
        "payload",
        "response_image_path",
        "task_start_ms",
        "task_end_ms",
        "participant_id",
        "figure_id",
        "interface",
    ]:
        assert field in record

    # Payload must be a JSON‑encoded string
    assert isinstance(record["payload"], str)
    # Validate against the schema
    validate(instance=record, schema=INTERACTION_SCHEMA)

def test_deterministic_logging_reproducibility():
    set_deterministic(True)
    log_interaction(
        participant_id="det_user",
        figure_id="figure_1",
        interface="chat",
        payload={"message": "make axis red"},
        iteration=1,
    )
    first_line = LOG_PATH.read_text(encoding="utf-8").strip()
    LOG_PATH.unlink()  # clear file
    clear_logs()
    set_deterministic(True)
    log_interaction(
        participant_id="det_user",
        figure_id="figure_1",
        interface="chat",
        payload={"message": "make axis red"},
        iteration=1,
    )
    second_line = LOG_PATH.read_text(encoding="utf-8").strip()
    assert first_line == second_line
    # Ensure the deterministic log_id follows the expected pattern
    record = json.loads(first_line)
    assert record["log_id"].startswith("det-")
    set_deterministic(False)