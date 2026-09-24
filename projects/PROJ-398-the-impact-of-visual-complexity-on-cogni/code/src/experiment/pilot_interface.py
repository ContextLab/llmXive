"""
Pilot Interface for collecting human visual complexity ratings.

This module provides:
- ensure_output_dir(): Guarantees the existence of the directory where
  human ratings are persisted.
- list_stimuli_images(): Returns a list of image file paths from the
  `data/stimuli/` directory (used by the Streamlit UI to present stimuli).
- append_rating(image_id: str, participant_id: str, complexity_score: int):
  Persists a single rating to `data/measurements/human_ratings.csv` with
  columns ``image_id, participant_id, complexity_score``.  The function is
  idempotent with respect to the header – it creates the file with a header
  if it does not exist and appends subsequent rows.
- main(): Streamlit entry‑point that displays the stimuli, collects ratings,
  and stores them using ``append_rating``.
"""

import csv
import os
from pathlib import Path
from typing import List

import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
# Root of the repository (two levels up from this file)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Directory where raw stimulus images are stored
STIMULI_DIR = REPO_ROOT / "data" / "stimuli"

# Output CSV for human ratings
RATINGS_CSV = REPO_ROOT / "data" / "measurements" / "human_ratings.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_output_dir() -> None:
    """
    Ensure that the directory for the human ratings CSV exists.
    Creates ``data/measurements`` if it does not already exist.
    """
    output_dir = RATINGS_CSV.parent
    output_dir.mkdir(parents=True, exist_ok=True)


def list_stimuli_images() -> List[Path]:
    """
    Return a list of image file paths in the stimuli directory.
    Only files with typical image extensions are returned.
    """
    if not STIMULI_DIR.is_dir():
        raise FileNotFoundError(f"Stimuli directory not found: {STIMULI_DIR}")

    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}
    return [
        p
        for p in STIMULI_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    ]


def _initialize_csv() -> None:
    """
    Create the CSV file with a header if it does not already exist.
    This helper is called by ``append_rating`` before writing rows.
    """
    if not RATINGS_CSV.exists():
        ensure_output_dir()
        with RATINGS_CSV.open(mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_id", "participant_id", "complexity_score"])


def append_rating(image_id: str, participant_id: str, complexity_score: int) -> None:
    """
    Persist a single human rating to the CSV file.

    Parameters
    ----------
    image_id: str
        Identifier of the stimulus image (typically the filename without
        extension).
    participant_id: str
        Unique identifier for the participant (e.g., a UUID or short code).
    complexity_score: int
        Rating given by the participant on the 1‑10 scale.

    The function writes a new row to ``data/measurements/human_ratings.csv``.
    It creates the file with a header if it does not already exist.
    """
    # Basic validation
    if not isinstance(image_id, str) or not image_id:
        raise ValueError("image_id must be a non‑empty string")
    if not isinstance(participant_id, str) or not participant_id:
        raise ValueError("participant_id must be a non‑empty string")
    if not isinstance(complexity_score, int):
        raise ValueError("complexity_score must be an integer")
    if not (1 <= complexity_score <= 10):
        raise ValueError("complexity_score must be between 1 and 10 inclusive")

    _initialize_csv()

    # Append the rating
    with RATINGS_CSV.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([image_id, participant_id, complexity_score])


# ----------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------
def main() -> None:
    """
    Streamlit application entry point.

    The UI presents each stimulus image sequentially and asks the
    participant to provide a complexity rating (1‑10).  After a rating
    is submitted, it is persisted via ``append_rating``.
    """
    st.title("Visual Complexity Pilot Study")
    st.markdown(
        """
        Please rate the visual complexity of each background image on a scale
        from **1 (very simple)** to **10 (very complex)**.
        """
    )

    # Participant ID – generated once per session
    if "participant_id" not in st.session_state:
        # A simple UUID without hyphens for readability
        st.session_state.participant_id = (
            __import__("uuid").uuid4().hex[:12]
        )
        st.sidebar.success(
            f"Your participant ID: {st.session_state.participant_id}"
        )

    # Load stimuli
    try:
        stimuli = list_stimuli_images()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    if not stimuli:
        st.warning("No stimulus images found in the stimuli directory.")
        return

    # Navigation state
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    idx = st.session_state.current_index
    image_path = stimuli[idx]

    # Display image
    st.image(str(image_path), caption=image_path.name, use_column_width=True)

    # Rating widget
    rating = st.slider(
        "Complexity rating (1‑10)", min_value=1, max_value=10, value=5, key="rating_slider"
    )

    # Submit button
    if st.button("Submit rating"):
        image_id = image_path.stem  # filename without extension
        append_rating(
            image_id=image_id,
            participant_id=st.session_state.participant_id,
            complexity_score=rating,
        )
        st.success(f"Rating for **{image_path.name}** saved.")

        # Move to next image
        if idx + 1 < len(stimuli):
            st.session_state.current_index = idx + 1
            st.experimental_rerun()
        else:
            st.balloons()
            st.success("Thank you! You have completed all ratings.")
            # Reset for a new participant if desired
            del st.session_state.current_index

# When the module is executed directly, launch the Streamlit app.
if __name__ == "__main__":
    # Streamlit expects the script to be run via `streamlit run <script>`.
    # However, for convenience during development we allow a direct call.
    # This will invoke Streamlit's CLI programmatically.
    import sys

    if "streamlit" in sys.modules:
        # Already running under Streamlit
        main()
    else:
        # Launch Streamlit as a subprocess
        import subprocess

        subprocess.run(
            ["streamlit", "run", __file__],
            check=True,
        )