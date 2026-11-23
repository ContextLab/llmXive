#!/usr/bin/env python
"""
T030d: Compute FID and CLIP Scores (Full)

Computes metrics for the full set of generated images (Teacher vs Tree).
Reads from data/results/teacher_baseline_images_full/ and 
data/results/tree_generated_images_full/.
Writes aggregated metrics to data/results/fidelity_metrics_full.csv.

Dependencies:
  - T005b: utils.metrics (calculate_clip_score, calculate_fid)
  - T028b: Full image generation
  - T033a: utils.timer (timeout handling)
"""
import argparse
import json
import os
import sys
import signal
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import torch
import numpy as np
from PIL import Image

# Local imports
from utils.config import get_config
from utils.metrics import calculate_clip_score, calculate_fid
from utils.timer import TimeoutError, timeout_handler, setup_timeout, cancel_timeout, save_partial_results, check_timeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[1]

def get_image_paths(image_dir: Path) -> List[Path]:
    """
    Get sorted list of image paths in a directory.
    Ensures consistent ordering for pairing.
    """
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")
    
    # Get all image files (common extensions)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    paths = [
        p for p in image_dir.iterdir() 
        if p.suffix.lower() in image_extensions
    ]
    
    if not paths:
        logger.warning(f"No images found in {image_dir}")
        return []
    
    # Sort by filename to ensure consistent pairing
    paths.sort(key=lambda x: x.name)
    return paths

def load_image_pair(teacher_path: Path, tree_path: Path) -> Tuple[Image.Image, Image.Image]:
    """
    Load a pair of images (teacher baseline and tree generated).
    Returns PIL Images.
    """
    try:
        teacher_img = Image.open(teacher_path).convert('RGB')
        tree_img = Image.open(tree_path).convert('RGB')
        return teacher_img, tree_img
    except Exception as e:
        logger.error(f"Failed to load image pair ({teacher_path.name}, {tree_path.name}): {e}")
        return None, None

def compute_metrics_for_depth(
    teacher_images_dir: Path,
    tree_images_dir: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute FID and CLIP scores for a single depth/tree configuration.
    
    Returns:
        Dictionary with metrics: fid, clip_mean, clip_std, n_samples, status
    """
    setup_timeout(config.get('TIMEOUT_HOURS', 6) * 3600)
    
    teacher_paths = get_image_paths(teacher_images_dir)
    tree_paths = get_image_paths(tree_images_dir)
    
    if len(teacher_paths) != len(tree_paths):
        logger.error(f"Image count mismatch: Teacher={len(teacher_paths)}, Tree={len(tree_paths)}")
        return {
            'fid': float('nan'),
            'clip_mean': float('nan'),
            'clip_std': float('nan'),
            'n_samples': 0,
            'status': 'mismatch',
            'error': f"Image count mismatch: Teacher={len(teacher_paths)}, Tree={len(tree_paths)}"
        }
    
    if len(teacher_paths) == 0:
        logger.warning("No images found to compute metrics")
        return {
            'fid': float('nan'),
            'clip_mean': float('nan'),
            'clip_std': float('nan'),
            'n_samples': 0,
            'status': 'no_images',
            'error': "No images found"
        }
    
    logger.info(f"Processing {len(teacher_paths)} image pairs")
    
    clip_scores = []
    failed_pairs = 0
    
    for i, (teacher_path, tree_path) in enumerate(zip(teacher_paths, tree_paths)):
        if check_timeout():
            logger.warning("Timeout reached during metric computation")
            return {
                'fid': float('nan'),
                'clip_mean': float('nan'),
                'clip_std': float('nan'),
                'n_samples': len(clip_scores),
                'status': 'partial',
                'error': "Timeout"
            }
        
        teacher_img, tree_img = load_image_pair(teacher_path, tree_path)
        
        if teacher_img is None or tree_img is None:
            failed_pairs += 1
            continue
        
        # Compute CLIP score for this pair
        # calculate_clip_score returns List[float] (per-sample scores)
        pair_scores = calculate_clip_score(teacher_img, tree_img)
        
        if pair_scores and not any(np.isnan(s) for s in pair_scores):
            # Take the mean of the pair scores
            clip_scores.append(np.mean(pair_scores))
        else:
            logger.warning(f"Invalid CLIP scores for pair {i}: {pair_scores}")
            failed_pairs += 1
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(teacher_paths)} pairs")
    
    cancel_timeout()
    
    n_valid = len(clip_scores)
    if n_valid == 0:
        logger.error("No valid CLIP scores computed")
        return {
            'fid': float('nan'),
            'clip_mean': float('nan'),
            'clip_std': float('nan'),
            'n_samples': 0,
            'status': 'failed',
            'error': "No valid CLIP scores"
        }
    
    # Aggregate CLIP scores
    clip_mean = float(np.mean(clip_scores))
    clip_std = float(np.std(clip_scores))
    
    # Compute FID on the full sets
    try:
        fid_score = calculate_fid(teacher_images_dir, tree_images_dir)
    except Exception as e:
        logger.error(f"FID computation failed: {e}")
        fid_score = float('nan')
    
    logger.info(f"Metrics computed: FID={fid_score:.4f}, CLIP_mean={clip_mean:.4f}, CLIP_std={clip_std:.4f}")
    
    return {
        'fid': fid_score,
        'clip_mean': clip_mean,
        'clip_std': clip_std,
        'n_samples': n_valid,
        'status': 'complete',
        'failed_pairs': failed_pairs,
        'total_pairs': len(teacher_paths)
    }

def save_results(
    results: List[Dict[str, Any]],
    output_path: Path
):
    """
    Save computed metrics to CSV.
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
    
    # Also save a JSON summary for quick inspection
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"JSON summary saved to {json_path}")

def run_fidelity_metrics_computation(
    teacher_images_dir: Path,
    tree_images_dir: Path,
    output_path: Path,
    config: Dict[str, Any]
) -> bool:
    """
    Main runner for T030d.
    
    Steps:
    1. Verify input directories exist and contain images
    2. Compute CLIP scores (per-sample) and FID (dataset-level)
    3. Aggregate results
    4. Write to CSV
    
    Returns:
        True if successful, False otherwise
    """
    if not teacher_images_dir.exists():
        logger.error(f"Teacher images directory not found: {teacher_images_dir}")
        return False
    
    if not tree_images_dir.exists():
        logger.error(f"Tree images directory not found: {tree_images_dir}")
        return False
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Computing metrics for: {teacher_images_dir.name} vs {tree_images_dir.name}")
    
    # Compute metrics
    metrics = compute_metrics_for_depth(teacher_images_dir, tree_images_dir, config)
    
    # Save results
    save_results([metrics], output_path)
    
    if metrics['status'] in ['complete', 'partial']:
        return True
    else:
        logger.error(f"Metric computation failed with status: {metrics['status']}")
        return False

def main():
    """CLI entry point for T030d."""
    parser = argparse.ArgumentParser(description="Compute FID and CLIP scores for full fidelity evaluation")
    parser.add_argument(
        '--teacher-images',
        type=str,
        default=None,
        help='Path to teacher baseline images directory'
    )
    parser.add_argument(
        '--tree-images',
        type=str,
        default=None,
        help='Path to tree generated images directory'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for metrics CSV'
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    config = get_config()
    
    # Default paths
    if args.teacher_images is None:
        teacher_images_dir = project_root / 'data' / 'results' / 'teacher_baseline_images_full'
    else:
        teacher_images_dir = Path(args.teacher_images)
    
    if args.tree_images is None:
        tree_images_dir = project_root / 'data' / 'results' / 'tree_generated_images_full'
    else:
        tree_images_dir = Path(args.tree_images)
    
    if args.output is None:
        output_path = project_root / 'data' / 'results' / 'fidelity_metrics_full.csv'
    else:
        output_path = Path(args.output)
    
    logger.info(f"Teacher images: {teacher_images_dir}")
    logger.info(f"Tree images: {tree_images_dir}")
    logger.info(f"Output: {output_path}")
    
    success = run_fidelity_metrics_computation(
        teacher_images_dir,
        tree_images_dir,
        output_path,
        config
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()