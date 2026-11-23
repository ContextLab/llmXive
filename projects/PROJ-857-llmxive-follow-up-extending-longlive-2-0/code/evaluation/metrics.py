import torch
import torch.nn.functional as F
from typing import Union, List, Optional, Dict, Any
import numpy as np
import os
from evaluation.clip_evaluator import ClipTemporalEvaluator, create_clip_evaluator

def calculate_temporal_coherence(frames: np.ndarray, evaluator: Optional[ClipTemporalEvaluator] = None) -> float:
    """
    Calculates temporal coherence score for a video clip.
    """
    if evaluator is None:
        evaluator = create_clip_evaluator()
    return evaluator.evaluate(frames)

def calculate_motion_smoothness(frames: np.ndarray) -> float:
    """
    Calculates motion smoothness based on optical flow approximation (simple difference).
    """
    if len(frames) < 2:
        return 0.0
    
    diffs = []
    for i in range(len(frames) - 1):
        diff = np.mean(np.abs(frames[i+1].astype(float) - frames[i].astype(float)))
        diffs.append(diff)
    
    # Smoothness: lower variance in differences is smoother
    if not diffs:
        return 0.0
    return 1.0 / (1.0 + np.var(diffs))

def aggregate_video_scores(scores: List[float]) -> Dict[str, float]:
    """
    Aggregates a list of scores into summary statistics.
    """
    if not scores:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    
    arr = np.array(scores)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def main():
    print("Testing Metrics...")
    # Dummy data
    frames = np.random.randint(0, 255, (10, 224, 224, 3), dtype=np.uint8)
    score = calculate_temporal_coherence(frames)
    smooth = calculate_motion_smoothness(frames)
    print(f"Coherence: {score}, Smoothness: {smooth}")

if __name__ == "__main__":
    main()
