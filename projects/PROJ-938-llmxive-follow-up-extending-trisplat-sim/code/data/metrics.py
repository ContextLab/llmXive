"""
Metrics module for calculating Chamfer Distance and PSNR against ground truth.

This module provides functions to evaluate the geometric and photometric fidelity
of reconstructed scenes against ground truth data.

Dependencies:
    - numpy: For array operations
    - scipy: For nearest neighbor search (Chamfer Distance)
    - torch: For tensor handling and PSNR calculation
"""

import numpy as np
import torch
from scipy.spatial import cKDTree
from typing import Tuple, Union, Optional, List
import logging

# Configure logging
logger = logging.getLogger(__name__)


def calculate_chamfer_distance(
    points_pred: Union[np.ndarray, torch.Tensor],
    points_gt: Union[np.ndarray, torch.Tensor],
    symmetric: bool = True
) -> float:
    """
    Calculate the Chamfer Distance between two point clouds.

    The Chamfer Distance is defined as the average squared distance from each point
    in one set to its nearest neighbor in the other set.

    Args:
        points_pred: Predicted point cloud (N, 3) array or tensor.
        points_gt: Ground truth point cloud (M, 3) array or tensor.
        symmetric: If True, compute bidirectional distance (d1 + d2) / 2.
                  If False, compute only distance from pred to gt.

    Returns:
        float: The Chamfer Distance value.

    Raises:
        ValueError: If input shapes are invalid or points are empty.
    """
    # Convert to numpy if torch tensor
    if isinstance(points_pred, torch.Tensor):
        points_pred = points_pred.detach().cpu().numpy()
    if isinstance(points_gt, torch.Tensor):
        points_gt = points_gt.detach().cpu().numpy()

    # Validate inputs
    if points_pred.ndim != 2 or points_pred.shape[1] != 3:
        raise ValueError(f"points_pred must be (N, 3), got {points_pred.shape}")
    if points_gt.ndim != 2 or points_gt.shape[1] != 3:
        raise ValueError(f"points_gt must be (M, 3), got {points_gt.shape}")

    if points_pred.size == 0:
        raise ValueError("points_pred is empty")
    if points_gt.size == 0:
        raise ValueError("points_gt is empty")

    # Ensure float64 for precision
    points_pred = points_pred.astype(np.float64)
    points_gt = points_gt.astype(np.float64)

    # Build KD-Tree for ground truth
    tree_gt = cKDTree(points_gt)

    # Distance from predicted to ground truth
    dists_pred_to_gt, _ = tree_gt.query(points_pred, k=1)
    cd_pred_to_gt = np.mean(dists_pred_to_gt ** 2)

    if symmetric:
        # Build KD-Tree for predicted
        tree_pred = cKDTree(points_pred)
        # Distance from ground truth to predicted
        dists_gt_to_pred, _ = tree_pred.query(points_gt, k=1)
        cd_gt_to_pred = np.mean(dists_gt_to_pred ** 2)

        logger.debug(f"Chamfer Distance (pred->gt): {cd_pred_to_gt:.6f}, (gt->pred): {cd_gt_to_pred:.6f}")
        return float((cd_pred_to_gt + cd_gt_to_pred) / 2.0)
    else:
        logger.debug(f"Chamfer Distance (pred->gt): {cd_pred_to_gt:.6f}")
        return float(cd_pred_to_gt)


def calculate_psnr(
    image_pred: Union[np.ndarray, torch.Tensor],
    image_gt: Union[np.ndarray, torch.Tensor],
    max_value: float = 1.0
) -> float:
    """
    Calculate the Peak Signal-to-Noise Ratio (PSNR) between two images.

    PSNR is a measure of the quality of a reconstructed image compared to
    the original. Higher values indicate better quality.

    Args:
        image_pred: Predicted image (H, W, C) or (C, H, W) array or tensor.
        image_gt: Ground truth image (H, W, C) or (C, H, W) array or tensor.
        max_value: The maximum possible pixel value (e.g., 1.0 for normalized images).

    Returns:
        float: The PSNR value in dB. Returns -inf if MSE is 0 (perfect match).

    Raises:
        ValueError: If input shapes do not match or are invalid.
    """
    # Convert to numpy if torch tensor
    if isinstance(image_pred, torch.Tensor):
        image_pred = image_pred.detach().cpu().numpy()
    if isinstance(image_gt, torch.Tensor):
        image_gt = image_gt.detach().cpu().numpy()

    # Validate inputs
    if image_pred.shape != image_gt.shape:
        raise ValueError(
            f"Image shapes must match. Got pred: {image_pred.shape}, gt: {image_gt.shape}"
        )

    if image_pred.size == 0:
        raise ValueError("Input images are empty")

    # Ensure float64 for precision
    image_pred = image_pred.astype(np.float64)
    image_gt = image_gt.astype(np.float64)

    # Calculate Mean Squared Error
    mse = np.mean((image_pred - image_gt) ** 2)

    if mse == 0:
        # Perfect match
        logger.debug("MSE is 0, images are identical. PSNR: inf")
        return float('inf')

    # Calculate PSNR
    psnr = 20 * np.log10(max_value) - 10 * np.log10(mse)

    logger.debug(f"MSE: {mse:.6f}, PSNR: {psnr:.2f} dB")
    return float(psnr)


def calculate_metrics_batch(
    predictions: List[dict],
    ground_truths: List[dict],
    metric_types: Optional[List[str]] = None
) -> List[dict]:
    """
    Calculate metrics for a batch of predictions against ground truths.

    Args:
        predictions: List of dictionaries containing 'points' (for geometry)
                    or 'images' (for photometric) data.
        ground_truths: List of dictionaries containing corresponding ground truth data.
        metric_types: List of metrics to calculate. Options: ['chamfer', 'psnr'].
                     Defaults to all applicable based on data keys.

    Returns:
        List of dictionaries containing the calculated metrics for each pair.

    Raises:
        ValueError: If input lists are of different lengths or missing required keys.
    """
    if len(predictions) != len(ground_truths):
        raise ValueError(
            f"Number of predictions ({len(predictions)}) must match ground truths ({len(ground_truths)})"
        )

    if metric_types is None:
        metric_types = ['chamfer', 'psnr']

    results = []

    for i, (pred, gt) in enumerate(zip(predictions, ground_truths)):
        result = {'index': i}

        if 'chamfer' in metric_types and 'points' in pred and 'points' in gt:
            try:
                cd = calculate_chamfer_distance(pred['points'], gt['points'])
                result['chamfer_distance'] = cd
            except Exception as e:
                logger.warning(f"Failed to calculate Chamfer Distance for index {i}: {e}")
                result['chamfer_distance'] = None

        if 'psnr' in metric_types and 'images' in pred and 'images' in gt:
            try:
                psnr_val = calculate_psnr(pred['images'], gt['images'])
                result['psnr'] = psnr_val
            except Exception as e:
                logger.warning(f"Failed to calculate PSNR for index {i}: {e}")
                result['psnr'] = None

        results.append(result)

    return results