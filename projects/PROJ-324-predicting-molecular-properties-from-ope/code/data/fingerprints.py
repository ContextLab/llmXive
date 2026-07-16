"""
Fingerprint Generation Module for Open Babel Fingerprints.

This module generates MACCS, ECFP4, and FP2 fingerprints by invoking the
`obabel` command-line tool via subprocess, as required by FR-003.
It consumes the diverse dataset produced by T011 and outputs a Parquet file.

Priority: ECFP4 > MACCS > FP2 (to manage runtime per FR-009).
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from data.preprocess import load_preprocessed_data
from logging_utils import setup_logger

# Configure logging
logger = setup_logger(__name__)

# Constants
INPUT_FILE = Path("data/derived/diverse_dataset.csv")
OUTPUT_FILE = Path("data/derived/fingerprints.parquet")
MAX_MOLECULES = 5000  # Safety limit per FR-004/FR-009
BATCH_SIZE = 100  # Process in batches to avoid command line limits

def _run_obabel(smiles_list: List[str], fp_type: str, batch_size: int = 50) -> List[List[int]]:
    """
    Invokes the obabel command-line tool to generate fingerprints for a list of SMILES.

    Args:
        smiles_list: List of SMILES strings.
        fp_type: Type of fingerprint ('FP2', 'MACCS', 'ECFP4').
        batch_size: Number of molecules to process in one subprocess call.

    Returns:
        List of fingerprint bit arrays (lists of integers).
    """
    all_fingerprints = []

    # Map internal types to obabel flags
    # FP2: -xf2
    # MACCS: -xm
    # ECFP4: -xe4 (Note: ECFP4 is often 1024 bits in OpenBabel with -xe4)
    type_map = {
        "FP2": "f2",
        "MACCS": "m",
        "ECFP4": "e4"
    }

    if fp_type not in type_map:
        raise ValueError(f"Unsupported fingerprint type: {fp_type}. Supported: {list(type_map.keys())}")

    flag = type_map[fp_type]

    for i in range(0, len(smiles_list), batch_size):
        batch = smiles_list[i : i + batch_size]
        if not batch:
            continue

        # Create a temporary file for SMILES input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.smi', delete=False) as tmp_in:
            for smi in batch:
                tmp_in.write(f"{smi}\n")
            tmp_in_path = tmp_in.name

        try:
            # Construct command: obabel -ismi -ofpt -xf<flag>
            # Output format 'fpt' prints the fingerprint as a list of bit indices or hex
            # We need to parse the output carefully.
            # Command: obabel -ismi <input> -ofpt -xf<flag>
            cmd = [
                "obabel",
                "-ismi", tmp_in_path,
                "-ofpt",
                f"-x{flag}",
                "-O", "-"  # Output to stdout
            ]

            logger.debug(f"Running obabel for {fp_type} on batch of {len(batch)} molecules.")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300  # 5 min timeout per batch
            )

            if result.returncode != 0:
                logger.warning(f"Obabel failed for {fp_type} batch: {result.stderr}")
                # Append None for failed entries to maintain alignment
                all_fingerprints.extend([None] * len(batch))
                continue

            # Parse output
            # OpenBabel -ofpt output format: "MoleculeID: bit1 bit2 bit3 ..." or similar
            # We expect lines corresponding to each input molecule.
            lines = result.stdout.strip().split('\n')
            
            for idx, line in enumerate(lines):
                if not line.strip():
                    all_fingerprints.append(None)
                    continue
                
                # Typical format: "1 0 1 0 ..." or "1: 0 1 0..." depending on version
                # We assume space-separated bits or indices. 
                # Let's try to parse as space-separated integers.
                # If it contains colons, we might need to strip the ID part.
                parts = line.split()
                if not parts:
                    all_fingerprints.append(None)
                    continue

                # Heuristic: If the first token is a number and the line looks like a list of bits/indices
                # We will try to parse the whole line as a list of integers.
                # If the line contains ":", we might need to handle it.
                # For -ofpt, it often outputs "MoleculeID: bit1 bit2 ..."
                if ":" in line:
                    # Split on first colon
                    _, bits_str = line.split(":", 1)
                    parts = bits_str.split()
                
                try:
                    fp_bits = [int(x) for x in parts if x.isdigit()]
                    all_fingerprints.append(fp_bits)
                except ValueError:
                    logger.warning(f"Could not parse fingerprint line: {line}")
                    all_fingerprints.append(None)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)

    return all_fingerprints

def generate_fingerprints(smiles_list: List[str], fp_types: List[str]) -> Dict[str, List[Any]]:
    """
    Generates fingerprints for a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        fp_types: List of fingerprint types to generate (e.g., ['ECFP4', 'MACCS']).

    Returns:
        Dictionary mapping fingerprint type to list of fingerprints (or None if failed).
    """
    results = {}
    total = len(smiles_list)
    
    for fp_type in fp_types:
        logger.info(f"Generating {fp_type} fingerprints ({total} molecules)...")
        fps = _run_obabel(smiles_list, fp_type)
        results[fp_type] = fps
        logger.info(f"Completed {fp_type}. Success rate: {sum(1 for x in fps if x is not None) / total:.2%}")
    
    return results

def process_dataset():
    """
    Main processing function:
    1. Loads diverse dataset from T011.
    2. Limits to MAX_MOLECULES.
    3. Generates fingerprints (ECFP4, MACCS, FP2).
    4. Saves to Parquet.
    """
    logger.info("Starting fingerprint generation pipeline (T019).")
    
    # 1. Load data
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. Ensure T011 has run.")
    
    df = load_preprocessed_data(INPUT_FILE)
    logger.info(f"Loaded {len(df)} molecules from {INPUT_FILE}.")
    
    if len(df) == 0:
        raise ValueError("Input dataset is empty.")

    # Limit dataset size for runtime feasibility (FR-009)
    if len(df) > MAX_MOLECULES:
        logger.warning(f"Dataset size ({len(df)}) exceeds limit ({MAX_MOLECULES}). Sampling first {MAX_MOLECULES}.")
        df = df.head(MAX_MOLECULES)

    smiles_list = df['smiles'].tolist()
    
    # 2. Generate Fingerprints
    # Priority: ECFP4 > MACCS > FP2
    fp_types = ["ECFP4", "MACCS", "FP2"]
    fp_results = generate_fingerprints(smiles_list, fp_types)
    
    # 3. Construct DataFrame
    # Convert list of bits to fixed-length arrays or keep as lists if variable?
    # Parquet supports lists, but for ML we often want fixed length.
    # OpenBabel MACCS is 167 bits, FP2 is 1024 bits, ECFP4 is usually 1024 bits.
    # We will store as lists of integers (bit indices set to 1) to save space,
    # or we can expand to dense arrays. Given the task asks for "fingerprints",
    # storing the list of active bits is often more efficient for sparse data.
    # However, for consistency with typical ML pipelines, we might want dense arrays.
    # Let's store as lists of integers (sparse representation) to avoid massive memory spikes
    # if the fingerprint length is large, unless the length is small (like MACCS 167).
    # Actually, for Random Forest, dense arrays are standard.
    # Let's determine the max length from the data or use standard lengths.
    # MACCS: 167, FP2: 1024, ECFP4: 1024 (default in obabel).
    
    def to_dense(fingerprint_bits, length):
        if fingerprint_bits is None:
            return [0] * length
        arr = [0] * length
        for bit in fingerprint_bits:
            if 0 <= bit < length:
                arr[bit] = 1
        return arr

    # We need to know the length of each fingerprint type.
    # We can infer from the max bit index seen, or use standard defaults.
    # Let's infer from the successful ones to be safe, or default if none.
    
    final_data = {
        'smiles': smiles_list,
        'mol_id': df['mol_id'].values if 'mol_id' in df.columns else range(len(smiles_list))
    }
    
    # Determine lengths
    lengths = {}
    for fp_type in fp_types:
        fps = fp_results[fp_type]
        valid_fps = [f for f in fps if f is not None]
        if valid_fps:
            max_bit = max(max(f) for f in valid_fps)
            # Add a small buffer or use standard if it matches
            # Standard: MACCS=167, FP2=1024, ECFP4=1024
            if fp_type == "MACCS":
                lengths[fp_type] = 167
            elif fp_type in ["FP2", "ECFP4"]:
                lengths[fp_type] = 1024
            else:
                lengths[fp_type] = max(max_bit + 1, 1024) # Fallback
        else:
            # Default lengths if all failed
            if fp_type == "MACCS":
                lengths[fp_type] = 167
            else:
                lengths[fp_type] = 1024
    
    logger.info(f"Detected/Assigned fingerprint lengths: {lengths}")

    for fp_type in fp_types:
        fps = fp_results[fp_type]
        length = lengths[fp_type]
        dense_fps = [to_dense(f, length) for f in fps]
        final_data[f'{fp_type}_fingerprint'] = dense_fps
        
        # Check for failure rate
        fail_count = sum(1 for f in fps if f is None)
        if fail_count > 0:
            logger.warning(f"{fp_type} failed for {fail_count} molecules ({fail_count/len(fps):.2%}).")

    df_fp = pd.DataFrame(final_data)
    
    # 4. Save to Parquet
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_fp.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Fingerprints saved to {OUTPUT_FILE}")
    
    return df_fp

def main():
    """Entry point for the script."""
    try:
        process_dataset()
        logger.info("T019 Fingerprint Generation completed successfully.")
    except Exception as e:
        logger.error(f"T019 Fingerprint Generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()