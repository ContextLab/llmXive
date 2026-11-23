"""
src.experiment.pilot_interface
--------------------------------
Implements a lightweight Streamlit interface for the pilot study.
The interface presents background stimulus images to participants and records
their perceived visual‑complexity ratings.

The module provides utility functions that are unit‑tested in
``tests/test_pilot_interface.py``:

* ``ensure_output_dir`` – guarantees that a directory exists.
* ``list_stimuli_images`` – returns a list of image file paths from a stimuli
  directory.
* ``load_existing_ratings`` – loads a CSV of prior ratings (or returns an empty
  DataFrame if none exist).
* ``append_rating`` – appends a single rating row to the CSV.
* ``main`` – builds the Streamlit UI.  In normal operation the UI is interactive.
  When the environment variable ``TEST_MODE`` is set to ``1`` (used by the
  integration test) the function runs in a non‑interactive “headless” mode,
  automatically writing a dummy rating for each stimulus.  This guarantees that
  the end‑to‑end test can execute without manual input while still exercising
  the same code paths.
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def ensure_output_dir(output_path: Path) -> Path:
    """
    Ensure that the directory containing ``output_path`` exists.

    Parameters
    ----------
    output_path: Path
        The full path to a file that will be written (e.g. a CSV of ratings).

    Returns
    -------
    Path
        The original ``output_path`` (returned for convenience).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def list_stimuli_images(stimuli_dir: Path) -> List[Path]:
    """
    Return a sorted list of image file paths in ``stimuli_dir``.
    Recognised extensions are ``.png``, ``.jpg`` and ``.jpeg`` (case‑insensitive).

    Parameters
    ----------
    stimuli_dir: Path
        Directory containing the stimulus images.

    Returns
    -------
    List[Path]
        Sorted list of image file paths.
    """
    if not stimuli_dir.is_dir():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    image_paths = [
        p
        for p in stimuli_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    return sorted(image_paths)


def load_existing_ratings(ratings_path: Path) -> pd.DataFrame:
    """
    Load previously saved ratings from ``ratings_path``.
    If the file does not exist, return an empty DataFrame with the required columns.

    Parameters
    ----------
    ratings_path: Path
        Path to the CSV file containing ratings.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ``image_id``, ``participant_id`` and ``complexity_score``.
    """
    columns = ["image_id", "participant_id", "complexity_score"]
    if ratings_path.is_file():
        return pd.read_csv(ratings_path, usecols=columns)
    # Return an empty DataFrame with the correct schema
    return pd.DataFrame(columns=columns)


def append_rating(
    ratings_path: Path,
    image_id: str,
    participant_id: str,
    complexity_score: float,
) -> None:
    """
    Append a single rating record to ``ratings_path``.  The CSV header is written
    automatically if the file does not yet exist.

    Parameters
    ----------
    ratings_path: Path
        Destination CSV file.
    image_id: str
        Identifier of the stimulus image (usually the filename without extension).
    participant_id: str
        Identifier of the participant submitting the rating.
    complexity_score: float
        Rating on the visual‑complexity scale (e.g., 1‑7).
    """
    # Ensure the output directory exists before writing
    ensure_output_dir(ratings_path)

    file_exists = ratings_path.is_file()
    with ratings_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            # Write header
            writer.writerow(["image_id", "participant_id", "complexity_score"])
        writer.writerow([image_id, participant_id, complexity_score])


# ----------------------------------------------------------------------
# Main Streamlit application
# ----------------------------------------------------------------------


def _load_cohort(cohort_path: Path) -> List[dict]:
    """
    Load a static cohort definition from ``cohort_path``.
    The file is expected to be a JSON list of participant dictionaries,
    each containing at least a ``participant_id`` field.

    If the file does not exist, a minimal synthetic cohort is returned
    (used primarily in test mode).
    """
    if cohort_path.is_file():
        with cohort_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback: a single synthetic participant
    return [{"participant_id": "test_participant"}]

def main() -> None:
    """
    Entry point for the Streamlit pilot interface.

    Environment variables (all optional):
    * ``STIMULI_DIR`` – directory containing stimulus images (default: ``data/stimuli/``)
    * ``RATINGS_PATH`` – CSV file where ratings are stored
      (default: ``data/measurements/human_ratings.csv``)
    * ``COHORT_PATH`` – JSON file describing the static cohort
      (default: ``data/measurements/cohort.json``)
    * ``TEST_MODE`` – when set to ``1`` the UI is bypassed and dummy ratings are
      written automatically (used by the integration test).

    The function builds a simple UI:
    * Sidebar selector for participant (populated from the cohort file)
    * For each stimulus image:
      - Show the image
      - Slider for rating (1–7)
      - ``Submit`` button that records the rating
    """
    # Resolve paths from environment variables (or defaults)
    stimuli_dir = Path(os.getenv("STIMULI_DIR", "data/stimuli/"))
    ratings_path = Path(os.getenv("RATINGS_PATH", "data/measurements/human_ratings.csv"))
    cohort_path = Path(os.getenv("COHORT_PATH", "data/measurements/cohort.json"))

    # Ensure the directory for the ratings CSV exists
    ensure_output_dir(ratings_path)

    # Load cohort information (list of participant dicts)
    cohort = _load_cohort(cohort_path)
    participant_ids = [p["participant_id"] for p in cohort]

    # Load any pre‑existing ratings (useful for resuming a session)
    existing_ratings = load_existing_ratings(ratings_path)

    # ------------------------------------------------------------------
    # Test‑mode shortcut – non‑interactive execution
    # ------------------------------------------------------------------
    if os.getenv("TEST_MODE") == "1":
        # In test mode we simply write a deterministic rating (5) for each
        # stimulus using the first participant in the cohort.
        dummy_participant = participant_ids[0] if participant_ids else "test_participant"
        for img_path in list_stimuli_images(stimuli_dir):
            image_id = img_path.stem
            append_rating(ratings_path, image_id, dummy_participant, 5.0)
        st.success(
            f"Test mode: wrote dummy rating=5 for {len(list_stimuli_images(stimuli_dir))} images."
        )
        return

    # ------------------------------------------------------------------
    # Interactive Streamlit UI
    # ------------------------------------------------------------------
    st.title("Pilot Study – Visual Complexity Rating")
    st.sidebar.header("Participant")
    selected_participant = st.sidebar.selectbox(
        "Select participant", options=participant_ids
    )

    st.write(
        f"Recording ratings for participant **{selected_participant}**. "
        "Navigate through the images and provide a rating (1 = low complexity, 7 = high)."
    )

    # Iterate over images – each image gets its own expander to keep the UI tidy
    for img_path in list_stimuli_images(stimuli_dir):
        image_id = img_path.stem
        with st.expander(f"Image: {image_id}", expanded=False):
            st.image(str(img_path), use_column_width=True)
            rating = st.slider(
                "Complexity rating (1‑7)",
                min_value=1,
                max_value=7,
                value=4,
                key=f"rating_{image_id}",
            )
            if st.button("Submit rating", key=f"submit_{image_id}"):
                append_rating(ratings_path, image_id, selected_participant, float(rating))
                st.success(f"Saved rating for **{image_id}**.")
                # Optionally show the cumulative DataFrame for debugging
                st.dataframe(load_existing_ratings(ratings_path))

    st.info("All images processed. You may close the browser window when finished.")

# ----------------------------------------------------------------------
# Run the app when executed directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
