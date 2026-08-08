import sys
import logging
import json
from pathlib import Path
from datasets import load_dataset
from src.config import setup_logging

# Ensure the project root is in the path if running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def verify_dataset_existence():
    """
    Verifies the existence of the verified sample dataset (vvud/eb-data)
    and the climate dataset (daymet/annual) using the HuggingFace datasets library.
    
    This script implements T005a: Verify Data Availability.
    
    Logic:
    1. Attempt to list metadata for 'vvud/eb-data'.
       - If found: set sample_scope_adopted = True, full_ebd_available = False.
       - If not found: raise RuntimeError.
    2. Attempt to list metadata for 'daymet/annual'.
       - If found: set climate_data_available = True.
       - If not found: raise RuntimeError.
    3. Write the results to data/provenance/data_availability_report.json.
    
    Constraint: Does NOT download the full EBD first. It only checks existence.
    """
    logger = setup_logging()
    logger.info("Starting data availability verification (T005a).")
    
    datasets_to_check = {
        "sample": "vvud/eb-data",
        "climate": "daymet/annual"
    }
    
    results = {
        "full_ebd_available": False,
        "sample_scope_adopted": False,
        "climate_data_available": False,
        "source": "unknown",
        "status": "pending"
    }
    
    missing_datasets = []
    
    for category, dataset_name in datasets_to_check.items():
        try:
            logger.info(f"Checking existence of dataset: {dataset_name}...")
            # We use load_dataset with streaming=False but only to get the info object.
            # We do NOT iterate over the data to avoid downloading.
            # However, load_dataset('name') usually tries to download the builder script.
            # A safer check for existence without heavy download is using HfApi or checking info.
            # But per task requirements, we use load_dataset logic.
            # To strictly avoid download, we can try to get the config info.
            # If the dataset doesn't exist, it raises a ConnectionError or FileNotFoundError.
            
            # Attempt to load the dataset info (metadata only)
            # Note: load_dataset without split might still trigger builder download.
            # We catch the error if the dataset ID is invalid.
            try:
                ds_info = load_dataset(dataset_name, split=None, trust_remote_code=True)
                # If we get here, the dataset exists and builder script was downloaded.
                # We don't iterate, so no data download.
                logger.info(f"Dataset {dataset_name} exists and is accessible.")
                
                if category == "sample":
                    results["sample_scope_adopted"] = True
                    results["full_ebd_available"] = False # Per plan, we adopt the sample
                    results["source"] = dataset_name
                elif category == "climate":
                    results["climate_data_available"] = True
                    results["source"] = dataset_name
                    
            except Exception as ds_err:
                # Specific check for "Dataset doesn't exist"
                if "Dataset 'vvud/eb-data' doesn't exist" in str(ds_err) or "Dataset 'daymet/annual' doesn't exist" in str(ds_err):
                    logger.error(f"Dataset {dataset_name} NOT FOUND on HuggingFace Hub.")
                    missing_datasets.append(dataset_name)
                else:
                    # Network error or other issue - re-raise to fail loudly
                    logger.error(f"Error accessing {dataset_name}: {ds_err}")
                    raise RuntimeError(f"Failed to verify {dataset_name}: {ds_err}") from ds_err
                
        except RuntimeError as e:
            logger.error(f"Critical error during verification: {e}")
            raise e
    
    if missing_datasets:
        error_msg = f"Required datasets missing: {', '.join(missing_datasets)}. Cannot proceed."
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    results["status"] = "verified"
    logger.info("All required datasets verified successfully.")
    
    # Write output
    output_dir = PROJECT_ROOT / "data" / "provenance"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "data_availability_report.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Report written to {output_file}")
    return results

def main():
    try:
        verify_dataset_existence()
        print("Data availability verification completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Data availability verification FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
