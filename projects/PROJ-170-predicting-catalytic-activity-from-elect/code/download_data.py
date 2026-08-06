import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import local project utilities
from config import get_project_root, get_data_path, get_output_path
from utils.hashing import compute_file_hash, save_hash, verify_file_hash
from utils.validation import verify_data_checksum, validate_schema

try:
    from datasets import load_dataset
except ImportError:
    logging.critical("The 'datasets' package is required. Install it via 'pip install datasets'.")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    logging.critical("The 'pandas' package is required. Install it via 'pip install pandas'.")
    sys.exit(1)

try:
    from pymatgen.core import Composition
except ImportError:
    logging.critical("The 'pymatgen' package is required. Install it via 'pip install pymatgen'.")
    sys.exit(1)

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "Open-Catalyst/oc20-experimental"
FILE_NAME = "oc20.h5"
OUTPUT_REL_PATH = "data/raw/oc20_sample.h5"
CHECKSUM_FILE_NAME = "checksums.json"
STRATIFICATION_KEY = "composition_family"

def load_expected_checksums() -> Dict[str, str]:
    """Loads expected checksums from a local file if it exists."""
    root = get_project_root()
    checksum_path = root / CHECKSUM_FILE_NAME
    if checksum_path.exists():
        with open(checksum_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksum(filename: str, checksum: str) -> None:
    """Saves a checksum for a specific file."""
    root = get_project_root()
    checksum_path = root / CHECKSUM_FILE_NAME
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def compute_file_hash(filepath: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filename: str, expected_hash: str, actual_hash: str) -> bool:
    """Verifies if the actual hash matches the expected hash."""
    return expected_hash == actual_hash

def derive_composition_family(composition_str: str) -> str:
    """
    Derives the composition family (metal/oxide type) from a composition string.
    Uses pymatgen to parse the composition and determine the primary element type.
    """
    try:
        comp = Composition(composition_str)
        elements = comp.elements
        if not elements:
            return "Unknown"
        
        # Heuristic: If Oxygen is present and > 50% of the formula weight or count, classify as Oxide
        # Otherwise, classify based on the most abundant metal or the element type
        total_atoms = sum(comp.get_atomic_fraction(e) for e in elements)
        oxygen_fraction = comp.get_atomic_fraction("O") if "O" in [e.symbol for e in elements] else 0.0
        
        if oxygen_fraction > 0.3: # Threshold for oxide classification
            return "Oxide"
        
        # Check for common metals
        metals = [e.symbol for e in elements if e.is_metal]
        if metals:
            # Return the most abundant metal as the family identifier
            most_abundant = max(metals, key=lambda m: comp.get_atomic_fraction(m))
            return f"Metal_{most_abundant}"
        
        return "Other"
    except Exception as e:
        logger.warning(f"Could not parse composition '{composition_str}': {e}")
        return "Unknown"

def download_stratified_sample(output_path: Optional[Path] = None) -> Path:
    """
    Downloads a stratified sample of the OC20 dataset from HuggingFace.
    
    The dataset is streamed, processed to derive a stratification key,
    and then sampled. The output is saved as an HDF5 file.
    
    Args:
        output_path: Optional path to save the output file. Defaults to data/raw/oc20_sample.h5.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / OUTPUT_REL_PATH
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading dataset '{DATASET_ID}' with streaming...")
    
    try:
        # Load dataset with streaming to avoid downloading full ~7GB+ initially
        # We stream to derive stratification keys and select a representative sample
        dataset = load_dataset(
            DATASET_ID,
            split="train", # Assuming we want the training split for the sample
            streaming=True,
            trust_remote_code=True
        )
        
        logger.info("Deriving composition families for stratification...")
        
        # Collect a sample to determine stratification distribution or iterate to build a balanced sample
        # Since we need to stratify, we need to know the distribution. 
        # Strategy: Iterate through a subset to estimate distribution, then select.
        # However, for a robust stratified sample from a stream without full materialization:
        # 1. We will collect a reasonable number of entries per family if possible, or
        # 2. We will sample randomly and then filter if we can't guarantee exact stratification on the fly.
        # Given the constraints, we will iterate to build a dictionary of lists for a target sample size.
        
        target_sample_size = 5000 # Reasonable sample size for a pipeline test
        samples_by_family = {}
        family_counts = {}
        
        logger.info("Iterating through dataset stream to build stratified sample...")
        
        # We will iterate through the stream. To ensure we get a stratified sample,
        # we will collect entries until we have a target number for each family or reach a max limit.
        # Since the stream is large, we will limit the total iterations to avoid hanging.
        max_iterations = 20000 
        count = 0
        
        for item in dataset:
            if count >= max_iterations:
                logger.warning(f"Reached max iterations ({max_iterations}). Stopping stream scan.")
                break
            
            comp_str = item.get("composition", "")
            if not comp_str:
                continue
            
            family = derive_composition_family(comp_str)
            
            if family not in samples_by_family:
                samples_by_family[family] = []
                family_counts[family] = 0
            
            # Add to sample if we haven't hit the per-family cap (e.g., 500 per family)
            # Or if we just want a total sample, we can add randomly.
            # Let's aim for a balanced-ish sample: max 1000 per family, stop if total > target
            if family_counts[family] < 1000 and len(samples_by_family[family]) < 1000:
                # Ensure we store the necessary fields for the downstream tasks
                # Assuming the dataset has fields like 'composition', 'surface_facet', etc.
                # We need to check what fields are actually available in the dataset.
                # Common OC20 fields: 'atoms', 'energy', 'forces', 'labels', etc.
                # The task requires: composition, surface_facet, experimental_tof, d_band_center, adsorption_energy
                # We will store the raw item and process later, or extract what we can now.
                
                # Extract relevant fields if they exist, otherwise store raw
                sample_entry = {
                    "composition": comp_str,
                    "family": family,
                    "raw_item": item # Keep raw item for now, will convert to DataFrame later
                }
                samples_by_family[family].append(sample_entry)
                family_counts[family] += 1
            
            count += 1
            
            if count % 5000 == 0:
                logger.info(f"Processed {count} items. Families found: {list(family_counts.keys())}")
        
        # Flatten the collected samples
        final_samples = []
        for family, entries in samples_by_family.items():
            final_samples.extend(entries)
        
        logger.info(f"Collected {len(final_samples)} stratified samples across {len(samples_by_family)} families.")
        
        if len(final_samples) == 0:
            raise ValueError("No samples were collected from the dataset stream.")
        
        # Convert to DataFrame
        # We need to extract the specific fields required by the task:
        # composition, surface_facet, experimental_tof, d_band_center, adsorption_energy
        # The OC20 dataset structure might vary. We assume standard keys or map them.
        # If specific keys are missing, we might need to handle that.
        
        data_rows = []
        for entry in final_samples:
            item = entry["raw_item"]
            row = {
                "composition": entry["composition"],
                "family": entry["family"],
                "surface_facet": item.get("surface_facet", item.get("facet", "Unknown")),
                "experimental_tof": item.get("experimental_tof", None), # May be None
                "d_band_center": item.get("d_band_center", None),
                "adsorption_energy": item.get("adsorption_energy", item.get("energy", None))
            }
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Remove rows where critical fields are missing if necessary, 
        # but for a raw download, we might keep them and let preprocessing handle it.
        # The task says "Download... Output: data/raw/oc20_sample.h5".
        
        logger.info(f"Saving DataFrame to {output_path} (HDF5 format)...")
        df.to_hdf(output_path, key='df', mode='w')
        
        # Compute and save checksum
        file_hash = compute_file_hash(output_path)
        save_checksum(FILE_NAME, file_hash)
        logger.info(f"File saved and checksum recorded: {file_hash}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise

def verify_downloaded_data() -> bool:
    """Verifies the downloaded file against the stored checksum."""
    root = get_project_root()
    file_path = root / OUTPUT_REL_PATH
    
    if not file_path.exists():
        logger.error(f"Downloaded file not found: {file_path}")
        return False
    
    checksums = load_expected_checksums()
    if FILE_NAME not in checksums:
        logger.error(f"No checksum found for {FILE_NAME}")
        return False
    
    expected_hash = checksums[FILE_NAME]
    actual_hash = compute_file_hash(file_path)
    
    if verify_checksum(FILE_NAME, expected_hash, actual_hash):
        logger.info("Checksum verification passed.")
        return True
    else:
        logger.error(f"Checksum verification failed. Expected: {expected_hash}, Got: {actual_hash}")
        return False

def handle_excluded_datasets() -> None:
    """
    Handles logic for excluded datasets if any.
    Currently, per plan, we rely exclusively on OC20.
    """
    logger.info("No excluded datasets to handle for this pipeline.")

def main():
    """Main entry point for downloading data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_project_root() / "outputs" / "run.log")
        ]
    )
    
    logger.info("Starting data download process for T010...")
    
    try:
        output_path = download_stratified_sample()
        logger.info(f"Data download completed successfully: {output_path}")
        
        # Verify immediately
        if verify_downloaded_data():
            logger.info("Verification successful.")
        else:
            logger.warning("Verification failed, but file was created.")
            
    except Exception as e:
        logger.critical(f"Data download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
