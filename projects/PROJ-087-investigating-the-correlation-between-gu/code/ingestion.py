import os
import sys
import logging
import time
import requests
import yaml
import pandas as pd
import numpy as np
from scipy import stats
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(config.PROJECT_ROOT, 'logs', 'pipeline.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
TARGET_POWER = 0.8
TARGET_EFFECT_SIZE = 0.3
MIN_SAMPLE_SIZE = 30

def check_variable_existence(metadata_df):
    """
    Verify that necessary variables exist in the metadata.
    Checks for 'sleep_efficiency' OR 'sleep_quality' (proxy) and 'antibiotic_use_last_3mo'.
    """
    required_vars = ['antibiotic_use_last_3mo']
    sleep_vars = ['sleep_efficiency', 'sleep_quality']
    
    missing_required = [v for v in required_vars if v not in metadata_df.columns]
    if missing_required:
        logger.error(f"Missing required variables: {missing_required}")
        return False
    
    sleep_var_found = None
    for var in sleep_vars:
        if var in metadata_df.columns:
            sleep_var_found = var
            break
    
    if not sleep_var_found:
        logger.error("Neither 'sleep_efficiency' nor 'sleep_quality' found in metadata.")
        return False
    
    if sleep_var_found == 'sleep_quality':
        logger.info("Scope Narrowed: Using Self-Reported Sleep Quality as proxy.")
    
    return True

def define_mapping_schema():
    """
    Define the schema for the data mapping table.
    """
    schema = {
        "sample_id": {"type": "string", "required": True},
        "otu_count_col": {"type": "string", "required": True},
        "metadata_cols": {
            "type": "list",
            "required": True,
            "items": ["sleep_efficiency", "sleep_quality", "antibiotic_use_last_3mo", "age", "bmi", "diet", "medication"]
        }
    }
    return schema

def generate_mapping_table(otu_df, metadata_df, schema):
    """
    Generate the mapping table linking OTU counts to metadata.
    """
    # This is a simplified logic assuming sample IDs align or can be merged
    mapping_records = []
    common_ids = set(otu_df.index).intersection(set(metadata_df.index))
    
    if not common_ids:
        logger.warning("No common sample IDs found between OTU table and metadata.")
        return pd.DataFrame()
    
    for sample_id in common_ids:
        mapping_records.append({
            "sample_id": sample_id,
            "otu_count_col": sample_id, # Assuming OTU columns are sample IDs or vice versa
            "metadata_cols": schema["metadata_cols"]["items"]
        })
    
    return pd.DataFrame(mapping_records)

def download_data(otu_url, metadata_url, output_otu, output_metadata, max_retries=3):
    """
    Download data with retry/backoff logic.
    """
    def download_file(url, path, attempt):
        try:
            logger.info(f"Downloading {url} (Attempt {attempt})...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded to {path}")
            return True
        except requests.RequestException as e:
            logger.warning(f"Download failed: {e}")
            return False

    if not os.path.exists(os.path.dirname(output_otu)):
        os.makedirs(os.path.dirname(output_otu))
    
    for attempt in range(1, max_retries + 1):
        if download_file(otu_url, output_otu, attempt):
            break
        if attempt < max_retries:
            time.sleep(2 ** attempt) # Exponential backoff
    else:
        logger.error("Failed to download OTU data after retries.")
        return False

    for attempt in range(1, max_retries + 1):
        if download_file(metadata_url, output_metadata, attempt):
            break
        if attempt < max_retries:
            time.sleep(2 ** attempt)
    else:
        logger.error("Failed to download metadata after retries.")
        return False
    
    return True

def calculate_mdes(n, alpha=0.05, power=TARGET_POWER, r=TARGET_EFFECT_SIZE):
    """
    Calculate Minimum Detectable Effect Size (MDES) for a correlation test.
    Uses the approximation for Pearson/Spearman correlation power analysis.
    Formula derived from power analysis for correlation:
    n = (Z_alpha/2 + Z_beta)^2 / (0.5 * ln((1+r)/(1-r)))^2
    Rearranging to solve for r (MDES) given n.
    
    Alternatively, we can estimate MDES directly:
    MDES approx = sqrt( (Z_alpha/2 + Z_beta)^2 / (n + (Z_alpha/2 + Z_beta)^2) )
    """
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Sum of Z-scores squared
    sum_z_sq = (z_alpha + z_beta) ** 2
    
    # Approximate MDES calculation
    # Fisher's z transformation approach is more accurate but complex to invert analytically
    # Using the simplified approximation for large n:
    # r = sqrt( sum_z_sq / (n + sum_z_sq) )
    if n <= sum_z_sq:
        return 1.0 # Impossible to detect any effect with this power/sample size
    
    mdes = np.sqrt(sum_z_sq / (n + sum_z_sq))
    return mdes

def run_power_analysis(df, sleep_col, min_n=MIN_SAMPLE_SIZE):
    """
    Perform power analysis and sample size check.
    - Checks if N >= min_n
    - Calculates MDES for the given N
    - Returns True if power is sufficient (MDES <= TARGET_EFFECT_SIZE)
    - Returns False and logs HALT condition if not.
    """
    n = len(df)
    logger.info(f"Running power analysis on {n} samples.")
    
    if n < min_n:
        logger.error(f"Insufficient Power: Sample size N={n} is less than minimum required {min_n}.")
        return False, f"N < {min_n}"
    
    mdes = calculate_mdes(n)
    logger.info(f"Calculated MDES: {mdes:.4f} (Target: {TARGET_EFFECT_SIZE})")
    
    if mdes > TARGET_EFFECT_SIZE:
        logger.error(f"Insufficient Power: MDES ({mdes:.4f}) > Target Effect Size ({TARGET_EFFECT_SIZE}).")
        return False, f"MDES > {TARGET_EFFECT_SIZE}"
    
    logger.info("Power analysis passed. Proceeding.")
    return True, "OK"

def run_ingestion_pipeline():
    """
    Main pipeline execution function.
    Includes the Phase 0.5 Power Check gate.
    """
    logger.info("Starting Ingestion Pipeline...")
    
    # 1. Download Data (T006)
    otu_path = os.path.join(config.DATA_RAW_DIR, "otu_counts.csv")
    meta_path = os.path.join(config.DATA_RAW_DIR, "metadata.csv")
    
    if not os.path.exists(otu_path) or not os.path.exists(meta_path):
        # Attempt download if files missing (assuming URLs in config)
        if not hasattr(config, 'OTU_URL') or not hasattr(config, 'META_URL'):
            logger.error("Data URLs not configured in config.py.")
            return False
        if not download_data(config.OTU_URL, config.META_URL, otu_path, meta_path):
            return False
    
    # 2. Load Data
    try:
        otu_df = pd.read_csv(otu_path, index_col=0)
        meta_df = pd.read_csv(meta_path, index_col=0)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False
    
    # 3. Variable Check (T005)
    if not check_variable_existence(meta_df):
        return False
    
    # 4. Filtering (T016 - Antibiotic users)
    # Assuming 'antibiotic_use_last_3mo' is boolean or 1/0
    if 'antibiotic_use_last_3mo' in meta_df.columns:
        initial_count = len(meta_df)
        meta_df = meta_df[meta_df['antibiotic_use_last_3mo'] == False]
        logger.info(f"Filtered out {initial_count - len(meta_df)} antibiotic users.")
    
    # 5. Sleep Data Cleaning (T017 - Proxy fallback)
    sleep_col = 'sleep_efficiency' if 'sleep_efficiency' in meta_df.columns else 'sleep_quality'
    meta_df = meta_df.dropna(subset=[sleep_col])
    logger.info(f"Dropped {len(meta_df) - len(meta_df)} samples with missing sleep data.")
    
    # 6. Phase 0.5: Power Analysis (T018) - CRITICAL GATE
    # This must happen before diversity calculation
    power_ok, reason = run_power_analysis(meta_df, sleep_col)
    if not power_ok:
        logger.critical(f"HALT: Power analysis failed. Reason: {reason}. Pipeline stopped.")
        sys.exit(1)
    
    # 7. Merge and Save (T020 placeholder)
    # Ensure indices align
    common_ids = otu_df.index.intersection(meta_df.index)
    if len(common_ids) < MIN_SAMPLE_SIZE:
        logger.error(f"Insufficient samples after merging: {len(common_ids)}.")
        sys.exit(1)
    
    merged_df = meta_df.loc[common_ids]
    processed_path = os.path.join(config.DATA_PROCESSED_DIR, "analysis_data.csv")
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    merged_df.to_csv(processed_path)
    
    logger.info(f"Pipeline complete. Processed data saved to {processed_path}")
    return True

if __name__ == "__main__":
    run_ingestion_pipeline()
