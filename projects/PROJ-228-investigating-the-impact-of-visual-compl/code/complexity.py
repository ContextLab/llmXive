"""
Complexity analysis module for visual stimuli.

Provides functions to calculate Shannon Entropy, Fractal Dimension,
and Texture Complexity metrics for image analysis.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union
from PIL import Image
from skimage.feature import graycomatrix, graycoprops
from scipy import ndimage
import logging

logger = logging.getLogger(__name__)

def _load_image_as_grayscale(image_path: Union[str, Path]) -> np.ndarray:
    """Load an image and convert to grayscale numpy array."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        img = Image.open(path).convert('L')
        return np.array(img, dtype=np.float64)
    except Exception as e:
        raise ValueError(f"Failed to load image {image_path}: {e}")

def calculate_entropy(image_path: Union[str, Path]) -> float:
    """
    Calculate the Shannon Entropy of an image.
    
    Shannon entropy measures the amount of information or randomness
    in the image's pixel intensity distribution.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        float: Shannon entropy value in bits.
        
    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image cannot be loaded or processed.
    """
    image = _load_image_as_grayscale(image_path)
    
    # Calculate histogram
    hist, _ = np.histogram(image, bins=256, range=(0, 256))
    
    # Normalize to probability distribution
    prob = hist / hist.sum()
    
    # Remove zero probabilities to avoid log(0)
    prob = prob[prob > 0]
    
    # Calculate Shannon entropy
    entropy = -np.sum(prob * np.log2(prob))
    
    return float(entropy)

def calculate_fractal_dimension(image_path: Union[str, Path]) -> float:
    """
    Calculate the Fractal Dimension of an image using the Box-Counting method.
    
    The fractal dimension estimates the complexity of the image structure
    by counting how the detail in the image changes with scale.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        float: Fractal dimension value (typically between 1 and 2 for 2D images).
        
    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image cannot be loaded or processed.
    """
    image = _load_image_as_grayscale(image_path)
    
    # Normalize image to 0-1 range for thresholding
    img_norm = (image - image.min()) / (image.max() - image.min())
    
    # Convert to binary using Otsu's thresholding approximation
    # Use simple mean threshold for robustness
    threshold = img_norm.mean()
    binary_img = (img_norm > threshold).astype(float)
    
    # Box-counting method
    # Try different box sizes (powers of 2)
    sizes = []
    counts = []
    
    img_size = binary_img.shape[0]
    
    # Use box sizes from img_size down to 2
    for scale in [2**i for i in range(int(np.log2(img_size)) - 1, 0, -1)]:
        if scale < 2:
            continue
            
        # Count non-empty boxes
        # Resize image to box size and count non-zero pixels
        small_img = ndimage.zoom(binary_img, scale / img_size, order=0)
        count = np.sum(small_img > 0)
        
        if count > 0:
            sizes.append(scale)
            counts.append(count)
    
    if len(sizes) < 2:
        # Fallback for very small images
        return 1.5
    
    # Linear regression to estimate fractal dimension
    # log(N) = -D * log(s) + C
    log_sizes = np.log(sizes)
    log_counts = np.log(counts)
    
    # Fit line: y = mx + c, where m = -D
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = -coeffs[0]
    
    # Ensure reasonable bounds for 2D images
    fractal_dim = np.clip(fractal_dim, 1.0, 2.0)
    
    return float(fractal_dim)

def calculate_texture_complexity(image_path: Union[str, Path]) -> Dict[str, float]:
    """
    Calculate texture complexity metrics using GLCM (Gray-Level Co-occurrence Matrix).
    
    Computes contrast, correlation, energy, and homogeneity, then combines them
    into a composite score.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        dict: Dictionary containing texture metrics and composite score.
        
    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image cannot be loaded or processed.
    """
    image = _load_image_as_grayscale(image_path)
    
    # Normalize to 0-255 and convert to uint8
    img_norm = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
    
    # Calculate GLCM with 4 directions and distance=1
    glcm = graycomatrix(img_norm, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
                        levels=256, symmetric=True, normed=True)
    
    # Calculate texture properties
    contrast = float(graycoprops(glcm, 'contrast').mean())
    correlation = float(graycoprops(glcm, 'correlation').mean())
    energy = float(graycoprops(glcm, 'energy').mean())
    homogeneity = float(graycoprops(glcm, 'homogeneity').mean())
    
    # Composite score: weighted combination
    # Higher contrast and lower homogeneity/energy indicate more complexity
    composite_score = (contrast * 0.4) + (1 - homogeneity) * 0.3 + (1 - energy) * 0.3
    
    return {
        'contrast': contrast,
        'correlation': correlation,
        'energy': energy,
        'homogeneity': homogeneity,
        'composite_score': composite_score
    }

def convolve_with_hrf(signal: np.ndarray, tr: float = 2.0, 
                     peak_time: float = 5.0, undershoot_time: float = 15.0) -> np.ndarray:
    """
    Convolve a signal with a canonical Hemodynamic Response Function (HRF).
    
    Uses a double-gamma HRF model to simulate the BOLD response.
    
    Args:
        signal: Input time series (complexity metrics).
        tr: Repetition time in seconds.
        peak_time: Time to peak of the HRF in seconds.
        undershoot_time: Time to undershoot of the HRF in seconds.
        
    Returns:
        np.ndarray: HRF-convolved signal.
    """
    n = len(signal)
    t = np.arange(n) * tr
    
    # Create HRF kernel using double-gamma model
    # First gamma (positive response)
    hrf1 = (t / peak_time) ** 6 * np.exp(-(t - peak_time) / (peak_time / 6))
    hrf1[t < 0] = 0
    
    # Second gamma (undershoot)
    hrf2 = 0.35 * (t / undershoot_time) ** 12 * np.exp(-(t - undershoot_time) / (undershoot_time / 12))
    hrf2[t < 0] = 0
    
    # Combined HRF
    hrf = hrf1 - hrf2
    
    # Normalize HRF
    hrf = hrf / (hrf.sum() + 1e-10)
    
    # Convolve
    convolved = np.convolve(signal, hrf, mode='same')
    
    return convolved

def batch_process_complexity(image_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
    """
    Process multiple images and compute complexity metrics for each.
    
    Args:
        image_paths: List of paths to image files.
        
    Returns:
        list: List of dictionaries containing metrics for each image.
    """
    results = []
    
    for path in image_paths:
        try:
            entropy_val = calculate_entropy(path)
            fractal_val = calculate_fractal_dimension(path)
            texture_metrics = calculate_texture_complexity(path)
            
            results.append({
                'path': str(path),
                'entropy': entropy_val,
                'fractal_dimension': fractal_val,
                'texture': texture_metrics,
                'composite_score': texture_metrics['composite_score']
            })
            logger.info(f"Processed {path}: entropy={entropy_val:.4f}, fractal={fractal_val:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            results.append({
                'path': str(path),
                'entropy': None,
                'fractal_dimension': None,
                'texture': None,
                'composite_score': None,
                'error': str(e)
            })
    
    return results