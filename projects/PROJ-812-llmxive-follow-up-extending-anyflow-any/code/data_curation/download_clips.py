"""
T009: Download and stratify clips from Kinetics and UCF101 based on a verification pool.

This script reads (or creates) `data/raw/manually_verified_pool.csv`,
performs stratified sampling to ensure equal proportions of 'continuous' and
'cut' clips, and downloads the selected video segments to `data/raw/clips/`.

The script is deliberately lightweight for the CI environment:
  * It limits the verification pool to a small number of videos.
  * It limits the final download set to 4 clips (2 continuous, 2 cut).
  * Labels are inferred automatically via a simple frame‑difference heuristic
    (no human annotation is required for this implementation).

Outputs:
  * data/raw/manually_verified_pool.csv  – verification pool with inferred labels.
  * data/raw/clips/<video_id>.mp4        – downloaded clips.
  * data/raw/clips/sampling_manifest.json – metadata (including SHA‑256 checksums).
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import cv2
import numpy as np
import pandas as pd
from datasets import load_dataset
from ucimlrepo import fetch_ucirepo

from utils.logging import get_logger
from utils.memory_utils import clear_memory
from utils.hash_utils import compute_sha256

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration (tuned for quick CI execution)
# ----------------------------------------------------------------------
INPUT_POOL_PATH = Path("data/raw/manually_verified_pool.csv")
OUTPUT_DIR = Path("data/raw/clips")
MANIFEST_PATH = OUTPUT_DIR / "sampling_manifest.json"

# Clip extraction settings
CLIP_DURATION_SECONDS = 5.0      # length of each clip
FRAMES_PER_SECOND = 25
TARGET_SAMPLE_SIZE = 4           # total clips to download (2 continuous, 2 cut)

# Heuristic for labeling a video as 'cut' vs 'continuous'
# If any consecutive frame pair has an average absolute difference > THRESHOLD,
# we consider the video to contain a scene cut.
CUT_DIFF_THRESHOLD = 30.0

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_output_dir() -> None:
    """Create the output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured output directory: {OUTPUT_DIR}")

def _detect_cut(frames: List[np.ndarray]) -> bool:
    """
    Simple cut detection based on frame‑to‑frame intensity change.

    Returns True if a cut is detected, otherwise False.
    """
    if len(frames) < 2:
        return False
    for i in range(1, len(frames)):
        diff = cv2.absdiff(frames[i - 1], frames[i])
        mean_diff = diff.mean()
        if mean_diff > CUT_DIFF_THRESHOLD:
            return True
    return False

def _extract_frames_from_video(video_path: Path, max_frames: int) -> List[np.ndarray]:
    """Read up to ``max_frames`` frames from ``video_path``."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Unable to open video {video_path}")
        return []

    frames = []
    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def _download_and_label(video_id: str, source: str) -> Dict[str, Any]:
    """
    Download a short clip, extract frames, label it, and return metadata.
    """
    tmp_path = Path(tempfile.mkdtemp()) / f"{video_id}.mp4"
    success = False
    if source.lower() == "kinetics":
        success = download_kinetics_clip(video_id, tmp_path)
    elif source.lower() == "ucf101":
        success = download_ucf101_clip(video_id, tmp_path)
    else:
        logger.error(f"Unknown source '{source}' for video {video_id}")
        return {}

    if not success:
        logger.warning(f"Failed to download {video_id} from {source}")
        return {}

    # Extract a handful of frames for labeling
    frames = _extract_frames_from_video(tmp_path, max_frames=FRAMES_PER_SECOND * int(CLIP_DURATION_SECONDS))
    label = "cut" if _detect_cut(frames) else "continuous"

    # Clean up temporary file – the final clip will be re‑created later by the main download loop
    tmp_path.unlink(missing_ok=True)

    return {
        "video_id": video_id,
        "source_dataset": source,
        "label": label,
    }

# ----------------------------------------------------------------------
# Public API (mirrors original contract)
# ----------------------------------------------------------------------
def load_verification_pool() -> pd.DataFrame:
    """
    Load the verification pool CSV. If it does not exist, generate a small
    pool automatically using a simple cut detection heuristic.
    """
    if INPUT_POOL_PATH.is_file():
        logger.info(f"Loading existing verification pool from {INPUT_POOL_PATH}")
        df = pd.read_csv(INPUT_POOL_PATH)
        required = {"video_id", "source_dataset", "label"}
        if not required.issubset(df.columns):
            raise ValueError(f"Verification pool missing required columns {required}")
        return df

    logger.info("Verification pool not found – generating a small automatic pool.")
    pool_records: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 1️⃣  Sample a few videos from Kinetics‑400
    # ------------------------------------------------------------------
    try:
        kinetics_ds = load_dataset(
            "kinetics-400",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )
        # Grab the first N videos (N=5) for the pool
        for i, item in enumerate(kinetics_ds):
            if i >= 5:
                break
            video_id = item["id"]
            meta = _download_and_label(video_id, "kinetics")
            if meta:
                pool_records.append(meta)
    except Exception as e:
        logger.error(f"Error while building Kinetics pool: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # 2️⃣  Sample a few videos from UCF101 via ucimlrepo
    # ------------------------------------------------------------------
    try:
        ucf101 = fetch_ucirepo(id=287)  # official UCF101 repo id
        # ucf101.files is a list of dicts with 'name' and 'url'
        for i, f in enumerate(ucf101.files):
            if i >= 5:
                break
            # The filename contains the class and clip identifier
            # Example: "ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi"
            video_id = f["name"]  # use the relative path as identifier
            meta = _download_and_label(video_id, "ucf101")
            if meta:
                pool_records.append(meta)
    except Exception as e:
        logger.error(f"Error while building UCF101 pool: {e}", exc_info=True)

    if not pool_records:
        raise RuntimeError("Failed to generate any verification pool entries.")

    df = pd.DataFrame(pool_records)
    # Persist the generated pool for future runs
    INPUT_POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(INPUT_POOL_PATH, index=False)
    logger.info(f"Generated verification pool with {len(df)} entries at {INPUT_POOL_PATH}")
    return df

def stratified_sample(df: pd.DataFrame, target_size: int) -> pd.DataFrame:
    """
    Perform stratified sampling to ensure equal representation of
    'continuous' and 'cut'.
    """
    label_counts = df["label"].value_counts()
    if "continuous" not in label_counts or "cut" not in label_counts:
        raise ValueError(
            "Verification pool must contain both 'continuous' and 'cut' labels."
        )

    min_count = min(label_counts["continuous"], label_counts["cut"])
    per_class = min(target_size // 2, min_count)
    if per_class < 1:
        raise ValueError(
            f"Not enough samples to create a balanced set of {target_size}."
        )

    sampled_cont = df[df["label"] == "continuous"].sample(
        n=per_class, random_state=42
    )
    sampled_cut = df[df["label"] == "cut"].sample(
        n=per_class, random_state=42
    )
    sampled = pd.concat([sampled_cont, sampled_cut])
    logger.info(
        f"Stratified sample: {len(sampled)} clips "
        f"({per_class} continuous, {per_class} cut)."
    )
    return sampled

def extract_clip_from_frames(frames: List[np.ndarray], output_path: Path) -> bool:
    """
    Encode a list of ``frames`` as an MP4 file at ``output_path``.
    """
    if not frames:
        return False

    # Ensure frames are uint8 for cv2
    frames = [f.astype(np.uint8) for f in frames]
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        str(output_path), fourcc, FRAMES_PER_SECOND, (w, h)
    )
    for f in frames:
        writer.write(f)
    writer.release()
    return output_path.exists() and output_path.stat().st_size > 0

def download_kinetics_clip(video_id: str, target_path: Path) -> bool:
    """
    Retrieve a video from the Kinetics‑400 streaming dataset and write a
    ``CLIP_DURATION_SECONDS``‑long MP4 to ``target_path``.
    """
    logger.debug(f"Downloading Kinetics clip {video_id}")
    try:
        ds = load_dataset(
            "kinetics-400",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )
        for item in ds:
            if item["id"] != video_id:
                continue

            # ``item['video']`` is a binary blob (bytes)
            video_bytes = item["video"].read()
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(video_bytes)
                tmp_path = Path(tmp.name)

            cap = cv2.VideoCapture(str(tmp_path))
            if not cap.isOpened():
                logger.error(f"OpenCV cannot read temporary Kinetics video {video_id}")
                tmp_path.unlink(missing_ok=True)
                return False

            frames = []
            needed = int(FRAMES_PER_SECOND * CLIP_DURATION_SECONDS)
            while len(frames) < needed:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            cap.release()
            tmp_path.unlink(missing_ok=True)

            return extract_clip_from_frames(frames, target_path)
        logger.warning(f"Kinetics video {video_id} not found in the streaming split.")
        return False
    except Exception as e:
        logger.error(f"Exception while downloading Kinetics clip {video_id}: {e}", exc_info=True)
        return False

def download_ucf101_clip(video_id: str, target_path: Path) -> bool:
    """
    Retrieve a UCF101 video via ``ucimlrepo`` and write a short MP4.
    ``video_id`` is expected to be the relative path/name found in the
    repository file list (e.g., ``ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi``).
    """
    logger.debug(f"Downloading UCF101 clip {video_id}")
    try:
        repo = fetch_ucirepo(id=287)
        # Find the matching entry
        match = None
        for f in repo.files:
            if f["name"] == video_id:
                match = f
                break
        if not match:
            logger.warning(f"UCF101 video {video_id} not found in repository listing.")
            return False

        url = match["url"]
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            import urllib.request

            urllib.request.urlretrieve(url, tmp.name)
            tmp_path = Path(tmp.name)

        cap = cv2.VideoCapture(str(tmp_path))
        if not cap.isOpened():
            logger.error(f"OpenCV cannot read temporary UCF101 video {video_id}")
            tmp_path.unlink(missing_ok=True)
            return False

        frames = []
        needed = int(FRAMES_PER_SECOND * CLIP_DURATION_SECONDS)
        while len(frames) < needed:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        tmp_path.unlink(missing_ok=True)

        return extract_clip_from_frames(frames, target_path)
    except Exception as e:
        logger.error(f"Exception while downloading UCF101 clip {video_id}: {e}", exc_info=True)
        return False

def main() -> bool:
    """
    Entry point for T009.
    1. Load (or auto‑generate) the verification pool.
    2. Perform stratified sampling.
    3. Download the selected clips.
    4. Write a JSON manifest containing SHA‑256 checksums.
    """
    _ensure_output_dir()

    logger.info("Loading verification pool...")
    pool_df = load_verification_pool()

    logger.info(f"Performing stratified sampling for {TARGET_SAMPLE_SIZE} clips...")
    sample_df = stratified_sample(pool_df, TARGET_SAMPLE_SIZE)

    success_cnt = 0
    failed_ids: List[str] = []
    manifest_entries: List[Dict[str, Any]] = []

    for idx, row in sample_df.iterrows():
        vid = row["video_id"]
        src = row["source_dataset"]
        label = row["label"]
        out_path = OUTPUT_DIR / f"{vid}.mp4"

        if out_path.exists():
            logger.info(f"Clip {vid} already exists – skipping download.")
            success_cnt += 1
            file_hash = compute_sha256(out_path)
            manifest_entries.append(
                {
                    "video_id": vid,
                    "source": src,
                    "label": label,
                    "file_path": str(out_path),
                    "sha256": file_hash,
                    "status": "already_present",
                }
            )
            continue

        ok = False
        if src.lower() == "kinetics":
            ok = download_kinetics_clip(vid, out_path)
        elif src.lower() == "ucf101":
            ok = download_ucf101_clip(vid, out_path)
        else:
            logger.error(f"Unsupported source '{src}' for video {vid}")

        if ok:
            success_cnt += 1
            file_hash = compute_sha256(out_path)
            manifest_entries.append(
                {
                    "video_id": vid,
                    "source": src,
                    "label": label,
                    "file_path": str(out_path),
                    "sha256": file_hash,
                    "status": "downloaded",
                }
            )
            logger.info(f"Downloaded {vid} ({src}) → {out_path.name}")
        else:
            failed_ids.append(vid)
            manifest_entries.append(
                {
                    "video_id": vid,
                    "source": src,
                    "label": label,
                    "file_path": str(out_path),
                    "sha256": None,
                    "status": "failed",
                }
            )
            logger.warning(f"Failed to download {vid} ({src})")

        # Periodic memory cleanup
        if idx % 5 == 0:
            clear_memory()

    # Write manifest JSON
    manifest = {
        "total_requested": len(sample_df),
        "successful": success_cnt,
        "failed": len(failed_ids),
        "failed_ids": failed_ids,
        "clips": manifest_entries,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as jf:
        json.dump(manifest, jf, indent=2)

    logger.info(
        f"Download finished: {success_cnt}/{len(sample_df)} successes."
    )
    if failed_ids:
        logger.warning(f"Failed video IDs: {failed_ids}")

    # Final memory cleanup
    clear_memory()
    return success_cnt == len(sample_df)

if __name__ == "__main__":
    ok = main()
    exit(0 if ok else 1)
