"""
Metrics calculation: Chamfer Distance and PSNR.
"""
import numpy as np
import torch
from scipy.spatial import cKDTree
from typing import Tuple, Union, Optional, List
import logging

logger = logging.getLogger(__name__)

def calculate_psnr(pred: np.ndarray, target: np.ndarray, max_val: float = 255.0) -> float:
    """Calculate PSNR between prediction and target."""
    if pred.shape != target.shape:
        raise ValueError(f"Shape mismatch: {pred.shape} vs {target.shape}")
    
    mse = np.mean((pred.astype(float) - target.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    psnr = 20 * np.log10(max_val) - 10 * np.log10(mse)
    return psnr

def calculate_chamfer_distance(points1: np.ndarray, points2: np.ndarray) -> float:
    """
    Calculate Chamfer Distance between two point clouds.
    points1, points2: (N, 3) numpy arrays.
    """
    if len(points1) == 0 or len(points2) == 0:
        return float('inf')
    
    # KDTree for nearest neighbor search
    tree1 = cKDTree(points1)
    tree2 = cKDTree(points2)
    
    # Distance from 1 to 2
    dists1, _ = tree1.query(points2, k=1)
    # Distance from 2 to 1
    dists2, _ = tree2.query(points1, k=1)
    
    cd = (np.mean(dists1) + np.mean(dists2)) / 2.0
    return cd

def calculate_metrics_batch(pred_points: np.ndarray, target_points: np.ndarray, 
                            pred_img: Optional[np.ndarray] = None, 
                            target_img: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Calculate batch metrics: Chamfer Distance and optionally PSNR.
    """
    results = {}
    
    if pred_points is not None and target_points is not None:
        cd = calculate_chamfer_distance(pred_points, target_points)
        results['chamfer_distance'] = cd
        logger.info(f"Chamfer Distance: {cd:.4f}")
    
    if pred_img is not None and target_img is not None:
        psnr = calculate_psnr(pred_img, target_img)
        results['psnr'] = psnr
        logger.info(f"PSNR: {psnr:.2f}")
    
    return results
