import os
import sys
import logging
from utils import checksum_file
from generate_data import set_seed, generate_gene_coordinates, generate_peak_coordinates, generate_counts_matrix, write_counts_csv, write_peaks_bed

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/t011_execution.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting T011: Generating synthetic paired RNA-seq and DNase-seq counts")

    # Configuration
    seed = 42
    cell_lines = ['GM12878', 'K562', 'HMEC', 'IMR90', 'HepG2']
    num_genes = 1000
    num_peaks = 2000
    
    output_counts_path = 'data/raw/synthetic_counts.csv'
    output_peaks_path = 'data/raw/synthetic_peaks.bed'
    checksum_log_path = 'logs/checksums.txt'

    # Ensure directories exist
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    try:
        # Set seed for reproducibility
        set_seed(seed)
        logger.info(f"Seed set to {seed}")

        # Generate gene coordinates
        logger.info("Generating gene coordinates...")
        gene_coords = generate_gene_coordinates(num_genes, cell_lines)
        
        # Generate peak coordinates
        logger.info("Generating peak coordinates...")
        peak_coords = generate_peak_coordinates(num_peaks, cell_lines)
        
        # Generate counts matrix
        logger.info("Generating counts matrix...")
        counts_data = generate_counts_matrix(gene_coords, peak_coords, cell_lines)
        
        # Write outputs
        logger.info(f"Writing counts to {output_counts_path}...")
        write_counts_csv(counts_data, output_counts_path, cell_lines)
        
        logger.info(f"Writing peaks to {output_peaks_path}...")
        write_peaks_bed(peak_coords, output_peaks_path, cell_lines)
        
        # Verify files exist
        if not os.path.exists(output_counts_path):
            raise FileNotFoundError(f"Failed to create {output_counts_path}")
        if not os.path.exists(output_peaks_path):
            raise FileNotFoundError(f"Failed to create {output_peaks_path}")
        
        # Calculate checksums
        logger.info("Calculating checksums...")
        counts_checksum = checksum_file(output_counts_path)
        peaks_checksum = checksum_file(output_peaks_path)
        
        # Log checksums
        os.makedirs(os.path.dirname(checksum_log_path), exist_ok=True)
        with open(checksum_log_path, 'a') as f:
            f.write(f"T011_synthetic_counts: {counts_checksum}\n")
            f.write(f"T011_synthetic_peaks: {peaks_checksum}\n")
        
        logger.info(f"Checksums recorded in {checksum_log_path}")
        logger.info(f"  Counts: {counts_checksum}")
        logger.info(f"  Peaks: {peaks_checksum}")
        
        logger.info("T011 completed successfully")
        return 0

    except Exception as e:
        logger.error(f"T011 failed: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    sys.exit(main())
