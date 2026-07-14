import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from config import get_features_dir, get_stratified_dir

def load_sequence_frames(sequence_path: Path) -> list:
    """Load frames from a sequence directory."""
    frames = []
    for img_path in sorted(sequence_path.glob("*.jpg")):
        frame = cv2.imread(str(img_path))
        if frame is not None:
            frames.append(frame)
    return frames

def extract_sparse_features(frame: np.ndarray) -> tuple:
    """Extract SIFT/ORB features."""
    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(frame, None)
    return kp, des

def is_fast_sequence(sequence_path: Path) -> bool:
    """Check if sequence is fast (mocked)."""
    return False

def process_sequence(sequence_path: Path, stratum_name: str):
    """Process a single sequence."""
    frames = load_sequence_frames(sequence_path)
    if not frames:
        return
    features_dir = get_features_dir() / stratum_name
    features_dir.mkdir(parents=True, exist_ok=True)
    # Mock processing
    np.save(features_dir / f"{sequence_path.stem}.npy", np.array([0, 0]))

def main():
    print("Extracting features...")
    stratified_dir = get_stratified_dir()
    for stratum in ["Static-High", "Static-Low", "Fast-High", "Fast-Low"]:
        stratum_path = stratified_dir / stratum
        if stratum_path.exists():
            for seq in stratum_path.glob("*"):
                if seq.is_dir():
                    process_sequence(seq, stratum)
    print("Feature extraction complete.")

if __name__ == "__main__":
    main()