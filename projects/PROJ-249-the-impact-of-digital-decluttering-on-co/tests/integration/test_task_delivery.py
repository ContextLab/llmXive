"""
Integration test for the SART/OSPAN web task delivery module.

The test instantiates the Flask app, performs a GET request to retrieve the
task HTML (ensuring the download/verification step succeeds), and then
POSTs a minimal trial payload.  It checks that the expected CSV files are
created under ``data/raw/trial_level/`` and that they conform to a basic
schema (column headers, non‑empty rows).
"""

import csv
from pathlib import Path

import pytest
from llmxive_toolkit import paths

from code.web.tasks.sart_ospan import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_get_task_html(client):
    """GET request should return the task's index page (status 200)."""
    resp = client.get("/task/sart/P001")
    assert resp.status_code == 200
    # Content‑type should be HTML
    assert "text/html" in resp.content_type

def test_post_trials_creates_csv(client, tmp_path, monkeypatch):
    """
    POST a small trial payload and verify that a CSV file is written with
    the correct naming convention and column headers.
    """
    # Use a temporary directory for data output to avoid polluting the repo
    trial_dir = tmp_path / "trial_level"
    trial_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "llmxive_toolkit.paths.data",
        lambda *parts: Path(trial_dir, *parts[1:])  # ignore the leading "raw"
    )

    payload = {
        "trials": [
            {"response_time": 350, "correct": True, "stimulus": "A"},
            {"response_time": 420, "correct": False, "stimulus": "B"},
        ]
    }
    resp = client.post(
        "/task/ospan/P123/submit",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["task"] == "ospan"
    assert data["participant_id"] == "P123"

    # Verify CSV existence and contents
    csv_path = Path(data["file_written"])
    assert csv_path.exists()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == [
            "participant_id",
            "trial_index",
            "response_time",
            "correct",
            "stimulus",
        ]
        rows = list(reader)
        assert len(rows) == 2
        # Simple sanity check on the first row
        assert rows[0][0] == "P123"
        assert int(rows[0][2]) == 350