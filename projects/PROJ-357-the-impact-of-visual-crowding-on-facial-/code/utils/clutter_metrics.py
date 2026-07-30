import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/interim/clutter_metrics.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
STIMULI_DIR = Path("data/interim/stimuli")
MANIFEST_PATH = Path("data/interim/stimuli_manifest.json")
OUTPUT_PATH = Path("data/processed/clutter_metrics.csv")
VALIDATION_REPORT_PATH = Path("data/processed/validation_report.json")

# Memory constraints (in GB)
MAX_MEMORY_GB = 7.0
MEMORY_SAFETY_FACTOR = 0.8  # Use 80% of available memory as threshold
SAMPLE_SIZE_THRESHOLD = 100  # Minimum sample size before switching to sampling fallback

def get_available_memory_gb() -> float:
    """Estimate available system memory in GB."""
    try:
        import psutil
        available_bytes = psutil.virtual_memory().available
        return available_bytes / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not available, assuming 4GB available memory")
        return 4.0
    except Exception as e:
        logger.warning(f"Could not determine available memory: {e}, assuming 4GB")
        return 4.0

def determine_flanker_region(image: np.ndarray, flanker_count: int, eccentricity: float) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Determine the flanker region of the stimulus image.
    
    Args:
        image: Input image array (H, W, C)
        flanker_count: Number of flankers in the stimulus
        eccentricity: Eccentricity value used in stimulus generation
    
    Returns:
        Tuple of (flanker_region_array, metadata_dict)
    """
    h, w = image.shape[:2]
    center_y, center_x = h // 2, w // 2
    
    # Calculate flanker region based on eccentricity
    # Assuming eccentricity is in degrees and we approximate 1 degree ≈ 20 pixels
    radius = int(eccentricity * 20)
    
    # Define region of interest around the center
    y1 = max(0, center_y - radius)
    y2 = min(h, center_y + radius)
    x1 = max(0, center_x - radius)
    x2 = min(w, center_x + radius)
    
    flanker_region = image[y1:y2, x1:x2]
    
    metadata = {
        'region_coords': {'y1': y1, 'y2': y2, 'x1': x1, 'x2': x2},
        'radius': radius,
        'center': (center_x, center_y)
    }
    
    return flanker_region, metadata

def compute_local_contrast_variance(flanker_region: np.ndarray) -> float:
    """
    Compute local contrast variance for the flanker region.
    
    Args:
        flanker_region: Image region to analyze (H, W, C) or (H, W)
    
    Returns:
        Local contrast variance value
    """
    if flanker_region.ndim == 3:
        # Convert to grayscale if needed
        if flanker_region.shape[2] == 3:
            gray = np.dot(flanker_region[..., :3], [0.2989, 0.5870, 0.1140])
        else:
            gray = flanker_region[..., 0]
    else:
        gray = flanker_region
    
    # Ensure float for calculations
    gray = gray.astype(np.float32)
    
    # Normalize to 0-1
    gray = gray / 255.0
    
    # Compute local contrast using a sliding window
    window_size = 5
    h, w = gray.shape
    
    # Pad the image
    padded = np.pad(gray, ((window_size//2, window_size//2), 
                           (window_size//2, window_size//2)), 
                   mode='reflect')
    
    contrasts = []
    for i in range(h):
        for j in range(w):
            window = padded[i:i+window_size, j:j+window_size]
            mean_val = np.mean(window)
            std_val = np.std(window)
            if mean_val > 0:
                contrast = std_val / mean_val
            else:
                contrast = 0.0
            contrasts.append(contrast)
    
    contrasts = np.array(contrasts)
    variance = np.var(contrasts)
    
    return float(variance)

def compute_spatial_frequency_energy(flanker_region: np.ndarray) -> float:
    """
    Compute spatial frequency energy for the flanker region.
    
    Args:
        flanker_region: Image region to analyze (H, W, C) or (H, W)
    
    Returns:
        Spatial frequency energy value
    """
    if flanker_region.ndim == 3:
        # Convert to grayscale if needed
        if flanker_region.shape[2] == 3:
            gray = np.dot(flanker_region[..., :3], [0.2989, 0.5870, 0.1140])
        else:
            gray = flanker_region[..., 0]
    else:
        gray = flanker_region
    
    # Ensure float for calculations
    gray = gray.astype(np.float32)
    
    # Normalize to 0-1
    gray = gray / 255.0
    
    # Compute 2D FFT
    fft_result = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft_result)
    
    # Compute magnitude spectrum
    magnitude = np.abs(fft_shift)
    
    # Compute energy (sum of squared magnitudes)
    energy = np.sum(magnitude ** 2)
    
    # Normalize by number of pixels
    h, w = gray.shape
    normalized_energy = energy / (h * w)
    
    return float(normalized_energy)

def process_stimulus_image(image_path: Path, manifest_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single stimulus image and compute clutter metrics.
    
    Args:
        image_path: Path to the stimulus image
        manifest_entry: Entry from the stimuli manifest containing metadata
    
    Returns:
        Dictionary containing image path and computed metrics
    """
    try:
        from PIL import Image
        image = np.array(Image.open(image_path))
    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        return None
    
    # Extract metadata from manifest entry
    flanker_count = manifest_entry.get('flanker_count', 0)
    eccentricity = manifest_entry.get('eccentricity', 0.0)
    
    # Determine flanker region
    flanker_region, region_metadata = determine_flanker_region(image, flanker_count, eccentricity)
    
    # Compute metrics
    local_contrast_variance = compute_local_contrast_variance(flanker_region)
    spatial_frequency_energy = compute_spatial_frequency_energy(flanker_region)
    
    result = {
        'image_path': str(image_path),
        'emotion': manifest_entry.get('emotion', 'unknown'),
        'flanker_count': flanker_count,
        'eccentricity': eccentricity,
        'local_contrast_variance': local_contrast_variance,
        'spatial_frequency_energy': spatial_frequency_energy,
        'region_metadata': region_metadata,
        'status': 'success'
    }
    
    return result

def compute_clutter_metrics(sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Compute clutter metrics for all stimuli in the manifest.
    
    Args:
        sample_size: Optional number of stimuli to process (for sampling fallback)
    
    Returns:
        List of dictionaries containing image paths and computed metrics
    """
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    
    stimuli_files = [entry for entry in manifest if entry.get('status') == 'success']
    
    if sample_size is not None and sample_size < len(stimuli_files):
        logger.info(f"Using sampling fallback: processing {sample_size} of {len(stimuli_files)} stimuli")
        import random
        random.seed(42)  # For reproducibility
        stimuli_files = random.sample(stimuli_files, sample_size)
    
    results = []
    estimated_memory_per_item = 0.01  # Estimated MB per item (rough estimate)
    current_memory_usage = 0.0
    
    for i, entry in enumerate(stimuli_files):
        image_path = STIMULI_DIR / entry['file_path']
        
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            results.append({
                'image_path': str(image_path),
                'emotion': entry.get('emotion', 'unknown'),
                'flanker_count': entry.get('flanker_count', 0),
                'eccentricity': entry.get('eccentricity', 0.0),
                'status': 'error',
                'error': 'Image not found'
            })
            continue
        
        # Check memory usage
        current_memory_usage += estimated_memory_per_item
        available_memory = get_available_memory_gb() * 1024  # Convert to MB
        
        # If memory usage exceeds threshold, switch to sampling fallback
        if current_memory_usage > (available_memory * MEMORY_SAFETY_FACTOR):
            logger.warning(f"Memory threshold exceeded ({current_memory_usage:.2f}MB > {available_memory * MEMORY_SAFETY_FACTOR:.2f}MB)")
            logger.info("Switching to sampling fallback mechanism")
            
            # Calculate remaining items to process with sampling
            remaining_items = len(stimuli_files) - i
            if remaining_items > SAMPLE_SIZE_THRESHOLD:
                # Sample a subset of remaining items
                sample_count = min(SAMPLE_SIZE_THRESHOLD, remaining_items)
                remaining_files = stimuli_files[i:]
                import random
                random.seed(42)
                sampled_files = random.sample(remaining_files, sample_count)
                
                # Process sampled files
                for sampled_entry in sampled_files:
                    sampled_path = STIMULI_DIR / sampled_entry['file_path']
                    if sampled_path.exists():
                        result = process_stimulus_image(sampled_path, sampled_entry)
                        if result:
                            results.append(result)
                    else:
                        results.append({
                            'image_path': str(sampled_path),
                            'emotion': sampled_entry.get('emotion', 'unknown'),
                            'flanker_count': sampled_entry.get('flanker_count', 0),
                            'eccentricity': sampled_entry.get('eccentricity', 0.0),
                            'status': 'error',
                            'error': 'Image not found'
                        })
            else:
                # Process all remaining items (not enough to justify sampling)
                for remaining_entry in stimuli_files[i:]:
                    remaining_path = STIMULI_DIR / remaining_entry['file_path']
                    if remaining_path.exists():
                        result = process_stimulus_image(remaining_path, remaining_entry)
                        if result:
                            results.append(result)
                    else:
                        results.append({
                            'image_path': str(remaining_path),
                            'emotion': remaining_entry.get('emotion', 'unknown'),
                            'flanker_count': remaining_entry.get('flanker_count', 0),
                            'eccentricity': remaining_entry.get('eccentricity', 0.0),
                            'status': 'error',
                            'error': 'Image not found'
                        })
            break
        
        # Process current item
        result = process_stimulus_image(image_path, entry)
        if result:
            results.append(result)
        else:
            results.append({
                'image_path': str(image_path),
                'emotion': entry.get('emotion', 'unknown'),
                'flanker_count': entry.get('flanker_count', 0),
                'eccentricity': entry.get('eccentricity', 0.0),
                'status': 'error',
                'error': 'Processing failed'
            })
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(stimuli_files)} stimuli")
    
    return results

def save_metrics_to_csv(results: List[Dict[str, Any]]) -> None:
    """
    Save computed metrics to a CSV file.
    
    Args:
        results: List of dictionaries containing metrics
    """
    import csv
    
    if not results:
        logger.warning("No results to save")
        return
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', newline='') as csvfile:
        fieldnames = ['image_path', 'emotion', 'flanker_count', 'eccentricity', 
                     'local_contrast_variance', 'spatial_frequency_energy', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            row = {key: result.get(key, '') for key in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Saved metrics to {OUTPUT_PATH}")

def generate_validation_report(results: List[Dict[str, Any]]) -> None:
    """
    Generate a validation report checking correlation between clutter metrics and flanker count.
    
    Args:
        results: List of dictionaries containing metrics
    """
    import scipy.stats as stats
    
    # Filter successful results
    successful_results = [r for r in results if r.get('status') == 'success']
    
    if not successful_results:
        report = {
            'status': 'error',
            'message': 'No successful results to validate'
        }
    else:
        # Extract data for correlation analysis
        flanker_counts = [r['flanker_count'] for r in successful_results]
        spatial_frequencies = [r['spatial_frequency_energy'] for r in successful_results]
        
        # Compute correlation
        correlation, p_value = stats.pearsonr(flanker_counts, spatial_frequencies)
        
        report = {
            'status': 'success',
            'total_stimuli_processed': len(successful_results),
            'correlation_analysis': {
                'metric': 'spatial_frequency_energy vs flanker_count',
                'correlation_coefficient': float(correlation),
                'p_value': float(p_value),
                'significant_at_0.05': p_value < 0.05
            },
            'local_contrast_variance_stats': {
                'mean': float(np.mean([r['local_contrast_variance'] for r in successful_results])),
                'std': float(np.std([r['local_contrast_variance'] for r in successful_results])),
                'min': float(np.min([r['local_contrast_variance'] for r in successful_results])),
                'max': float(np.max([r['local_contrast_variance'] for r in successful_results]))
            },
            'spatial_frequency_energy_stats': {
                'mean': float(np.mean([r['spatial_frequency_energy'] for r in successful_results])),
                'std': float(np.std([r['spatial_frequency_energy'] for r in successful_results])),
                'min': float(np.min([r['spatial_frequency_energy'] for r in successful_results])),
                'max': float(np.max([r['spatial_frequency_energy'] for r in successful_results]))
            }
        }
    
    # Ensure output directory exists
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved validation report to {VALIDATION_REPORT_PATH}")

def main():
    """Main entry point for clutter metrics computation."""
    logger.info("Starting clutter metrics computation")
    
    try:
        # Compute metrics with automatic sampling fallback if needed
        results = compute_clutter_metrics()
        
        if not results:
            logger.error("No results generated")
            sys.exit(1)
        
        # Save results to CSV
        save_metrics_to_csv(results)
        
        # Generate validation report
        generate_validation_report(results)
        
        logger.info("Clutter metrics computation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during clutter metrics computation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()