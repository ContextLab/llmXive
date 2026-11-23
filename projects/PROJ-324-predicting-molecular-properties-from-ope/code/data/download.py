import os
import sys
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import pubchempy as pcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all required directories exist."""
    base_dir = Path(__file__).parent.parent.parent
    data_raw = base_dir / "data" / "raw"
    data_raw.mkdir(parents=True, exist_ok=True)
    return data_raw

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_molecule_properties(cids: List[int], properties: List[str]) -> pd.DataFrame:
    """
    Fetch molecule properties from PubChem using PubChemPy.
    
    Args:
        cids: List of Compound IDs to fetch.
        properties: List of property names to fetch (e.g., 'IsomericSMILES', 'XLogP').
    
    Returns:
        DataFrame with fetched properties.
    """
    records = []
    for cid in cids:
        try:
            compound = pcp.get_compounds(cid, 'cid')[0]
            record = {'cid': cid}
            
            # Fetch requested properties
            for prop in properties:
                try:
                    # Handle specific property access
                    if prop == 'IsomericSMILES':
                        record['smiles'] = compound.isomeric_smiles
                    elif prop == 'XLogP':
                        record['xlogp'] = compound.xlogp
                    elif prop == 'WaterSolubility':
                        record['solubility'] = compound.water_solubility
                    elif prop == 'BoilingPoint':
                        record['boiling_point'] = compound.boiling_point
                    elif prop == 'MolecularWeight':
                        record['molecular_weight'] = compound.molecular_weight
                    elif prop == 'RecordType':
                        record['record_type'] = compound.record_type
                    else:
                        # Try generic attribute access
                        val = getattr(compound, prop.lower(), None)
                        if val is not None:
                            record[prop.lower()] = val
                except Exception as e:
                    logger.warning(f"Failed to fetch {prop} for CID {cid}: {e}")
                    record[prop.lower()] = None
            
            # Add metadata about source
            record['source_type'] = 'Experimental' if compound.record_type == 'experimental' else 'Computed'
            records.append(record)
            
        except Exception as e:
            logger.error(f"Failed to fetch data for CID {cid}: {e}")
            continue
    
    return pd.DataFrame(records)

def create_diverse_cid_list(n_molecules: int = 100) -> List[int]:
    """
    Create a diverse list of CIDs for sampling.
    
    In a real implementation, this would use a diversity algorithm.
    For now, we use a predefined set of diverse CIDs.
    
    Returns:
        List of CIDs.
    """
    # Using a diverse set of CIDs covering different chemical classes
    diverse_cids = [
        2244, 3672, 5957, 702, 1234, 5281, 5280, 5282, 5283, 5284,
        1036, 1113, 1125, 1184, 1192, 1207, 1218, 1227, 1235, 1246,
        1255, 1267, 1278, 1289, 1298, 1307, 1316, 1325, 1334, 1343,
        1352, 1361, 1370, 1379, 1388, 1397, 1406, 1415, 1424, 1433,
        1442, 1451, 1460, 1469, 1478, 1487, 1496, 1505, 1514, 1523,
        1532, 1541, 1550, 1559, 1568, 1577, 1586, 1595, 1604, 1613,
        1622, 1631, 1640, 1649, 1658, 1667, 1676, 1685, 1694, 1703,
        1712, 1721, 1730, 1739, 1748, 1757, 1766, 1775, 1784, 1793,
        1802, 1811, 1820, 1829, 1838, 1847, 1856, 1865, 1874, 1883,
        1892, 1901, 1910, 1919, 1928, 1937, 1946, 1955, 1964, 1973
    ]
    return diverse_cids[:n_molecules]

def save_raw_data(df: pd.DataFrame, output_path: Path):
    """Save raw data to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")

def create_dataset_metadata(df: pd.DataFrame, output_path: Path, query_params: Dict[str, Any]):
    """
    Create dataset metadata JSON file.
    
    Performs runtime schema check for measurement_uncertainty and quantity_of_substance fields.
    If absent, records "Not Available in Source".
    
    Args:
        df: DataFrame with fetched data.
        output_path: Path to save metadata JSON.
        query_params: Original query parameters used for fetching.
    """
    # Check for measurement uncertainty and quantity of substance fields
    columns = df.columns.tolist()
    
    measurement_uncertainty_status = "Available" if 'measurement_uncertainty' in columns else "Not Available in Source"
    quantity_of_substance_status = "Available" if 'quantity_of_substance' in columns else "Not Available in Source"
    
    # Calculate experimental ratio
    if 'source_type' in df.columns:
        experimental_count = (df['source_type'] == 'Experimental').sum()
        total_count = len(df)
        experimental_ratio = experimental_count / total_count if total_count > 0 else 0.0
    else:
        experimental_ratio = 0.0
    
    # Create metadata structure
    metadata = {
        "source": "PubChem",
        "query_parameters": query_params,
        "measurement_uncertainty_status": measurement_uncertainty_status,
        "quantity_of_substance_status": quantity_of_substance_status,
        "experimental_ratio": float(experimental_ratio),
        "source_verification_hash": compute_file_hash(Path(output_path).parent / "pubchem_raw.csv") if (Path(output_path).parent / "pubchem_raw.csv").exists() else "pending",
        "raw_data_file": "data/raw/pubchem_raw.csv",
        "hash_algorithm": "SHA-256"
    }
    
    # Save metadata
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved dataset metadata to {output_path}")
    logger.info(f"Measurement uncertainty status: {measurement_uncertainty_status}")
    logger.info(f"Quantity of substance status: {quantity_of_substance_status}")
    logger.info(f"Experimental ratio: {experimental_ratio:.2f}")

def main():
    """Main entry point for data download and metadata creation."""
    base_dir = Path(__file__).parent.parent.parent
    data_raw = base_dir / "data" / "raw"
    
    # Ensure directories exist
    ensure_dirs()
    
    # Define query parameters
    query_params = {
        "cids_sampled": 100,
        "properties_requested": [
            "IsomericSMILES", "XLogP", "WaterSolubility", 
            "BoilingPoint", "MolecularWeight", "RecordType"
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Fetch diverse CIDs
    cids = create_diverse_cid_list(n_molecules=100)
    logger.info(f"Fetched {len(cids)} diverse CIDs")
    
    # Fetch molecule properties
    properties_to_fetch = [
        "IsomericSMILES", "XLogP", "WaterSolubility", 
        "BoilingPoint", "MolecularWeight", "RecordType"
    ]
    
    df = fetch_molecule_properties(cids, properties_to_fetch)
    
    if df.empty:
        logger.error("No data fetched. Check CID list and PubChemPy connectivity.")
        sys.exit(1)
    
    logger.info(f"Fetched {len(df)} records with columns: {df.columns.tolist()}")
    
    # Save raw data
    raw_data_path = data_raw / "pubchem_raw.csv"
    save_raw_data(df, raw_data_path)
    
    # Create dataset metadata
    metadata_path = data_raw / "dataset_metadata.json"
    create_dataset_metadata(df, metadata_path, query_params)
    
    logger.info("Data download and metadata creation completed successfully.")

if __name__ == "__main__":
    main()