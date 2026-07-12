import signal
import zlib
import time
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, Tuple, List
import pandas as pd
import numpy as np

from rdkit import Chem
from rdkit.Chem import Descriptors, QED
from rdkit.Chem.SA_Score import sascorer

from config import get_project_root, get_metrics_path, SAMPLE_SIZE
from logging_setup import get_logger, log_skipped_molecule, log_timeout_event

# Configure logger
logger = get_logger(__name__)

# Custom Timeout Error class for clarity
class TimeoutError(Exception):
    pass

def timeout(seconds: float):
    """
    Decorator to enforce a timeout on a function using SIGALRM.
    Raises custom TimeoutError if the function takes too long.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the alarm
            old_handler = signal.signal(signal.SIGALRM, lambda signum, frame: exec("raise TimeoutError('Function timed out')"))
            try:
                signal.alarm(int(seconds) + 1) # Add 1s buffer for integer conversion
                result = func(*args, **kwargs)
                return result
            except TimeoutError as e:
                logger.warning(f"Timeout occurred in {func.__name__}: {e}")
                raise
            finally:
                # Cancel the alarm and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

@timeout(30)
def compute_shannon_entropy(mol: Chem.Mol) -> float:
    """
    Compute Shannon entropy based on vertex degree distribution.
    """
    if mol is None:
        return np.nan

    degrees = []
    for atom in mol.GetAtoms():
        degrees.append(atom.GetDegree())

    if not degrees:
        return 0.0

    counts = np.bincount(degrees)
    probs = counts[counts > 0] / len(degrees)
    entropy = -np.sum(probs * np.log2(probs))
    return float(entropy)

@timeout(30)
def compute_lz_complexity(smiles: str) -> float:
    """
    Compute Lempel-Ziv complexity on the canonical SMILES string.
    """
    if not smiles or not isinstance(smiles, str):
        return np.nan

    try:
        data = smiles.encode('utf-8')
        # Compress and get the compressed size
        compressed = zlib.compress(data, level=9)
        # Normalized complexity: compressed size / original size
        # This is a proxy for complexity; higher ratio = less compressible = more complex
        original_size = len(data)
        if original_size == 0:
            return 0.0
        return float(len(compressed) / original_size)
    except Exception as e:
        logger.error(f"LZ compression failed for SMILES: {e}")
        return np.nan

@timeout(30)
def compute_sa_qed(mol: Chem.Mol) -> Tuple[float, float]:
    """
    Compute Synthetic Accessibility (SA) and Quantitative Estimate of Drug-likeness (QED).
    Returns (SA, QED).
    """
    if mol is None:
        return (np.nan, np.nan)

    try:
        sa_score = sascorer.calculateScore(mol)
        qed_score = QED.qed(mol)
        return (float(sa_score), float(qed_score))
    except Exception as e:
        logger.error(f"SA/QED calculation failed: {e}")
        return (np.nan, np.nan)

def process_chunk(df_chunk: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process a chunk of the dataframe, computing metrics for each row.
    Handles timeouts and invalid molecules gracefully.
    """
    results = []
    
    for idx, row in df_chunk.iterrows():
        smiles = row['canonical_smiles']
        cid = row['cid']
        
        # Parse molecule
        mol = Chem.MolFromSmiles(smiles)
        
        row_data = {
            'cid': cid,
            'smiles': smiles,
            'entropy': np.nan,
            'lz_complexity': np.nan,
            'sa_score': np.nan,
            'qed_score': np.nan,
            'status': 'success'
        }

        if mol is None:
            log_skipped_molecule(cid, "Invalid molecule (RDKit parsing failed)")
            row_data['status'] = 'invalid_mol'
            results.append(row_data)
            continue

        try:
            # Compute Entropy
            row_data['entropy'] = compute_shannon_entropy(mol)
            
            # Compute LZ Complexity
            row_data['lz_complexity'] = compute_lz_complexity(smiles)
            
            # Compute SA and QED
            sa, qed = compute_sa_qed(mol)
            row_data['sa_score'] = sa
            row_data['qed_score'] = qed

        except TimeoutError:
            log_timeout_event(cid)
            row_data['status'] = 'timeout'
        except Exception as e:
            logger.error(f"Unexpected error processing CID {cid}: {e}")
            row_data['status'] = 'error'
        
        results.append(row_data)
    
    return results

def main():
    """
    Main pipeline entry point for Task T012.
    Iterates through the sampled dataset, computes metrics, and saves to CSV.
    """
    project_root = get_project_root()
    raw_data_path = project_root / "data" / "raw" / "sampled_dataset.csv"
    output_path = get_metrics_path()

    if not raw_data_path.exists():
        logger.error(f"Raw dataset not found at {raw_data_path}. Run download.py first.")
        return

    logger.info(f"Loading dataset from {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    logger.info(f"Loaded {len(df)} molecules.")

    all_results = []
    
    # Process in chunks to manage memory (T023 constraint)
    # Although we already sampled, chunking ensures we don't hold too many intermediate objects
    chunk_size = 500 
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1} (rows {i} to {min(i+chunk_size, len(df))})")
        results = process_chunk(chunk)
        all_results.extend(results)
        
        # Log progress
        if (i + chunk_size) % 1000 == 0 or (i + chunk_size) >= len(df):
            success_count = sum(1 for r in all_results if r['status'] == 'success')
            logger.info(f"Progress: {success_count}/{len(all_results)} successful so far.")

    # Create DataFrame from results
    results_df = pd.DataFrame(all_results)
    
    # Ensure column order and types
    cols = ['cid', 'smiles', 'entropy', 'lz_complexity', 'sa_score', 'qed_score', 'status']
    results_df = results_df[cols]
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Metrics saved to {output_path}")
    logger.info(f"Total molecules processed: {len(results_df)}")
    logger.info(f"Successful: {results_df[results_df['status'] == 'success'].shape[0]}")
    logger.info(f"Failed/Timeout/Invalid: {results_df[results_df['status'] != 'success'].shape[0]}")

if __name__ == "__main__":
    main()