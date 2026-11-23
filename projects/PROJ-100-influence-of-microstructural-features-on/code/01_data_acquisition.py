import os
import sys
import time
import random
import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from utils.config import set_seed, get_config_value
from utils.generator_config import get_generator_config
from utils.logging import get_main_logger, get_exclusion_logger, get_fallback_logger, log_exclusion, log_fallback_event, log_pipeline_step

# Constants
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
RESULTS_DIR = "results"
SYNTHETIC_IMAGES_DIR = "data/raw/synthetic_images"
VALIDATED_CSV_PATH = "data/raw/validated_data.csv"
CLEANED_CSV_PATH = "data/processed/cleaned_aluminum_fatigue.csv"
EXCLUSION_REPORT_PATH = "results/exclusion_report.log"
DATA_SOURCE_REPORT_PATH = "results/data_source_report.md"

# Setup logging
main_logger = get_main_logger()
exclusion_logger = get_exclusion_logger()
fallback_logger = get_fallback_logger()

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        f"{RESULTS_DIR}/plots",
        SYNTHETIC_IMAGES_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    main_logger.info(f"Ensured directories: {dirs}")

def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            main_logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    return None

def load_synthetic_config() -> Dict[str, Any]:
    """Load synthetic data generation configuration."""
    return get_generator_config()

def generate_synthetic_data(n_samples: int = 150, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic aluminum alloy fatigue data."""
    set_seed(seed)
    config = load_synthetic_config()
    
    data = {}
    # Microstructural features
    data['grain_size'] = np.random.normal(config['grain_size']['mean'], config['grain_size']['std'], n_samples)
    data['secondary_phase_fraction'] = np.random.normal(config['secondary_phase']['mean'], config['secondary_phase']['std'], n_samples)
    data['dislocation_density_proxy'] = np.random.normal(config['dislocation']['mean'], config['dislocation']['std'], n_samples)
    
    # Fatigue life (log-transformed for normality)
    # Correlate with microstructural features
    fatigue_log = (
        config['fatigue']['intercept'] + 
        config['fatigue']['grain_coef'] * data['grain_size'] +
        config['fatigue']['secondary_coef'] * data['secondary_phase_fraction'] +
        config['fatigue']['dislocation_coef'] * data['dislocation_density_proxy'] +
        np.random.normal(0, config['fatigue']['noise_std'], n_samples)
    )
    data['fatigue_cycles'] = 10 ** fatigue_log
    
    # Metadata
    alloy_batches = [f"batch_{i}" for i in range(1, 6)]
    heat_treatments = [f"HT_{i}" for i in range(1, 4)]
    data['alloy_batch_id'] = [random.choice(alloy_batches) for _ in range(n_samples)]
    data['heat_treatment_group'] = [random.choice(heat_treatments) for _ in range(n_samples)]
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values for testing imputation logic (approx 15%)
    missing_indices = np.random.choice(df.index, size=int(n_samples * 0.15), replace=False)
    df.loc[missing_indices, 'secondary_phase_fraction'] = np.nan
    
    main_logger.info(f"Generated {n_samples} synthetic records.")
    return df

def generate_voronoi_images(n_images: int = 10, size: int = 512, seed: int = 42) -> List[str]:
    """Generate synthetic Voronoi tessellation images for testing."""
    set_seed(seed)
    import cv2
    import matplotlib.pyplot as plt
    
    image_paths = []
    for i in range(n_images):
        # Create random points for Voronoi
        points = np.random.rand(50, 2) * size
        
        # Create image
        img = np.zeros((size, size), dtype=np.uint8)
        
        # Simple Voronoi-like pattern (using distance transform approximation)
        for y in range(size):
            for x in range(size):
                min_dist = float('inf')
                for p in points:
                    dist = np.sqrt((x - p[0])**2 + (y - p[1])**2)
                    if dist < min_dist:
                        min_dist = dist
                # Normalize and scale to 0-255
                val = int(min_dist * 255 / (size / 2))
                val = min(255, max(0, val))
                img[y, x] = val
        
        # Save image
        filename = f"voronoi_{i:03d}.png"
        path = os.path.join(SYNTHETIC_IMAGES_DIR, filename)
        cv2.imwrite(path, img)
        image_paths.append(path)
    
    main_logger.info(f"Generated {n_images} Voronoi images in {SYNTHETIC_IMAGES_DIR}")
    return image_paths

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate data meets statistical properties and required columns."""
    required_cols = [
        'grain_size', 'secondary_phase_fraction', 'dislocation_density_proxy',
        'fatigue_cycles', 'alloy_batch_id', 'heat_treatment_group'
    ]
    
    # Check columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Log missing data percentages
    for col in required_cols:
        missing_pct = (df[col].isna().sum() / len(df)) * 100
        main_logger.info(f"Column '{col}' missing: {missing_pct:.2f}%")
    
    # Filter out records with missing fatigue_cycles (critical target)
    initial_count = len(df)
    df = df.dropna(subset=['fatigue_cycles'])
    excluded_count = initial_count - len(df)
    if excluded_count > 0:
        exclusion_logger.info(f"Excluded {excluded_count} records with missing fatigue_cycles.")
    
    # Filter records with unverified microstructure (all microstructural features present)
    micro_cols = ['grain_size', 'secondary_phase_fraction', 'dislocation_density_proxy']
    initial_count = len(df)
    df = df.dropna(subset=micro_cols)
    excluded_count = initial_count - len(df)
    if excluded_count > 0:
        exclusion_logger.info(f"Excluded {excluded_count} records with unverified microstructure.")
    
    main_logger.info(f"Validation complete. {len(df)} records remain.")
    return df

def clean_and_impute_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Clean and impute data according to T014 requirements.
    
    Logic:
    1. Remove records with missing fatigue cycles or unverified microstructure.
    2. Calculate missing microstructural features percentage.
    3. If missing < 20% of remaining records, impute using median.
    4. Otherwise, exclude the record.
    
    Returns:
        Tuple of (cleaned_df, stats_dict)
    """
    stats = {
        'initial_count': len(df),
        'excluded_missing_fatigue': 0,
        'excluded_unverified_micro': 0,
        'excluded_high_missing': 0,
        'imputed_records': 0,
        'final_count': 0
    }
    
    # Step 1: Remove records with missing fatigue cycles
    initial_count = len(df)
    df = df.dropna(subset=['fatigue_cycles'])
    stats['excluded_missing_fatigue'] = initial_count - len(df)
    if stats['excluded_missing_fatigue'] > 0:
        log_exclusion(stats['excluded_missing_fatigue'], 'missing_fatigue_cycles', 'fatigue_cycles')
    
    # Step 2: Remove records with unverified microstructure (all micro features missing)
    micro_cols = ['grain_size', 'secondary_phase_fraction', 'dislocation_density_proxy']
    initial_count = len(df)
    # Exclude if ANY of the microstructural features are missing? 
    # The prompt says "unverified microstructure", implying the whole set is missing.
    # However, standard practice is to drop if critical features are missing.
    # Let's interpret "unverified" as having at least one missing micro feature for strictness,
    # but the prompt's "conditional logic" implies we keep some to impute.
    # Re-reading: "Remove records with ... unverified microstructure."
    # Then "If missing microstructural features < 20% ... impute".
    # This implies we keep records with SOME missing micro features, but drop if ALL are missing?
    # Let's drop rows where ALL micro features are missing (unverified).
    df = df.dropna(subset=micro_cols, how='all')
    stats['excluded_unverified_micro'] = initial_count - len(df)
    if stats['excluded_unverified_micro'] > 0:
        log_exclusion(stats['excluded_unverified_micro'], 'unverified_microstructure', 'all_micro_features')
    
    # Step 3: Check missing percentage of microstructural features
    # Count rows that have at least one missing micro feature
    rows_with_missing_micro = df[micro_cols].isna().any(axis=1).sum()
    total_records = len(df)
    
    if total_records == 0:
        main_logger.warning("No records remaining after initial cleaning.")
        return df, stats
    
    missing_pct = (rows_with_missing_micro / total_records) * 100
    main_logger.info(f"Percentage of records with missing microstructural features: {missing_pct:.2f}%")
    
    impute_threshold = 20.0
    
    if missing_pct < impute_threshold:
        # Impute using median
        main_logger.info(f"Missing percentage ({missing_pct:.2f}%) < {impute_threshold}%. Imputing with median.")
        for col in micro_cols:
            median_val = df[col].median()
            if pd.isna(median_val):
                # Fallback if column is all NaN (shouldn't happen after dropna how='all')
                median_val = 0.0
            imputed_count = df[col].isna().sum()
            if imputed_count > 0:
                df[col] = df[col].fillna(median_val)
                stats['imputed_records'] += imputed_count
                exclusion_logger.info(f"Imputed {imputed_count} missing values in '{col}' with median {median_val:.4f}")
    else:
        # Exclude records with missing microstructural features
        main_logger.warning(f"Missing percentage ({missing_pct:.2f}%) >= {impute_threshold}%. Excluding records.")
        initial_count = len(df)
        df = df.dropna(subset=micro_cols)
        excluded_count = initial_count - len(df)
        stats['excluded_high_missing'] = excluded_count
        log_exclusion(excluded_count, 'high_missing_micro_features', 'exceeded_20pct_threshold')
    
    stats['final_count'] = len(df)
    return df, stats

def save_cleaned_data(df: pd.DataFrame, stats: Dict[str, int], output_path: str):
    """Save cleaned data and log statistics."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    main_logger.info(f"Saved cleaned data to {output_path} ({len(df)} records)")
    
    # Log exclusion report
    log_path = EXCLUSION_REPORT_PATH
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(f"--- Exclusion Report for {output_path} ---\n")
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Initial Records: {stats['initial_count']}\n")
        f.write(f"Excluded (Missing Fatigue): {stats['excluded_missing_fatigue']}\n")
        f.write(f"Excluded (Unverified Micro): {stats['excluded_unverified_micro']}\n")
        f.write(f"Excluded (High Missing): {stats['excluded_high_missing']}\n")
        f.write(f"Imputed Records: {stats['imputed_records']}\n")
        f.write(f"Final Records: {stats['final_count']}\n")
        f.write(f"Method: {'Median Imputation' if stats['imputed_records'] > 0 else 'Exclusion'}\n")
        f.write("----------------------------------------\n\n")
    
    main_logger.info(f"Exclusion report saved to {log_path}")

def update_data_source_report(source_type: str, reason: str):
    """Update the data source report."""
    os.makedirs(os.path.dirname(DATA_SOURCE_REPORT_PATH), exist_ok=True)
    with open(DATA_SOURCE_REPORT_PATH, 'a') as f:
        f.write(f"### Data Source Update\n")
        f.write(f"- **Source Type**: {source_type}\n")
        f.write(f"- **Reason**: {reason}\n")
        f.write(f"- **Timestamp**: {pd.Timestamp.now()}\n\n")

def main():
    """Main execution flow for T014."""
    main_logger.info("Starting T014: Clean and Impute Data")
    ensure_directories()
    
    # Load validated data (from T012)
    if not os.path.exists(VALIDATED_CSV_PATH):
        main_logger.error(f"Validated data not found at {VALIDATED_CSV_PATH}.")
        sys.exit(1)
    
    df = pd.read_csv(VALIDATED_CSV_PATH)
    main_logger.info(f"Loaded {len(df)} records from {VALIDATED_CSV_PATH}")
    
    # Clean and impute
    cleaned_df, stats = clean_and_impute_data(df)
    
    # Save results
    save_cleaned_data(cleaned_df, stats, CLEANED_CSV_PATH)
    
    main_logger.info("T014 completed successfully.")
    return cleaned_df

if __name__ == "__main__":
    main()
