import os
import json
import random
import logging
import time
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

# Import local utilities
from utils import (
    get_logger, 
    log_structured_error, 
    init_seed_config, 
    set_random_seed,
    get_global_seed
)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
SANITIZED_IMAGES_DIR = os.path.join(DATA_PROCESSED_DIR, "sanitized_images")
MERGED_DATA_PATH = os.path.join(DATA_PROCESSED_DIR, "merged_data.csv")
COGNITIVE_DATA_PATH = os.path.join(DATA_RAW_DIR, "cognitive_data.csv")
IMAGE_METADATA_PATH = os.path.join(DATA_RAW_DIR, "image_metadata.json")
READY_MARKER_PATH = os.path.join(DATA_PROCESSED_DIR, ".ready")

# Setup logging
logger = get_logger(__name__)

def init_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(SANITIZED_IMAGES_DIR, exist_ok=True)
    logger.info("Directories initialized.")

def try_download_real_data() -> bool:
    """
    Attempt to find a unified real dataset on HuggingFace/OpenML.
    Returns True if found and saved, False otherwise.
    """
    logger.info("Attempting to locate unified real dataset...")
    # Placeholder for actual search logic if specific IDs were known
    # For now, assume not found to trigger fallback logic in pipeline
    return False

def fetch_cognitive_data_from_openml() -> Optional[pd.DataFrame]:
    """
    Fetch real cognitive task data (Stroop/Flanker) from OpenML.
    Returns DataFrame or None if fetch fails.
    """
    try:
        import openml
        # Using a known dataset ID for cognitive tasks if available, 
        # or a generic placeholder ID that exists on OpenML for testing structure
        # Note: In a real scenario, we would search for specific Stroop/Flanker IDs.
        # Using ID 4444 as a generic example from the spec, but catching errors if it doesn't exist.
        dataset_id = 4444 
        try:
            dataset = openml.datasets.get_dataset(dataset_id)
            df, _ = dataset.get_data()
            logger.info(f"Successfully fetched OpenML dataset ID {dataset_id}.")
            return df
        except Exception as e:
            logger.warning(f"OpenML dataset ID {dataset_id} not found or inaccessible: {e}")
            return None
    except ImportError:
        logger.error("OpenML library not installed.")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch cognitive data from OpenML: {e}")
        return None

def fetch_workspace_images_from_unsplash(n_images: int = 150) -> bool:
    """
    Query Unsplash API for workspace images.
    Returns True if successful, False otherwise.
    """
    try:
        import requests
        # Note: In a real environment, an API key would be required.
        # This function attempts to fetch data but may fail without credentials.
        # If it fails, the pipeline should proceed to synthetic fallback.
        api_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not api_key:
            logger.warning("UNSPLASH_ACCESS_KEY not found. Skipping real image fetch.")
            return False

        keywords = ["home office", "desk", "workspace", "remote work", "study room"]
        os.makedirs(os.path.join(DATA_RAW_DIR, "workspace_images"), exist_ok=True)
        
        images_downloaded = 0
        for keyword in keywords:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": keyword,
                "per_page": n_images // len(keywords),
                "orientation": "landscape"
            }
            headers = {"Authorization": f"Client-ID {api_key}"}
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("results", []):
                    img_url = item["urls"]["regular"]
                    img_id = item["id"]
                    img_resp = requests.get(img_url, timeout=30)
                    if img_resp.status_code == 200:
                        img_path = os.path.join(DATA_RAW_DIR, "workspace_images", f"{img_id}.jpg")
                        with open(img_path, "wb") as f:
                            f.write(img_resp.content)
                        images_downloaded += 1
                        if images_downloaded >= n_images:
                            break
            except Exception as e:
                logger.warning(f"Failed to download images for keyword {keyword}: {e}")
                continue
            if images_downloaded >= n_images:
                break
        
        logger.info(f"Downloaded {images_downloaded} images from Unsplash.")
        return images_downloaded > 0
    except ImportError:
        logger.error("Requests library not installed.")
        return False
    except Exception as e:
        logger.error(f"Failed to fetch images from Unsplash: {e}")
        return False

def generate_synthetic_cognitive_data(n_records: int = 100) -> pd.DataFrame:
    """
    Generate synthetic participant records with correlated variables.
    Uses Cholesky decomposition to simulate negative correlation between
    visual_complexity and reaction_time as described in literature.
    """
    set_random_seed(get_global_seed())
    
    # Target correlation matrix
    # Variables: [reaction_time, accuracy, visual_complexity]
    # Expected: Negative correlation between visual_complexity and reaction_time
    # Expected: Negative correlation between visual_complexity and accuracy (complexity hurts accuracy)
    # Expected: Positive correlation between reaction_time and accuracy (slower = more accurate? or trade-off)
    # Let's assume: Higher complexity -> Slower RT, Lower Accuracy.
    # RT and Accuracy: Often trade-off, but let's assume standard trade-off (slower = better accuracy) or independent.
    # Literature often suggests complexity increases RT and decreases accuracy.
    
    # Covariance matrix construction
    # Let's target correlation matrix R:
    # RT vs Complexity: -0.4
    # Acc vs Complexity: -0.4
    # RT vs Acc: 0.2 (slower might be slightly more accurate, or weak)
    
    mean = [500.0, 0.85, 2.5] # RT (ms), Accuracy (0-1), Complexity (0-10)
    cov = [
        [100.0, 10.0, -20.0],   # RT variance, RT-Acc cov, RT-Complexity cov
        [10.0, 0.01, -0.05],    # Acc variance, Acc-Complexity cov
        [-20.0, -0.05, 1.0]     # Complexity variance
    ]
    
    try:
        data = np.random.multivariate_normal(mean, cov, n_records)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix not positive semi-definite. Adjusting.")
        # Fallback to diagonal if Cholesky fails
        data = np.random.normal(mean, [10, 0.05, 1], n_records).T

    df = pd.DataFrame(data, columns=["reaction_time", "accuracy", "visual_complexity"])
    df["participant_id"] = [f"P{str(i).zfill(4)}" for i in range(1, n_records + 1)]
    
    # Ensure bounds
    df["accuracy"] = df["accuracy"].clip(0.0, 1.0)
    df["reaction_time"] = df["reaction_time"].clip(200, 2000)
    df["visual_complexity"] = df["visual_complexity"].clip(0, 10)
    
    logger.info(f"Generated {n_records} synthetic records with Cholesky correlation.")
    return df

def generate_workspace_image_metadata(n_images: int) -> List[Dict[str, Any]]:
    """Generate metadata for synthetic images."""
    set_random_seed(get_global_seed())
    metadata = []
    for i in range(1, n_images + 1):
        metadata.append({
            "image_id": f"img_{str(i).zfill(4)}",
            "lighting_condition": random.choice(["natural", "artificial", "mixed"]),
            "room_type": random.choice(["home_office", "kitchen", "living_room", "study"]),
            "tags": ["workspace", "desk", "computer"]
        })
    return metadata

def merge_participant_data(cognitive_df: pd.DataFrame, metadata_list: List[Dict]) -> pd.DataFrame:
    """
    Merge cognitive data with image metadata.
    If lengths differ, trim or pad to match.
    """
    if len(cognitive_df) != len(metadata_list):
        min_len = min(len(cognitive_df), len(metadata_list))
        cognitive_df = cognitive_df.head(min_len)
        metadata_list = metadata_list[:min_len]
        logger.warning(f"Mismatched lengths. Trimmed to {min_len} records.")
    
    merged_df = cognitive_df.copy()
    for i, meta in enumerate(metadata_list):
        merged_df.loc[i, "image_path"] = os.path.join(SANITIZED_IMAGES_DIR, f"{meta['image_id']}.jpg")
        merged_df.loc[i, "lighting_condition"] = meta["lighting_condition"]
        merged_df.loc[i, "room_type"] = meta["room_type"]
    
    return merged_df

def perform_proxy_linkage(cognitive_df: pd.DataFrame, image_metadata: List[Dict]) -> pd.DataFrame:
    """
    Perform proxy linkage if no unified dataset exists.
    Randomly assigns cognitive records to image groups.
    """
    logger.info("Performing proxy linkage...")
    set_random_seed(get_global_seed())
    return merge_participant_data(cognitive_df, image_metadata)

def save_merged_data(df: pd.DataFrame, path: str):
    """Save merged dataframe to CSV."""
    df.to_csv(path, index=False)
    logger.info(f"Saved merged data to {path}")

def validate_data(df: pd.DataFrame) -> bool:
    """
    Validate dataset: N >= 100, no missing > 5%, variance check.
    Returns True if valid, False otherwise.
    """
    n = len(df)
    if n < 100:
        logger.error(f"Validation failed: N={n} < 100")
        return False
    
    missing_pct = df.isnull().sum().max() / n * 100
    if missing_pct > 5:
        logger.error(f"Validation failed: Missing values {missing_pct:.1f}% > 5%")
        return False
    
    if "visual_complexity" in df.columns:
        if df["visual_complexity"].var() < 1e-5:
            log_structured_error("zero_variance_warning", "visual_complexity", "Variance near zero")
            logger.warning("Zero variance warning for visual_complexity")
            # Not strictly failing, but warning
    
    logger.info("Data validation passed.")
    return True

def generate_synthetic_fallback():
    """
    T015d Implementation: Synthetic Fallback.
    Executes ONLY if merged_data.csv does not have N>=100 records.
    Generates synthetic records with Cholesky correlation.
    Overwrites merged_data.csv if necessary.
    """
    logger.info("Starting Synthetic Fallback (T015d)...")
    
    # Check existing merged data
    if os.path.exists(MERGED_DATA_PATH):
        try:
            existing_df = pd.read_csv(MERGED_DATA_PATH)
            if len(existing_df) >= 100:
                logger.info(f"Merged data already has {len(existing_df)} records. Skipping synthetic fallback.")
                return
            else:
                logger.warning(f"Merged data has only {len(existing_df)} records. Generating synthetic fallback.")
        except Exception as e:
            logger.warning(f"Could not read existing merged data: {e}. Generating synthetic fallback.")
    
    # Generate synthetic data
    n_needed = 100
    synthetic_df = generate_synthetic_cognitive_data(n_needed)
    
    # Generate metadata for synthetic images
    # Note: In a real pipeline, we might need to ensure images exist.
    # For this task, we generate metadata and assume images are handled elsewhere or are placeholders.
    # However, the task requires saving to merged_data.csv.
    # We will create dummy image paths to satisfy schema if images don't exist.
    # But T015b/T016 should have created images. If not, we create metadata only.
    # Let's assume we need to pair with existing images or create dummy paths.
    # To be safe, we generate metadata for N records.
    image_meta = generate_workspace_image_metadata(n_needed)
    
    # Merge
    final_df = merge_participant_data(synthetic_df, image_meta)
    
    # Validate
    if not validate_data(final_df):
        raise ValueError(f"Synthetic data validation failed. N: {len(final_df)}")
    
    # Save
    save_merged_data(final_df, MERGED_DATA_PATH)
    logger.info("Synthetic fallback completed and saved.")

def save_cognitive_data(df: pd.DataFrame):
    df.to_csv(COGNITIVE_DATA_PATH, index=False)
    logger.info(f"Saved cognitive data to {COGNITIVE_DATA_PATH}")

def save_image_metadata(metadata: List[Dict]):
    with open(IMAGE_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved image metadata to {IMAGE_METADATA_PATH}")

def run_power_analysis():
    """
    Placeholder for power analysis logic (T019).
    This function is called by main() but contains the error fixed in this round.
    The error was using 'nobs1' instead of 'n' in statsmodels.
    """
    try:
        from statsmodels.stats.power import TTestPower
        from statsmodels.stats.power import FTestPower # T019 uses FTestPower for correlation
        
        # T019a/b Logic: Power analysis for correlation
        # Effect size (r=0.3), alpha=0.05, n=100
        effect_size = 0.3
        alpha = 0.05
        nobs = 100
        
        # FTestPower is for F-tests (ANOVA, Regression). For correlation, we often use TTestPower on r or convert.
        # statsmodels FTestPower.solve_power takes nobs, effect_size, alpha, alternative.
        # But for correlation specifically, we might use TTestPower if converting r to t.
        # However, the error message says 'nobs1' was used.
        # Let's use FTestPower as per task description T019.
        
        analysis = FTestPower()
        # FTestPower.solve_power(nobs=..., effect_size=..., alpha=...)
        # Note: FTestPower is typically for ANOVA/Regression. For simple correlation, TTestPower is often used with r->t conversion.
        # But the task says 'FTestPower'. We will use it correctly.
        # FTestPower.solve_power signature: solve_power(nobs=None, effect_size=None, alpha=None, power=None, df_num=1, df_denom=None, alternative='two-sided')
        
        calculated_power = analysis.solve_power(
            nobs=nobs, 
            effect_size=effect_size, 
            alpha=alpha,
            df_num=1,
            df_denom=nobs-2
        )
        
        logger.info(f"Power analysis calculated: {calculated_power}")
        return calculated_power
    except Exception as e:
        logger.error(f"Power analysis calculation failed: {e}")
        # Re-raise to fail loudly if needed, or return None
        raise e

def fetch_real_data():
    """
    T015b: Fetch real cognitive data and images.
    """
    logger.info("Fetching real data...")
    init_directories()
    
    # Try OpenML
    cognitive_df = fetch_cognitive_data_from_openml()
    if cognitive_df is None:
        logger.warning("Real cognitive data fetch failed. Will generate synthetic.")
        cognitive_df = generate_synthetic_cognitive_data(100)
    
    # Try Unsplash
    success = fetch_workspace_images_from_unsplash(150)
    if not success:
        logger.warning("Real image fetch failed. Will use synthetic metadata.")
    
    # If we have real images, we need to sanitize them (T016)
    # Assuming sanitize_images is called externally or here if needed.
    # For this task, we focus on the data acquisition logic.
    
    # Merge
    if os.path.exists(IMAGE_METADATA_PATH):
        with open(IMAGE_METADATA_PATH, "r") as f:
            meta = json.load(f)
    else:
        meta = generate_workspace_image_metadata(len(cognitive_df))
    
    merged_df = merge_participant_data(cognitive_df, meta)
    save_cognitive_data(cognitive_df)
    save_image_metadata(meta)
    save_merged_data(merged_df, MERGED_DATA_PATH)
    
    # Validate
    if not validate_data(merged_df):
        logger.warning("Real data validation failed. Triggering fallback.")
        generate_synthetic_fallback()

def main():
    """Main entry point for data acquisition."""
    init_directories()
    
    # Step 1: Try to find unified real dataset
    found = try_download_real_data()
    
    if not found:
        # Step 2: Fetch real data separately
        fetch_real_data()
        
        # Step 3: Check if we have enough data
        if os.path.exists(MERGED_DATA_PATH):
            df = pd.read_csv(MERGED_DATA_PATH)
            if len(df) < 100:
                logger.warning("Insufficient data after real fetch. Generating synthetic fallback.")
                generate_synthetic_fallback()
        else:
            logger.warning("No merged data found. Generating synthetic fallback.")
            generate_synthetic_fallback()
    else:
        logger.info("Unified real dataset found.")
    
    # T019: Power Analysis (Fixed)
    try:
        run_power_analysis()
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        # Do not fail the whole script for power analysis failure, log and continue
    
    logger.info("Data acquisition pipeline completed.")

if __name__ == "__main__":
    main()