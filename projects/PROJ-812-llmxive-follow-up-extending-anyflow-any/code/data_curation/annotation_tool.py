"""
Annotation Tool for Human-in-the-Loop Verification (T008a).

This Streamlit application allows human experts to label video clips as 'continuous'
or 'cut' based solely on pixel frames (blinding protocol). It accepts a score [0.0, 1.0]
and outputs the results to `data/raw/manually_verified_pool.csv`.

Requirements:
- streamlit
- pandas
- opencv-python-headless
- utils (logging, hash_utils)
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import streamlit as st
import pandas as pd
import cv2
import numpy as np
from PIL import Image

# Project imports
from utils.logging import get_logger, setup_module_logger
from utils.hash_utils import compute_sha256, save_checksums

# Initialize logger
logger = setup_module_logger(__name__)

# Configuration
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "manually_verified_pool.csv"
CHECKSUM_FILE = OUTPUT_DIR / "manually_verified_pool.csv.sha256"
SESSION_STATE_KEY = "annotation_state"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_existing_annotations() -> pd.DataFrame:
    """Load existing annotations if the output file exists."""
    if OUTPUT_FILE.exists():
        try:
            df = pd.read_csv(OUTPUT_FILE)
            logger.info(f"Loaded existing annotations from {OUTPUT_FILE}. Rows: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"Failed to load existing annotations: {e}")
            return pd.DataFrame(columns=["video_id", "frame_count", "score", "annotator_id", "timestamp", "checksum"])
    return pd.DataFrame(columns=["video_id", "frame_count", "score", "annotator_id", "timestamp", "checksum"])

def save_annotation(video_id: str, frame_count: int, score: float, annotator_id: str, timestamp: str) -> None:
    """Save a single annotation to the CSV and update checksum."""
    new_row = {
        "video_id": video_id,
        "frame_count": frame_count,
        "score": score,
        "annotator_id": annotator_id,
        "timestamp": timestamp,
        "checksum": ""  # Placeholder, will be updated later
    }

    df = load_existing_annotations()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Re-calculate checksums for the whole file to ensure integrity
    df.to_csv(OUTPUT_FILE, index=False)

    # Generate and save checksum
    file_hash = compute_sha256(OUTPUT_FILE)
    save_checksums(OUTPUT_FILE, file_hash)
    logger.info(f"Annotation saved for {video_id} (Score: {score}). Checksum updated.")

def render_video_frames(video_path: str, num_frames: int = 5) -> List[Image.Image]:
    """
    Extract a representative set of frames from the video for display.
    Uses OpenCV to read frames and PIL for Streamlit rendering.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        logger.warning(f"Video has 0 frames: {video_path}")
        return []

    # Select evenly spaced frames
    indices = np.linspace(0, total_frames - 1, num_frames).astype(int)
    frames = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR (OpenCV) to RGB (PIL)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            frames.append(pil_img)
        else:
            logger.warning(f"Failed to read frame {idx} from {video_path}")

    cap.release()
    return frames

def generate_video_id_from_path(path: str) -> str:
    """Generate a unique ID from the file path and modification time."""
    stat = os.stat(path)
    content = f"{path}_{stat.st_mtime}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]

def main():
    st.set_page_config(page_title="Continuity Annotation Tool", layout="wide")
    st.title("Human-in-the-Loop Video Continuity Annotation")
    st.markdown("""
    **Instructions**:
    1. View the frames below.
    2. Rate the continuity of motion on a scale of **0.0 (Definite Cut)** to **1.0 (Perfectly Continuous)**.
    3. Enter your Annotator ID.
    4. Click 'Submit'.
    """)

    # Sidebar for configuration
    st.sidebar.header("Configuration")
    annotator_id = st.sidebar.text_input("Annotator ID", value="expert_01")
    input_dir = st.sidebar.text_input("Video Directory", value="data/raw/clips")
    video_files = [f for f in os.listdir(input_dir) if f.endswith(('.mp4', '.avi', '.mov'))]

    if not video_files:
        st.warning(f"No video files found in {input_dir}. Please ensure clips are downloaded.")
        return

    # Load existing progress
    df_existing = load_existing_annotations()
    processed_ids = set(df_existing["video_id"].unique())

    # Filter out already processed videos
    pending_videos = [f for f in video_files if generate_video_id_from_path(os.path.join(input_dir, f)) not in processed_ids]

    if not pending_videos:
        st.success("All videos in the directory have been annotated.")
        if st.button("Refresh Status"):
            st.rerun()
        return

    # Select video to annotate
    video_options = {generate_video_id_from_path(os.path.join(input_dir, f)): f for f in pending_videos}
    selected_key = st.selectbox("Select Video to Annotate", list(video_options.keys()))
    selected_filename = video_options[selected_key]
    selected_path = os.path.join(input_dir, selected_filename)

    # Display frames (Blinding: No model metrics)
    st.subheader(f"Video: {selected_filename}")
    frames = render_video_frames(selected_path)

    if not frames:
        st.error("Could not load frames for this video.")
    else:
        cols = st.columns(len(frames))
        for i, col in enumerate(cols):
            with col:
                st.image(frames[i], use_column_width=True)
                st.caption(f"Frame {i+1}")

    # Input form
    st.markdown("---")
    st.subheader("Annotation")
    score = st.slider("Continuity Score (0.0 = Cut, 1.0 = Continuous)", 0.0, 1.0, 0.5, 0.01)

    col1, col2 = st.columns([1, 4])
    with col1:
        submit_btn = st.button("Submit Annotation", type="primary")

    if submit_btn:
        if not annotator_id:
            st.error("Please enter an Annotator ID.")
        else:
            try:
                timestamp = pd.Timestamp.now().isoformat()
                frame_count = int(cv2.VideoCapture(selected_path).get(cv2.CAP_PROP_FRAME_COUNT))
                cv2.VideoCapture(selected_path).release()

                save_annotation(
                    video_id=selected_key,
                    frame_count=frame_count,
                    score=score,
                    annotator_id=annotator_id,
                    timestamp=timestamp
                )
                st.success("Annotation saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving annotation: {e}")
                logger.exception("Annotation submission failed")

    # Footer
    st.markdown("---")
    st.caption(f"Total annotated: {len(processed_ids)} | Pending: {len(pending_videos)}")

if __name__ == "__main__":
    main()
