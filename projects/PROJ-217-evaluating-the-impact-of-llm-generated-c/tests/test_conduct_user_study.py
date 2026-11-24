"""
test_conduct_user_study.py
-------------------------

Minimal test suite for the ``src.data.conduct_user_study`` module.
The tests verify that the module:

1. Raises a clear error when the required Prolific token is missing.
2. Writes the expected artefacts (task answer keys JSON and an empty CSV)
   when the token is present (the Prolific request is mocked).

The test suite does **not** attempt a real network call – it monkey‑patches
``requests.post`` to return a fabricated successful response.  This keeps
CI fast, deterministic and within the resource limits.
"""

import json
import os
import types
from pathlib import Path

import pytest

# Import the module under test.
from src.data import conduct_user_study as study_module

# Helper: a fake successful Prolific response object.
class _FakeResponse:
    def __init__(self, json_data, status_code=201):
        self._json = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self._json

@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """
    Configure the project to use a temporary ``data`` directory for the duration
    of the test.  This prevents polluting the real repository data.
    """
    # Point the module‑level Path constants to the temporary location.
    monkeypatch.setattr(study_module, "LOG_PATH", tmp_path / "conduct_user_study.log")
    monkeypatch.setattr(study_module, "VALIDATED_SNIPPETS_PATH", tmp_path / "validated_snippets.jsonl")
    monkeypatch.setattr(study_module, "TASK_ANSWER_KEYS_PATH", tmp_path / "task_answer_keys.json")
    monkeypatch.setattr(study_module, "PROLIFIC_STUDY_INFO_PATH", tmp_path / "prolific_study.json")
    monkeypatch.setattr(study_module, "HUMAN_STUDY_RESPONSES_PATH", tmp_path / "human_study_responses.csv")
    return tmp_path

def _write_dummy_validated_snippets(path: Path):
    """Write a minimal validated snippets file with two entries."""
    snippets = [
        {"snippet_id": "snip_001", "code": "def add(a, b):\n    return a + b"},
        {"snippet_id": "snip_002", "code": "def mul(a, b):\n    return a * b"},
    ]
    with path.open("w", encoding="utf-8") as f:
        for rec in snippets:
            f.write(json.dumps(rec) + "\n")

def test_missing_prolific_token(tmp_data_dir, monkeypatch):
    """
    When ``PROLIFIC_TOKEN`` is not set the script must raise RuntimeError.
    """
    _write_dummy_validated_snippets(study_module.VALIDATED_SNIPPETS_PATH)

    # Ensure the environment variable is absent.
    monkeypatch.delenv("PROLIFIC_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="PROLIFIC_TOKEN"):
        study_module.main()

def test_successful_run(tmp_data_dir, monkeypatch):
    """
    With a valid token and a mocked ``requests.post`` the script should
    create the expected artefacts and exit without raising.
    """
    _write_dummy_validated_snippets(study_module.VALIDATED_SNIPPETS_PATH)

    # Provide a dummy token.
    monkeypatch.setenv("PROLIFIC_TOKEN", "dummy-token")

    # Mock the HTTP POST call used in ``_create_prolific_study``.
    def _mock_post(url, headers=None, json=None, timeout=None):
        # Verify that the function is called with the expected endpoint.
        assert url == study_module.PROLIFIC_STUDIES_ENDPOINT
        # Return a fabricated successful response.
        return _FakeResponse({"id": "fake-study-id", "name": json.get("name")})

    monkeypatch.setattr(study_module.requests, "post", _mock_post)

    # Run the main function – it should complete without exception.
    study_module.main()

    # --------------------------------------------------------------
    # Assertions – check that the artefacts exist and contain plausible data.
    # --------------------------------------------------------------
    # 1. Log file created.
    assert study_module.LOG_PATH.is_file()

    # 2. Task answer keys JSON written and contains entries for both snippets.
    with study_module.TASK_ANSWER_KEYS_PATH.open("r", encoding="utf-8") as f:
        answer_keys = json.load(f)
    assert set(answer_keys.keys()) == {"snip_001", "snip_002"}
    for entry in answer_keys.values():
        assert "task" in entry and "answer" in entry

    # 3. Prolific study metadata persisted.
    with study_module.PROLIFIC_STUDY_INFO_PATH.open("r", encoding="utf-8") as f:
        study_info = json.load(f)
    assert study_info["id"] == "fake-study-id"

    # 4. Empty responses CSV with correct header.
    with study_module.HUMAN_STUDY_RESPONSES_PATH.open("r", encoding="utf-8") as f:
        header_line = f.readline().strip()
    expected_header = ",".join(
        [
            "participant_id",
            "snippet_id",
            "condition",
            "completion_time_sec",
            "accuracy",
            "subjective_helpfulness",
        ]
    )
    assert header_line == expected_header