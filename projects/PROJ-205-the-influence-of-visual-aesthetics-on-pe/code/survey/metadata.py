"""
Survey Metadata Extraction Module.

Implements logic to extract system-derived metadata for survey submissions,
matching the METADATA_SCHEMA defined in constants.py.
"""
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Import the schema definition from constants
from survey.constants import METADATA_SCHEMA


def extract_metadata(participant_id: str, session_start_time: str = None, hashed_ip: str = None) -> Dict[str, Any]:
    """
    Extract system-derived metadata for a survey submission.

    This function gathers metadata that is NOT entered by the user in the form,
    but is derived from the system environment, session state, and HTTP headers.

    Args:
        participant_id (str): The unique UUID v4 for the participant.
        session_start_time (str, optional): ISO8601 timestamp of session start.
            If not provided, attempts to read from st.session_state (requires Streamlit context).
        hashed_ip (str, optional): The pre-computed hashed IP.
            If not provided, must be available in st.session_state.

    Returns:
        Dict[str, Any]: A dictionary containing the metadata fields defined in METADATA_SCHEMA
            (excluding form inputs like age, education, ratings).
            Keys: participant_id, timestamp, browser_version, session_start_time, stimulus_id, hashed_ip.
            Note: stimulus_id is required by schema but must be provided by caller or session state.

    Raises:
        RuntimeError: If required context (headers, session state) is missing or invalid.
    """
    import streamlit as st

    metadata = {}

    # 1. Participant ID (Provided as arg, but validated)
    if not participant_id:
        raise RuntimeError("participant_id is required for metadata extraction.")
    metadata["participant_id"] = participant_id

    # 2. Timestamp (System-derived: current time at extraction)
    metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

    # 3. Browser Version (Extracted from User-Agent header)
    # In Streamlit, st.context.headers is available
    user_agent = st.context.headers.get("user_agent", "")
    if not user_agent:
        # Fallback or error? The schema requires it.
        # If we can't extract it, we must fail loudly as per security/integrity constraints.
        raise RuntimeError("Unable to extract User-Agent header. Browser version is required.")

    # Simple extraction logic: look for common browser patterns
    # This is a basic heuristic; for production, a dedicated library like `user-agents` could be used.
    # However, to avoid new dependencies, we parse manually.
    browser_version = "Unknown"
    user_agent_lower = user_agent.lower()

    if "chrome" in user_agent_lower:
        # Extract version after Chrome/
        import re
        match = re.search(r"Chrome/(\d+\.\d+\.\d+\.\d+)", user_agent)
        if match:
            browser_version = f"Chrome {match.group(1)}"
        else:
            browser_version = "Chrome"
    elif "firefox" in user_agent_lower:
        match = re.search(r"Firefox/(\d+\.\d+)", user_agent)
        if match:
            browser_version = f"Firefox {match.group(1)}"
        else:
            browser_version = "Firefox"
    elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
        match = re.search(r"Version/(\d+\.\d+)", user_agent)
        if match:
            browser_version = f"Safari {match.group(1)}"
        else:
            browser_version = "Safari"
    elif "edge" in user_agent_lower:
        match = re.search(r"Edg/(\d+\.\d+\.\d+)", user_agent)
        if match:
            browser_version = f"Edge {match.group(1)}"
        else:
            browser_version = "Edge"

    metadata["browser_version"] = browser_version

    # 4. Session Start Time
    # Priority: Provided arg > st.session_state > Current time (fallback, though ideally session start is set at init)
    if session_start_time:
        metadata["session_start_time"] = session_start_time
    elif "session_start_time" in st.session_state:
        metadata["session_start_time"] = st.session_state["session_start_time"]
    else:
        # Fallback to current time if not set (should not happen in normal flow)
        metadata["session_start_time"] = datetime.now(timezone.utc).isoformat()

    # 5. Stimulus ID
    # This is critical for analysis. It should be set in session_state by the rendering loop.
    if "current_stimulus_id" in st.session_state:
        metadata["stimulus_id"] = st.session_state["current_stimulus_id"]
    else:
        # If no stimulus is active, we might be in a summary state.
        # For the purpose of the metadata extraction function called during submission,
        # we assume the last viewed stimulus or raise an error if none found.
        # Given the schema requirement, we must have a value.
        # If the user submits after viewing multiple, the last one is the context.
        # If this is called per-stimulus, it's set.
        # If called at the end for all, we might need to aggregate.
        # Assuming this function is called per-stimulus rating or the final aggregate.
        # For T069b, we implement the extraction logic.
        if "last_stimulus_id" in st.session_state:
            metadata["stimulus_id"] = st.session_state["last_stimulus_id"]
        else:
            # Fallback: 'unknown' or raise. Let's raise to enforce integrity.
            raise RuntimeError("No stimulus_id found in session state. Cannot extract metadata.")

    # 6. Hashed IP
    # Should be set at session init (T022b)
    if hashed_ip:
        metadata["hashed_ip"] = hashed_ip
    elif "hashed_ip" in st.session_state:
        metadata["hashed_ip"] = st.session_state["hashed_ip"]
    else:
        raise RuntimeError("Hashed IP not found in session state. Identity verification failed.")

    # Validation against schema (optional but good practice)
    # Ensure all required keys are present
    for key, spec in METADATA_SCHEMA.items():
        if spec.get("required") and key not in metadata:
            # Some keys like 'age' and 'education' are form inputs, not extracted here.
            # This function extracts SYSTEM metadata.
            # We only validate the keys this function is responsible for.
            if key in ["timestamp", "browser_version", "session_start_time", "stimulus_id", "hashed_ip", "participant_id"]:
                 raise RuntimeError(f"Missing required system metadata field: {key}")

    return metadata
