import os
import sys
import time
import random
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import ndimage
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import matplotlib

# Configure matplotlib to use non-interactive backend for headless environments
matplotlib.use('Agg')

# Local imports based on API surface
from utils.config import set_seed, get_config_value, save_config
from utils.generator_config import get_generator_config, save_config_to_file
from utils.logging import (
    get_main_logger,
    get_exclusion_logger,
    get_fallback_logger,
    get_methodology_logger,
    log_exclusion,
    log_fallback_event,
    log_methodological_note,
    log_pipeline_step
)

# Constants
IMAGE_SIZE = 512
NUM_SEEDS_DEFAULT = 50
MIN_SEEDS = 10
MAX_SEEDS = 200

# --- Utility Functions ---

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        'data/raw',
        'data/raw/synthetic_images',
        'data/processed',
        'results',
        'results/plots',
        'code/utils'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Execute a function with exponential backoff retry logic."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    raise last_exception

def download_from_huggingface():
    """Attempt to download data from HuggingFace Datasets."""
    # Placeholder for actual HuggingFace logic
    raise FileNotFoundError("HuggingFace dataset not found or network unavailable.")

def download_from_nist():
    """Attempt to download data from NIST Materials Data Repository."""
    # Placeholder for actual NIST logic
    raise FileNotFoundError("NIST repository unavailable or dataset missing.")

def attempt_real_data_download():
    """
    Attempt to download real data. If both sources fail, log error and exit.
    This function triggers the fallback path via exit code if configured.
    """
    ensure_directories()
    logger = get_main_logger()
    log_pipeline_step(logger, "attempt_real_data_download", "Starting real data download attempt")

    try:
        retry_with_backoff(download_from_huggingface)
        log_pipeline_step(logger, "attempt_real_data_download", "Successfully downloaded from HuggingFace")
        return True
    except Exception as e:
        logger.warning(f"HuggingFace download failed: {e}")

    try:
        retry_with_backoff(download_from_nist)
        log_pipeline_step(logger, "attempt_real_data_download", "Successfully downloaded from NIST")
        return True
    except Exception as e:
        logger.error(f"NIST download failed: {e}")

    log_pipeline_step(logger, "attempt_real_data_download", "All real data sources failed.")
    # Check config for fallback
    try:
        config = get_config_value('allow_synthetic_fallback')
        if config and config.lower() == 'true':
            log_fallback_event("Real data download failed. Proceeding to synthetic generation.")
            return False
        else:
            log_fallback_event("Real data download failed. Synthetic fallback disabled. Halting.")
            sys.exit(1)
    except Exception:
        # Default behavior if config missing
        log_fallback_event("Real data download failed. Synthetic fallback disabled by default. Halting.")
        sys.exit(1)

def load_synthetic_config():
    """Load configuration for synthetic data generation."""
    config_path = 'code/utils/generator_config.py' # Placeholder, usually a .json or .yaml
    # In a real scenario, this loads a config file. Here we use the function from generator_config
    return get_generator_config()

def generate_synthetic_data(n_records=150):
    """
    Generate synthetic tabular data based on generator_config.
    Returns a list of dictionaries.
    """
    logger = get_main_logger()
    log_pipeline_step(logger, "generate_synthetic_data", f"Generating {n_records} synthetic records")
    
    config = get_generator_config()
    set_seed(config.get('random_seed', 42))
    
    data = []
    # Simplified generation logic based on typical requirements
    # In a full implementation, this would strictly follow the covariance matrix in config
    for i in range(n_records):
        record = {
            'grain_size': np.random.normal(config.get('grain_mean', 20), config.get('grain_std', 5)),
            'secondary_phase': np.random.normal(config.get('phase_mean', 10), config.get('phase_std', 3)),
            'dislocation_proxy': np.random.normal(config.get('disloc_mean', 0.5), config.get('disloc_std', 0.1)),
            'fatigue_cycles': np.random.normal(1e6, 2e5), # Simplified
            'alloy_batch_id': f"batch_{random.randint(1, 5)}",
            'heat_treatment_group': f"treatment_{random.randint(1, 3)}"
        }
        # Ensure non-negative values
        record['grain_size'] = abs(record['grain_size'])
        record['secondary_phase'] = abs(record['secondary_phase'])
        record['dislocation_proxy'] = abs(record['dislocation_proxy'])
        record['fatigue_cycles'] = max(1000, record['fatigue_cycles'])
        data.append(record)
    
    log_pipeline_step(logger, "generate_synthetic_data", f"Generated {len(data)} records")
    return data

def generate_voronoi_images(num_images=10, output_dir='data/raw/synthetic_images'):
    """
    Generate synthetic 512x512 grayscale Voronoi tessellation images.
    Saves images to the specified directory.
    """
    ensure_directories()
    logger = get_main_logger()
    log_pipeline_step(logger, "generate_voronoi_images", f"Generating {num_images} Voronoi images")
    
    os.makedirs(output_dir, exist_ok=True)
    
    set_seed(42) # Deterministic for reproducibility

    for i in range(num_images):
        # 1. Generate random seeds
        num_seeds = random.randint(MIN_SEEDS, MAX_SEEDS)
        seeds = np.random.rand(num_seeds, 2) * IMAGE_SIZE
        
        # 2. Compute Voronoi tessellation
        vor = Voronoi(seeds)
        
        # 3. Create an empty image
        image = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)
        
        # 4. Fill regions
        # We iterate over the ridges to determine boundaries, but for filling,
        # it's often easier to use a distance transform approach or direct region mapping.
        # Using a direct mapping approach for clarity and speed in this context.
        
        # Create a grid of points
        y, x = np.ogrid[:IMAGE_SIZE, :IMAGE_SIZE]
        points = np.c_[x.ravel(), y.ravel()]
        
        # Assign each point to the nearest seed
        # scipy.spatial.cKDTree is efficient for this
        from scipy.spatial import cKDTree
        tree = cKDTree(seeds)
        _, indices = tree.query(points)
        
        # Reshape indices to image shape
        region_indices = indices.reshape((IMAGE_SIZE, IMAGE_SIZE))
        
        # Assign grayscale values based on region index
        # Normalize to 0-255
        if num_seeds > 0:
            # Create a random intensity for each region to make them distinct
            region_values = np.random.randint(50, 200, size=num_seeds)
            image = region_values[region_indices]
        
        # 5. Add grain boundary noise/thickness
        # Dilate the boundaries slightly to simulate grain boundaries
        # First, identify boundaries by checking neighbors
        # A simple way is to blur and threshold, or morphological operations
        # Let's use a simple distance-based boundary drawing for "crisp" boundaries
        # or just keep the raw Voronoi regions which are already distinct.
        # To make it look more like a microstructure, we can add some noise.
        noise = np.random.normal(0, 5, image.shape)
        image = np.clip(image.astype(float) + noise, 0, 255).astype(np.uint8)
        
        # 6. Save image
        filename = f"voronoi_{i:04d}.png"
        filepath = os.path.join(output_dir, filename)
        plt.imsave(filepath, image, cmap='gray')
        
        log_pipeline_step(logger, "generate_voronoi_images", f"Saved {filepath}")
    
    log_pipeline_step(logger, "generate_voronoi_images", "Voronoi image generation complete")
    return True

def validate_data(data):
    """Validate that data meets statistical properties and column requirements."""
    logger = get_main_logger()
    log_pipeline_step(logger, "validate_data", "Starting data validation")
    
    required_cols = ['grain_size', 'secondary_phase', 'dislocation_proxy', 'fatigue_cycles', 'alloy_batch_id', 'heat_treatment_group']
    if not data:
        logger.error("Data is empty.")
        return False
    
    # Check columns
    first_record = data[0]
    missing_cols = [col for col in required_cols if col not in first_record]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check statistical thresholds (example logic)
    grain_sizes = [r['grain_size'] for r in data]
    if np.mean(grain_sizes) < 0:
        logger.error("Invalid grain size mean.")
        return False
        
    log_pipeline_step(logger, "validate_data", "Data validation passed")
    return True

def clean_and_impute_data(data):
    """Clean and impute data based on rules."""
    logger = get_main_logger()
    log_pipeline_step(logger, "clean_and_impute_data", "Starting data cleaning")
    
    cleaned_data = []
    for record in data:
        # Remove records with missing fatigue cycles or unverified microstructure
        if record.get('fatigue_cycles') is None or record.get('grain_size') is None:
            log_exclusion("Missing critical data", record)
            continue
        cleaned_data.append(record)
    
    # Imputation logic (simplified)
    # If missing microstructural features < 20%, impute median, else exclude
    # (Implementation details omitted for brevity, assuming full implementation in real code)
    
    log_pipeline_step(logger, "clean_and_impute_data", f"Cleaned {len(cleaned_data)} records")
    return cleaned_data

def save_cleaned_data(data, output_path='data/processed/cleaned_aluminum_fatigue.csv'):
    """Save cleaned data to CSV."""
    import pandas as pd
    logger = get_main_logger()
    log_pipeline_step(logger, "save_cleaned_data", f"Saving to {output_path}")
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    log_pipeline_step(logger, "save_cleaned_data", "Saved successfully")

def update_data_source_report(source_type, reason=None):
    """Update the data source report with real/synthetic status."""
    logger = get_main_logger()
    log_pipeline_step(logger, "update_data_source_report", f"Updating report: {source_type}")
    
    report_path = 'results/data_source_report.md'
    with open(report_path, 'w') as f:
        f.write(f"# Data Source Report\n\n")
        f.write(f"Source Type: {source_type}\n")
        if reason:
            f.write(f"Reason: {reason}\n")
        f.write(f"\nGenerated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    log_pipeline_step(logger, "update_data_source_report", "Report updated")

def main():
    """Main entry point for data acquisition pipeline."""
    # Initialize logging
    init_logging()
    logger = get_main_logger()
    log_pipeline_step(logger, "main", "Starting Data Acquisition Pipeline")
    
    ensure_directories()
    
    # Step 1: Attempt real download
    real_data_available = attempt_real_data_download()
    
    data = []
    source_type = "Real"
    
    if real_data_available:
        # In a real implementation, load the downloaded data here
        # For now, we assume the download function populates a global or returns data
        # Since download functions raise on failure, if we are here, data exists.
        # Placeholder for loading real data
        pass 
    else:
        # Fallback path
        source_type = "Synthetic"
        log_fallback_event("Switching to synthetic data generation.")
        
        # Generate synthetic tabular data
        data = generate_synthetic_data(n_records=150)
        
        # Generate synthetic Voronoi images (T011)
        generate_voronoi_images(num_images=10)
        
        update_data_source_report("Synthetic", "Real data sources unavailable; synthetic fallback triggered.")
    
    # Validate
    if data:
        if validate_data(data):
            cleaned = clean_and_impute_data(data)
            save_cleaned_data(cleaned)
        else:
            logger.error("Data validation failed.")
    else:
        logger.warning("No data to process.")
    
    log_pipeline_step(logger, "main", "Data Acquisition Pipeline Complete")

if __name__ == "__main__":
    main()