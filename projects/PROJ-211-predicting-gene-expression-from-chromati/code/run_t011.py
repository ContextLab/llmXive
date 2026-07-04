"""
Task T011: Execute generate_data.py and compute checksums.

This script:
1. Runs code/generate_data.py to produce synthetic data
2. Computes checksums of the output files
3. Records checksums in logs/checksums.txt
"""
import os
import sys
import logging
from utils import checksum_file

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/t011_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Task T011: Execute generate_data.py and compute checksums")
    
    # Import and run the data generator
    from generate_data import main as generate_main
    
    # Ensure directories exist
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run data generation
    logger.info("Running data generation...")
    counts_path, peaks_path = generate_main()
    
    # Verify files exist
    if not os.path.exists(counts_path):
        raise FileNotFoundError(f"Expected counts file not found: {counts_path}")
    if not os.path.exists(peaks_path):
        raise FileNotFoundError(f"Expected peaks file not found: {peaks_path}")
    
    logger.info(f"Generated files: {counts_path}, {peaks_path}")
    
    # Compute checksums
    counts_checksum = checksum_file(counts_path)
    peaks_checksum = checksum_file(peaks_path)
    
    logger.info(f"Counts checksum: {counts_checksum}")
    logger.info(f"Peaks checksum: {peaks_checksum}")
    
    # Record checksums
    checksums_file = 'logs/checksums.txt'
    with open(checksums_file, 'a') as f:
        f.write(f"T011_counts: {counts_checksum}  {counts_path}\n")
        f.write(f"T011_peaks: {peaks_checksum}  {peaks_path}\n")
    
    logger.info(f"Checksums recorded in {checksums_file}")
    
    # Verify dimensions
    import pandas as pd
    counts_df = pd.read_csv(counts_path, index_col=0)
    
    expected_cell_lines = ['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2']
    expected_genes = 10000
    expected_peaks = 10000
    
    assert counts_df.shape[0] == expected_genes, f"Expected {expected_genes} genes, got {counts_df.shape[0]}"
    assert counts_df.shape[1] == len(expected_cell_lines), f"Expected {len(expected_cell_lines)} cell lines, got {counts_df.shape[1]}"
    assert list(counts_df.columns) == expected_cell_lines, f"Cell line mismatch"
    
    logger.info("Dimension verification passed:")
    logger.info(f"  Genes: {counts_df.shape[0]} (expected {expected_genes})")
    logger.info(f"  Cell lines: {counts_df.shape[1]} (expected {len(expected_cell_lines)})")
    logger.info(f"  Peaks: {expected_peaks}")
    
    logger.info("Task T011 completed successfully")

if __name__ == '__main__':
    main()
