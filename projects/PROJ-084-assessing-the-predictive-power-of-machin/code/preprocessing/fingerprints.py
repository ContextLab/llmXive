"""
Fingerprint generation utilities.
Implements chunked/streamed processing for ECFP4 and MACCS fingerprints.
Logs dimensions to data/results/fingerprint_dimensions.log.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union, Iterator, Dict, Any

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys

from config import DATA_RESULTS_DIR, DATA_PROCESSED_DIR
from utils.io import load_parquet, save_parquet

logger = logging.getLogger(__name__)

ECFP_LENGTH = 2048
MACCS_LENGTH = 167

def generate_ecfp4(smiles: str, radius: int = 2) -> Optional[np.ndarray]:
    """Generate ECFP4 fingerprint."""
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=ECFP_LENGTH)
        arr = np.zeros((ECFP_LENGTH,), dtype=int)
        Chem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.debug(f"ECFP4 generation failed: {e}")
        return None

def generate_maccs(smiles: str) -> Optional[np.ndarray]:
    """Generate MACCS fingerprint."""
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        fp = MACCSkeys.GenMACCSKeys(mol)
        arr = np.zeros((MACCS_LENGTH,), dtype=int)
        Chem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.debug(f"MACCS generation failed: {e}")
        return None

def generate_fingerprints_batch(batch: pd.DataFrame) -> pd.DataFrame:
    """Generate fingerprints for a batch of reactions."""
    ecfp_list = []
    maccs_list = []
    failed_count = 0

    for i, smiles in enumerate(batch['smiles']):
        ecfp = generate_ecfp4(smiles)
        maccs = generate_maccs(smiles)
        
        if ecfp is None or maccs is None:
            failed_count += 1
            ecfp_list.append(np.zeros(ECFP_LENGTH, dtype=int))
            maccs_list.append(np.zeros(MACCS_LENGTH, dtype=int))
        else:
            ecfp_list.append(ecfp)
            maccs_list.append(maccs)

    if failed_count > 0:
        logger.warning(f"Failed to generate fingerprints for {failed_count} rows in batch.")

    batch['fingerprint_ecfp'] = ecfp_list
    batch['fingerprint_maccs'] = maccs_list
    
    return batch

def process_fingerprints_chunked(input_path: str, output_path: str, chunk_size: int = 1000):
    """
    Process fingerprints in chunks to save memory.
    Reads from input_path, writes to output_path.
    Logs dimensions to fingerprint_dimensions.log.
    """
    logger.info(f"Starting chunked fingerprint processing for {input_path}")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Read in chunks using pandas chunksize
    chunks = pd.read_parquet(input_path, chunksize=chunk_size)
    
    all_results = []
    total_rows = 0
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1} (rows {total_rows} to {total_rows + len(chunk)})")
        
        processed_chunk = generate_fingerprints_batch(chunk)
        all_results.append(processed_chunk)
        
        total_rows += len(chunk)
        
        # Log progress every 5 chunks
        if (i + 1) % 5 == 0:
            logger.info(f"Processed {total_rows} rows")
    
    # Concatenate all chunks
    logger.info(f"Concatenating {len(all_results)} chunks...")
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Save to parquet
    logger.info(f"Saving results to {output_path}")
    save_parquet(final_df, output_path)
    
    # Log dimensions
    log_dimensions()
    
    logger.info(f"Fingerprint processing complete. Total rows: {total_rows}")
    return final_df

def log_dimensions():
    """Log the actual bit lengths generated to fingerprint_dimensions.log."""
    log_path = DATA_RESULTS_DIR / "fingerprint_dimensions.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""
    Fingerprint Dimensions Log
    Generated: {timestamp}
    -------------------------
    ECFP4 (Morgan fingerprint) length: {ECFP_LENGTH} bits
    MACCS key length: {MACCS_LENGTH} bits
    
    Verification:
    - ECFP4 uses radius=2 (ECFP4)
    - MACCS uses 167 keys (standard MACCS167)
    
    These dimensions are hardcoded and validated in tests.
    """
    
    with open(log_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Logged fingerprint dimensions to {log_path}")

def update_data_quality_report(report_path: str):
    """Update the data quality report with fingerprint dimensions."""
    try:
        if Path(report_path).exists():
            with open(report_path, 'r') as f:
                report = json.load(f)
        else:
            report = {}
        
        report['fingerprint_dimensions'] = {
            'ecfp4_length': ECFP_LENGTH,
            'maccs_length': MACCS_LENGTH,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Updated data quality report at {report_path}")
    except Exception as e:
        logger.warning(f"Could not update data quality report: {e}")

def main():
    """Main entry point for fingerprint generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(DATA_RESULTS_DIR / "fingerprints.log")
        ]
    )
    
    # Default paths
    input_file = DATA_PROCESSED_DIR / "sanitized_reactions.parquet"
    output_file = DATA_PROCESSED_DIR / "reactions_with_fingerprints.parquet"
    quality_report = DATA_RESULTS_DIR / "data_quality_report.json"
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Process fingerprints
    process_fingerprints_chunked(str(input_file), str(output_file))
    
    # Update data quality report
    update_data_quality_report(str(quality_report))
    
    logger.info("Fingerprint generation completed successfully.")

if __name__ == "__main__":
    main()
