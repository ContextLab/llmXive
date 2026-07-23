"""
Fingerprint generation module using Open Babel command-line tool.

Implements T019: Generate Open Babel fingerprints (MACCS, ECFP4, FP2)
by invoking the `obabel` command-line tool via subprocess.
"""
import os
import sys
import subprocess
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FINGERPRINT_TYPES = ['ECFP4', 'MACCS', 'FP2']
OUTPUT_FILE = Path('data/processed/train_fingerprints.parquet')
INPUT_FILE = Path('data/derived/train_set.csv')
TIMEOUT_PER_MOLECULE = 30  # seconds
MAX_TOTAL_TIME_HOURS = 6
OBABEL_TIMEOUT_CMD = ['timeout', str(TIMEOUT_PER_MOLECULE), 'obabel']
OBABEL_CMD = ['obabel']

def ensure_dirs() -> None:
    """Ensure output directories exist."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_FILE.parent}")

def check_obabel_available() -> bool:
    """Check if obabel is available in the system PATH."""
    try:
        result = subprocess.run(
            ['obabel', '-h'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Open Babel (obabel) is available.")
            return True
        else:
            logger.error("Open Babel returned non-zero exit code on help.")
            return False
    except FileNotFoundError:
        logger.error("Open Babel (obabel) not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Open Babel help command timed out.")
        return False

def smiles_to_obabel_fingerprint(smiles: str, fingerprint_type: str) -> Optional[str]:
    """
    Generate a single fingerprint for a SMILES string using obabel.
    
    Args:
        smiles: SMILES string of the molecule
        fingerprint_type: Type of fingerprint (ECFP4, MACCS, FP2)
        
    Returns:
        Fingerprint string (space-separated bits) or None if failed
    """
    cmd = [
        'obabel', '-i', 'smiles', smiles, '-o', 'txt', '-xf', fingerprint_type
    ]
    
    try:
        # Use timeout to prevent hanging
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_PER_MOLECULE
        )
        
        if result.returncode == 0:
            # Output format: "SMILES FINGERPRINT_BITS"
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 1:
                # The fingerprint is the second part of the first line
                parts = lines[0].split(None, 1)
                if len(parts) == 2:
                    return parts[1]
                else:
                    logger.warning(f"Unexpected output format for {smiles}: {lines[0]}")
                    return None
            return None
        else:
            logger.warning(f"obabel failed for {smiles}: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.warning(f"obabel timed out for {smiles}")
        return None
    except Exception as e:
        logger.error(f"Error generating fingerprint for {smiles}: {e}")
        return None

def generate_fingerprints_batch(smiles_list: List[str], fingerprint_type: str) -> Dict[str, Optional[str]]:
    """
    Generate fingerprints for a batch of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings
        fingerprint_type: Type of fingerprint to generate
        
    Returns:
        Dictionary mapping SMILES to fingerprint string
    """
    results = {}
    for smiles in tqdm(smiles_list, desc=f"Generating {fingerprint_type} fingerprints"):
        fp = smiles_to_obabel_fingerprint(smiles, fingerprint_type)
        results[smiles] = fp
    return results

def parse_fingerprint_string(fp_str: str) -> List[int]:
    """
    Parse a space-separated fingerprint string into a list of integers.
    
    Args:
        fp_str: Space-separated bit string
        
    Returns:
        List of integers (0 or 1)
    """
    if fp_str is None:
        return []
    try:
        return [int(bit) for bit in fp_str.split()]
    except ValueError:
        logger.warning(f"Could not parse fingerprint string: {fp_str}")
        return []

def process_dataset(input_file: Path, output_file: Path) -> None:
    """
    Process the training dataset to generate fingerprints.
    
    Args:
        input_file: Path to the input CSV with SMILES
        output_file: Path to the output Parquet file
    """
    if not check_obabel_available():
        logger.error("Open Babel is not available. Cannot proceed.")
        sys.exit(1)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info(f"Loading dataset from {input_file}")
    df = pd.read_csv(input_file)
    
    # Ensure we have SMILES column
    if 'smiles' not in df.columns:
        logger.error(f"Input file must contain 'smiles' column. Found: {df.columns.tolist()}")
        sys.exit(1)
    
    # Remove any rows with missing SMILES
    df = df.dropna(subset=['smiles'])
    df = df[df['smiles'].astype(str).str.strip() != '']
    
    logger.info(f"Processing {len(df)} molecules")
    
    # Check time budget
    start_time = time.time()
    max_seconds = MAX_TOTAL_TIME_HOURS * 3600
    
    all_fingerprints = {fp_type: {} for fp_type in FINGERPRINT_TYPES}
    
    # Process each fingerprint type
    for fp_type in FINGERPRINT_TYPES:
        logger.info(f"Starting {fp_type} fingerprint generation")
        fp_results = generate_fingerprints_batch(df['smiles'].tolist(), fp_type)
        all_fingerprints[fp_type] = fp_results
        
        elapsed = time.time() - start_time
        if elapsed > max_seconds * 0.8:  # Stop if we've used 80% of time
            logger.warning(f"Time budget nearly exhausted ({elapsed:.1f}s / {max_seconds:.1f}s). Stopping.")
            break
    
    # Build output DataFrame
    output_data = {'smiles': df['smiles'].tolist()}
    
    for fp_type in FINGERPRINT_TYPES:
        fp_list = []
        for smiles in df['smiles']:
            fp_str = all_fingerprints[fp_type].get(smiles)
            if fp_str:
                fp_list.append(fp_str)
            else:
                # Use empty list for failed generations
                fp_list.append("")
        output_data[f'{fp_type.lower()}_bits'] = fp_list
    
    output_df = pd.DataFrame(output_data)
    
    # Save to Parquet
    logger.info(f"Saving fingerprints to {output_file}")
    output_df.to_parquet(output_file, index=False)
    
    elapsed = time.time() - start_time
    logger.info(f"Fingerprint generation completed in {elapsed:.1f} seconds")
    
    # Verify output
    if output_file.exists():
        logger.info(f"Output file created: {output_file} ({output_file.stat().st_size} bytes)")
    else:
        logger.error("Failed to create output file")
        sys.exit(1)

def main() -> None:
    """Main entry point for fingerprint generation."""
    logger.info("Starting fingerprint generation for training set")
    
    ensure_dirs()
    
    if not INPUT_FILE.exists():
        logger.error(f"Training set not found: {INPUT_FILE}")
        logger.error("Please ensure T011.5 (Split) and T010.1 (MaxMin) are completed first.")
        sys.exit(1)
    
    process_dataset(INPUT_FILE, OUTPUT_FILE)
    
    logger.info("Fingerprint generation completed successfully")

if __name__ == "__main__":
    main()