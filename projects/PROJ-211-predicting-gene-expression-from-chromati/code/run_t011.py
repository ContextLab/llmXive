import os
import sys
import logging
from utils import checksum_file
from generate_data import set_seed, generate_gene_coordinates, generate_peak_coordinates, generate_counts_matrix, write_counts_csv, write_peaks_bed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/t011_execution.log')
    ]
)

def main():
    """
    Executes T011: Generate synthetic paired RNA-seq and DNase-seq counts
    for specific cell lines to serve as a CI validation dataset when real
    ENCODE data is unavailable.

    Deliverables:
      - data/raw/synthetic_counts.csv
      - data/raw/synthetic_peaks.bed
      - logs/checksums.txt (updated with new checksums)
    """
    logging.info("Starting T011: Synthetic Data Generation")
    
    # Configuration from task description
    seed = 42
    cell_lines = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
    
    # Ensure directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Set global seed
    set_seed(seed)
    logging.info(f"Seed set to {seed}")

    # Generate gene coordinates (needed for peak generation context)
    logging.info("Generating gene coordinates...")
    gene_coords = generate_gene_coordinates(seed=seed, num_genes=5000)
    
    # Generate peak coordinates
    logging.info("Generating peak coordinates...")
    peak_coords = generate_peak_coordinates(seed=seed, num_peaks=10000, gene_coords=gene_coords)
    
    # Generate counts matrix
    # Dimensions: genes x cell lines x peaks (simplified for synthetic generation)
    # The generate_counts_matrix function returns a dict of cell_line -> (genes x peaks) matrix
    logging.info(f"Generating counts matrix for cell lines: {cell_lines}...")
    counts_data = generate_counts_matrix(
        seed=seed,
        cell_lines=cell_lines,
        num_genes=5000,
        num_peaks=10000,
        gene_coords=gene_coords,
        peak_coords=peak_coords
    )

    # Write outputs
    counts_path = "data/raw/synthetic_counts.csv"
    peaks_path = "data/raw/synthetic_peaks.bed"

    logging.info(f"Writing counts to {counts_path}...")
    write_counts_csv(counts_data, counts_path)

    logging.info(f"Writing peaks to {peaks_path}...")
    write_peaks_bed(peak_coords, peaks_path)

    # Calculate and record checksums
    logging.info("Calculating checksums...")
    checksums = {}
    checksums["synthetic_counts.csv"] = checksum_file(counts_path)
    checksums["synthetic_peaks.bed"] = checksum_file(peaks_path)

    checksum_log_path = "logs/checksums.txt"
    with open(checksum_log_path, "a") as f:
        f.write(f"\n--- T011 Run (Seed={seed}) ---\n")
        for fname, cksum in checksums.items():
            f.write(f"{fname}: {cksum}\n")
    
    logging.info(f"Checksums recorded in {checksum_log_path}")
    logging.info("T011 completed successfully.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
