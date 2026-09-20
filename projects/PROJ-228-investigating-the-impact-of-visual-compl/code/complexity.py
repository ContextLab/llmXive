import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from PIL import Image
from skimage.feature import graycomatrix, graycoprops
from scipy import ndimage
import pandas as pd
from scipy.signal import convolve
import logging
import psutil
import os

from config import init_seeds, DATA_INTERIM, DATA_RAW
from update_metadata import init_metadata, update_metadata_with_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/complexity_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize seeds
init_seeds()

def calculate_entropy(image_path: Path) -> float:
    """
    Calculate Shannon Entropy of a grayscale image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Shannon entropy value.
    """
    img = Image.open(image_path).convert('L')
    img_array = np.array(img, dtype=float)
    
    # Normalize to 0-1
    img_array = img_array / 255.0
    
    # Calculate histogram
    hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 1))
    hist = hist / hist.sum()
    
    # Remove zero probabilities to avoid log(0)
    hist = hist[hist > 0]
    
    entropy = -np.sum(hist * np.log2(hist))
    return float(entropy)

def calculate_fractal_dimension(image_path: Path) -> float:
    """
    Calculate Fractal Dimension using the Box-Counting method.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Fractal dimension value.
    """
    img = Image.open(image_path).convert('L')
    img_array = np.array(img, dtype=float)
    
    # Normalize
    img_array = img_array / 255.0
    
    # Box counting
    sizes = [2**i for i in range(1, 6)]
    counts = []
    
    for size in sizes:
        if size >= img_array.shape[0] or size >= img_array.shape[1]:
            continue
            
        # Count non-empty boxes
        count = 0
        for i in range(0, img_array.shape[0], size):
            for j in range(0, img_array.shape[1], size):
                box = img_array[i:i+size, j:j+size]
                if np.max(box) - np.min(box) > 0.01:  # Threshold for non-empty
                    count += 1
        counts.append(count)
    
    if len(counts) < 2:
        return 1.0  # Default fallback
        
    # Linear regression on log-log plot
    log_sizes = np.log(sizes[:len(counts)])
    log_counts = np.log(counts)
    
    slope, _ = np.polyfit(log_sizes, log_counts, 1)
    fractal_dim = -slope
    
    return float(fractal_dim)

def calculate_texture_complexity(image_path: Path) -> float:
    """
    Calculate texture complexity using GLCM properties.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Texture complexity score.
    """
    img = Image.open(image_path).convert('L')
    img_array = np.array(img, dtype=np.uint8)
    
    # Calculate GLCM
    glcm = graycomatrix(img_array, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
    
    # Extract properties
    contrast = graycoprops(glcm, 'contrast')[0, 0]
    dissimilarity = graycoprops(glcm, 'dissimilarity')[0, 0]
    homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
    energy = graycoprops(glcm, 'energy')[0, 0]
    correlation = graycoprops(glcm, 'correlation')[0, 0]
    
    # Combine into a single complexity score
    complexity = (contrast + dissimilarity - homogeneity - energy) / 2
    
    return float(complexity)

def convolve_with_hrf(complexity_values: np.ndarray, tr: float = 2.0, 
                     peak: float = 5.0, undershoot: float = 15.0) -> np.ndarray:
    """
    Convolve complexity values with a double-gamma HRF model.
    
    Args:
        complexity_values: Array of complexity values over time.
        tr: Repetition time in seconds.
        peak: Peak of the HRF in seconds.
        undershoot: Undershoot of the HRF in seconds.
        
    Returns:
        HRF-convolved complexity values.
    """
    # Create time vector for HRF
    hrf_duration = 32  # Standard HRF duration
    hrf_time = np.arange(0, hrf_duration, tr)
    
    # Double-gamma HRF model
    # First gamma (peak)
    alpha1 = 6
    beta1 = 1
    gamma1 = 1
    hrf1 = (hrf_time / alpha1)**(beta1 - 1) * np.exp(-hrf_time / (alpha1 * beta1))
    
    # Second gamma (undershoot)
    alpha2 = 12
    beta2 = 1
    gamma2 = 0.35
    hrf2 = (hrf_time / alpha2)**(beta2 - 1) * np.exp(-hrf_time / (alpha2 * beta2))
    
    # Combine with appropriate scaling
    hrf = gamma1 * hrf1 - gamma2 * hrf2
    hrf = hrf / np.max(hrf)  # Normalize
    
    # Convolve
    convolved = convolve(complexity_values, hrf, mode='full')
    
    # Trim to original length (center alignment)
    start_idx = (len(convolved) - len(complexity_values)) // 2
    end_idx = start_idx + len(complexity_values)
    
    return convolved[start_idx:end_idx]

def batch_process_complexity(image_dir: Path, output_path: Path, 
                            tr: float = 2.0, 
                            max_memory_gb: float = 6.0) -> None:
    """
    Process all images in a directory and write complexity metrics to CSV.
    
    Args:
        image_dir: Directory containing stimulus images.
        output_path: Path for the output CSV file.
        tr: Repetition time in seconds.
        max_memory_gb: Maximum memory usage in GB.
    """
    # Check memory before processing
    process = psutil.Process(os.getpid())
    current_memory = process.memory_info().rss / (1024 ** 3)
    
    if current_memory > max_memory_gb:
        logger.error(f"Memory usage ({current_memory:.2f} GB) exceeds limit ({max_memory_gb} GB)")
        raise MemoryError(f"Memory usage exceeds limit: {current_memory:.2f} GB > {max_memory_gb} GB")
    
    # Get all image files
    image_files = sorted(list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg")))
    
    if not image_files:
        logger.warning(f"No image files found in {image_dir}")
        return
    
    logger.info(f"Processing {len(image_files)} images...")
    
    results = []
    
    for i, img_path in enumerate(image_files):
        # Check memory periodically
        if i % 10 == 0:
            current_memory = process.memory_info().rss / (1024 ** 3)
            if current_memory > max_memory_gb:
                logger.error(f"Memory usage ({current_memory:.2f} GB) exceeds limit during processing")
                raise MemoryError(f"Memory usage exceeded limit: {current_memory:.2f} GB")
        
        try:
            # Calculate metrics
            entropy = calculate_entropy(img_path)
            fractal_dim = calculate_fractal_dimension(img_path)
            texture_complexity = calculate_texture_complexity(img_path)
            
            # Store results
            results.append({
                'frame_id': i,
                'timestamp': i * tr,
                'entropy': entropy,
                'fractal_dim': fractal_dim,
                'texture_complexity': texture_complexity
            })
            
            logger.debug(f"Processed {img_path.name}: entropy={entropy:.4f}, fractal_dim={fractal_dim:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing {img_path}: {str(e)}")
            # Replace with 0 for NaN/Inf handling
            results.append({
                'frame_id': i,
                'timestamp': i * tr,
                'entropy': 0.0,
                'fractal_dim': 0.0,
                'texture_complexity': 0.0
            })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convolve with HRF
    logger.info("Applying HRF convolution...")
    df['hrf_convolved'] = convolve_with_hrf(
        df['texture_complexity'].values, 
        tr=tr
    )
    
    # Handle NaN/Inf values
    nan_count = df.isna().sum().sum()
    inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
    
    if nan_count > 0 or inf_count > 0:
        logger.warning(f"Found {nan_count} NaN and {inf_count} Inf values. Replacing with 0.")
        df = df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    # Log first 5 rows
    logger.info("First 5 rows of output:")
    for _, row in df.head().iterrows():
        logger.info(f"  {row.to_dict()}")
    
    logger.info(f"Successfully wrote complexity metrics to {output_path}")

def main():
    """Main entry point for complexity analysis."""
    # Define paths
    stimulus_dir = DATA_RAW / "ds000246" / "stimuli"
    output_file = DATA_INTERIM / "complexity_metrics.csv"
    
    # Ensure directories exist
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    
    # Process images
    batch_process_complexity(stimulus_dir, output_file, tr=2.0)
    
    return output_file

if __name__ == "__main__":
    main()