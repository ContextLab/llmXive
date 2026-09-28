"""
src/experiment/pilot_interface.py

Streamlit interface for the local pilot study.

The module provides a small Streamlit app that iterates over a directory of
stimulus images, presents each image to the participant, and records a
perceived visual‑complexity rating.  Ratings are persisted to a CSV file
under ``data/measurements/human_ratings.csv``.  The helper functions are
deliberately small and test‑able without launching Streamlit, allowing the
unit‑ and integration‑tests in ``tests/test_pilot_interface.py`` to verify
behaviour.

Functions
----------
* ``ensure_output_dir()`` – creates the directory that will hold the ratings
  CSV (``data/measurements``) and returns the ``Path``.
* ``list_stimuli_images(stimuli_dir)`` – returns a sorted list of image
  ``Path`` objects (PNG/JPG/JPEG) found in ``stimuli_dir``.
* ``load_existing_ratings(ratings_path)`` – loads the CSV if it exists,
  otherwise returns an empty ``pandas.DataFrame`` with the required columns.
* ``append_rating(ratings_path, image_id, participant_id, score)`` – appends a
  single rating row to the CSV, creating the file with a header if necessary.
* ``main()`` – Streamlit entry‑point that wires the above helpers together.
"""

import csv
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Configuration constants (project‑relative)
# ----------------------------------------------------------------------
RATINGS_DIR = Path("data/measurements")
RATINGS_FILE = RATINGS_DIR / "human_ratings.csv"
DEFAULT_STIMULI_DIR = Path("data/stimuli/raw")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def ensure_output_dir() -> Path:
    """
    Ensure that the directory for storing human rating CSV files exists.

    Returns
    -------
    Path
        The absolute path to the ratings directory.
    """
    RATINGS_DIR.mkdir(parents=True, exist_ok=True)
    return RATINGS_DIR


def list_stimuli_images(stimuli_dir: Path) -> List[Path]:
    """
    List all image files in ``stimuli_dir`` that match known image extensions.

    Parameters
    ----------
    stimuli_dir : Path
        Directory containing stimulus images.

    Returns
    -------
    List[Path]
        Sorted list of image file paths.
    """
    if not stimuli_dir.is_dir():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    images = [
        p
        for p in stimuli_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    # Sort for deterministic ordering (important for tests)
    images.sort()
    return images


def load_existing_ratings(ratings_path: Path) -> pd.DataFrame:
    """
    Load existing human ratings from ``ratings_path`` if the file exists.

    Parameters
    ----------
    ratings_path : Path
        Path to the CSV file containing previously collected ratings.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ``image_id``, ``participant_id``, ``complexity_score``.
        Returns an empty DataFrame with those columns if the file does not exist.
    """
    if ratings_path.is_file():
        df = pd.read_csv(ratings_path)
    else:
        df = pd.DataFrame(
            columns=["image_id", "participant_id", "complexity_score"]
        )
    return df


def append_rating(
    ratings_path: Path,
    image_id: str,
    participant_id: str,
    score: int,
) -> None:
    """
    Append a single rating row to the CSV file.

    The function creates the file (with a header) if it does not already exist.

    Parameters
    ----------
    ratings_path : Path
        Destination CSV file.
    image_id : str
        Identifier of the stimulus image (typically the filename stem).
    participant_id : str
        Identifier for the participant (e.g., a UUID or short string).
    score : int
        Complexity rating supplied by the participant.
    """
    # Ensure the parent directory exists
    ratings_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = ratings_path.is_file()
    with ratings_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            # Write header
            writer.writerow(["image_id", "participant_id", "complexity_score"])
        writer.writerow([image_id, participant_id, score])


# ----------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------


def main() -> None:
    """
    Streamlit entry point for the pilot interface.

    The UI walks the participant through each stimulus image, asks for a
    rating via a slider (1‑10), and records the response.  The participant
    identifier is collected once at the top of the session.
    """
    st.title("Visual Complexity Pilot Study")
    st.write(
        """
        This short study asks you to rate the visual complexity of each background
        image. Please provide a unique participant ID (e.g., your initials or a short
        code) so that your responses can be linked together.
        """
    )

    # ------------------------------------------------------------------
    # Participant ID
    # ------------------------------------------------------------------
    participant_id = st.text_input("Participant ID", value="", max_chars=20)
    if not participant_id:
        st.warning("Please enter a participant ID to begin.")
        st.stop()

    # ------------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------------
    ensure_output_dir()
    stimuli_dir = DEFAULT_STIMULI_DIR
    try:
        images = list_stimuli_images(stimuli_dir)
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    if not images:
        st.error(f"No stimulus images found in `{stimuli_dir}`.")
        st.stop()

    # Session state for navigation
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    idx = st.session_state.current_idx
    current_image_path = images[idx]

    # ------------------------------------------------------------------
    # Display current image and collect rating
    # ------------------------------------------------------------------
    st.subheader(f"Image {idx + 1} of {len(images)}")
    st.image(str(current_image_path), use_column_width=True)

    rating = st.slider(
        "Rate the visual complexity (1 = very simple, 10 = very complex)",
        min_value=1,
        max_value=10,
        value=5,
    )

    if st.button("Submit rating"):
        # Record the rating
        image_id = current_image_path.stem
        append_rating(RATINGS_FILE, image_id, participant_id, rating)

        # Move to next image
        if idx + 1 < len(images):
            st.session_state.current_idx = idx + 1
            st.experimental_rerun()
        else:
            st.success("Thank you! You have completed all ratings.")
            st.balloons()
            # Reset index for a possible new participant
            st.session_state.current_idx = 0

    # ------------------------------------------------------------------
    # Debug / progress information (optional, can be hidden)
    # ------------------------------------------------------------------
    if st.checkbox("Show progress (debug)"):
        df = load_existing_ratings(RATINGS_FILE)
        st.write("Current ratings file preview:")
        st.dataframe(df)


if __name__ == "__main__":
    # Allow running the script directly (`python pilot_interface.py`)
    main()