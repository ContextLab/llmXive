"""
Survey application core logic for capturing and exporting participant data.

This module implements the functionality required by task T022f:
on form submission, a row is atomically appended to `data/raw/submissions.csv`
following the schema defined in `code/survey/constants.py` (METADATA_SCHEMA).

The implementation avoids any synthetic data generation and writes real
measurements (timestamp, hashed IP, etc.) to disk.
"""

import os
import csv
import uuid
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import streamlit as st

# Import helper utilities
from utils.helpers import hash_ip, get_project_root, ensure_data_dirs

# Constants module where METADATA_SCHEMA is defined
from survey.constants import METADATA_SCHEMA

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def _get_submissions_csv_path() -> Path:
    """
    Returns the absolute path to the submissions CSV file.
    """
    project_root = get_project_root()
    return project_root / "data" / "raw" / "submissions.csv"

def _atomic_write_row(row: Dict[str, Any]) -> None:
    """
    Atomically writes a single row to the submissions CSV.

    The function writes to a temporary file in the same directory and then
    renames it to the target path, ensuring that a partially written file
    never appears.

    If the target CSV does not exist, it is created with a header derived
    from METADATA_SCHEMA.
    """
    submissions_path = _get_submissions_csv_path()
    temp_path = submissions_path.with_suffix(".tmp")

    # Ensure the parent directory exists
    submissions_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = submissions_path.is_file()

    # Open the temporary file for writing
    with temp_path.open(mode="w", newline="", encoding="utf-8") as tmp_file:
        writer = csv.DictWriter(tmp_file, fieldnames=METADATA_SCHEMA)
        if not file_exists:
            # Write header only if the target file does not yet exist
            writer.writeheader()
        else:
            # If the file exists, copy its current contents first
            with submissions_path.open(mode="r", newline="", encoding="utf-8") as existing_file:
                for line in existing_file:
                    tmp_file.write(line)

        # Write the new row
        writer.writerow(row)

    # Atomically replace the old file with the new one
    os.replace(str(temp_path), str(submissions_path))

# ----------------------------------------------------------------------
# Core Survey Functions
# ----------------------------------------------------------------------
def init_session_state() -> None:
    """
    Initializes required keys in Streamlit's session_state.
    This function is idempotent.
    """
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = str(uuid.uuid4())
    if "session_start" not in st.session_state:
        # Record the start time as an aware UTC datetime
        st.session_state.session_start = datetime.now(timezone.utc)

def extract_and_validate_ip() -> str:
    """
    Extracts the client IP address from Streamlit's request headers and
    validates its presence. Raises an error if the IP cannot be determined.
    Returns the raw IP address string.
    """
    # Streamlit provides request context via st.experimental_get_query_params()
    # but for IP we rely on the underlying WSGI environment.
    ip = st.context.headers.get("X-Forwarded-For")
    if not ip:
        st.error("Session Rejected: Unable to verify identity.")
        st.stop()
    return ip

def hash_participant_ip(raw_ip: str) -> str:
    """
    Hashes the participant's IP address using the PBKDF2 helper.
    """
    return hash_ip(raw_ip)

def get_browser_version() -> str:
    """
    Retrieves the User-Agent header and extracts a simplified browser version.
    """
    user_agent = st.context.headers.get("User-Agent", "unknown")
    # Very simple extraction: take the first token before a space
    return user_agent.split(" ")[0]

def compute_session_duration_seconds() -> int:
    """
    Computes the session duration in seconds from the start time stored in
    session_state.
    """
    start = st.session_state.get("session_start")
    if not start:
        return 0
    now = datetime.now(timezone.utc)
    return int((now - start).total_seconds())

def prepare_submission_row(
    participant_id: str,
    age: int,
    education: str,
    hashed_ip: str,
    browser_version: str,
    session_duration: int,
) -> Dict[str, Any]:
    """
    Constructs a dictionary matching METADATA_SCHEMA for a single submission.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    row = {
        "participant_id": participant_id,
        "age": age,
        "education": education,
        "timestamp": timestamp,
        "hashed_ip": hashed_ip,
        "browser_version": browser_version,
        "session_duration": session_duration,
    }
    # Ensure the row contains exactly the keys defined in the schema
    missing = set(METADATA_SCHEMA) - set(row.keys())
    if missing:
        raise ValueError(f"Missing required fields for submission: {missing}")
    return row

def submit_survey(age: int, education: str) -> None:
    """
    Handles the final submission of the survey.

    This function:
    1. Retrieves the participant ID from session_state.
    2. Extracts and hashes the IP address.
    3. Determines the browser version.
    4. Calculates the session duration.
    5. Writes the data atomically to `data/raw/submissions.csv`.
    6. Triggers any downstream side‑effects (e.g., checksum updates) via
       helpers if they are registered elsewhere.
    """
    # Ensure session state is initialized
    init_session_state()

    participant_id = st.session_state.participant_id
    raw_ip = extract_and_validate_ip()
    hashed_ip = hash_participant_ip(raw_ip)
    browser_version = get_browser_version()
    session_duration = compute_session_duration_seconds()

    # Build the row according to the schema
    row = prepare_submission_row(
        participant_id=participant_id,
        age=age,
        education=education,
        hashed_ip=hashed_ip,
        browser_version=browser_version,
        session_duration=session_duration,
    )

    # Perform the atomic write
    _atomic_write_row(row)

    st.success("Thank you! Your responses have been recorded.")
    # Optionally, advance to the next page or display a thank‑you message
    # st.switch_page("thank_you.py")  # Placeholder for actual navigation

# ----------------------------------------------------------------------
# Streamlit UI Flow (simplified for the purpose of this task)
# ----------------------------------------------------------------------
def main() -> None:
    """
    Minimal Streamlit app demonstrating the capture and export workflow.
    In the full application other steps (consent, stimulus rendering, etc.)
    are executed before reaching this point.
    """
    st.title("Demographic Survey")

    # Initialise session state (participant ID, start time, etc.)
    init_session_state()

    # Simple demographic form
    with st.form(key="demographics_form"):
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        education = st.selectbox(
            "Highest level of education",
            options=["High School", "Bachelor's", "Master's", "PhD", "Other"],
        )
        submitted = st.form_submit_button(label="Submit")

        if submitted:
            # Validate inputs before submission
            if age == 0 or not education:
                st.error("Please provide both age and education.")
            else:
                submit_survey(age=int(age), education=education)

if __name__ == "__main__":
    # Running the module directly launches the Streamlit UI.
    # In production the app is launched via `streamlit run code/survey/app.py`
    main()