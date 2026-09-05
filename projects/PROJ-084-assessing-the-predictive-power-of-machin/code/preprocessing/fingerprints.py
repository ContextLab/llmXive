"""
Preprocessing module for generating molecular fingerprints (ECFP4 and MACCS).

Implements chunked/streamed processing to handle large datasets within memory constraints.
Generates ECFP4 (2048 bits) and MACCS (167 bits) fingerprints for all reactions.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union, Iterator, Dict, Any

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import RDLogger

# Silence RDKit warnings during processing
RDLogger.DisableLog('rdApp.*')

from utils.io import load_parquet, save_parquet, check_memory_limit
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
ECFP_SIZE = 2048
MACCS_SIZE = 167
CHUNK_SIZE = 5000  # Rows per chunk for memory management
MEMORY_LIMIT_GB = 6.5  # Leave headroom below 7GB limit

def generate_ecfp4(mol: Chem.Mol, radius: int = ECFP_RADIUS, nBits: int = ECFP_SIZE) -> List[int]:
    """
    Generate ECFP4 fingerprint for a molecule.

    Args:
        mol: RDKit Mol object
        radius: Radius for Morgan fingerprint (2 for ECFP4)
        nBits: Number of bits in the fingerprint

    Returns:
        List of integers (0 or 1) representing the fingerprint
    """
    if mol is None:
        return [0] * nBits

    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nBits)
    arr = np.zeros((nBits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr.tolist()

def generate_maccs(mol: Chem.Mol) -> List[int]:
    """
    Generate MACCS keys fingerprint for a molecule.

    Args:
        mol: RDKit Mol object

    Returns:
        List of integers (0 or 1) representing the MACCS keys
    """
    if mol is None:
        return [0] * MACCS_SIZE

    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros((MACCS_SIZE,), dtype=int)
    fp.CopyTo(arr)
    return arr.tolist()

def generate_fingerprints_batch(
    smiles_list: List[str],
    chunk_size: int = CHUNK_SIZE
) -> Tuple[List[List[int]], List[List[int]], List[int]]:
    """
    Generate fingerprints for a batch of SMILES strings.

    Args:
        smiles_list: List of SMILES strings
        chunk_size: Number of molecules to process in one batch

    Returns:
        Tuple of (ecfp_fingerprints, maccs_fingerprints, valid_indices)
    """
    ecfp_fps = []
    maccs_fps = []
    valid_indices = []

    for i, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                # Log invalid SMILES but continue
                continue

            ecfp_fp = generate_ecfp4(mol)
            maccs_fp = generate_maccs(mol)

            ecfp_fps.append(ecfp_fp)
            maccs_fps.append(maccs_fp)
            valid_indices.append(i)

        except Exception as e:
            logger.warning(f"Failed to process SMILES at index {i}: {e}")
            continue

        # Periodic memory check
        if (i + 1) % 1000 == 0:
            check_memory_limit(MEMORY_LIMIT_GB)

    return ecfp_fps, maccs_fps, valid_indices

def process_fingerprints_chunked(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    chunk_size: int = CHUNK_SIZE
) -> Dict[str, Any]:
    """
    Process fingerprints in chunks to prevent OOM errors.

    Args:
        input_path: Path to input Parquet file with sanitized data
        output_path: Path to output Parquet file
        chunk_size: Number of rows to process per chunk

    Returns:
        Dictionary with processing statistics
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    results_path = Path('data/results')
    results_path.mkdir(parents=True, exist_ok=True)

    stats = {
        'total_rows': 0,
        'processed_rows': 0,
        'invalid_rows': 0,
        'start_time': datetime.now().isoformat(),
        'fingerprint_dimensions': {
            'ecfp4': ECFP_SIZE,
            'maccs': MACCS_SIZE
        }
    }

    # Log fingerprint dimensions
    log_path = results_path / 'fingerprint_dimensions.log'
    with open(log_path, 'w') as f:
        f.write(f"Fingerprint Dimensions Log - {datetime.now().isoformat()}\n")
        f.write(f"ECFP4: {ECFP_SIZE} bits\n")
        f.write(f"MACCS: {MACCS_SIZE} bits\n")
        f.write(f"Processing started: {stats['start_time']}\n")

    logger.info(f"Starting fingerprint generation from {input_path}")

    # Load data in chunks
    try:
        df = load_parquet(input_path)
        stats['total_rows'] = len(df)
        logger.info(f"Loaded {stats['total_rows']} rows")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise

    # Process in chunks
    all_ecfp = []
    all_maccs = []
    all_smiles = []
    all_yields = []
    all_reaction_classes = []

    for start_idx in range(0, len(df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(df))
        chunk_df = df.iloc[start_idx:end_idx]

        logger.info(f"Processing chunk {start_idx}-{end_idx}")

        # Generate fingerprints for this chunk
        ecfp_fps, maccs_fps, valid_indices = generate_fingerprints_batch(
            chunk_df['smiles'].tolist()
        )

        # Track statistics
        stats['processed_rows'] += len(valid_indices)
        stats['invalid_rows'] += (len(chunk_df) - len(valid_indices))

        # Collect results
        for i, idx in enumerate(valid_indices):
            all_ecfp.append(ecfp_fps[i])
            all_maccs.append(maccs_fps[i])
            all_smiles.append(chunk_df.iloc[idx]['smiles'])
            all_yields.append(chunk_df.iloc[idx]['yield'])
            all_reaction_classes.append(chunk_df.iloc[idx].get('reaction_class', 'unknown'))

        # Force garbage collection periodically
        if (start_idx + chunk_size) % (chunk_size * 5) == 0:
            import gc
            gc.collect()
            check_memory_limit(MEMORY_LIMIT_GB)

    # Create output dataframe
    output_df = pd.DataFrame({
        'smiles': all_smiles,
        'yield': all_yields,
        'reaction_class': all_reaction_classes,
        'fingerprint_ecfp': all_ecfp,
        'fingerprint_maccs': all_maccs
    })

    # Validate fingerprint dimensions
    logger.info("Validating fingerprint dimensions...")
    ecfp_lengths = [len(fp) for fp in all_ecfp]
    maccs_lengths = [len(fp) for fp in all_maccs]

    if not all(l == ECFP_SIZE for l in ecfp_lengths):
        raise ValueError(f"ECFP4 fingerprint length mismatch: expected {ECFP_SIZE}, got {set(ecfp_lengths)}")
    if not all(l == MACCS_SIZE for l in maccs_lengths):
        raise ValueError(f"MACCS fingerprint length mismatch: expected {MACCS_SIZE}, got {set(maccs_lengths)}")

    # Append validation results to log
    with open(log_path, 'a') as f:
        f.write(f"Validation passed: ECFP4={ecfp_lengths[0]}, MACCS={maccs_lengths[0]}\n")
        f.write(f"Processed rows: {stats['processed_rows']}\n")
        f.write(f"Invalid rows: {stats['invalid_rows']}\n")

    # Save output
    logger.info(f"Saving processed data to {output_path}")
    save_parquet(output_df, output_path)

    stats['end_time'] = datetime.now().isoformat()
    logger.info(f"Processing complete. Output saved to {output_path}")

    return stats

def main():
    """Main entry point for fingerprint generation."""
    logger.info("Starting fingerprint generation pipeline")

    input_path = Path('data/processed/sanitized_reactions.parquet')
    output_path = Path('data/processed/fingerprinted_reactions.parquet')

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run sanitize.py first to create sanitized_reactions.parquet")
        sys.exit(1)

    try:
        stats = process_fingerprints_chunked(input_path, output_path)

        # Log final statistics
        logger.info(f"Final Statistics:")
        logger.info(f"  Total rows: {stats['total_rows']}")
        logger.info(f"  Processed rows: {stats['processed_rows']}")
        logger.info(f"  Invalid rows: {stats['invalid_rows']}")
        logger.info(f"  ECFP4 dimensions: {stats['fingerprint_dimensions']['ecfp4']}")
        logger.info(f"  MACCS dimensions: {stats['fingerprint_dimensions']['maccs']}")

        # Write dimensions log
        log_path = Path('data/results/fingerprint_dimensions.log')
        with open(log_path, 'a') as f:
            f.write(f"\nProcessing completed: {stats['end_time']}\n")
            f.write(f"Total rows: {stats['total_rows']}\n")
            f.write(f"Processed rows: {stats['processed_rows']}\n")
            f.write(f"Invalid rows: {stats['invalid_rows']}\n")

        logger.info("Fingerprint generation completed successfully")

    except Exception as e:
        logger.error(f"Error during fingerprint generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
