"""
Pilot Interface for Human Complexity Ratings.

This Streamlit application presents background images from the local archive
to real participants, collects their perceived visual complexity ratings,
and persists them to data/measurements/human_ratings.csv.

Features:
- Captures git commit hash for reproducibility (Constitution Principle VII).
- Links ratings to a specific cohort registered in data/measurements/cohort.json.
- Validates image readability before presentation.
- Prevents duplicate ratings for the same participant/image pair.
"""
import os
import json
import csv
import subprocess
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import streamlit as st
from PIL import Image

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COHORT_FILE = DATA_DIR / "measurements" / "cohort.json"
RATINGS_FILE = DATA_DIR / "measurements" / "human_ratings.csv"
STIMULI_DIR = DATA_DIR / "stimuli" / "raw"

# Ensure output directories exist
def ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def get_git_commit_hash() -> str:
    """Retrieve the current git commit hash for reproducibility."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown_git_hash"

def list_stimuli_images() -> List[Path]:
    """List all valid image files in the stimuli raw directory."""
    if not STIMULI_DIR.exists():
        return []
    valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    images = []
    for f in STIMULI_DIR.iterdir():
        if f.suffix.lower() in valid_extensions:
            images.append(f)
    return sorted(images)

def load_existing_ratings() -> pd.DataFrame:
    """Load existing ratings from the CSV file."""
    if not RATINGS_FILE.exists():
        return pd.DataFrame(columns=["image_id", "participant_id", "complexity_score", "git_commit_hash"])
    return pd.read_csv(RATINGS_FILE)

def load_cohort() -> Dict[str, Any]:
    """Load the cohort metadata."""
    if not COHORT_FILE.exists():
        st.error("Cohort file not found. Please run recruitment first.")
        st.stop()
    with open(COHORT_FILE, "r") as f:
        return json.load(f)

def append_rating(image_id: str, participant_id: str, score: float) -> bool:
    """Append a single rating to the CSV file."""
    ensure_output_dir(RATINGS_FILE)
    git_hash = get_git_commit_hash()
    
    new_row = {
        "image_id": image_id,
        "participant_id": participant_id,
        "complexity_score": score,
        "git_commit_hash": git_hash
    }
    
    # Check for duplicates
    df = load_existing_ratings()
    if not df.empty:
        duplicate = df[
            (df["image_id"] == image_id) & 
            (df["participant_id"] == participant_id)
        ]
        if not duplicate.empty:
            return False
    
    # Append
    new_df = pd.DataFrame([new_row])
    if df.empty:
        new_df.to_csv(RATINGS_FILE, index=False)
    else:
        new_df.to_csv(RATINGS_FILE, mode='a', header=False, index=False)
    return True

def main():
    st.set_page_config(page_title="Visual Complexity Pilot", layout="wide")
    
    # --- Sidebar: Cohort & Session Info ---
    st.sidebar.header("Session Info")
    cohort = load_cohort()
    
    # Extract participant ID from session or ask for it
    if "participant_id" not in st.session_state:
        st.session_state.participant_id = st.sidebar.text_input(
            "Participant ID (from Cohort)", 
            help="Enter the unique ID assigned during recruitment."
        )
        if not st.session_state.participant_id:
            st.warning("Please enter a Participant ID to proceed.")
            st.stop()
        
        # Validate ID exists in cohort
        if "participant_ids" in cohort:
            if st.session_state.participant_id not in cohort["participant_ids"]:
                st.error(f"Participant ID '{st.session_state.participant_id}' not found in cohort.")
                st.stop()
        else:
            st.warning("Cohort does not list participant IDs. Proceeding with validation disabled.")

    git_hash = get_git_commit_hash()
    st.sidebar.markdown(f"**Git Commit:** `{git_hash}`")
    st.sidebar.markdown(f"**Cohort ID:** `{cohort.get('cohort_id', 'N/A')}`")

    # --- Main Content: Image Presentation ---
    st.title("Visual Complexity Rating Task")
    st.markdown("Please rate the perceived visual complexity of the background image below.")
    st.markdown("*Scale: 1 (Very Simple) to 7 (Very Complex)*")

    images = list_stimuli_images()
    if not images:
        st.error("No stimuli images found in data/stimuli/raw/.")
        st.stop()

    existing_ratings = load_existing_ratings()
    current_participant = st.session_state.participant_id
    
    # Filter out images already rated by this participant
    rated_ids = set(
        existing_ratings[existing_ratings["participant_id"] == current_participant]["image_id"]
    )
    remaining_images = [img for img in images if img.stem not in rated_ids]

    if not remaining_images:
        st.success("All images have been rated by this participant.")
        st.balloons()
        st.stop()

    # Display the first remaining image
    current_image_path = remaining_images[0]
    
    try:
        img = Image.open(current_image_path)
        st.image(img, caption=current_image_path.name, use_column_width=True)
    except Exception as e:
        st.error(f"Error loading image {current_image_path.name}: {e}")
        st.stop()

    # Rating Input
    st.subheader("Rating")
    score = st.slider(
        "Perceived Visual Complexity",
        min_value=1,
        max_value=7,
        value=4,
        step=1
    )

    if st.button("Submit Rating"):
        success = append_rating(
            image_id=current_image_path.stem,
            participant_id=current_participant,
            score=float(score)
        )
        
        if success:
            st.success("Rating recorded successfully!")
            # Force reload of remaining images in next render
            st.rerun()
        else:
            st.error("Error: Rating for this image and participant already exists.")

    # Progress Bar
    total_images = len(images)
    rated_count = len(rated_ids)
    progress = rated_count / total_images if total_images > 0 else 0
    st.progress(progress)
    st.caption(f"{rated_count} / {total_images} images rated")

if __name__ == "__main__":
    main()
