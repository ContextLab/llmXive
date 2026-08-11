"""
Data extraction logic for NIST and Materials Project sources.
Implements the dual-source strategy (FR-001).
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib
import pandas as pd

# Import config for paths and API keys
from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()

# Initialize joblib memory for caching
memory = joblib.Memory(location=str(config.project_root / "data" / "cache"), verbose=0)

@memory.cache
def fetch_nist_data() -> Optional[pd.DataFrame]:
    """
    Fetches NIST materials data.
    
    Attempts to load from the 'nist_materials_data' HuggingFace dataset.
    If that fails, attempts a verified public CSV URL.
    
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        RuntimeError: If the fetch fails completely (no data source available).
        ValueError: If the data structure is invalid.
    """
    dataset_name = "nist_materials_data"
    fallback_url = "https://raw.githubusercontent.com/nist-materials-data/public/main/alloys.csv"
    
    # 1. Try HuggingFace datasets
    try:
        logger.info(f"Attempting to load dataset: {dataset_name}")
        from datasets import load_dataset
        
        ds = load_dataset(dataset_name, split="train")
        df = ds.to_pandas()
        
        if df.empty:
            raise ValueError("Dataset returned empty.")
            
        logger.info(f"Successfully loaded {len(df)} rows from HuggingFace: {dataset_name}")
        return df
        
    except Exception as e:
        logger.warning(f"HF Dataset fetch failed ({e}). Trying fallback URL...")
    
    # 2. Try Fallback URL
    try:
        logger.info(f"Attempting to fetch from fallback URL: {fallback_url}")
        df = pd.read_csv(fallback_url)
        
        if df.empty:
            raise ValueError("Fallback CSV returned empty.")
            
        logger.info(f"Successfully loaded {len(df)} rows from fallback URL.")
        return df
        
    except Exception as e:
        logger.critical(f"NIST fetch failed: {e}")
        raise RuntimeError("CRITICAL: NIST data source unavailable. Both HF and URL failed.")

def fetch_materials_project_data() -> Optional[pd.DataFrame]:
    """
    Fetches Materials Project data.
    
    Requires MP_API_KEY environment variable.
    Returns:
        pd.DataFrame: The loaded data.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
        return None
        
    try:
        from materialsproject import MPRester
        
        with MPRester(api_key) as mpr:
            # Query for Al alloys with Poisson and Young modulus
            docs = mpr.summary.search(
                elements=["Al"],
                property_ids=["poisson_ratio", "young_modulus"],
                limit=1000 # Limit for safety
            )
            
            if not docs:
                logger.warning("Materials Project returned 0 entries.")
                return None
                
            # Convert to DataFrame
            data = []
            for doc in docs:
                row = {
                    "material_id": doc.material_id,
                    "poisson_ratio": doc.poisson_ratio,
                    "young_modulus": doc.young_modulus,
                    "composition": doc.composition,
                    "source": "Materials Project"
                }
                data.append(row)
                
            df = pd.DataFrame(data)
            logger.info(f"Successfully loaded {len(df)} rows from Materials Project.")
            return df
            
    except Exception as e:
        logger.error(f"Materials Project fetch failed: {e}")
        return None

def run_extraction(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Orchestrates the dual-source extraction strategy.
    
    Strategy (FR-001):
    1. Attempt MP first.
    2. If MP returns zero entries, attempt NIST.
    3. If both fail, HALT with error.
    
    Args:
        output_dir: Directory to save raw data. Defaults to config.data_raw_dir.
        
    Returns:
        Dict with counts and status.
        
    Raises:
        RuntimeError: If no valid data is found in either source.
    """
    if output_dir is None:
        output_dir = config.data_raw_dir
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "mp_count": 0,
        "nist_count": 0,
        "total_count": 0,
        "status": "success",
        "errors": []
    }
    
    # 1. Attempt MP
    mp_df = fetch_materials_project_data()
    if mp_df is not None and not mp_df.empty:
        result["mp_count"] = len(mp_df)
        mp_path = output_dir / "materials_project_raw.csv"
        mp_df.to_csv(mp_path, index=False)
        logger.info(f"Saved MP data to {mp_path}")
    
    # 2. Attempt NIST (if MP failed or empty)
    if result["mp_count"] == 0:
        try:
            nist_df = fetch_nist_data()
            if nist_df is not None and not nist_df.empty:
                result["nist_count"] = len(nist_df)
                nist_path = output_dir / "nist_raw.csv"
                nist_df.to_csv(nist_path, index=False)
                logger.info(f"Saved NIST data to {nist_path}")
        except RuntimeError as e:
            result["errors"].append(str(e))
            logger.critical(str(e))
    
    # 3. Validation
    total = result["mp_count"] + result["nist_count"]
    if total == 0:
        msg = "CRITICAL: No valid data found in MP or NIST."
        logger.error(msg)
        result["status"] = "failed"
        raise RuntimeError(msg)
        
    result["total_count"] = total
    logger.info(f"Extraction complete. Total records: {total}")
    return result

def main():
    """Entry point for CLI."""
    log_operation("extraction_start")
    try:
        res = run_extraction()
        print(f"Extraction Result: {res}")
    except RuntimeError as e:
        print(f"Extraction Failed: {e}")
        raise

if __name__ == "__main__":
    main()