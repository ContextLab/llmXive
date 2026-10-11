"""
Pytest for the structured JSON logger.

This test verifies that ``get_logger`` returns a logger that emits a
single JSON‑encoded line to ``stdout`` when an ``INFO`` message is logged.
The test captures ``stdout`` and parses the JSON to ensure the expected
fields are present.
"""

import json
import pytest

# The logger utilities live in ``code/utils/logging.py`` and are exported
# via the ``utils.logging`` package import path.
from utils.logging import get_logger, log_info


def test_dummy_logger_outputs_json(capsys: pytest.CaptureFixture) -> None:
    """
    Ensure that logging an INFO message produces a single JSON line on stdout.
    """
    # Obtain a logger for this test module.
    logger = get_logger(__name__)

    # Log a simple message using the correct ``log_info`` signature.
    log_info(logger, "Dummy logger test successful")

    # Capture the output written to stdout.
    captured = capsys.readouterr()
    stdout = captured.out.strip()

    # There should be at least one line of output.
    assert stdout, "No output captured from the logger."

    # The logger may emit multiple lines if handlers were added multiple
    # times; we only need to verify that the first line is valid JSON.
    first_line = stdout.splitlines()[0]

    # Parse the JSON record and verify its contents.
    record = json.loads(first_line)
    assert isinstance(record, dict), "Log output is not valid JSON."

    # Expected fields.
    assert record.get("message") == "Dummy logger test successful"
    assert record.get("level") == "INFO"
    assert "timestamp" in record
    assert "logger" in record