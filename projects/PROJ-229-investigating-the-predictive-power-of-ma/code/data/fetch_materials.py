import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project utils as per API surface
from utils.logger import get_pipeline_logger, log_error, log_warning, log_info
from utils.error_handling import DataFetchError, handle_error

# Import from config
from config import get_config, get_api_key

# Import from matbench if available for fallback
# We use a try/except to check availability without hard dependency on failure
try:
    from datasets import load_dataset
    MATBENCH_AVAILABLE = True
except ImportError:
    MATBENCH_AVAILABLE = False
    log_warning("datasets library not installed. Fallback to matbench will be skipped.")


def fetch_materials_project_data(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches materials data from the Materials Project API.
    
    This function attempts to fetch data using the mp-api. If the API is unavailable
    (rate limit, network error, invalid key), it raises a DataFetchError.
    It does NOT handle fallback here; the main function handles the fallback logic.
    """
    if not api_key:
        raise DataFetchError("No API key provided for Materials Project.")

    try:
        # Import mp-api dynamically to avoid hard dependency if not installed
        # but we expect it to be in requirements.txt
        from mp_api.client import MPRester
        
        logger = get_pipeline_logger()
        logger.info("Connecting to Materials Project API...")
        
        with MPRester(api_key) as mpr:
            # Fetch a subset of materials with melting point data
            # Using a small limit for the initial fetch to test connectivity
            # In a real scenario, we might iterate through all materials
            docs = mpr.materials.search(
                fields=["material_id", "formula_pretty", "melting_point", "structure", "nsites"],
                limit=1000  # Limit for demo/initial run
            )
            
            data = []
            for doc in docs:
                entry = {
                    "material_id": doc.material_id,
                    "formula_pretty": doc.formula_pretty,
                    "melting_point": doc.melting_point,
                    "nsites": doc.nsites
                }
                # Handle structure serialization if needed, or omit for this task
                # Keeping it simple for now as per typical fetch patterns
                data.append(entry)
            
            log_info(f"Successfully fetched {len(data)} materials from Materials Project.")
            return data

    except Exception as e:
        # Log the specific error but raise a custom error to trigger fallback logic
        log_error(f"Failed to fetch from Materials Project API: {str(e)}")
        raise DataFetchError(f"Materials Project API fetch failed: {str(e)}")


def fetch_matbench_fallback() -> List[Dict[str, Any]]:
    """
    Fetches data from the matbench/literature_pcm_validation_set as a fallback.
    This is a verified real data source.
    """
    if not MATBENCH_AVAILABLE:
        raise DataFetchError("matbench dataset library not available for fallback.")

    try:
        logger = get_pipeline_logger()
        log_info("Fetching fallback data from matbench/literature_pcm_validation_set...")
        
        # Load the dataset
        dataset = load_dataset("matbench/literature_pcm_validation_set", split="train")
        
        # Convert to list of dicts
        # Ensure we have the necessary columns
        if "formula" not in dataset.column_names:
            raise DataFetchError("Fallback dataset missing 'formula' column.")
        
        data = []
        for item in dataset:
            # Map matbench fields to our expected format
            entry = {
                "material_id": item.get("formula", f"unknown_{hash(str(item))}"), # Fallback ID
                "formula_pretty": item.get("formula", "Unknown"),
                "melting_point": item.get("melting_point", None), # Check if column exists
                "nsites": item.get("nsites", None)
            }
            # Only include if melting point is present
            if entry["melting_point"] is not None:
                data.append(entry)
        
        log_info(f"Successfully fetched {len(data)} materials from matbench fallback.")
        return data

    except Exception as e:
        log_error(f"Failed to fetch fallback data from matbench: {str(e)}")
        raise DataFetchError(f"Matbench fallback fetch failed: {str(e)}")


def main():
    """
    Main entry point for fetching materials data.
    
    Logic:
    1. Attempt to fetch from Materials Project API.
    2. If successful, save to data/raw/materials_project_data.json.
    3. If API fails (DataFetchError), attempt fallback to matbench.
    4. If fallback succeeds, save to data/raw/materials_project_data.json (or a specific fallback file? 
       The task says 'proceed', implying we need data to continue. We will save to the standard path 
       but log that it's fallback data).
    5. If both fail, log critical error and exit (do not raise to pipeline, just log and stop).
    
    Constraint: MUST NOT raise error on fetch failure; MUST log fallback and proceed.
    """
    logger = get_pipeline_logger()
    logger.info("Starting materials data fetch (Task T033)...")
    
    config = get_config()
    api_key = get_api_key("MP_API_KEY")
    
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "materials_project_data.json"
    
    final_data = None
    source_used = None
    
    # 1. Try Materials Project
    try:
        logger.info("Attempting to fetch from Materials Project API...")
        final_data = fetch_materials_project_data(api_key)
        source_used = "materials_project"
        log_info("Primary fetch successful.")
    except DataFetchError as e:
        log_warning(f"Primary fetch failed: {e}. Attempting fallback to matbench.")
        
        # 2. Try Fallback
        try:
            final_data = fetch_matbench_fallback()
            source_used = "matbench_fallback"
            log_info("Fallback fetch successful.")
        except DataFetchError as e_fallback:
            log_error(f"Both primary and fallback fetches failed: {e_fallback}")
            # Do not raise, just log and exit. The pipeline will likely fail later 
            # if no data is present, but we followed the constraint of not raising here.
            return
    
    if final_data is None:
        log_error("No data was fetched from any source.")
        return

    # 3. Save Data
    try:
        with open(output_file, 'w') as f:
            json.dump(final_data, f, indent=2)
        
        log_info(f"Data saved to {output_file} from source: {source_used}")
        
        # Validate output
        if not os.path.exists(output_file):
            log_error("Output file was not created.")
        elif os.path.getsize(output_file) == 0:
            log_error("Output file is empty.")
        else:
            log_info("Fetch and save completed successfully.")
            
    except IOError as e:
        log_error(f"Failed to write data to file: {e}")
        # Critical failure in saving, but we still followed the fetch logic


if __name__ == "__main__":
    main()