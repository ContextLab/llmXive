"""
SART and OSPAN Task Delivery Module
-----------------------------------

This module provides a minimal Flask web interface for delivering the
Sustained Attention to Response Task (SART) and the Operation Span (OSPAN)
cognitive tasks. The task code is downloaded from the Open Science
Framework (OSF) at runtime, verified against a SHA‑256 checksum defined in
the study configuration, and served to participants. Trial‑level responses
are collected via a JSON POST request and written to CSV files under
``data/raw/trial_level/`` with the naming convention:

    sart_trials_<participant_id>.csv
    ospan_trials_<participant_id>.csv

The implementation follows the "fail loudly" principle: any problem with
downloading, checksum verification, or data validation raises an exception
rather than falling back to synthetic data.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List

import requests
import yaml
from flask import Flask, abort, jsonify, request, send_from_directory

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration loading
# ----------------------------------------------------------------------
CONFIG_PATH = paths.code("config", "study_config.yaml")

def load_config() -> Dict:
    """
    Load the study configuration YAML file.

    The configuration must contain a ``tasks`` mapping with entries for
    ``sart`` and ``ospan``. Each entry must provide a ``url`` and a
    ``checksum`` (SHA‑256 hex string).

    Example:

        tasks:
          sart:
            url: "https://osf.io/abcd1/download"
            checksum: "3a7bd3e2360a..."
          ospan:
            url: "https://osf.io/efgh2/download"
            checksum: "9c1f2d5e8b4c..."
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Study configuration not found at {CONFIG_PATH}. "
            "Define task URLs and checksums under the ``tasks`` key."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if "tasks" not in cfg or not isinstance(cfg["tasks"], dict):
        raise ValueError("Configuration file must contain a top‑level ``tasks`` mapping.")
    for name in ("sart", "ospan"):
        if name not in cfg["tasks"]:
            raise ValueError(f"Missing configuration for task '{name}'.")
        if "url" not in cfg["tasks"][name] or "checksum" not in cfg["tasks"][name]:
            raise ValueError(
                f"Task '{name}' must define both ``url`` and ``checksum`` entries."
            )
    return cfg

_CONFIG = load_config()

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_bytes(data: bytes) -> str:
    """Return the hex SHA‑256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()

def download_and_verify(task_name: str) -> Path:
    """
    Download the OSF task bundle for *task_name* (``sart`` or ``ospan``).

    The bundle is saved under ``code/web/tasks/cached/<task_name>``.
    After download the file's SHA‑256 hash is compared to the expected
    checksum from the configuration. If the hash does not match, a
    ``ValueError`` is raised.

    Returns the path to the extracted directory containing the task's
    static assets (HTML, JS, CSS). The OSF repository is expected to be a
    zip archive; if it is not, the raw file is returned.
    """
    task_cfg = _CONFIG["tasks"][task_name]
    url = task_cfg["url"]
    expected_checksum = task_cfg["checksum"]

    cache_dir = paths.code("web", "tasks", "cached", task_name)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename from URL
    filename = url.split("/")[-1] or f"{task_name}_task"
    download_path = cache_dir / filename

    # Download only if the file does not already exist
    if not download_path.exists():
        log.info(f"Downloading {task_name.upper()} task from {url}")
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        with open(download_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # Verify checksum
    with open(download_path, "rb") as f:
        file_bytes = f.read()
    actual_checksum = _sha256_of_bytes(file_bytes)
    if actual_checksum.lower() != expected_checksum.lower():
        raise ValueError(
            f"Checksum mismatch for {task_name.upper()} task: "
            f"expected {expected_checksum}, got {actual_checksum}"
        )
    log.info(f"{task_name.upper()} task verified (SHA‑256={actual_checksum})")

    # If the file is a zip archive, unpack it; otherwise assume it is an
    # HTML file that can be served directly.
    if download_path.suffix.lower() == ".zip":
        import zipfile

        extract_dir = cache_dir / "extracted"
        if not extract_dir.exists():
            log.info(f"Extracting {download_path.name}")
            with zipfile.ZipFile(download_path, "r") as zf:
                zf.extractall(extract_dir)
        return extract_dir
    else:
        # Single HTML file – serve it from its parent directory
        return download_path.parent

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
            ["participant_id", "trial_index", "response_time", "correct", "stimulus"]
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
# Flask application
# ----------------------------------------------------------------------
app = Flask(__name__)

@app.route("/task/<task_name>/<participant_id>", methods=["GET"])
def serve_task(task_name: str, participant_id: str):
    """
    Serve the static HTML/JS for *task_name* (``sart`` or ``ospan``).

    The task bundle is downloaded and verified on‑first request.
    The participant ID is not used for serving the static assets but is
    captured in the URL so that client‑side code can embed it in the
    POST payload.
    """
    task_name = task_name.lower()
    if task_name not in ("sart", "ospan"):
        abort(404, description="Unknown task")

    task_dir = download_and_verify(task_name)

    # Assume the OSF bundle contains an ``index.html`` at its root.
    index_file = task_dir / "index.html"
    if not index_file.exists():
        # Fallback: serve the first HTML file found.
        html_files = list(task_dir.rglob("*.html"))
        if not html_files:
            raise FileNotFoundError(f"No HTML entry point found for {task_name.upper()} task.")
        index_file = html_files[0]

    # ``send_from_directory`` requires a directory, not a full file path.
    return send_from_directory(index_file.parent, index_file.name)

@app.route("/task/<task_name>/<participant_id>/submit", methods=["POST"])
def receive_trials(task_name: str, participant_id: str):
    """
    Receive trial‑level data for *task_name*.

    Expects a JSON payload of the form:

        {
            "trials": [
                {"response_time": 342, "correct": true, "stimulus": "X"},
                ...
            ]
        }

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
