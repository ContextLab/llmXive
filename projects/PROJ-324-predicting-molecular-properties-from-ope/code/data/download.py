"""
Download and process molecular data from PubChem.

This module handles fetching compound data, saving raw data,
creating metadata with source verification hashes, and managing
the initial dataset acquisition pipeline.
"""

import os
import sys
import json
import logging
import hashlib
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.config import get_runtime_config
    from logging_utils import setup_logger
else:
    from code.utils.config import get_runtime_config
    from code.logging_utils import setup_logger

# Configure logging
logger = setup_logger(__name__)

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "data/derived/figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {dirs}")

def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file for provenance verification.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise

def fetch_molecule_properties(cids: List[int], properties: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch molecular properties from PubChem using PubChemPy.

    Args:
        cids: List of PubChem Compound IDs.
        properties: List of property names to fetch.

    Returns:
        List of dictionaries containing compound data.
    """
    try:
        import pubchempy as pcp
    except ImportError:
        logger.error("PubChemPy not installed. Please install with: pip install pubchempy")
        raise

    records = []
    batch_size = 100
    
    for i in range(0, len(cids), batch_size):
        batch_cids = cids[i:i+batch_size]
        logger.info(f"Fetching batch {i//batch_size + 1}: CIDs {batch_cids[0]}-{batch_cids[-1]}")
        
        try:
            compounds = pcp.get_compounds(batch_cids, 'cid', properties=properties)
            
            for c in compounds:
                rec = {}
                if getattr(c, 'isomeric_smiles', None):
                    rec['SMILES'] = c.isomeric_smiles
                if getattr(c, 'xlogp', None) is not None:
                    rec['LogP'] = c.xlogp
                if getattr(c, 'water_solubility', None) is not None:
                    rec['Solubility'] = c.water_solubility
                if getattr(c, 'boiling_point', None) is not None:
                    rec['Boiling Point'] = c.boiling_point
                if getattr(c, 'molecular_weight', None) is not None:
                    rec['Molecular Weight'] = c.molecular_weight
                if getattr(c, 'record_type', None) is not None:
                    rec['Property Type'] = c.record_type
                
                # Add CID for traceability
                rec['CID'] = c.cid
                
                if rec:
                    records.append(rec)
                    
        except Exception as e:
            logger.warning(f"Error fetching batch {batch_cids}: {e}")
            continue
        
        # Rate limiting to avoid blocking
        time.sleep(0.5)

    logger.info(f"Fetched {len(records)} records from PubChem")
    return records

def create_diverse_cid_list(query: str = "molecular weight > 200 AND < 500", 
                            target_count: int = 5000) -> List[int]:
    """
    Create a list of CIDs based on a PubChem query.
    
    Note: This is a placeholder for a more sophisticated sampling strategy.
    For now, we use a predefined list of diverse compounds for demonstration.
    In a production setting, this would query PubChem's PUG-REST API.

    Args:
        query: PubChem query string (currently unused in demo).
        target_count: Target number of CIDs.

    Returns:
        List of CIDs.
    """
    # Using a diverse set of CIDs for demonstration
    # In production, this would be replaced with actual query results
    base_cids = [2244, 3672, 5957, 702, 5281, 1234, 5678, 9012, 3456, 7890]
    
    # Expand to target count by cycling and adding variations
    # This is a simplified approach; real implementation would use PubChem search
    cids = []
    current = 2244
    while len(cids) < target_count:
        cids.append(current)
        current += 1000  # Simple increment to get diverse compounds
        
    return cids[:target_count]

def save_raw_data(records: List[Dict[str, Any]], output_path: str):
    """
    Save raw data records to a CSV file.

    Args:
        records: List of record dictionaries.
        output_path: Path to output CSV file.
    """
    if not records:
        logger.warning("No records to save.")
        return

    df = pd.DataFrame(records)
    
    # Ensure required columns exist
    required_cols = ['SMILES', 'CID']
    for col in required_cols:
        if col not in df.columns:
            logger.warning(f"Missing required column: {col}")
            df[col] = None

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def create_dataset_metadata(cids: List[int], properties: List[str], 
                            raw_file_path: str, metadata_path: str):
    """
    Create dataset metadata JSON with source verification hash.
    
    This function computes a SHA-256 hash of the raw downloaded CSV file
    and records it alongside the PubChem query parameters to ensure
    cryptographic traceability of the data source.

    Args:
        cids: List of CIDs used for fetching.
        properties: List of properties fetched.
        raw_file_path: Path to the raw CSV file.
        metadata_path: Path to save the metadata JSON.
    """
    if not os.path.exists(raw_file_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_file_path}")

    # Compute hash of the raw file
    file_hash = compute_file_hash(raw_file_path)
    
    # Check for optional fields in the raw data
    df = pd.read_csv(raw_file_path)
    has_uncertainty = 'Measurement_Uncertainty' in df.columns
    has_quantity = 'Quantity_of_Substance' in df.columns
    
    # Determine experimental ratio (simplified - real implementation would parse 'Property Type')
    experimental_ratio = 0.0
    if 'Property Type' in df.columns:
        experimental_count = len(df[df['Property Type'] == 'Experimental'])
        experimental_ratio = experimental_count / len(df) if len(df) > 0 else 0.0

    metadata = {
        "source": "PubChem",
        "query_parameters": {
            "cids_sampled": len(cids),
            "properties_requested": properties,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "measurement_uncertainty_status": "Available" if has_uncertainty else "Not Available in Source",
        "quantity_of_substance_status": "Available" if has_quantity else "Not Available in Source",
        "experimental_ratio": round(experimental_ratio, 4),
        "source_verification_hash": file_hash,
        "raw_data_file": raw_file_path,
        "hash_algorithm": "SHA-256"
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Created dataset metadata with source hash: {file_hash[:16]}...")
    logger.info(f"Metadata saved to {metadata_path}")

def main():
    """Main entry point for data download pipeline."""
    logger.info("Starting data download pipeline...")
    
    ensure_dirs()
    
    # Configuration
    target_cids = 100  # Reduced for demo; increase for full dataset
    properties = ['IsomericSMILES', 'XLogP', 'WaterSolubility', 
                 'BoilingPoint', 'MolecularWeight', 'RecordType']
    
    # Create diverse CID list
    logger.info("Creating diverse CID list...")
    cids = create_diverse_cid_list(target_count=target_cids)
    
    # Fetch data
    logger.info("Fetching molecule properties from PubChem...")
    records = fetch_molecule_properties(cids, properties)
    
    if not records:
        logger.error("No data fetched. Exiting.")
        sys.exit(1)
    
    # Save raw data
    raw_output_path = "data/raw/pubchem_raw.csv"
    logger.info(f"Saving raw data to {raw_output_path}...")
    save_raw_data(records, raw_output_path)
    
    # Create metadata with source hash
    metadata_path = "data/raw/dataset_metadata.json"
    logger.info(f"Creating dataset metadata with source hash...")
    create_dataset_metadata(cids, properties, raw_output_path, metadata_path)
    
    logger.info("Data download pipeline completed successfully.")

if __name__ == "__main__":
    main()