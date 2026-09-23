"""
Ingestion module for MedMisBench dataset.

Handles downloading, filtering, schema validation, and checksum generation.
"""
import os
import hashlib
import csv
import yaml
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datasets import load_dataset
import re

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
DATASET_NAME = "medmisbench/medmisbench"
OUTPUT_FILE = "data/raw/medmis_subset.csv"
CHECKSUM_FILE = "state/artifact_hashes.yaml"
FILTER_LABELS = ["Authority-framed", "Exception-poisoning"]
REQUIRED_COLUMNS = ["prompt_id", "prompt_text", "false_claim", "correct_answer"]

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def extract_false_claim_from_text(text: str) -> Optional[str]:
    """
    Attempt to extract false_claim from prompt text using regex.
    Looks for patterns like 'false_claim: ...' or 'misleading: ...'
    """
    patterns = [
        r'false_claim[:\s]+["\']?([^"\']+)["\']?',
        r'misleading[:\s]+["\']?([^"\']+)["\']?',
        r'claim[:\s]+["\']?([^"\']+)["\']?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def load_and_filter_dataset() -> List[Dict[str, Any]]:
    """
    Load MedMisBench dataset with streaming and filter for target labels.
    
    Returns:
        List of filtered dataset items.
    
    Raises:
        DatasetDownloadError: If download fails or no real data is found.
    """
    logger.info(f"Loading dataset: {DATASET_NAME} with streaming=True")
    
    try:
        # Use streaming to handle large datasets
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        filtered_items = []
        count = 0
        total_count = 0
        
        for item in dataset:
            total_count += 1
            
            # Check if label matches our filter criteria
            label = item.get("label", "")
            if label in FILTER_LABELS:
                filtered_items.append(item)
                count += 1
                
                # Log progress every 1000 items
                if count % 1000 == 0:
                    logger.info(f"Processed {total_count} items, found {count} matches")
            
            # Safety break for testing (remove in production)
            # if total_count > 10000:
            #     break
        
        logger.info(f"Download complete. Total items: {total_count}, Filtered items: {count}")
        
        if count == 0:
            raise Exception("No items found matching filter criteria. Dataset may be empty or labels may have changed.")
        
        return filtered_items
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        raise Exception(f"Dataset download failed: {str(e)}. No synthetic fallback available.")

def validate_schema(items: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate that items have required columns.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not items:
        return False, "Dataset is empty"
    
    first_item = items[0]
    missing_cols = []
    
    for col in REQUIRED_COLUMNS:
        if col not in first_item:
            missing_cols.append(col)
    
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"
    
    return True, None

def save_to_csv(items: List[Dict[str, Any]], output_path: str) -> None:
    """Save items to CSV file."""
    if not items:
        raise Exception("Cannot save empty dataset")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Get fieldnames from first item
    fieldnames = list(items[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
    
    logger.info(f"Saved {len(items)} items to {output_path}")

def save_checksum_to_state(file_path: str, checksum_file: str) -> None:
    """Compute and save SHA-256 checksum to state file."""
    checksum = compute_sha256(file_path)
    
    # Ensure state directory exists
    state_dir = os.path.dirname(checksum_file)
    os.makedirs(state_dir, exist_ok=True)
    
    # Load existing state or create new
    state = {}
    if os.path.exists(checksum_file):
        try:
            with open(checksum_file, 'r') as f:
                state = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")
    
    # Update state with new checksum
    state["medmis_subset"] = {
        "file": file_path,
        "sha256": checksum,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write updated state
    with open(checksum_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Saved checksum for {file_path}: {checksum}")

def run_ingestion_pipeline() -> None:
    """Run the complete ingestion pipeline."""
    logger.info("Starting ingestion pipeline")
    
    # Step 1: Load and filter dataset
    items = load_and_filter_dataset()
    
    # Step 2: Validate schema
    is_valid, error_msg = validate_schema(items)
    if not is_valid:
        # Attempt regex extraction fallback for false_claim
        logger.warning(f"Schema validation failed: {error_msg}. Attempting regex extraction fallback.")
        
        if "false_claim" in error_msg:
            logger.info("Attempting to extract false_claim from prompt text...")
            extracted_count = 0
            
            for item in items:
                if "false_claim" not in item or not item["false_claim"]:
                    extracted = extract_false_claim_from_text(item.get("prompt_text", ""))
                    if extracted:
                        item["false_claim"] = extracted
                        extracted_count += 1
            
            logger.info(f"Successfully extracted false_claim for {extracted_count} items")
            
            # Re-validate
            is_valid, error_msg = validate_schema(items)
            if not is_valid:
                raise Exception(f"Schema validation failed after fallback: {error_msg}")
        else:
            raise Exception(f"Schema validation failed: {error_msg}")
    
    # Step 3: Save to CSV
    save_to_csv(items, OUTPUT_FILE)
    
    # Step 4: Compute and save checksum
    save_checksum_to_state(OUTPUT_FILE, CHECKSUM_FILE)
    
    logger.info("Ingestion pipeline completed successfully")

def main():
    """Main entry point."""
    try:
        run_ingestion_pipeline()
        print(f"Successfully processed dataset. Output: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
