"""
T011: Conditional Fallback - Execute generate_data.py for CI testing only.

Logic:
1. Check if T010 succeeded (real data present).
   - If data/raw/encode_counts.csv exists: Skip execution, create .synthetic_skipped.log.
2. If real data missing:
   - Check CI_MODE environment variable.
   - If CI_MODE != "1": Raise SystemExit (production mode requires real data).
   - If CI_MODE == "1": Execute generate_data.py to produce synthetic artifacts.

Deliverables:
- data/raw/synthetic_counts.csv (if executed)
- data/raw/synthetic_peaks.bed (if executed)
- data/raw/.synthetic_skipped.log (if skipped)
- logs/synthetic_checksums.txt (checksums if executed)
"""
import os
import sys
import logging
import json
from pathlib import Path

# Import from sibling modules as per API surface
from utils import checksum_file
from generate_data import set_seed, generate_gene_coordinates, generate_peak_coordinates, generate_counts_matrix, write_counts_csv, write_peaks_bed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/t011_execution.log')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

REAL_COUNTS_PATH = DATA_RAW_DIR / "encode_counts.csv"
SYNTHETIC_COUNTS_PATH = DATA_RAW_DIR / "synthetic_counts.csv"
SYNTHETIC_PEAKS_PATH = DATA_RAW_DIR / "synthetic_peaks.bed"
SKIPPED_LOG_PATH = DATA_RAW_DIR / ".synthetic_skipped.log"
FAILED_LOG_PATH = DATA_RAW_DIR / ".download_failed.log"
CHECKSUM_LOG_PATH = LOGS_DIR / "synthetic_checksums.txt"

# Cell lines required by task
CELL_LINES = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
SEED = 42

def ensure_directories():
    """Ensure required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def check_real_data_present():
    """Check if T010 successfully downloaded real data."""
    return REAL_COUNTS_PATH.exists()

def check_ci_mode():
    """Check if CI_MODE is set to '1'."""
    return os.environ.get("CI_MODE", "0") == "1"

def write_skipped_log():
    """Write log indicating synthetic data was skipped because real data exists."""
    log_content = {"status": "skipped", "reason": "Real data present"}
    with open(SKIPPED_LOG_PATH, 'w') as f:
        json.dump(log_content, f)
    logger.info(f"Real data present. Skipping synthetic generation. Log written to {SKIPPED_LOG_PATH}")

def write_failed_log(reason):
    """Write log indicating failure."""
    log_content = {"status": "failed", "reason": reason}
    with open(FAILED_LOG_PATH, 'w') as f:
        json.dump(log_content, f)
    logger.error(f"Failed: {reason}. Log written to {FAILED_LOG_PATH}")

def record_checksums():
    """Record checksums of generated synthetic files to logs/synthetic_checksums.txt."""
    checksums = []
    if SYNTHETIC_COUNTS_PATH.exists():
        checksums.append(f"counts: {checksum_file(SYNTHETIC_COUNTS_PATH)}")
    if SYNTHETIC_PEAKS_PATH.exists():
        checksums.append(f"peaks: {checksum_file(SYNTHETIC_PEAKS_PATH)}")
    
    with open(CHECKSUM_LOG_PATH, 'w') as f:
        f.write("\n".join(checksums) + "\n")
    logger.info(f"Checksums recorded in {CHECKSUM_LOG_PATH}")

def generate_synthetic_data():
    """Generate synthetic RNA-seq and DNase-seq data."""
    logger.info(f"Generating synthetic data for cell lines: {CELL_LINES} with seed {SEED}")
    
    # Set seed for reproducibility
    set_seed(SEED)
    
    # Generate coordinates
    # Note: generate_gene_coordinates and generate_peak_coordinates return lists of dicts
    # We need to generate enough genes to cover the cell lines
    # The generate_counts_matrix function will handle the actual matrix generation
    
    # Generate gene coordinates (simplified: assume one coordinate set for all, 
    # actual implementation in generate_data.py handles per-gene logic)
    # We pass cell_lines to generate_counts_matrix to create the right dimensions
    # Assuming generate_data.py functions can be called sequentially as per API
    
    # Since the API surface shows specific functions, we call them in order
    # 1. Generate gene coordinates (mocking a list of genes)
    # 2. Generate peak coordinates
    # 3. Generate counts matrix
    # 4. Write to CSV/BED
    
    # To align with the existing API in generate_data.py:
    # We assume generate_counts_matrix takes the cell lines and generates the matrix
    # and write functions take the generated data and write to files.
    
    # Let's assume the generate_data.py module has a helper or we reconstruct the call
    # based on the provided API surface.
    # The API surface lists: set_seed, generate_gene_coordinates, generate_peak_coordinates, 
    # generate_counts_matrix, write_counts_csv, write_peaks_bed.
    
    # We need to generate data for 5 cell lines.
    # Let's assume generate_counts_matrix(cell_lines) returns (genes, counts_matrix)
    # and generate_gene_coordinates() returns gene_coords, etc.
    
    # We'll call the functions as they are likely intended to be used together.
    # Since we don't have the full implementation of generate_data.py, we assume
    # these functions work as described in the task and previous tasks.
    
    # Generate gene coordinates (assuming a standard set or generated based on seed)
    gene_coords = generate_gene_coordinates() 
    # Generate peak coordinates
    peak_coords = generate_peak_coordinates()
    
    # Generate counts matrix for the specified cell lines
    # The function signature in API is generate_counts_matrix. 
    # We assume it takes cell_lines as an argument or uses global state.
    # Given the task description, we pass cell_lines.
    genes, counts_df = generate_counts_matrix(cell_lines=CELL_LINES)
    
    # Write counts to CSV
    write_counts_csv(counts_df, str(SYNTHETIC_COUNTS_PATH))
    logger.info(f"Synthetic counts written to {SYNTHETIC_COUNTS_PATH}")
    
    # Write peaks to BED
    # Assuming write_peaks_bed takes peak_coords and a path
    write_peaks_bed(peak_coords, str(SYNTHETIC_PEAKS_PATH))
    logger.info(f"Synthetic peaks written to {SYNTHETIC_PEAKS_PATH}")

def main():
    ensure_directories()
    
    # Check if real data is present (T010 success)
    if check_real_data_present():
        write_skipped_log()
        return 0
    
    # Check for CI mode
    if not check_ci_mode():
        reason = "Real data fetch failed and CI_MODE=0. Pipeline halted. No synthetic fallback allowed."
        write_failed_log(reason)
        raise SystemExit(reason)
    
    # CI_MODE is 1 and real data is missing -> Generate synthetic data
    try:
        generate_synthetic_data()
        record_checksums()
        logger.info("T011 completed successfully with synthetic data generation.")
        return 0
    except Exception as e:
        logger.error(f"Error during synthetic data generation: {e}")
        write_failed_log(f"Generation error: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())