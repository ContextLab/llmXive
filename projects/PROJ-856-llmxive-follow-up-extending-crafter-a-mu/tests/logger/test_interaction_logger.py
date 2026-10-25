"""
tests/logger/test_interaction_logger.py
---------------------------------------
Unit tests for the interaction logger ensuring that records conform to the
interaction_log schema.
"""

import json
import yaml
from pathlib import Path
import pytest
from jsonschema import validate

from src.logger.interaction_logger import clear_logs, log_interaction, set_deterministic, LOG_PATH

# Load the contract schema using yaml.safe_load to avoid JSONDecodeError on YAML files
SCHEMA_PATH = Path(__file__).parents[2] / "specs" / "001-llmxive-follow-up-extending-crafter-a-mu" / "contracts" / "interaction_log.schema.yaml"

@pytest.fixture(autouse=True)
def clean_log():
    clear_logs()
    yield
    clear_logs()

def test_basic_logging_schema_conformity():
    # Load schema
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    log_interaction(
        participant_id="test_user",
        figure_id="figure_0",
        interface="structured",
        payload={"action": "set_color", "target": "axis", "color": "red"},
        iteration=1,
    )
    
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    
    # Validate against the schema
    validate(instance=record, schema=schema)

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
    set_deterministic(False)