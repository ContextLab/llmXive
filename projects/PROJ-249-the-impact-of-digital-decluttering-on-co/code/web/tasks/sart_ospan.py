"""
SART and OSPAN Task Delivery Module (Simplified)
------------------------------------------------

This module provides a minimal Flask web interface for delivering the
Sustained Attention to Response Task (SART) and the Operation Span (OSPAN)
cognitive tasks. For the purposes of automated testing we avoid external
downloads and checksum verification **when a real OSF URL is not provided**;
however, the implementation includes the logic to download a task bundle
from a URL specified in the study configuration and verify its SHA‑256
checksum. If the URL is a ``local://`` placeholder (as in the current
configuration), the download step is skipped.

Trial‑level responses are collected via a JSON POST request and written to
CSV files under ``data/raw/trial_level/`` with the naming convention:

    sart_trials_<participant_id>.csv
    ospan_trials_<participant_id>.csv

The implementation follows the "fail loudly" principle: any problem with
data validation raises an exception rather than falling back to synthetic
data.
"""

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List

import yaml
import requests
from flask import Flask, abort, jsonify, request, Response

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Flask application
# ----------------------------------------------------------------------
app = Flask(__name__)

# ----------------------------------------------------------------------
# Configuration helpers
# ----------------------------------------------------------------------
_CONFIG_PATH = Path(__file__).resolve().parents[3] / "code" / "config" / "study_config.yaml"


def _load_study_config() -> Dict:
    """Load the YAML study configuration."""
    if not _CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Study config not found at {_CONFIG_PATH}")
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ensure_task_bundle(task_name: str) -> Path:
    """
    Ensure that the OSF task bundle for ``task_name`` exists locally and
    matches the declared SHA‑256 checksum.

    The configuration section ``tasks`` maps a task name to a ``url`` and
    ``checksum``. If the URL begins with ``http`` the file is downloaded;
    otherwise a ``local://`` scheme is interpreted as a path relative to
    the project root (used for the placeholder HTML in the test suite).

    Returns the path to the downloaded (or local) bundle.
    """
    cfg = _load_study_config()
    task_cfg = cfg.get("tasks", {}).get(task_name)
    if not task_cfg:
        raise ValueError(f"No configuration entry for task '{task_name}'")

    url = task_cfg.get("url")
    expected_checksum = task_cfg.get("checksum")

    # Resolve a local placeholder (e.g. "local://sart.html")
    if url.startswith("local://"):
        local_name = url.split("://", 1)[1]
        # Assume the placeholder file lives next to this module
        placeholder_path = Path(__file__).parent / local_name
        if not placeholder_path.is_file():
            raise FileNotFoundError(
                f"Local placeholder for task '{task_name}' not found at {placeholder_path}"
            )
        log.info(f"Using local placeholder for task '{task_name}' at {placeholder_path}")
        return placeholder_path

    # Remote download path (cached under data/raw/tasks)
    bundle_dir = paths.data("raw", "tasks")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(url).name
    bundle_path = bundle_dir / filename

    # Download if missing
    if not bundle_path.is_file():
        log.info(f"Downloading task bundle for '{task_name}' from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        bundle_path.write_bytes(response.content)
        log.info(f"Saved task bundle to {bundle_path}")

    # Verify checksum
    if expected_checksum:
        sha256 = hashlib.sha256()
        with open(bundle_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_checksum = sha256.hexdigest()
        if actual_checksum.lower() != expected_checksum.lower():
            raise ValueError(
                f"Checksum mismatch for task '{task_name}': expected {expected_checksum}, got {actual_checksum}"
            )
        log.info(f"Checksum verified for task '{task_name}'")

    return bundle_path

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_output_dir() -> Path:
    """Return the directory where trial‑level CSVs are stored."""
    out_dir = paths.data("raw", "trial_level")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _validate_trial_record(record: Dict) -> None:
    """
    Validate a single trial record.

    Required keys:
        - response_time (int or float) in milliseconds, 100 ≤ rt ≤ 5000
        - correct (bool)
        - stimulus (str)

    Raises ``ValueError`` on any validation failure.
    """
    required = {"response_time", "correct", "stimulus"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"Trial record missing fields: {missing}")

    rt = record["response_time"]
    if not isinstance(rt, (int, float)):
        raise ValueError("response_time must be numeric")
    if not (100 <= rt <= 5000):
        raise ValueError(f"response_time {rt} out of bounds (100‑5000 ms)")

    if not isinstance(record["correct"], bool):
        raise ValueError("correct must be a boolean")

    if not isinstance(record["stimulus"], str):
        raise ValueError("stimulus must be a string")


def _write_trials_csv(task_name: str, participant_id: str, trials: List[Dict]) -> Path:
    """
    Write *trials* to a CSV file named
    ``<task>_trials_<participant_id>.csv`` under the trial‑level data folder.

    The CSV columns are:
        participant_id, trial_index, response_time, correct, stimulus
    """
    out_dir = _ensure_output_dir()
    csv_path = out_dir / f"{task_name}_trials_{participant_id}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "participant_id",
                "trial_index",
                "response_time",
                "correct",
                "stimulus",
            ]
        )
        for idx, rec in enumerate(trials, start=1):
            writer.writerow(
                [
                    participant_id,
                    idx,
                    rec["response_time"],
                    rec["correct"],
                    rec["stimulus"],
                ]
            )
    log.info(f"Wrote {len(trials)} {task_name.upper()} trials to {csv_path}")
    return csv_path

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/task/<task_name>/<participant_id>", methods=["GET"])
def serve_task(task_name: str, participant_id: str):
    """
    Serve a minimal HTML page for *task_name* (``sart`` or ``ospan``).

    The page is a simple placeholder that includes the task name and
    participant identifier. If a real OSF bundle URL is configured, the
    bundle is downloaded (or retrieved from cache) and its contents are
    embedded in the page for debugging purposes.
    """
    task_name = task_name.lower()
    if task_name not in ("sart", "ospan"):
        abort(404, description="Unknown task")

    # Ensure the task bundle is present (or raise on checksum mismatch)
    try:
        bundle_path = _ensure_task_bundle(task_name)
    except Exception as e:
        log.error(f"Failed to prepare task bundle for '{task_name}': {e}")
        abort(500, description=str(e))

    # If the bundle is an HTML file, embed a link; otherwise just show placeholder.
    embed_note = ""
    if bundle_path.suffix.lower() == ".html":
        embed_note = f'<p>Task bundle: <a href="/static/{bundle_path.name}">{bundle_path.name}</a></p>'

    html_content = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{task_name.upper()} Task</title>
</head>
<body>
    <h1>{task_name.upper()} task placeholder</h1>
    <p>Participant ID: {participant_id}</p>
    {embed_note}
    <!-- In a real deployment this page would load the OSF task bundle. -->
</body>
</html>"""
    return Response(html_content, mimetype="text/html")


@app.route("/task/<task_name>/<participant_id>/submit", methods=["POST"])
def receive_trials(task_name: str, participant_id: str):
    """
    Receive trial‑level data for *task_name*.

    Expects a JSON payload of the form:

        {{
            "trials": [
                {{"response_time": 342, "correct": true, "stimulus": "X"}},
                ...
            ]
        }}

    Validates each trial, writes a CSV, and returns a JSON acknowledgment.
    """
    task_name = task_name.lower()
    if task_name not in ("sart", "ospan"):
        abort(404, description="Unknown task")

    if not request.is_json:
        abort(400, description="Request body must be JSON")

    payload = request.get_json()
    if "trials" not in payload or not isinstance(payload["trials"], list):
        abort(400, description="JSON must contain a ``trials`` list")

    trials = payload["trials"]
    if not trials:
        abort(400, description="Trial list is empty")

    # Validate each trial record
    for rec in trials:
        _validate_trial_record(rec)

    # Ensure the task bundle is present before accepting data (fails loudly if not)
    _ensure_task_bundle(task_name)

    csv_path = _write_trials_csv(task_name, participant_id, trials)

    return jsonify(
        {
            "status": "success",
            "task": task_name,
            "participant_id": participant_id,
            "file_written": str(csv_path),
            "num_trials": len(trials),
        }
    )

# ----------------------------------------------------------------------
# Convenience entry point
# ----------------------------------------------------------------------
def create_app() -> Flask:
    """
    Factory function used by external callers (e.g., the integration test)
    to obtain a Flask application instance.
    """
    return app

if __name__ == "__main__":
    # Running this module directly starts a development server.
    # In production the app should be launched via a WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=False)