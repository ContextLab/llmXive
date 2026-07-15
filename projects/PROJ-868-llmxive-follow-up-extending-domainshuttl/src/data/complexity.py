"""
Visual complexity scoring module for DomainShuttle follow-up.

Implements Sobel edge density scoring across equidistant frames per subject.
"""
import os
import math
from typing import List, Dict, Any, Optional

import numpy as np
import cv2
from datasets import load_dataset
from tqdm import tqdm

from src.config.settings import get_config
from src.utils.io import ensure_dir


def _load_frame_from_video(video_path: str, frame_index: int, total_frames: int) -> Optional[np.ndarray]:
    """
    Load a specific frame from a video file.
    
    Args:
        video_path: Path to the video file.
        frame_index: The index of the frame to load.
        total_frames: Total number of frames in the video.
        
    Returns:
        Frame as BGR numpy array, or None if loading fails.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    return frame


def _compute_sobel_magnitude(frame: np.ndarray) -> float:
    """
    Compute the mean magnitude of the Sobel gradient for a single frame.
    
    Args:
        frame: Input BGR image.
        
    Returns:
        Mean magnitude of the Sobel gradient.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Compute Sobel gradients
    # Kernel size 3 is standard for edge detection
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.CV_64F
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # Compute magnitude
    magnitude = cv2.magnitude(sobelx, sobely)
    
    # Return mean magnitude
    return float(np.mean(magnitude))


def compute_complexity_scores(
    dataset_name: str = "m-bain/webvid",
    subset_name: str = "10M",
    num_subjects: int = 100,
    seed: int = 42,
    frames_per_subject: int = 5,
    output_path: str = "data/processed/complexity_scores.csv"
) -> None:
    """
    Compute visual complexity scores for a subset of subjects.
    
    Loads a stratified random sample of subjects from the dataset,
    calculates Sobel edge density across equidistant frames, and
    saves the results to a CSV file.
    
    Args:
        dataset_name: Name of the HuggingFace dataset.
        subset_name: Subset name (e.g., "10M").
        num_subjects: Number of subjects to process.
        seed: Random seed for reproducibility.
        frames_per_subject: Number of equidistant frames to sample per subject.
        output_path: Path to save the output CSV.
    """
    config = get_config()
    ensure_dir(os.path.dirname(output_path))
    
    # Load dataset
    # Note: This assumes T009 has populated the data or the dataset is accessible
    # We use streaming to avoid loading the entire dataset into memory
    try:
        ds = load_dataset(
            dataset_name, 
            subset_name, 
            split="train", 
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset '{dataset_name}': {e}")
    
    # Convert to list for sampling (we need to sample by category)
    # Since streaming doesn't support random sampling by category directly,
    # we'll collect a sufficient number of items first
    # For a real implementation, we'd use a more sophisticated sampling strategy
    # but for this task, we'll sample the first N items and then stratify
    
    # Collect items with their categories
    items_with_category = []
    for item in ds:
        if len(items_with_category) >= num_subjects * 10:  # Collect more than needed
            break
        items_with_category.append(item)
    
    if len(items_with_category) == 0:
        raise RuntimeError("No items found in the dataset")
    
    # Group by category for stratified sampling
    category_groups = {}
    for item in items_with_category:
        category = item.get('category', 'unknown')
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(item)
    
    # Stratified sampling: aim for uniform distribution across top 10 categories
    np.random.seed(seed)
    sampled_items = []
    
    # Get top 10 categories by count
    sorted_categories = sorted(category_groups.keys(), key=lambda c: len(category_groups[c]), reverse=True)[:10]
    
    # Calculate how many items to sample per category
    items_per_category = num_subjects // len(sorted_categories)
    remainder = num_subjects % len(sorted_categories)
    
    for i, category in enumerate(sorted_categories):
        count = items_per_category + (1 if i < remainder else 0)
        category_items = category_groups[category]
        # Random sample from this category
        if count <= len(category_items):
            sampled = np.random.choice(category_items, count, replace=False)
        else:
            # If not enough items, take all and duplicate if necessary (though this shouldn't happen)
            sampled = category_items
            if len(sampled) < count:
                # Pad with random selections
                extra_needed = count - len(sampled)
                extra = np.random.choice(sampled, extra_needed, replace=True)
                sampled = list(sampled) + list(extra)
        sampled_items.extend(sampled)
    
    # Shuffle to mix categories
    np.random.shuffle(sampled_items)
    sampled_items = sampled_items[:num_subjects]
    
    # Compute complexity scores
    results = []
    
    print(f"Processing {len(sampled_items)} subjects...")
    for item in tqdm(sampled_items, desc="Computing complexity"):
        subject_id = item.get('videoid') or item.get('id')
        video_path = item.get('video_path') or item.get('path')
        
        if not video_path or not os.path.exists(video_path):
            # Try to download or skip
            # For now, we'll skip if the path doesn't exist
            # In a real implementation, we'd download the video
            continue
        
        # Get total frames
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames == 0:
            continue
        
        # Calculate equidistant frame indices
        frame_indices = [
            int(i * (total_frames - 1) / (frames_per_subject - 1)) 
            if frames_per_subject > 1 else 0
            for i in range(frames_per_subject)
        ]
        
        # Compute Sobel magnitude for each frame
        magnitudes = []
        for idx in frame_indices:
            frame = _load_frame_from_video(video_path, idx, total_frames)
            if frame is not None:
                mag = _compute_sobel_magnitude(frame)
                magnitudes.append(mag)
        
        if len(magnitudes) == 0:
            continue
        
        # Mean magnitude across frames
        mean_magnitude = float(np.mean(magnitudes))
        
        # L2 normalization (we'll normalize across all subjects later)
        # For now, store the raw mean magnitude
        results.append({
            'subject_id': subject_id,
            'mean_sobel_magnitude': mean_magnitude,
            'frames_processed': len(magnitudes)
        })
    
    if len(results) == 0:
        raise RuntimeError("No valid complexity scores computed")
    
    # L2 normalization across all subjects
    magnitudes = np.array([r['mean_sobel_magnitude'] for r in results])
    l2_norm = np.linalg.norm(magnitudes)
    if l2_norm > 0:
        normalized_magnitudes = magnitudes / l2_norm
        for i, r in enumerate(results):
            r['normalized_complexity_score'] = normalized_magnitudes[i]
    else:
        # If all magnitudes are zero, set to 0
        for r in results:
            r['normalized_complexity_score'] = 0.0
    
    # Save to CSV
    import pandas as pd
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Saved complexity scores to {output_path}")
    
    # Return the dataframe for verification (optional)
    return df


if __name__ == "__main__":
    compute_complexity_scores()
