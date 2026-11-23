"""
Pilot Annotation Tool for Dual-Annotator Calibration.

This Streamlit application collects dual-annotator scores for the pilot subset
defined in data/raw/pilot_subset_ids.csv (N=50).

STRICT BLINDING: The UI displays ONLY pixel frames. No model metrics, no
divergence scores, and no external hints are shown to the annotator.

Output: data/raw/calibration_scores.csv with columns:
video_id, annotator_id, score
"""
import os
import csv
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Project imports
from utils.logging import get_logger
from utils.memory_utils import clear_memory
from data_curation.annotation_tool import render_video_frames, generate_video_id_from_path

logger = get_logger(__name__)

# Constants
PILOT_SUBSET_FILE = Path("data/raw/pilot_subset_ids.csv")
OUTPUT_FILE = Path("data/raw/calibration_scores.csv")
CLIPS_DIR = Path("data/raw/clips")
ANNOTATOR_ID = "annotator_01"  # Default for this pilot run; can be overridden by session state or config
TOTAL_PILOT_SIZE = 50

# Ensure output directory exists
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
PILOT_SUBSET_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_pilot_subset() -> List[Dict[str, Any]]:
    """
    Load the pilot subset IDs from the CSV file.
    Expects columns: video_id, file_path (relative to data/raw/clips)
    """
    if not PILOT_SUBSET_FILE.exists():
        st.error(f"Pilot subset file not found: {PILOT_SUBSET_FILE}. Please run T009 first.")
        logger.error(f"Pilot subset file not found: {PILOT_SUBSET_FILE}")
        st.stop()

    clips = []
    with open(PILOT_SUBSET_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate required fields
            if "video_id" not in row or "file_path" not in row:
                logger.warning(f"Skipping row in pilot subset due to missing fields: {row}")
                continue
            clips.append(row)

    if not clips:
        st.error("Pilot subset is empty. Please ensure data/raw/pilot_subset_ids.csv has valid entries.")
        logger.error("Pilot subset is empty.")
        st.stop()

    logger.info(f"Loaded {len(clips)} clips for pilot annotation.")
    return clips

def load_existing_scores() -> Dict[str, float]:
    """
    Load existing calibration scores to resume annotation progress.
    Returns a dict mapping video_id -> score (if already annotated by current annotator).
    """
    if not OUTPUT_FILE.exists():
        return {}

    scores = {}
    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only load scores for the current annotator to allow multiple annotators
            if row.get("annotator_id") == ANNOTATOR_ID:
                scores[row["video_id"]] = float(row["score"])

    logger.info(f"Loaded existing scores for {len(scores)} clips from {OUTPUT_FILE}.")
    return scores

def save_score(video_id: str, score: float) -> None:
    """
    Append a new score to the calibration_scores.csv file.
    """
    file_exists = OUTPUT_FILE.exists()

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["video_id", "annotator_id", "score"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "video_id": video_id,
            "annotator_id": ANNOTATOR_ID,
            "score": score
        })

    logger.info(f"Saved score {score} for video {video_id} by {ANNOTATOR_ID}.")
    clear_memory()

def render_single_frame(video_path: Path, frame_idx: int = 0) -> Optional[Image.Image]:
    """
    Render a single frame from the video at the given index.
    Returns a PIL Image.
    """
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return None

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return None

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.warning(f"Failed to read frame {frame_idx} from {video_path}")
        return None

    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)

def main():
    st.set_page_config(page_title="Pilot Annotation Tool", layout="wide")
    st.title("Pilot Annotation: Dual-Annotator Calibration")
    st.markdown(
        "**Instructions**: Rate the continuity of the video clip on a scale from **0.0 to 1.0**.\n"
        "- **0.0**: Completely continuous motion (no cuts).\n"
        "- **1.0**: Complete discontinuity (hard cut or scene jump).\n"
        "- **0.5**: Ambiguous or moderate discontinuity.\n\n"
        "**BLINDING PROTOCOL**: You will see ONLY the pixel frames. No model scores or metrics are displayed."
    )

    # Initialize session state
    if "clip_index" not in st.session_state:
        st.session_state.clip_index = 0
    if "scores" not in st.session_state:
        st.session_state.scores = load_existing_scores()

    clips = load_pilot_subset()
    existing_count = len(st.session_state.scores)

    # Progress bar
    progress = existing_count / TOTAL_PILOT_SIZE
    st.progress(progress)
    st.write(f"Progress: {existing_count} / {TOTAL_PILOT_SIZE} clips annotated.")

    if existing_count >= len(clips):
        st.success("All clips in the pilot subset have been annotated by this annotator.")
        st.balloons()
        st.stop()

    current_clip = clips[st.session_state.clip_index]
    video_id = current_clip["video_id"]
    file_path = current_clip["file_path"]
    full_path = CLIPS_DIR / file_path

    if not full_path.exists():
        st.error(f"Video file not found at expected path: {full_path}")
        logger.error(f"Video file not found: {full_path}")
        # Skip this clip and move to next
        if st.button("Skip and Next"):
            st.session_state.clip_index += 1
            st.rerun()
        st.stop()

    # Display the video frame (BLINDING: No extra info)
    st.subheader(f"Video ID: {video_id}")
    st.caption(f"File: {file_path}")

    frame_img = render_single_frame(full_path, frame_idx=0)  # Show first frame for speed
    if frame_img:
        st.image(frame_img, caption="Visual Inspection Only", use_container_width=True)
    else:
        st.warning("Could not render video frame.")

    # Input for score
    st.markdown("### Annotation")
    score = st.slider(
        "Continuity Score (0.0 = Continuous, 1.0 = Discontinuous)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
        help="Rate based solely on visual inspection of the frames."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Score"):
            save_score(video_id, score)
            st.session_state.scores[video_id] = score
            st.session_state.clip_index += 1
            st.rerun()

    with col2:
        if st.button("Skip Clip"):
            st.session_state.clip_index += 1
            st.rerun()

    # Navigation
    st.divider()
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.session_state.clip_index > 0:
            if st.button("Previous"):
                st.session_state.clip_index -= 1
                st.rerun()
        else:
            st.button("Previous", disabled=True)

    with col_nav2:
        if st.session_state.clip_index < len(clips) - 1:
            if st.button("Next"):
                st.session_state.clip_index += 1
                st.rerun()
        else:
            st.button("Next", disabled=True)

    logger.info(f"Session ended at clip index {st.session_state.clip_index}")

if __name__ == "__main__":
    main()