"""
Fingerprint generation module for USPTO reaction data.

Generates ECFP4 (2048 bits) and MACCS (167 bits) fingerprints for reactants/reagents.
Implements chunked/streamed processing to prevent OOM errors on large datasets.
Logs fingerprint dimensions to data/results/fingerprint_dimensions.log.
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

# Project imports
from utils.io import load_parquet, save_parquet, get_file_size_mb
from utils.validators import validate_fingerprint_dimensions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/fingerprint_processing.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ECFP_RADIUS = 2
ECFP_BITS = 2048
MACCS_BITS = 167
CHUNK_SIZE = 5000  # Rows per chunk to prevent OOM

def generate_ecfp4(smiles: str, radius: int = ECFP_RADIUS, n_bits: int = ECFP_BITS) -> np.ndarray:
    """
    Generate ECFP4 fingerprint for a single SMILES string.
    
    Args:
        smiles: SMILES string of the molecule
        radius: Radius for Morgan fingerprint (2 for ECFP4)
        n_bits: Number of bits in the fingerprint (2048)
        
    Returns:
        numpy array of 2048 bits
        
    Raises:
        ValueError: If SMILES is invalid or cannot be parsed
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Generate Morgan fingerprint
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
    # Convert to numpy array
    arr = np.zeros((n_bits,), dtype=np.int8)
    for idx in fp.GetOnBits():
        arr[idx] = 1
        
    return arr

def generate_maccs(smiles: str) -> np.ndarray:
    """
    Generate MACCS keys fingerprint for a single SMILES string.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        numpy array of 167 bits (MACCS keys)
        
    Raises:
        ValueError: If SMILES is invalid or cannot be parsed
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Generate MACCS keys
    fp = MACCSkeys.GenMACCSKeys(mol)
    
    # Convert to numpy array
    arr = np.zeros((MACCS_BITS,), dtype=np.int8)
    for idx in fp.GetOnBits():
        arr[idx] = 1
        
    return arr

def generate_fingerprints_batch(
    df_chunk: pd.DataFrame,
    smiles_column: str = 'smiles',
    ecfp_bits: int = ECFP_BITS,
    maccs_bits: int = MACCS_BITS
) -> pd.DataFrame:
    """
    Generate fingerprints for a batch of molecules.
    
    Args:
        df_chunk: DataFrame containing SMILES strings
        smiles_column: Name of the column containing SMILES
        ecfp_bits: Expected ECFP bit length
        maccs_bits: Expected MACCS bit length
        
    Returns:
        DataFrame with added ECFP and MACCS fingerprint columns
        
    Raises:
        ValueError: If fingerprint dimensions don't match expected values
    """
    ecfp_list = []
    maccs_list = []
    valid_indices = []
    invalid_rows = []
    
    for idx, row in df_chunk.iterrows():
        try:
            smiles = row[smiles_column]
            if pd.isna(smiles) or not isinstance(smiles, str):
                invalid_rows.append((idx, "NaN or non-string SMILES"))
                continue
                
            ecfp_fp = generate_ecfp4(smiles, n_bits=ecfp_bits)
            maccs_fp = generate_maccs(smiles)
            
            # Validate dimensions
            if len(ecfp_fp) != ecfp_bits:
                raise ValueError(f"ECFP dimension mismatch: {len(ecfp_fp)} != {ecfp_bits}")
            if len(maccs_fp) != maccs_bits:
                raise ValueError(f"MACCS dimension mismatch: {len(maccs_fp)} != {maccs_bits}")
            
            ecfp_list.append(ecfp_fp)
            maccs_list.append(maccs_fp)
            valid_indices.append(idx)
            
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {str(e)}")
            invalid_rows.append((idx, str(e)))
    
    # Log invalid rows
    if invalid_rows:
        logger.warning(f"Failed to process {len(invalid_rows)} rows")
        for idx, reason in invalid_rows[:10]:  # Log first 10
            logger.warning(f"  Row {idx}: {reason}")
        if len(invalid_rows) > 10:
            logger.warning(f"  ... and {len(invalid_rows) - 10} more")
    
    # Add fingerprint columns to DataFrame
    result_df = df_chunk.copy()
    result_df['fingerprint_ecfp'] = [fp.tolist() for fp in ecfp_list]
    result_df['fingerprint_maccs'] = [fp.tolist() for fp in maccs_list]
    
    # Store valid indices for filtering
    result_df['_valid_fp'] = False
    result_df.loc[valid_indices, '_valid_fp'] = True
    
    return result_df, len(invalid_rows)

def process_fingerprints_chunked(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    smiles_column: str = 'smiles',
    chunk_size: int = CHUNK_SIZE,
    log_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Process fingerprints in chunks to prevent OOM.
    
    Args:
        input_path: Path to input Parquet file
        output_path: Path to output Parquet file
        smiles_column: Name of SMILES column
        chunk_size: Number of rows per chunk
        log_path: Path to log file for fingerprint dimensions
        
    Returns:
        Dictionary containing processing statistics
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    log_path = Path(log_path) if log_path else Path('data/results/fingerprint_dimensions.log')
    
    # Ensure output directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting chunked fingerprint generation")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Chunk size: {chunk_size}")
    
    # Verify input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    file_size_mb = get_file_size_mb(input_path)
    logger.info(f"Input file size: {file_size_mb:.2f} MB")
    
    total_rows = 0
    total_processed = 0
    total_invalid = 0
    ecfp_dims = []
    maccs_dims = []
    
    # Initialize output file
    first_chunk = True
    
    # Process in chunks
    for chunk_idx, chunk_df in enumerate(load_parquet(input_path, chunk_size=chunk_size)):
        logger.info(f"Processing chunk {chunk_idx + 1} ({len(chunk_df)} rows)")
        
        # Generate fingerprints for this chunk
        processed_df, invalid_count = generate_fingerprints_batch(
            chunk_df,
            smiles_column=smiles_column,
            ecfp_bits=ECFP_BITS,
            maccs_bits=MACCS_BITS
        )
        
        # Track statistics
        valid_count = len(processed_df[processed_df['_valid_fp']])
        total_rows += len(chunk_df)
        total_processed += valid_count
        total_invalid += invalid_count
        
        # Collect dimension info for validation
        if valid_count > 0:
            sample_ecfp = processed_df.loc[processed_df['_valid_fp'].iloc[0], 'fingerprint_ecfp']
            sample_maccs = processed_df.loc[processed_df['_valid_fp'].iloc[0], 'fingerprint_maccs']
            ecfp_dims.append(len(sample_ecfp))
            maccs_dims.append(len(sample_maccs))
        
        # Write chunk to output
        # Drop the temporary validation column
        output_chunk = processed_df.drop(columns=['_valid_fp'])
        
        if first_chunk:
            output_chunk.to_parquet(output_path, index=False)
            first_chunk = False
        else:
            # Append to existing file (requires re-reading or using pyarrow directly)
            # For simplicity, we'll re-save the accumulated data
            existing_df = load_parquet(output_path)
            combined_df = pd.concat([existing_df, output_chunk], ignore_index=True)
            combined_df.to_parquet(output_path, index=False)
        
        logger.info(f"Chunk {chunk_idx + 1} complete: {valid_count} valid, {invalid_count} invalid")
    
    # Calculate statistics
    exclusion_fraction = total_invalid / total_rows if total_rows > 0 else 0.0
    
    # Validate dimensions
    if ecfp_dims:
        unique_ecfp = set(ecfp_dims)
        unique_maccs = set(maccs_dims)
        
        if len(unique_ecfp) != 1 or unique_ecfp.pop() != ECFP_BITS:
            raise ValueError(f"ECFP dimension inconsistency detected: {unique_ecfp}")
        if len(unique_maccs) != 1 or unique_maccs.pop() != MACCS_BITS:
            raise ValueError(f"MACCS dimension inconsistency detected: {unique_maccs}")
    
    # Write fingerprint dimensions log
    dimensions_log = {
        "ecfp_bits": ECFP_BITS,
        "maccs_bits": MACCS_BITS,
        "total_rows": total_rows,
        "valid_rows": total_processed,
        "invalid_rows": total_invalid,
        "exclusion_fraction": exclusion_fraction,
        "ecfp_dimension_verified": ECFP_BITS,
        "maccs_dimension_verified": MACCS_BITS,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(log_path, 'w') as f:
        json.dump(dimensions_log, f, indent=2)
    
    logger.info(f"Fingerprint dimensions logged to: {log_path}")
    logger.info(f"Total rows: {total_rows}, Valid: {total_processed}, Invalid: {total_invalid}")
    logger.info(f"Exclusion fraction: {exclusion_fraction:.4f}")
    
    return dimensions_log

def main():
    """
    Main entry point for fingerprint generation.
    
    Reads from data/processed/parsed_reactions.parquet (or specified input)
    and writes to data/processed/fingerprinted_reactions.parquet.
    """
    # Default paths
    input_path = Path('data/processed/parsed_reactions.parquet')
    output_path = Path('data/processed/fingerprinted_reactions.parquet')
    log_path = Path('data/results/fingerprint_dimensions.log')
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        log_path = Path(sys.argv[3])
    
    try:
        logger.info("Starting fingerprint generation pipeline")
        
        # Process fingerprints in chunks
        stats = process_fingerprints_chunked(
            input_path=input_path,
            output_path=output_path,
            smiles_column='smiles',
            chunk_size=CHUNK_SIZE,
            log_path=log_path
        )
        
        logger.info("Fingerprint generation completed successfully")
        logger.info(f"Output written to: {output_path}")
        logger.info(f"Dimensions log written to: {log_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fingerprint generation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())