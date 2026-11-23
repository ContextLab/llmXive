"""
Metrics for visual complexity quantification.
Implements Edge Density, Entropy, and Fractal Dimension calculations.
"""
import numpy as np
import cv2
from scipy.stats import entropy
from typing import Tuple, Optional
from pathlib import Path
import logging

from utils.logging import get_logger, get_log_path

logger: logging.Logger = get_logger(__name__)

def calculate_edge_density(image: np.ndarray, low_threshold: int = 50, high_threshold: int = 150, kernel_size: int = 3) -> float:
    """
    Calculate edge density using Canny edge detection.

    Args:
        image: Input image (grayscale or BGR).
        low_threshold: Lower threshold for hysteresis.
        high_threshold: Upper threshold for hysteresis.
        kernel_size: Size of the Sobel kernel.

    Returns:
        float: Ratio of edge pixels to total pixels.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    edges = cv2.Canny(gray, low_threshold, high_threshold, apertureSize=kernel_size)
    total_pixels = edges.size
    edge_pixels = cv2.countNonZero(edges)

    if total_pixels == 0:
        return 0.0

    return float(edge_pixels) / float(total_pixels)

def calculate_entropy(image: np.ndarray) -> float:
    """
    Calculate Shannon entropy of the grayscale histogram.

    Args:
        image: Input image (grayscale or BGR).

    Returns:
        float: Entropy value.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    # Normalize histogram to get probabilities
    prob = hist.astype(float) / hist.sum()
    # Filter out zero probabilities to avoid log(0)
    prob = prob[prob > 0]

    if len(prob) == 0:
        return 0.0

    return float(entropy(prob, base=2))

def calculate_fractal_dim(image: np.ndarray, box_sizes: Optional[list[int]] = None) -> float:
    """
    Calculate fractal dimension using the box-counting method.
    Clamps values to [1.0, 3.0] if calculation fails or is out of range.

    Args:
        image: Input image (grayscale or BGR).
        box_sizes: List of box sizes to use for counting. If None, defaults to powers of 2.

    Returns:
        float: Fractal dimension (clamped to [1.0, 3.0]).
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Preprocess: Binarize the image (Otsu's thresholding)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary = binary // 255  # Convert to 0 and 1

    height, width = binary.shape
    min_dim = min(height, width)

    if box_sizes is None:
        # Generate box sizes as powers of 2, starting from largest power of 2 <= min_dim
        # ensuring we have at least 2 sizes for regression
        sizes = []
        current = 2
        while current <= min_dim // 2:
            sizes.append(current)
            current *= 2
        if not sizes:
            sizes = [2, 4] # Fallback
        box_sizes = sorted(sizes, reverse=True)

    counts: list[int] = []
    log_sizes: list[float] = []

    for size in box_sizes:
        if size >= min_dim:
            continue
        
        # Pad image to be divisible by size
        pad_h = (size - (height % size)) % size
        pad_w = (size - (width % size)) % size
        padded = np.pad(binary, ((0, pad_h), (0, pad_w)), mode='constant')
        
        # Count non-empty boxes
        h_boxes = padded.shape[0] // size
        w_boxes = padded.shape[1] // size
        
        count = 0
        for i in range(h_boxes):
            for j in range(w_boxes):
                box = padded[i*size:(i+1)*size, j*size:(j+1)*size]
                if np.any(box > 0):
                    count += 1
        
        if count > 0:
            counts.append(count)
            log_sizes.append(np.log(1.0 / size))

    if len(log_sizes) < 2 or len(counts) < 2:
        logger.warning(f"Fractal dimension calculation failed for image due to insufficient box sizes. Assigning NaN.")
        return float('nan')

    try:
        # Linear regression: log(count) = D * log(1/size) + C
        # We want D (slope)
        log_counts = np.log(counts)
        slope, _, _, _, _ = np.linalg.lstsq(np.vstack([log_sizes, np.ones(len(log_sizes))]).T, log_counts, rcond=None)
        fractal_dim = float(slope[0])

        # Clamp to valid range [1.0, 3.0]
        if not np.isfinite(fractal_dim):
            raise ValueError("Non-finite fractal dimension")

        if fractal_dim < 1.0:
            logger.warning(f"Fractal dimension {fractal_dim:.4f} < 1.0 for image. Clamping to 1.0.")
            return 1.0
        if fractal_dim > 3.0:
            logger.warning(f"Fractal dimension {fractal_dim:.4f} > 3.0 for image. Clamping to 3.0.")
            return 3.0
        
        return fractal_dim

    except Exception as e:
        logger.warning(f"Fractal dimension calculation failed for image due to error: {e}. Assigning NaN.")
        return float('nan')

def process_image_vectorized(image_path: str | Path) -> Tuple[float, float, float]:
    """
    Process a single image and return all three metrics.

    Args:
        image_path: Path to the image file.

    Returns:
        Tuple[float, float, float]: (edge_density, entropy, fractal_dim)
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not decode image: {path}")

    edge_density = calculate_edge_density(image)
    entropy_val = calculate_entropy(image)
    fractal_dim = calculate_fractal_dim(image)

    return edge_density, entropy_val, fractal_dim
