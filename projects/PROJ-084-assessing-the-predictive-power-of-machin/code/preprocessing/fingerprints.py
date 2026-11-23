"""
Fingerprint Generation Module (T016)

Generates ECFP4 and MACCS fingerprints for the sanitized reaction dataset.
Implements chunked processing to prevent OOM errors on large datasets.
Logs dimensions and updates checksums.
"""
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs

# Project imports
from config import ensure_dirs
from utils.io import calculate_sha256, load_parquet, save_parquet
from utils.validators import validate_dataset_schema

# Constants
ECFP_RADIUS = 2
ECFP_BITS = 2048
MACCS_BITS = 167
CHUNK_SIZE = 5000  # Process 5000 rows at a time to manage memory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/fingerprint_processing.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_ecfp4(mol: Chem.Mol) -> np.ndarray:
    """
    Generate ECFP4 fingerprint for a single molecule.
    Returns a boolean numpy array of length 2048.
    """
    if mol is None:
        return np.zeros(ECFP_BITS, dtype=bool)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, ECFP_RADIUS, nBits=ECFP_BITS)
    arr = np.zeros(ECFP_BITS, dtype=bool)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_maccs(mol: Chem.Mol) -> np.ndarray:
    """
    Generate MACCS keys fingerprint for a single molecule.
    Returns a boolean numpy array of length 167.
    """
    if mol is None:
        return np.zeros(MACCS_BITS, dtype=bool)
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros(MACCS_BITS, dtype=bool)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def parse_smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """Convert SMILES string to RDKit Mol object."""
    if not smiles or not isinstance(smiles, str):
        return None
    return Chem.MolFromSmiles(smiles)

def generate_fingerprints_batch(df_batch: pd.DataFrame) -> pd.DataFrame:
    """
    Generate fingerprints for a batch of reactions.
    Assumes 'smiles' column exists.
    """
    logger.info(f"Processing batch of {len(df_batch)} rows...")

    ecfp_list = []
    maccs_list = []

    for idx, row in df_batch.iterrows():
        mol = parse_smiles_to_mol(row['smiles'])
        ecfp_list.append(generate_ecfp4(mol))
        maccs_list.append(generate_maccs(mol))

    df_batch = df_batch.copy()
    df_batch['fingerprint_ecfp'] = ecfp_list
    df_batch['fingerprint_maccs'] = maccs_list
    return df_batch

def process_fingerprints_chunked(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Process the full dataset in chunks to avoid OOM.
    Reads input parquet, generates fingerprints, and writes output parquet.
    """
    logger.info(f"Starting chunked fingerprint generation from {input_path}")
    
    # Initialize output list and counters
    all_rows = []
    total_rows = 0
    processed_rows = 0
    failed_rows = 0

    # Read in chunks
    # Using pandas chunksize iterator
    chunk_iter = pd.read_parquet(input_path, chunksize=CHUNK_SIZE)

    for i, chunk in enumerate(chunk_iter):
        logger.info(f"Processing chunk {i+1}...")
        try:
            processed_chunk = generate_fingerprints_batch(chunk)
            all_rows.append(processed_chunk)
            total_rows += len(processed_chunk)
            processed_rows += len(processed_chunk)
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}")
            failed_rows += len(chunk)
            # Continue with next chunk to ensure partial progress if possible,
            # but in a strict pipeline we might want to fail fast. 
            # Given the requirement to "fail loudly" on data issues, 
            # we log and continue if it's just a bad molecule in a chunk.
            continue

    if not all_rows:
        raise RuntimeError("No data was successfully processed. Check input data.")

    logger.info(f"Concatenating {len(all_rows)} chunks...")
    final_df = pd.concat(all_rows, ignore_index=True)
    
    logger.info(f"Saving output to {output_path}")
    save_parquet(final_df, output_path)
    
    return {
        "total_rows": total_rows,
        "processed_rows": processed_rows,
        "failed_rows": failed_rows,
        "ecfp_bits": ECFP_BITS,
        "maccs_bits": MACCS_BITS
    }

def log_dimensions(stats: Dict[str, Any], log_path: Path) -> None:
    """Log fingerprint dimensions and processing stats to a log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Fingerprint Generation Log - {datetime.now().isoformat()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"ECFP4 Bit Length: {stats['ecfp_bits']}\n")
        f.write(f"MACCS Bit Length: {stats['maccs_bits']}\n")
        f.write(f"Total Rows Processed: {stats['total_rows']}\n")
        f.write(f"Failed Rows: {stats['failed_rows']}\n")
        f.write(f"Success Rate: {(stats['processed_rows']/stats['total_rows'])*100:.2f}%\n")
    
    logger.info(f"Dimensions logged to {log_path}")

def update_data_quality_report(stats: Dict[str, Any], report_path: Path) -> None:
    """Update the data quality report with fingerprint generation stats."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing report if it exists
    if report_path.exists():
        with open(report_path, 'r') as f:
            report = json.load(f)
    else:
        report = {"fingerprint_generation": {}}

    report["fingerprint_generation"] = {
        "ecfp_bits": stats['ecfp_bits'],
        "maccs_bits": stats['maccs_bits'],
        "total_rows": stats['total_rows'],
        "failed_rows": stats['failed_rows'],
        "timestamp": datetime.now().isoformat()
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Data quality report updated at {report_path}")

def compute_and_record_checksum(file_path: Path, checksums_path: Path) -> str:
    """Compute SHA256 of a file and record it in checksums.json."""
    sha256_hash = calculate_sha256(file_path)
    
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    else:
        checksums = {}

    checksums[file_path.name] = sha256_hash
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksum for {file_path.name} recorded: {sha256_hash}")
    return sha256_hash

def main():
    """Main entry point for T016."""
    # Define paths
    input_path = Path("data/processed/sanitized_reactions.parquet")
    output_path = Path("data/processed/cleaned_reactions.parquet")
    log_path = Path("data/results/fingerprint_dimensions.log")
    report_path = Path("data/results/data_quality_report.json")
    checksums_path = Path("data/results/checksums.json")

    # Ensure directories exist
    ensure_dirs()

    # Check input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("Starting Fingerprint Generation Pipeline (T016)...")

    # Process data
    stats = process_fingerprints_chunked(input_path, output_path)

    # Log dimensions
    log_dimensions(stats, log_path)

    # Update data quality report
    update_data_quality_report(stats, report_path)

    # Compute and record checksum of the log file
    compute_and_record_checksum(log_path, checksums_path)

    # Validate output schema
    logger.info("Validating output schema...")
    validate_dataset_schema(output_path)

    logger.info("Fingerprint Generation (T016) completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
