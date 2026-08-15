import json
import hashlib
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package is required. Install via: pip install datasets")
    sys.exit(1)

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_chembl_pharmacophores(output_path: Path) -> Dict[str, Any]:
    """
    Fetch bioactivity data from ChEMBL (Homo sapiens, IC50 or Ki) and generate
    a pharmacophore reference file.
    
    This function:
    1. Loads the 'chembl' dataset from Hugging Face.
    2. Filters for target organism 'Homo sapiens' and activity types 'IC50' or 'Ki'.
    3. Extracts representative molecular structures (SMILES) and activity values.
    4. Calculates a SHA256 checksum of the resulting JSON data.
    5. Raises an exception if the data fetch fails (no synthetic fallback).
    
    Args:
        output_path: Path where the pharmacophores.json file will be saved.
        
    Returns:
        Dictionary containing metadata and the pharmacophore data.
        
    Raises:
        RuntimeError: If the ChEMBL dataset cannot be fetched or filtered.
    """
    logger.info(f"Fetching ChEMBL data for Homo sapiens (IC50/Ki)...")
    
    # Define the query parameters for the dataset
    # We use the 'chembl' dataset from Hugging Face which is a standard source
    dataset_name = "chembl/chembl"
    
    try:
        # Load the dataset in streaming mode to handle large size without memory issues
        # We filter on the fly to avoid downloading the full dataset if not needed
        # Note: The exact column names might vary, but 'target_organism' and 'activity_type' are standard
        dataset = load_dataset(
            dataset_name, 
            split="train", 
            streaming=True
        )
    except Exception as e:
        logger.error(f"Failed to load ChEMBL dataset from Hugging Face: {e}")
        raise RuntimeError(f"CRITICAL: Could not fetch real data from ChEMBL. {e}")

    # Filter the dataset
    logger.info("Filtering for Homo sapiens and IC50/Ki activities...")
    filtered_data = []
    count = 0
    
    # We need to collect a representative set. 
    # Since streaming is used, we iterate and collect until we have enough or the dataset ends.
    # We'll aim for a reasonable number of entries to form a reference set.
    max_entries = 10000 
    
    try:
        for item in dataset:
            # Check target organism
            organism = item.get('target_organism', '')
            if 'Homo sapiens' not in organism:
                continue
            
            # Check activity type
            activity_type = item.get('activity_type', '')
            if activity_type not in ['IC50', 'Ki']:
                continue
            
            # Extract relevant fields
            # Standard ChEMBL fields: molecule_structures (SMILES), standard_value, standard_units, activity_type
            smiles = item.get('molecule_structures', {}).get('canonical_smiles')
            standard_value = item.get('standard_value')
            standard_units = item.get('standard_units')
            
            if not smiles or standard_value is None:
                continue
            
            # Convert to pIC50 or pKi if necessary for consistency
            # pX = -log10(X in M)
            # IC50/Ki are usually in nM or uM. We assume standard units are consistent with the dataset.
            # For simplicity, we store the raw value and unit, and the SMILES.
            
            entry = {
                "smiles": smiles,
                "activity_type": activity_type,
                "standard_value": standard_value,
                "standard_units": standard_units,
                "target_organism": organism
            }
            
            filtered_data.append(entry)
            count += 1
            
            if count >= max_entries:
                logger.info(f"Collected {count} entries. Stopping to keep reference set manageable.")
                break
                
    except Exception as e:
        logger.error(f"Error during dataset iteration: {e}")
        raise RuntimeError(f"CRITICAL: Failed to process ChEMBL data stream. {e}")

    if count == 0:
        raise RuntimeError("CRITICAL: No valid data found for Homo sapiens with IC50/Ki activities.")

    logger.info(f"Successfully filtered {count} entries.")

    # Prepare the final structure
    result = {
        "metadata": {
            "source": "ChEMBL",
            "dataset_version": "latest_streaming",
            "query": "target_organism=Homo sapiens AND activity_type='IC50' OR 'Ki'",
            "count": count,
            "timestamp": "generated_runtime"
        },
        "pharmacophores": filtered_data
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    # Calculate checksum
    checksum = calculate_sha256(output_path)
    result["metadata"]["sha256"] = checksum
    
    # Update the file with the checksum
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Pharmacophore reference saved to {output_path} with SHA256: {checksum}")
    return result

def main():
    """Main entry point for generating pharmacophores."""
    output_dir = Path("data/reference")
    output_file = output_dir / "pharmacophores.json"
    
    logger.info("Starting pharmacophore generation task T038a...")
    
    try:
        fetch_chembl_pharmacophores(output_file)
        logger.info("Task T038a completed successfully.")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()