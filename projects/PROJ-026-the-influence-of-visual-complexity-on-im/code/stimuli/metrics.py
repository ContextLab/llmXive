import numpy as np
import cv2
from scipy.stats import entropy
from typing import Tuple, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_edge_density(
    image: np.ndarray,
    low_threshold: int = 50,
    high_threshold: int = 150,
    kernel_size: int = 3
) -> float:
    """
    Calculate edge density using Canny edge detection.

    Args:
        image: Grayscale or BGR image
        low_threshold: Low threshold for Canny
        high_threshold: High threshold for Canny
        kernel_size: Kernel size for Gaussian blur

    Returns:
        Edge density as a float between 0 and 1
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Gaussian blur
    blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

    # Canny edge detection
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    # Calculate density
    total_pixels = edges.size
    edge_pixels = np.count_nonzero(edges)

    if total_pixels == 0:
        return 0.0

    return float(edge_pixels / total_pixels)


def calculate_entropy(image: np.ndarray) -> float:
    """
    Calculate entropy of grayscale histogram.

    Args:
        image: Grayscale or BGR image

    Returns:
        Entropy value
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Calculate histogram
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))

    # Normalize to probability
    prob = hist / hist.sum()

    # Remove zero probabilities
    prob = prob[prob > 0]

    # Calculate entropy
    ent = entropy(prob, base=2)

    return float(ent)


def calculate_fractal_dim(
    image: np.ndarray,
    box_sizes: Optional[np.ndarray] = None
) -> float:
    """
    Calculate fractal dimension using box-counting method.

    Args:
        image: Grayscale or BGR image
        box_sizes: Array of box sizes to use (logarithmically spaced)

    Returns:
        Fractal dimension (D)
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Binarize (threshold at mean)
    _, binary = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)

    height, width = binary.shape
    max_size = min(height, width)

    if box_sizes is None:
        # Generate box sizes: powers of 2 from 2 to max_size/2
        box_sizes = np.array([2**i for i in range(1, int(np.log2(max_size/2)) + 1)])

    # Filter valid box sizes
    box_sizes = box_sizes[box_sizes < max_size]

    if len(box_sizes) < 3:
        logger.warning("Insufficient box sizes for fractal dimension calculation.")
        return 1.5  # Default fallback

    counts = []

    for size in box_sizes:
        # Count non-empty boxes
        count = 0
        for y in range(0, height, int(size)):
            for x in range(0, width, int(size)):
                box = binary[y:y+int(size), x:x+int(size)]
                if np.any(box > 0):
                    count += 1

        counts.append(count)

    counts = np.array(counts)

    # Linear regression on log-log plot
    log_sizes = np.log(1 / box_sizes)
    log_counts = np.log(counts)

    # Fit line: log(N) = D * log(1/r) + c
    # D is the slope
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = coeffs[0]

    # Clamp to physical range [1, 2] for 2D images
    fractal_dim = np.clip(fractal_dim, 1.0, 2.0)

    return float(fractal_dim)


def process_image_vectorized(
    image_path: str,
    edge_low: int = 50,
    edge_high: int = 150,
    kernel_size: int = 3
) -> Tuple[float, float, float]:
    """
    Process a single image and return all complexity metrics.

    Args:
        image_path: Path to image file
        edge_low: Low threshold for Canny
        edge_high: High threshold for Canny
        kernel_size: Kernel size for Gaussian blur

    Returns:
        Tuple of (edge_density, entropy, fractal_dim)
    """
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    edge_density = calculate_edge_density(image, edge_low, edge_high, kernel_size)
    entropy_val = calculate_entropy(image)
    fractal_dim = calculate_fractal_dim(image)

    return edge_density, entropy_val, fractal_dim


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        ed, ent, fd = process_image_vectorized(path)
        print(f"Edge Density: {ed:.4f}")
        print(f"Entropy: {ent:.4f}")
        print(f"Fractal Dimension: {fd:.4f}")
