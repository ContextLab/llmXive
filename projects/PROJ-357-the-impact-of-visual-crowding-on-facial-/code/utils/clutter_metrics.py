import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import cv2

# Import project config
from config import ensure_directories, get_seed, set_all_seeds
from utils.manifest_validator import load_manifest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def compute_local_contrast_variance(image: np.ndarray, flanker_region: tuple) -> float:
    """
    Compute the local contrast variance within the specified flanker region.
    
    Args:
        image: Grayscale or color image as numpy array.
        flanker_region: Tuple (y_min, y_max, x_min, x_max) defining the ROI.
    
    Returns:
        float: Variance of local contrast in the region.
    """
    y_min, y_max, x_min, x_max = flanker_region
    
    # Extract ROI
    roi = image[y_min:y_max, x_min:x_max]
    
    if roi.size == 0:
        return 0.0
    
    # Convert to grayscale if necessary
    if len(roi.shape) == 3:
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    else:
        roi_gray = roi.astype(np.float32)
    
    # Compute local contrast using Sobel gradients
    # Sobel operator for X and Y directions
    sobelx = cv2.Sobel(roi_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(roi_gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # Magnitude of gradient
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    
    # Variance of gradient magnitude represents local contrast variance
    variance = np.var(gradient_magnitude)
    
    return float(variance)

def compute_spatial_frequency_energy(image: np.ndarray, flanker_region: tuple) -> float:
    """
    Compute the spatial frequency energy within the specified flanker region.
    
    Uses 2D Fast Fourier Transform (FFT) to analyze spatial frequencies.
    The energy is the sum of squared magnitudes of the frequency components.
    
    Args:
        image: Grayscale or color image as numpy array.
        flanker_region: Tuple (y_min, y_max, x_min, x_max) defining the ROI.
    
    Returns:
        float: Total spatial frequency energy in the region.
    """
    y_min, y_max, x_min, x_max = flanker_region
    
    # Extract ROI
    roi = image[y_min:y_max, x_min:x_max]
    
    if roi.size == 0:
        return 0.0
    
    # Convert to grayscale if necessary
    if len(roi.shape) == 3:
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    else:
        roi_gray = roi.astype(np.float32)
    
    # Apply 2D FFT
    fft_result = np.fft.fft2(roi_gray)
    fft_shift = np.fft.fftshift(fft_result)
    
    # Compute magnitude spectrum
    magnitude_spectrum = np.abs(fft_shift)
    
    # Compute energy (sum of squared magnitudes)
    energy = np.sum(magnitude_spectrum ** 2)
    
    return float(energy)

def determine_flanker_region(image_shape: tuple, eccentricity: float, flanker_count: int) -> tuple:
    """
    Determine the bounding box for the flanker region based on stimulus parameters.
    
    This is a heuristic approximation since we don't have the exact geometric
    construction parameters stored. We assume flankers are arranged in a ring
    around the central target at a distance defined by eccentricity.
    
    Args:
        image_shape: Tuple (height, width, channels) of the full image.
        eccentricity: Eccentricity value (visual angle or relative distance).
        flanker_count: Number of flankers.
    
    Returns:
        Tuple (y_min, y_max, x_min, x_max) for the flanker region ROI.
    """
    h, w = image_shape[:2]
    center_y, center_x = h // 2, w // 2
    
    # Normalize eccentricity to pixels (assuming max eccentricity ~10% of image dimension)
    # This is an approximation; in a real implementation, we'd use the exact construction params
    max_dim = max(h, w)
    eccentricity_pixels = (eccentricity / 100.0) * (max_dim / 2) if eccentricity > 1.0 else eccentricity * (max_dim / 2)
    
    # Define a ring region around the center
    # The flanker region is the area where flankers are placed
    # We'll define a bounding box that encompasses the expected flanker positions
    ring_radius = eccentricity_pixels
    flanker_size_estimate = 20  # Approximate flanker size in pixels
    
    y_min = max(0, int(center_y - ring_radius - flanker_size_estimate))
    y_max = min(h, int(center_y + ring_radius + flanker_size_estimate))
    x_min = max(0, int(center_x - ring_radius - flanker_size_estimate))
    x_max = min(w, int(center_x + ring_radius + flanker_size_estimate))
    
    return (y_min, y_max, x_min, x_max)

def process_stimulus_image(image_path: Path, manifest_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute clutter metrics for a single stimulus image.
    
    Args:
        image_path: Path to the stimulus image file.
        manifest_entry: Dictionary containing stimulus metadata.
    
    Returns:
        Dictionary with computed metrics.
    """
    try:
        # Load image
        img = Image.open(str(image_path))
        img_array = np.array(img)
        
        # Extract parameters from manifest
        eccentricity = float(manifest_entry.get('eccentricity', 0))
        flanker_count = int(manifest_entry.get('flanker_count', 0))
        
        # Determine flanker region
        flanker_region = determine_flanker_region(img_array.shape, eccentricity, flanker_count)
        
        # Compute metrics
        local_contrast_var = compute_local_contrast_variance(img_array, flanker_region)
        spatial_freq_energy = compute_spatial_frequency_energy(img_array, flanker_region)
        
        return {
            'file_path': str(image_path),
            'local_contrast_variance': local_contrast_var,
            'spatial_frequency_energy': spatial_freq_energy,
            'flanker_count': flanker_count,
            'eccentricity': eccentricity,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}")
        return {
            'file_path': str(image_path),
            'local_contrast_variance': None,
            'spatial_frequency_energy': None,
            'flanker_count': manifest_entry.get('flanker_count', 0),
            'eccentricity': manifest_entry.get('eccentricity', 0),
            'status': 'error',
            'error_message': str(e)
        }

def compute_clutter_metrics(manifest_path: Path, stimuli_dir: Path, output_path: Path, chunk_size: int = 100):
    """
    Compute clutter metrics for all stimuli in the manifest.
    
    Implements chunked processing to manage memory usage.
    
    Args:
        manifest_path: Path to stimuli_manifest.json.
        stimuli_dir: Directory containing stimulus images.
        output_path: Path for the output CSV file.
        chunk_size: Number of images to process per chunk.
    """
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}")
    manifest = load_manifest(manifest_path)
    
    if not manifest or 'stimuli' not in manifest:
        logger.error("Invalid manifest format or empty stimuli list")
        return
    
    stimuli_list = manifest['stimuli']
    total_items = len(stimuli_list)
    logger.info(f"Processing {total_items} stimuli")
    
    results = []
    
    # Process in chunks to manage memory
    for i in range(0, total_items, chunk_size):
        chunk = stimuli_list[i:i + chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1}: items {i} to {min(i + chunk_size - 1, total_items - 1)}")
        
        for entry in chunk:
            # Construct image path
            filename = entry.get('file_path', '')
            if not filename:
                # Try to reconstruct from other fields if file_path is missing
                emotion = entry.get('emotion', 'unknown')
                flanker_count = entry.get('flanker_count', 0)
                eccentricity = entry.get('eccentricity', 0)
                filename = f"stimulus_emotion_{emotion}_flankers_{flanker_count}_ecc_{eccentricity}.png"
            
            image_path = stimuli_dir / filename
            
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}")
                results.append({
                    'file_path': str(image_path),
                    'local_contrast_variance': None,
                    'spatial_frequency_energy': None,
                    'flanker_count': entry.get('flanker_count', 0),
                    'eccentricity': entry.get('eccentricity', 0),
                    'status': 'missing_image',
                    'error_message': 'Image file not found'
                })
                continue
            
            # Process image
            result = process_stimulus_image(image_path, entry)
            results.append(result)
        
        # Optional: Force garbage collection between chunks
        if i + chunk_size < total_items:
            import gc
            gc.collect()
    
    # Write results to CSV
    logger.info(f"Writing results to {output_path}")
    
    # Prepare CSV data
    csv_headers = ['file_path', 'local_contrast_variance', 'spatial_frequency_energy', 
                  'flanker_count', 'eccentricity', 'status', 'error_message']
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(','.join(csv_headers) + '\n')
        
        for res in results:
            row = [
                res['file_path'],
                str(res['local_contrast_variance']) if res['local_contrast_variance'] is not None else '',
                str(res['spatial_frequency_energy']) if res['spatial_frequency_energy'] is not None else '',
                str(res['flanker_count']),
                str(res['eccentricity']),
                res['status'],
                res.get('error_message', '')
            ]
            # Escape commas in file paths
            row = [f'"{val}"' if ',' in val else val for val in row]
            f.write(','.join(row) + '\n')
    
    # Log summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] != 'success')
    logger.info(f"Completed: {success_count} successful, {error_count} errors")

def main():
    """Main entry point for clutter metrics computation."""
    # Set seed for reproducibility
    set_all_seeds(get_seed())
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / 'data' / 'interim' / 'stimuli_manifest.json'
    stimuli_dir = project_root / 'data' / 'interim' / 'stimuli'
    output_path = project_root / 'data' / 'processed' / 'clutter_metrics.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if manifest exists
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        sys.exit(1)
    
    # Check if stimuli directory exists
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        sys.exit(1)
    
    # Run computation
    compute_clutter_metrics(manifest_path, stimuli_dir, output_path)
    
    logger.info("Clutter metrics computation completed successfully")

if __name__ == '__main__':
    main()
