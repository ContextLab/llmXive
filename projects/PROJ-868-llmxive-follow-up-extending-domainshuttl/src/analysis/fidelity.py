"""
Fidelity Curve Scoring Module (T020).

Implements full fidelity-vs-dimension scoring by generating videos across
all dimensions [16, 32, 64, 128, 256] and styles ['Anime', 'Photorealistic', 'Sketch']
for all subjects, then computing CLIP Image Similarity scores.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch
from PIL import Image
import numpy as np
from tqdm import tqdm

# Import from existing API surface
from src.utils.timeout import with_timeout, _log_timeout, LOG_FILE, LOG_DIR
from src.analysis.generation import generate_video_for_subject
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
DIMENSIONS = [16, 32, 64, 128, 256]
STYLES = ['Anime', 'Photorealistic', 'Sketch']
NUM_FRAMES_TO_SAMPLE = 5
CLIP_MODEL_NAME = "ViT-B/32"
OUTPUT_FILE = "data/results/fidelity_vs_dimension_curve.json"
LOG_DIR_PATH = Path(LOG_DIR)
LOG_FILE_PATH = Path(LOG_FILE)

def _load_clip_model(device: str = "cpu"):
    """Load CLIP model for image similarity scoring."""
    import clip
    model, preprocess = clip.load(CLIP_MODEL_NAME, device=device, download_root="data/models/clip")
    return model, preprocess

def _extract_frames(video_path: Path, num_frames: int = NUM_FRAMES_TO_SAMPLE) -> List[Image.Image]:
    """Extract equidistant frames from a video file."""
    import cv2
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        raise ValueError(f"Video has 0 frames: {video_path}")

    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
        else:
            logger.warning(f"Failed to read frame {idx} from {video_path}")

    cap.release()
    return frames

def _compute_clip_similarity(
    model,
    preprocess,
    reference_frames: List[Image.Image],
    generated_frames: List[Image.Image],
    device: str
) -> float:
    """Compute mean CLIP image-image similarity between reference and generated frames."""
    reference_tensor = torch.stack([preprocess(img).to(device) for img in reference_frames])
    generated_tensor = torch.stack([preprocess(img).to(device) for img in generated_frames])

    with torch.no_grad():
        ref_features = model.encode_image(reference_tensor)
        gen_features = model.encode_image(generated_tensor)

        # Normalize features
        ref_features = ref_features / ref_features.norm(dim=-1, keepdim=True)
        gen_features = gen_features / gen_features.norm(dim=-1, keepdim=True)

        # Compute cosine similarity
        similarities = (ref_features @ gen_features.T).mean().item()

    return similarities

def _run_generation_with_timeout(
    subject_id: str,
    dimension: int,
    style: str,
    timeout_seconds: int = 300
) -> Optional[Path]:
    """Wrapper to run generation with per-sample timeout."""
    def generation_task():
        output_path = generate_video_for_subject(subject_id, dimension, style)
        return output_path

    # Use the timeout wrapper from T017
    try:
        result = with_timeout(generation_task, timeout=timeout_seconds)
        return result
    except Exception as e:
        logger.error(f"Generation failed for {subject_id}, dim={dimension}, style={style}: {e}")
        _log_timeout(subject_id, timeout_seconds, str(e))
        return None

def run_fidelity_curve_scoring(
    subject_ids: List[str],
    dimensions: List[int] = None,
    styles: List[str] = None,
    timeout_per_sample: int = 300,
    device: str = "cpu"
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Generate videos and compute CLIP similarity scores for all subjects,
    dimensions, and styles.

    Args:
        subject_ids: List of subject IDs to process.
        dimensions: List of dimensions to sweep (default: [16, 32, 64, 128, 256]).
        styles: List of styles to generate (default: ['Anime', 'Photorealistic', 'Sketch']).
        timeout_per_sample: Timeout in seconds per generation task.
        device: Device to run CLIP model on.

    Returns:
        Dictionary: {subject_id: {dimension: {style: clip_score}}}
    """
    if dimensions is None:
        dimensions = DIMENSIONS
    if styles is None:
        styles = STYLES

    # Ensure output directory exists
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load reference data (complexity scores) to get reference video paths
    # Assuming T012 produced data/processed/complexity_scores.csv with subject_id and reference_video_path
    # If the path is not in that CSV, we might need to infer it or load from a manifest.
    # For now, we assume the generation function handles the reference video lookup internally.

    # Load CLIP model
    logger.info(f"Loading CLIP model {CLIP_MODEL_NAME} on {device}...")
    clip_model, preprocess = _load_clip_model(device)

    # Initialize results structure
    results = {}

    # Process each subject
    for subject_id in tqdm(subject_ids, desc="Processing Subjects"):
        results[subject_id] = {}

        # Check if this subject is in the failed subjects log
        failed_log_path = Path("data/processed/failed_subjects.log")
        if failed_log_path.exists():
            with open(failed_log_path, 'r') as f:
                failed_subjects = [line.strip() for line in f if line.strip()]
            if subject_id in failed_subjects:
                logger.info(f"Skipping failed subject: {subject_id}")
                continue

        for dim in dimensions:
            results[subject_id][str(dim)] = {}
            for style in styles:
                logger.info(f"Generating: {subject_id}, dim={dim}, style={style}")

                # Run generation with timeout
                video_path = _run_generation_with_timeout(
                    subject_id, dim, style, timeout_per_sample
                )

                if video_path is None or not video_path.exists():
                    logger.warning(f"Video generation failed or missing: {subject_id}, dim={dim}, style={style}")
                    results[subject_id][str(dim)][style] = None
                    continue

                # Extract frames from generated video
                try:
                    generated_frames = _extract_frames(video_path, NUM_FRAMES_TO_SAMPLE)
                except Exception as e:
                    logger.error(f"Frame extraction failed for {video_path}: {e}")
                    results[subject_id][str(dim)][style] = None
                    continue

                # We need reference frames. Assuming the generation script
                # uses a reference video associated with the subject.
                # We'll re-extract frames from the reference video used in generation.
                # This requires knowing the reference video path.
                # For now, we'll assume the generation function has access to it
                # and we can re-load it here. This is a simplification.
                # In a real implementation, we'd store the reference video path in the results
                # or have a separate lookup.

                # Attempt to load reference video (this logic might need adjustment
                # based on how T019/T009 stores reference video paths)
                reference_video_path = Path(f"data/raw/{subject_id}/reference.mp4")
                if not reference_video_path.exists():
                    # Fallback: check common patterns
                    reference_video_path = Path(f"data/raw/{subject_id}.mp4")

                if reference_video_path.exists():
                    try:
                        reference_frames = _extract_frames(reference_video_path, NUM_FRAMES_TO_SAMPLE)
                        score = _compute_clip_similarity(
                            clip_model, preprocess, reference_frames, generated_frames, device
                        )
                        results[subject_id][str(dim)][style] = score
                    except Exception as e:
                        logger.error(f"CLIP scoring failed for {subject_id}, dim={dim}, style={style}: {e}")
                        results[subject_id][str(dim)][style] = None
                else:
                    logger.error(f"Reference video not found for {subject_id}: {reference_video_path}")
                    results[subject_id][str(dim)][style] = None

        # Save intermediate results to avoid losing progress
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

    logger.info(f"Full fidelity curve scoring complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for running the fidelity curve scoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Run full fidelity curve scoring.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per generation task (seconds)")
    parser.add_argument("--device", type=str, default="cpu", help="Device for CLIP model (cpu/cuda)")
    args = parser.parse_args()

    # Load subject IDs from the complexity scores CSV
    import pandas as pd
    complexity_df = pd.read_csv("data/processed/complexity_scores.csv")
    subject_ids = complexity_df["subject_id"].tolist()

    logger.info(f"Starting fidelity curve scoring for {len(subject_ids)} subjects...")
    results = run_fidelity_curve_scoring(
        subject_ids=subject_ids,
        timeout_per_sample=args.timeout,
        device=args.device
    )

    # Final save
    output_path = Path(OUTPUT_FILE)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info("Fidelity curve scoring completed successfully.")

if __name__ == "__main__":
    main()
