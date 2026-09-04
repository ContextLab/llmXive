import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import time

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

# Local imports from within the package structure implied by the API surface
# Note: The API surface lists imports as `from data.download import ...`
# and `from utils.logger import ...`. We assume standard package structure.

logger = get_logger(__name__)

def discover_real_datasets() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Queries HuggingFace, OpenML, and OSF for datasets containing RSES, INCOM,
    pre/post self-esteem variables.
    
    Returns:
        Tuple of (found: bool, dataset_id: str | None, reason: str | None)
    """
    log_execution_start(logger, "discover_real_datasets")
    
    # Simulated discovery logic based on the project's constraints
    # In a real implementation, this would make API calls to HF/OpenML/OSF
    # For this task, we check if a real dataset is "found" based on a 
    # configuration flag or a specific file marker that indicates a verified source.
    
    config = get_config()
    search_paths = [
        "data/raw/verified_real_dataset.csv",
        "data/raw/hf_dataset.csv",
        "data/raw/osf_dataset.csv"
    ]
    
    found_path = None
    for p in search_paths:
        if Path(p).exists():
            found_path = p
            break
    
    if found_path:
        logger.info(f"Real dataset found at: {found_path}")
        return True, found_path, "Real dataset discovered in data/raw"
    
    logger.warning("No real dataset found in expected locations.")
    return False, None, "No real dataset found in data/raw"

def verify_irb_consent(dataset_path: str) -> Tuple[bool, Optional[str]]:
    """
    Verifies metadata for IRB approval by checking HuggingFace/OSF metadata fields
    or a local metadata file for 'license' containing 'IRB' or specific consent tags.
    
    Args:
        dataset_path: Path to the dataset or metadata file.
        
    Returns:
        Tuple of (is_valid: bool, reason: str | None)
    """
    log_execution_start(logger, "verify_irb_consent")
    
    # Check for a companion metadata file
    meta_path = Path(dataset_path).with_suffix('.meta.yaml')
    if not meta_path.exists():
        # Try to infer from filename if it's a known real source
        # In a real scenario, we'd fetch metadata from the API
        logger.warning(f"No metadata file found at {meta_path}. Assuming blocked.")
        return False, "Missing metadata file for IRB verification"
    
    import yaml
    try:
        with open(meta_path, 'r') as f:
            meta = yaml.safe_load(f)
        
        license_info = meta.get('license', '').lower()
        consent_info = meta.get('consent', '').lower()
        
        if 'irb' in license_info or 'consent' in consent_info:
            logger.info("IRB/Consent verification passed.")
            return True, None
        else:
            logger.warning(f"Missing IRB/Consent tags in metadata: {meta}")
            return False, "Missing IRB or consent tags in metadata"
            
    except Exception as e:
        logger.error(f"Error reading metadata: {e}")
        return False, f"Error reading metadata: {e}"

def generate_synthetic_dataset(n_samples: int = 100, seed: int = 42) -> Path:
    """
    Generates a synthetic dataset with N >= 100, interaction beta = 0.2,
    and labels it as "Pipeline Validation Only".
    
    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        Path to the generated CSV file.
    """
    log_execution_start(logger, "generate_synthetic_dataset")
    
    import numpy as np
    import pandas as pd
    
    np.random.seed(seed)
    random.seed(seed)
    
    # Ground truth parameters
    beta_intercept = 0.0
    beta_avatar = 0.5  # Effect of avatar condition
    beta_pre = 0.8     # Effect of pre-self-esteem
    beta_comparison = 0.1 # Effect of comparison tendency
    beta_interaction = 0.2 # Interaction effect
    
    # Generate features
    avatar_condition = np.random.choice([0, 1], size=n_samples) # 0: Control, 1: High Comparison
    comparison_tendency = np.random.normal(0, 1, size=n_samples)
    pre_self_esteem = np.random.normal(50, 10, size=n_samples)
    
    # Generate outcome
    noise = np.random.normal(0, 2, size=n_samples)
    post_self_esteem = (
        beta_intercept +
        beta_avatar * avatar_condition +
        beta_pre * pre_self_esteem +
        beta_comparison * comparison_tendency +
        beta_interaction * (avatar_condition * comparison_tendency) +
        noise
    )
    
    df = pd.DataFrame({
        'avatar_condition': avatar_condition,
        'pre_self_esteem': pre_self_esteem,
        'post_self_esteem': post_self_esteem,
        'comparison_tendency': comparison_tendency
    })
    
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "synthetic_dataset.csv"
    df.to_csv(output_path, index=False)
    
    # Create a metadata file to indicate this is synthetic
    meta_path = output_dir / "synthetic_dataset.meta.yaml"
    with open(meta_path, 'w') as f:
        f.write("source_type: synthetic\n")
        f.write("label: Pipeline Validation Only\n")
        f.write("ground_truth_params:\n")
        f.write(f"  beta_avatar: {beta_avatar}\n")
        f.write(f"  beta_pre: {beta_pre}\n")
        f.write(f"  beta_comparison: {beta_comparison}\n")
        f.write(f"  beta_interaction: {beta_interaction}\n")
    
    logger.info(f"Synthetic dataset generated at: {output_path}")
    return output_path

def load_or_generate_data() -> Tuple[Path, str]:
    """
    Implements the fallback logic: if real data not found, trigger synthetic generation
    and set `data_source_type` flag.
    
    Returns:
        Tuple of (data_path: Path, source_type: str)
    """
    log_execution_start(logger, "load_or_generate_data")
    
    # Step 1: Try to discover real datasets
    found, real_path, reason = discover_real_datasets()
    
    if found:
        # Step 2: Verify IRB/Consent
        is_valid, irb_reason = verify_irb_consent(real_path)
        if is_valid:
            logger.info("Real data found and verified. Using real data.")
            return Path(real_path), "real"
        else:
            logger.warning(f"Real data found but IRB verification failed: {irb_reason}. Falling back to synthetic.")
    
    # Step 3: Fallback to synthetic generation
    logger.info("No valid real data found. Triggering synthetic generation.")
    synthetic_path = generate_synthetic_dataset()
    
    logger.info(f"Fallback to synthetic data completed. Path: {synthetic_path}")
    return synthetic_path, "synthetic"

def run_loader():
    """
    Main entry point to run the data loading/fallback logic.
    """
    log_execution_start(logger, "run_loader")
    
    try:
        data_path, source_type = load_or_generate_data()
        
        # Log the result
        logger.info(f"Data loading complete. Source: {source_type}, Path: {data_path}")
        
        # Return the result for downstream consumption
        return {
            "data_path": str(data_path),
            "data_source_type": source_type
        }
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

if __name__ == "__main__":
    result = run_loader()
    print(f"Result: {result}")
