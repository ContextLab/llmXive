"""
Fingerprint generation module for crystal structure prediction.

This module handles the conversion of molecular SMILES to ECFP4 fingerprints
using batch processing to optimize memory usage.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator, Iterator

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit import DataStructs

# Import project utilities
from config import get_path_processed_data, get_path_results, get_config_dict, ensure_directory
from logging_config import get_logger, log_event

# Constants
DEFAULT_FP_SIZE = 2048
DEFAULT_RADIUS = 2
DEFAULT_BATCH_SIZE = 1000
DEFAULT_MIN_MW = 50.0
DEFAULT_MAX_MW = 1000.0

logger = get_logger(__name__)


class FingerprintError(Exception):
    """Custom exception for fingerprint generation errors."""
    pass


def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """Convert SMILES string to RDKit Mol object."""
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Sanitize the molecule
        Chem.SanitizeMol(mol)
        return mol
    except Exception as e:
        logger.warning(f"Failed to parse SMILES '{smiles}': {e}")
        return None


def generate_ecfp4(mol: Chem.Mol, fp_size: int = DEFAULT_FP_SIZE, radius: int = DEFAULT_RADIUS) -> np.ndarray:
    """
    Generate ECFP4 fingerprint for a molecule.

    Args:
        mol: RDKit Mol object
        fp_size: Size of the fingerprint (number of bits)
        radius: Radius of the fingerprint (ECFP4 uses radius=2)

    Returns:
        Numpy array of bits (0 or 1)
    """
    try:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=fp_size)
        arr = np.zeros((fp_size,), dtype=int)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.warning(f"Failed to generate ECFP4 fingerprint: {e}")
        return None


def get_molecular_weight(mol: Chem.Mol) -> Optional[float]:
    """Calculate molecular weight of a molecule."""
    try:
        return rdMolDescriptors.CalcExactMolWt(mol)
    except Exception as e:
        logger.warning(f"Failed to calculate molecular weight: {e}")
        return None


def process_molecule_for_fingerprint(smiles: str, fp_size: int = DEFAULT_FP_SIZE) -> Optional[Tuple[str, np.ndarray, float]]:
    """
    Process a single molecule: parse SMILES, validate, and generate fingerprint.

    Args:
        smiles: SMILES string
        fp_size: Fingerprint size

    Returns:
        Tuple of (smiles, fingerprint_array, molecular_weight) or None if invalid
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        return None

    mw = get_molecular_weight(mol)
    if mw is None or mw < DEFAULT_MIN_MW or mw > DEFAULT_MAX_MW:
        return None

    fp = generate_ecfp4(mol, fp_size=fp_size)
    if fp is None:
        return None

    return (smiles, fp, mw)


def stream_dataset_rows(input_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Stream rows from a CSV/Parquet dataset file.

    Args:
        input_path: Path to the input file

    Yields:
        Dictionary containing row data
    """
    import pandas as pd

    # Check file extension
    suffix = input_path.suffix.lower()

    if suffix == '.csv':
        df = pd.read_csv(input_path, chunksize=DEFAULT_BATCH_SIZE)
        for chunk in df:
            for _, row in chunk.iterrows():
                yield row.to_dict()
    elif suffix == '.parquet':
        df = pd.read_parquet(input_path)
        for _, row in df.iterrows():
            yield row.to_dict()
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def generate_fingerprints_streaming(
    input_path: Path,
    output_path: Path,
    fp_size: int = DEFAULT_FP_SIZE,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict[str, int]:
    """
    Generate fingerprints for a dataset using batch processing to optimize memory.

    This function processes the input dataset in batches, generating fingerprints
    for each molecule and writing the results to the output file.

    Args:
        input_path: Path to input dataset (CSV or Parquet)
        output_path: Path to output dataset with fingerprints
        fp_size: Size of the fingerprint
        batch_size: Number of rows to process in each batch

    Returns:
        Dictionary with processing statistics
    """
    import pandas as pd

    stats = {
        'total_rows': 0,
        'processed_rows': 0,
        'skipped_rows': 0,
        'failed_rows': 0,
        'batches_processed': 0
    }

    ensure_directory(output_path.parent)

    # Read all rows into a list first to avoid chunking issues with iterrows
    # but we'll process them in batches
    input_suffix = input_path.suffix.lower()
    if input_suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_suffix}")

    stats['total_rows'] = len(df)
    logger.info(f"Starting fingerprint generation for {stats['total_rows']} rows in batches of {batch_size}")

    # Prepare output lists
    output_records = []
    failed_smiles = []

    # Process in batches
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batch_results = []

        for idx, row in batch_df.iterrows():
            smiles = row.get('smiles') or row.get('SMILES')
            if not smiles:
                stats['skipped_rows'] += 1
                continue

            result = process_molecule_for_fingerprint(str(smiles), fp_size=fp_size)
            if result is None:
                stats['skipped_rows'] += 1
                failed_smiles.append(smiles)
                continue

            smiles_out, fp, mw = result
            batch_results.append({
                'smiles': smiles_out,
                'molecular_weight': mw,
                'fingerprint': fp.tolist()
            })
            stats['processed_rows'] += 1

        # Append batch results
        output_records.extend(batch_results)
        stats['batches_processed'] += 1

        # Log progress
        if stats['batches_processed'] % 10 == 0:
            logger.info(f"Processed {stats['batches_processed'] * batch_size} / {stats['total_rows']} rows")

    # Write output
    if output_records:
        # Convert fingerprints to separate columns for CSV/Parquet compatibility
        # or store as JSON strings if the format supports it
        output_df = pd.DataFrame(output_records)

        # Expand fingerprint array into separate columns if needed
        # For Parquet, we can store lists directly
        if output_suffix == '.parquet':
            output_df.to_parquet(output_path, index=False)
        else:
            # For CSV, convert fingerprint list to string representation
            output_df['fingerprint'] = output_df['fingerprint'].apply(lambda x: json.dumps(x))
            output_df.to_csv(output_path, index=False)

        logger.info(f"Wrote {len(output_records)} records to {output_path}")
    else:
        logger.warning("No valid records to write")

    # Log exclusion details
    exclusion_log_path = get_path_results() / 'exclusion_log.json'
    ensure_directory(exclusion_log_path.parent)
    with open(exclusion_log_path, 'w') as f:
        json.dump({
            'stats': stats,
            'failed_smiles_sample': failed_smiles[:100]  # Limit to first 100
        }, f, indent=2)

    logger.info(f"Fingerprint generation complete. Stats: {stats}")
    return stats


def generate_fingerprints_for_dataset(
    input_path: Path,
    output_path: Path,
    fp_size: int = DEFAULT_FP_SIZE,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict[str, int]:
    """
    Wrapper for generate_fingerprints_streaming to maintain backward compatibility.

    Args:
        input_path: Path to input dataset
        output_path: Path to output dataset
        fp_size: Fingerprint size
        batch_size: Batch size for processing

    Returns:
        Processing statistics
    """
    return generate_fingerprints_streaming(input_path, output_path, fp_size, batch_size)


def save_fingerprints_to_csv(
    fingerprints: List[np.ndarray],
    smiles_list: List[str],
    output_path: Path
) -> None:
    """
    Save fingerprints and SMILES to a CSV file.

    Args:
        fingerprints: List of fingerprint arrays
        smiles_list: List of SMILES strings
        output_path: Path to output file
    """
    import pandas as pd

    ensure_directory(output_path.parent)

    records = []
    for smiles, fp in zip(smiles_list, fingerprints):
        records.append({
            'smiles': smiles,
            'fingerprint': fp.tolist()
        })

    df = pd.DataFrame(records)
    df['fingerprint'] = df['fingerprint'].apply(lambda x: json.dumps(x))
    df.to_csv(output_path, index=False)

    logger.info(f"Saved {len(records)} fingerprints to {output_path}")


def main():
    """Main entry point for fingerprint generation script."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate ECFP4 fingerprints for molecular dataset')
    parser.add_argument('--input', type=str, required=True, help='Input dataset path (CSV or Parquet)')
    parser.add_argument('--output', type=str, required=True, help='Output dataset path')
    parser.add_argument('--fp_size', type=int, default=DEFAULT_FP_SIZE, help='Fingerprint size')
    parser.add_argument('--batch_size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for processing')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    stats = generate_fingerprints_streaming(
        input_path,
        output_path,
        fp_size=args.fp_size,
        batch_size=args.batch_size
    )

    # Print summary
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()