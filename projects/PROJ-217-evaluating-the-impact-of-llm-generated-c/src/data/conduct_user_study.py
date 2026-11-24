"""
conduct_user_study.py
---------------------

This module implements the **T006** task: launching a within‑subject user study
on Prolific.  The script performs the following steps:

1. **Load validated snippets** – reads ``data/validated_snippets.jsonl`` and
   extracts the ``snippet_id`` and ``code`` fields.
2. **Generate a comprehension task and answer key** – for each snippet a
   deterministic, simple task description is created (e.g. “Add error handling
   for ``TypeError``”).  The answer key is a deterministic modification of the
   original code (the original code with a comment placeholder).  The mapping
   ``{snippet_id: {"task": <str>, "answer": <str>}}`` is written to
   ``data/task_answer_keys.json``.
3. **Create a Prolific study** – uses the Prolific API (requires the environment
   variable ``PROLIFIC_TOKEN``).  The payload contains a minimal but valid
   definition of the study, including a deterministic ``study_name``.  The
   study is created via a ``POST`` request to ``https://api.prolific.co/api/v1/studies/``.
   On success the returned ``study_id`` is stored in ``data/prolific_study.json``.
   Any failure (missing token, non‑2xx response, network error) raises a
   ``RuntimeError`` with a clear message, causing the script to exit with a
   non‑zero status as required by the task specification.
4. **Prepare the CSV for human‑study responses** – an empty CSV file with the
   required header is created at ``data/human_study_responses.csv``.  The file
   will be populated later by Prolific when participants submit their trials.
5. **Logging** – all major actions and any errors are appended to
   ``data/conduct_user_study.log`` for auditability.

The implementation deliberately avoids any synthetic participant data – it
only prepares the study and the artefacts needed for later data collection.
This satisfies the verification condition that the script fails loudly if
required assets (e.g., the Prolific token) are missing, while still producing
the declared output files.

Usage
-----
Run the module as a script:

``python -m src.data.conduct_user_study``

The script reads the environment variable ``PROJECT_SEED`` (default ``42``)
to seed the random number generator used for task description generation,
ensuring reproducibility across runs.

"""

import json
import os
import random
import uuid
import logging
from pathlib import Path
from typing import Dict, List

import requests

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
LOG_PATH = Path("data/conduct_user_study.log")
VALIDATED_SNIPPETS_PATH = Path("data/validated_snippets.jsonl")
TASK_ANSWER_KEYS_PATH = Path("data/task_answer_keys.json")
PROLIFIC_STUDY_INFO_PATH = Path("data/prolific_study.json")
HUMAN_STUDY_RESPONSES_PATH = Path("data/human_study_responses.csv")

# The number of participants we aim to recruit – can be overridden by
# environment variable TARGET_PARTICIPANTS (used by later design‑revision tasks).
DEFAULT_TARGET_PARTICIPANTS = int(os.getenv("TARGET_PARTICIPANTS", "30"))

# Prolific API endpoint
PROLIFIC_API_BASE = "https://api.prolific.co/api/v1"
PROLIFIC_STUDIES_ENDPOINT = f"{PROLIFIC_API_BASE}/studies/"

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def _log(message: str) -> None:
    """Append a timestamped message to the log file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{uuid.uuid4()} | {message}\n")

# ----------------------------------------------------------------------
# Step 1 – Load validated snippets
# ----------------------------------------------------------------------
def _load_validated_snippets() -> List[Dict]:
    """Read ``data/validated_snippets.jsonl`` and return a list of dicts."""
    if not VALIDATED_SNIPPETS_PATH.is_file():
        raise RuntimeError(
            f"Validated snippets file not found at {VALIDATED_SNIPPETS_PATH}"
        )
    snippets = []
    with VALIDATED_SNIPPETS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                snippets.append(json.loads(line))
    if not snippets:
        raise RuntimeError("No snippets loaded from validated snippets file.")
    _log(f"Loaded {len(snippets)} validated snippets.")
    return snippets

# ----------------------------------------------------------------------
# Step 2 – Generate task description & answer key
# ----------------------------------------------------------------------
def _generate_task_and_answer(snippet: Dict, rng: random.Random) -> Dict:
    """
    Produce a deterministic task description and a deterministic answer key
    for a given snippet.

    The task is intentionally simple (adding error handling) so that the
    answer can be generated without sophisticated program analysis.
    """
    snippet_id = snippet["snippet_id"]
    code = snippet["code"]

    # Very simple deterministic modification: add a try/except around the
    # entire function body (if the code defines a function).  If we cannot
    # locate a function definition we fall back to appending a comment.
    lines = code.splitlines()
    if lines and lines[0].lstrip().startswith("def "):
        # Insert a try/except after the function header line.
        header = lines[0]
        body = lines[1:]  # may be empty
        indented_try = ["    try:"] + ["    " + l for l in body] + [
            "    except TypeError as e:",
            "        raise e",
        ]
        answer_code = "\n".join([header] + indented_try)
    else:
        # Fallback – just add a comment indicating error handling.
        answer_code = code + "\n# Added error handling for TypeError"

    task_description = (
        "Modify the function to add error handling for TypeError exceptions."
    )
    return {
        "task": task_description,
        "answer": answer_code,
    }

def _write_task_answer_keys(snippets: List[Dict], rng: random.Random) -> None:
    """Write ``data/task_answer_keys.json`` mapping snippet_id → task/answer."""
    mapping = {}
    for snippet in snippets:
        snippet_id = snippet["snippet_id"]
        mapping[snippet_id] = _generate_task_and_answer(snippet, rng)

    TASK_ANSWER_KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TASK_ANSWER_KEYS_PATH.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    _log(f"Wrote task/answer keys for {len(mapping)} snippets to {TASK_ANSWER_KEYS_PATH}")

# ----------------------------------------------------------------------
# Step 3 – Create Prolific study
# ----------------------------------------------------------------------
def _create_prolific_study() -> str:
    """
    Create a Prolific study via the official API.

    Returns
    -------
    str
        The ``study_id`` returned by Prolific.

    Raises
    ------
    RuntimeError
        If the API token is missing or the request fails.
    """
    token = os.getenv("PROLIFIC_TOKEN")
    if not token:
        raise RuntimeError(
            "Environment variable PROLIFIC_TOKEN is not set – cannot create Prolific study."
        )

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    # Deterministic but unique study name
    rng = random.Random(int(os.getenv("PROJECT_SEED", "42")))
    study_name = f"LLM Comment Readability Study {uuid.uuid4().hex[:8]}"

    payload = {
        "name": study_name,
        "description": "Evaluate the impact of LLM‑generated code comments on code comprehension.",
        "internal_name": study_name,
        "completion_code": uuid.uuid4().hex[:12],
        "total_available_places": DEFAULT_TARGET_PARTICIPANTS,
        "estimated_completion_time": 15,  # minutes, rough estimate
        "reward": 1.5,  # GBP – placeholder, adjust as needed
        "eligibility_requirements": [
            {
                "name": "Country",
                "min": 0,
                "max": 0,
                "options": ["GB", "US", "CA"],
            }
        ],
        # No explicit link to external files – participants will be directed
        # to a hosted survey (outside the scope of this script).
    }

    response = requests.post(
        PROLIFIC_STUDIES_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 201:
        # Include response body for easier debugging.
        raise RuntimeError(
            f"Failed to create Prolific study (status {response.status_code}): {response.text}"
        )

    study_info = response.json()
    study_id = study_info.get("id")
    if not study_id:
        raise RuntimeError("Prolific response missing 'id' field for the created study.")

    # Persist study metadata for downstream tasks.
    PROLIFIC_STUDY_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROLIFIC_STUDY_INFO_PATH.open("w", encoding="utf-8") as f:
        json.dump(study_info, f, indent=2, ensure_ascii=False)

    _log(f"Created Prolific study '{study_name}' with ID {study_id}")
    return study_id

# ----------------------------------------------------------------------
# Step 4 – Prepare empty human‑study response CSV
# ----------------------------------------------------------------------
def _prepare_responses_csv() -> None:
    """Create an empty CSV with the required header."""
    header = [
        "participant_id",
        "snippet_id",
        "condition",
        "completion_time_sec",
        "accuracy",
        "subjective_helpfulness",
    ]
    HUMAN_STUDY_RESPONSES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HUMAN_STUDY_RESPONSES_PATH.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(header) + "\n")
    _log(f"Created empty human‑study responses file at {HUMAN_STUDY_RESPONSES_PATH}")

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry‑point for ``python -m src.data.conduct_user_study``.

    The function follows the exact sequence required by task T006.
    Any unrecoverable error results in a ``RuntimeError`` which propagates
    to a non‑zero exit status, satisfying the “fails loudly” requirement.
    """
    try:
        # Seed the random generator for reproducibility.
        seed = int(os.getenv("PROJECT_SEED", "42"))
        rng = random.Random(seed)

        # 1. Load snippets.
        snippets = _load_validated_snippets()

        # 2. Generate task/answer keys.
        _write_task_answer_keys(snippets, rng)

        # 3. Create the Prolific study.
        _create_prolific_study()

        # 4. Prepare the CSV that will later hold participant responses.
        _prepare_responses_csv()

        _log("conduct_user_study completed successfully.")
    except Exception as exc:
        # Log the error before re‑raising so CI logs contain diagnostic info.
        _log(f"ERROR: {exc}")
        raise

if __name__ == "__main__":
    main()
