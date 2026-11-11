"""
Annotation Tool for Human-in-the-Loop Verification (T008a).

This Streamlit application allows human experts to label video clips as 'continuous'
or 'cut' based solely on pixel frames (blinding), accept a score [0.0, 1.0],
and output the results to `data/raw/manually_verified_pool.csv`.

Requirements:
- streamlit
- pandas
- opencv-python-headless
- pillow
- utils (logging, hash_utils)
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import cv2
import numpy as np
from PIL import Image

# Project imports
from utils.logging import setup_module_logger
from utils.hash_utils import compute_sha256

# Initialize logger for this module
logger = setup_module_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
OUTPUT_DIR: Path = Path("data/raw")
OUTPUT_FILE: Path = OUTPUT_DIR / "manually_verified_pool.csv"
CHECKSUM_FILE: Path = OUTPUT_DIR / "manually_verified_pool.csv.sha256"
SESSION_STATE_KEY = "annotation_state"

# Ensure the output directory exists at import time
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_existing_annotations() -> pd.DataFrame:
    """
    Load existing annotations if the CSV already exists.
    Returns a DataFrame with the expected columns. If the file does not exist
    or cannot be read, an empty DataFrame with the correct schema is returned.
    """
    if OUTPUT_FILE.exists():
        try:
            df = pd.read_csv(OUTPUT_FILE)
            logger.info(f"Loaded {len(df)} existing annotations from {OUTPUT_FILE}")
            return df
        except Exception as e:
            logger.error(f"Failed to read existing annotations: {e}")
    # Return an empty DataFrame with the required schema
    columns = ["video_id", "frame_count", "score", "annotator_id", "timestamp", "checksum"]
    return pd.DataFrame(columns=columns)

def _write_checksum(file_path: Path) -> None:
    """
    Compute the SHA‑256 checksum of ``file_path`` and write it to ``CHECKSUM_FILE``.
    The checksum file contains only the hex digest (compatible with typical
    ``sha256sum`` output).
    """
    try:
        checksum = compute_sha256(file_path)
        CHECKSUM_FILE.write_text(f"{checksum}  {file_path.name}\n")
        logger.info(f"Checksum written to {CHECKSUM_FILE}")
    except Exception as e:
        logger.error(f"Unable to write checksum for {file_path}: {e}")

def save_annotation(
    video_id: str,
    frame_count: int,
    score: float,
    annotator_id: str,
    timestamp: str,
) -> None:
    """
    Append a new annotation row to the CSV and update the checksum file.
    """
    new_row = {
        "video_id": video_id,
        "frame_count": frame_count,
        "score": score,
        "annotator_id": annotator_id,
        "timestamp": timestamp,
        "checksum": "",  # will be filled after file write
    }

    df = load_existing_annotations()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Write CSV
    df.to_csv(OUTPUT_FILE, index=False)

    # Update checksum file for the whole CSV (ensures integrity)
    _write_checksum(OUTPUT_FILE)

    logger.info(f"Saved annotation for video_id={video_id}, score={score}")

def render_video_frames(video_path: str, num_frames: int = 5) -> List[Image.Image]:
    """
    Extract ``num_frames`` evenly spaced frames from ``video_path``.
    Returns a list of Pillow ``Image`` objects suitable for Streamlit display.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Unable to open video file: {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        logger.warning(f"Video has zero frames: {video_path}")
        cap.release()
        return []

    # Choose evenly spaced frame indices
    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames: List[Image.Image] = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            # Convert BGR (OpenCV) to RGB (Pillow)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            frames.append(pil_img)
        else:
            logger.warning(f"Failed to read frame {idx} from {video_path}")

    cap.release()
    return frames

def generate_video_id_from_path(path: str) -> str:
    """
    Generate a deterministic short identifier for a video based on its absolute
    path and modification timestamp. The identifier is the first 12 hex digits
    of the SHA‑256 hash.
    """
    stat = os.stat(path)
    content = f"{path}_{stat.st_mtime}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]

# ----------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Continuity Annotation Tool", layout="wide")
    st.title("Human‑in‑the‑Loop Video Continuity Annotation")
    st.markdown(
        """
        **Instructions**
        1. Browse the video clips in the selected directory.
        2. Examine the displayed frames (no model metrics are shown).
        3. Use the slider to assign a continuity score:
           *0.0 = Definite cut* → *1.0 = Perfectly continuous*.
        4. Enter your annotator ID.
        5. Click **Submit Annotation**.
        """
    )

    # ------------------------------------------------------------------
    # Sidebar configuration
    # ------------------------------------------------------------------
    annotator_id = st.sidebar.text_input("Annotator ID", value="expert_01")
    input_dir = st.sidebar.text_input("Video Directory", value="data/raw/clips")
    video_files = [
        f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))
    ]

    if not video_files:
        st.warning(f"No video files found in `{input_dir}`.")
        return

    # ------------------------------------------------------------------
    # Load progress and determine pending videos
    # ------------------------------------------------------------------
    existing_df = load_existing_annotations()
    processed_ids = set(existing_df["video_id"].unique())

    pending_videos = [
        f
        for f in video_files
        if generate_video_id_from_path(os.path.join(input_dir, f)) not in processed_ids
    ]

    if not pending_videos:
        st.success("All videos in the directory have been annotated.")
        if st.button("Refresh"):
            st.rerun()
        return

    # Mapping from generated video_id -> filename for the pending set
    video_map: Dict[str, str] = {
        generate_video_id_from_path(os.path.join(input_dir, fname)): fname
        for fname in pending_videos
    }

    selected_vid = st.selectbox("Select a video to annotate", list(video_map.keys()))
    selected_filename = video_map[selected_vid]
    selected_path = os.path.join(input_dir, selected_filename)

    # ------------------------------------------------------------------
    # Display frames (blinded UI)
    # ------------------------------------------------------------------
    st.subheader(f"Video: {selected_filename}")
    frames = render_video_frames(selected_path)

    if not frames:
        st.error("Unable to extract frames from the selected video.")
    else:
        cols = st.columns(len(frames))
        for idx, col in enumerate(cols):
            with col:
                st.image(frames[idx], use_column_width=True)
                st.caption(f"Frame {idx + 1}")

    # ------------------------------------------------------------------
    # Annotation input
    # ------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Your Annotation")
    score = st.slider(
        "Continuity Score (0.0 = Cut, 1.0 = Continuous)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
    )

    submit = st.button("Submit Annotation", type="primary")

    if submit:
        if not annotator_id:
            st.error("Please provide an Annotator ID.")
        else:
            try:
                # Capture frame count for provenance
                cap = cv2.VideoCapture(selected_path)
                frame_cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()

                timestamp = pd.Timestamp.now().isoformat()
                save_annotation(
                    video_id=selected_vid,
                    frame_count=frame_cnt,
                    score=score,
                    annotator_id=annotator_id,
                    timestamp=timestamp,
                )
                st.success("Annotation saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save annotation: {e}")
                logger.exception("Error during annotation saving")

    # ------------------------------------------------------------------
    # Footer status
    # ------------------------------------------------------------------
    st.markdown("---")
    st.caption(
        f"Annotated: {len(processed_ids)} | Remaining: {len(pending_videos)}"
    )

if __name__ == "__main__":
    main()
