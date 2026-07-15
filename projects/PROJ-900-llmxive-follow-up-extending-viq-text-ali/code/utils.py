"""
Utility functions for metric calculation in the llmXive ViQ pipeline.

Implements:
- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index Measure)
- Cosine Similarity
- Texture Complexity (Variance of Laplacian)
"""
from typing import Tuple, Union

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from skimage.metrics import structural_similarity as ssim_fn


def calculate_psnr(
    img1: Union[np.ndarray, torch.Tensor],
    img2: Union[np.ndarray, torch.Tensor],
    data_range: float = 1.0
) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR) between two images.

    Args:
        img1: First image (H, W, C) or (C, H, W). Values in [0, 1] or [0, 255].
        img2: Second image, same shape as img1.
        data_range: The dynamic range of the image (1.0 for [0,1], 255.0 for [0,255]).

    Returns:
        PSNR value in dB.

    Raises:
        ValueError: If images are not the same shape or are empty.
    """
    if isinstance(img1, torch.Tensor):
        img1 = img1.detach().cpu().numpy()
    if isinstance(img2, torch.Tensor):
        img2 = img2.detach().cpu().numpy()

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    if img1.shape != img2.shape:
        raise ValueError(f"Image shapes do not match: {img1.shape} vs {img2.shape}")

    if img1.size == 0:
        raise ValueError("Input images are empty.")

    mse = np.mean((img1 - img2) ** 2)

    if mse == 0:
        return float('inf')

    psnr = 20 * np.log10(data_range) - 10 * np.log10(mse)
    return float(psnr)


def calculate_ssim(
    img1: Union[np.ndarray, torch.Tensor],
    img2: Union[np.ndarray, torch.Tensor],
    channel_axis: int = -1
) -> Tuple[float, np.ndarray]:
    """
    Calculate Structural Similarity Index Measure (SSIM) between two images.

    Args:
        img1: First image.
        img2: Second image.
        channel_axis: Axis of the channel dimension (0 for CHW, 2 for HWC).

    Returns:
        Tuple of (mean_ssim, full_ssim_map).
    """
    if isinstance(img1, torch.Tensor):
        img1 = img1.detach().cpu().numpy()
    if isinstance(img2, torch.Tensor):
        img2 = img2.detach().cpu().numpy()

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    if img1.shape != img2.shape:
        raise ValueError(f"Image shapes do not match: {img1.shape} vs {img2.shape}")

    # Convert to grayscale if multi-channel, or handle directly
    # skimage expects HWC by default, but can handle CHW with channel_axis
    if channel_axis == 0:
        # Convert CHW to HWC for skimage compatibility if needed, or pass channel_axis
        # skimage.metrics.structural_similarity supports channel_axis in newer versions
        # To be safe and consistent with standard usage:
        if img1.shape[0] in [1, 3]:
            img1 = np.transpose(img1, (1, 2, 0))
            img2 = np.transpose(img2, (1, 2, 0))
            channel_axis = 2
        else:
            channel_axis = 2 # Assume HWC if not 1/3 channels at start

    # Ensure range is [0, 1] or [0, 255] for skimage
    # Assuming input is normalized to [0, 1] based on typical pipeline
    max_val = 1.0
    min_val = 0.0
    full_range = max_val - min_val

    try:
        score, diff = ssim_fn(
            img1, img2,
            data_range=full_range,
            channel_axis=channel_axis,
            full=True
        )
    except TypeError:
        # Fallback for older skimage versions without channel_axis
        if img1.ndim == 3:
            # If multi-channel, compute per channel or convert to grayscale
            # Simple approach: convert to grayscale
            img1_gray = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            img2_gray = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
            score, diff = ssim_fn(img1_gray, img2_gray, data_range=full_range, full=True)
        else:
            score, diff = ssim_fn(img1, img2, data_range=full_range, full=True)

    return float(score), diff


def calculate_cosine_similarity(
    vec1: Union[np.ndarray, torch.Tensor],
    vec2: Union[np.ndarray, torch.Tensor]
) -> float:
    """
    Calculate Cosine Similarity between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Cosine similarity value in range [-1, 1].
    """
    if isinstance(vec1, torch.Tensor):
        vec1 = vec1.detach().cpu().numpy()
    if isinstance(vec2, torch.Tensor):
        vec2 = vec2.detach().cpu().numpy()

    vec1 = vec1.flatten().astype(np.float64)
    vec2 = vec2.flatten().astype(np.float64)

    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def calculate_texture_complexity(
    img: Union[np.ndarray, torch.Tensor],
    normalized: bool = True
) -> float:
    """
    Calculate Texture Complexity using the Variance of the Laplacian.

    This metric measures the amount of detail (edges, textures) in an image.
    Higher values indicate more complex textures.

    Args:
        img: Input image (H, W) or (H, W, C). If C > 1, converted to grayscale.
        normalized: If True, divides variance by the number of pixels to normalize.

    Returns:
        Texture complexity score (variance of Laplacian).
    """
    if isinstance(img, torch.Tensor):
        img = img.detach().cpu().numpy()

    img = img.astype(np.float64)

    # Convert to grayscale if necessary
    if img.ndim == 3:
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        elif img.shape[2] == 1:
            img = img.squeeze(axis=2)
        else:
            # Fallback: simple mean
            img = np.mean(img, axis=2)

    if img.ndim != 2:
        raise ValueError(f"Expected 2D grayscale image, got shape {img.shape}")

    # Compute Laplacian
    laplacian = cv2.Laplacian(img, cv2.CV_64F)

    variance = np.var(laplacian)

    if normalized:
        # Normalize by number of pixels to make it somewhat scale-invariant
        # Note: Variance is already an average of squared deviations, so this
        # might be redundant depending on interpretation, but per spec:
        variance = variance / img.size

    return float(variance)