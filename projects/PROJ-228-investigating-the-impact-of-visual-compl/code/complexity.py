import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from PIL import Image
from skimage.feature import graycomatrix, graycoprops
from scipy import ndimage
import csv
import logging
import os
import sys

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR, DATASET_ID, HRF_PEAK, HRF_UNDERSHOOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_INTERIM_DIR / "complexity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def calculate_entropy(image_path: Path) -> float:
    """
    Calculate Shannon Entropy of an image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Shannon entropy value.
    """
    try:
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        img_array = np.array(img)
        
        # Calculate histogram
        hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
        hist = hist / hist.sum()  # Normalize
        
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        return float(entropy)
    except Exception as e:
        logger.error(f"Error calculating entropy for {image_path}: {e}")
        return 0.0

def calculate_fractal_dimension(image_path: Path) -> float:
    """
    Calculate Fractal Dimension (Box-counting method approximation) of an image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Approximate fractal dimension.
    """
    try:
        img = Image.open(image_path).convert('L')
        img_array = np.array(img, dtype=float)
        
        # Normalize to 0-1
        img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min() + 1e-10)
        
        # Simple box-counting approximation
        # Using a few scales to estimate slope
        sizes = [2**i for i in range(1, 5)] # 2, 4, 8, 16
        counts = []
        
        for size in sizes:
            if size >= img_array.shape[0] or size >= img_array.shape[1]:
                continue
            
            # Count non-empty boxes
            count = 0
            for i in range(0, img_array.shape[0], size):
                for j in range(0, img_array.shape[1], size):
                    box = img_array[i:i+size, j:j+size]
                    if np.max(box) > 0: # Non-empty
                        count += 1
            counts.append(count)
        
        if len(counts) < 2:
            return 1.5 # Default fallback
        
        # Linear regression to find slope
        log_sizes = np.log(1/np.array(sizes[:len(counts)]))
        log_counts = np.log(counts)
        
        slope, _ = np.polyfit(log_sizes, log_counts, 1)
        return float(slope)
    except Exception as e:
        logger.error(f"Error calculating fractal dimension for {image_path}: {e}")
        return 0.0

def calculate_texture_complexity(image_path: Path) -> Dict[str, float]:
    """
    Calculate texture complexity using GLCM.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Dictionary with texture features.
    """
    try:
        img = Image.open(image_path).convert('L')
        img_array = np.array(img)
        
        # Calculate GLCM
        glcm = graycomatrix(img_array, distances=[5], angles=[0], levels=256, symmetric=True, normed=True)
        
        # Calculate properties
        contrast = graycoprops(glcm, 'contrast')[0, 0]
        dissimilarity = graycoprops(glcm, 'dissimilarity')[0, 0]
        homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        energy = graycoprops(glcm, 'energy')[0, 0]
        correlation = graycoprops(glcm, 'correlation')[0, 0]
        ASM = graycoprops(glcm, 'ASM')[0, 0]
        
        return {
            'contrast': float(contrast),
            'dissimilarity': float(dissimilarity),
            'homogeneity': float(homogeneity),
            'energy': float(energy),
            'correlation': float(correlation),
            'ASM': float(ASM)
        }
    except Exception as e:
        logger.error(f"Error calculating texture complexity for {image_path}: {e}")
        return {}

def convolve_with_hrf(time_series: List[float], tr: float = 2.0) -> List[float]:
    """
    Convolve a time series with a canonical HRF (double-gamma).
    
    Args:
        time_series: Input time series (complexity metrics).
        tr: Repetition Time in seconds.
        
    Returns:
        Convolved time series.
    """
    # Simple double-gamma HRF approximation
    # Peak = 5s, Undershoot = 15s
    n_points = int((HRF_PEAK + HRF_UNDERSHOOT) / tr) + 10
    hrf = []
    
    for t in range(n_points):
        time = t * tr
        # Double gamma function
        gamma_peak = (time ** 6) * np.exp(-time / 1.0) # Approximate peak
        gamma_undershoot = 0.35 * (time ** 12) * np.exp(-time / 2.0) # Approximate undershoot
        hrf_val = gamma_peak - gamma_undershoot
        hrf.append(hrf_val)
    
    # Normalize HRF
    hrf = np.array(hrf)
    hrf = hrf / (np.max(hrf) + 1e-10)
    
    # Convolve
    convolved = np.convolve(time_series, hrf, mode='full')
    
    # Truncate to original length (or pad if necessary)
    if len(convolved) > len(time_series):
        convolved = convolved[:len(time_series)]
    elif len(convolved) < len(time_series):
        convolved = np.pad(convolved, (0, len(time_series) - len(convolved)), mode='edge')
        
    return convolved.tolist()

def batch_process_complexity() -> Path:
    """
    Batch process all stimulus images in data/raw/DATASET_ID.
    Computes entropy, fractal dimension, and HRF-convolved values.
    Writes results to data/interim/complexity_metrics.csv.
    
    Returns:
        Path to the output CSV file.
    """
    # Find stimulus images
    # Assuming structure: data/raw/ds000246/stimuli/... or similar
    # We search recursively for image files
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    image_files = []
    
    search_path = DATA_RAW_DIR / DATASET_ID
    if not search_path.exists():
        logger.error(f"Search path {search_path} does not exist. Cannot process complexity.")
        raise FileNotFoundError(f"Dataset directory {search_path} not found.")
    
    for ext in image_extensions:
        image_files.extend(search_path.rglob(f"*{ext}"))
        image_files.extend(search_path.rglob(f"*{ext.upper()}"))
    
    if not image_files:
        logger.warning(f"No image files found in {search_path}.")
        # Create empty CSV with headers
        output_path = DATA_INTERIM_DIR / "complexity_metrics.csv"
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["frame_id", "timestamp", "entropy", "fractal_dim", "hrf_convolved"])
        return output_path

    logger.info(f"Found {len(image_files)} images to process.")
    
    results = []
    entropy_values = []
    
    # Sort files to ensure consistent ordering (e.g., by name or timestamp if available)
    image_files.sort(key=lambda x: x.name)
    
    for idx, img_path in enumerate(image_files):
        logger.info(f"Processing {idx+1}/{len(image_files)}: {img_path.name}")
        
        entropy = calculate_entropy(img_path)
        fractal_dim = calculate_fractal_dimension(img_path)
        
        # Handle NaN/Inf
        if np.isnan(entropy) or np.isinf(entropy):
            logger.warning(f"NaN/Inf entropy for {img_path.name}, replacing with 0")
            entropy = 0.0
        if np.isnan(fractal_dim) or np.isinf(fractal_dim):
            logger.warning(f"NaN/Inf fractal_dim for {img_path.name}, replacing with 0")
            fractal_dim = 0.0
            
        entropy_values.append(entropy)
        
        results.append({
            'frame_id': idx,
            'timestamp': idx * 2.0, # Assuming TR=2.0s for simplicity, or derived from data
            'entropy': entropy,
            'fractal_dim': fractal_dim
        })
    
    # Convolve with HRF
    hrf_convolved = convolve_with_hrf(entropy_values, tr=2.0)
    
    for i, res in enumerate(results):
        res['hrf_convolved'] = hrf_convolved[i]
    
    # Write to CSV
    output_path = DATA_INTERIM_DIR / "complexity_metrics.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["frame_id", "timestamp", "entropy", "fractal_dim", "hrf_convolved"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Complexity metrics written to {output_path}")
    return output_path

def main():
    """Main entry point for complexity calculation."""
    logger.info("Starting complexity calculation...")
    try:
        output_path = batch_process_complexity()
        logger.info(f"Complexity calculation complete. Output: {output_path}")
    except Exception as e:
        logger.error(f"Complexity calculation failed: {e}")
        raise

if __name__ == "__main__":
    main()
