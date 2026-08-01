"""
T007: Perform post-verification check to ensure every sample in PairedSampleIndex
has both expression and metabolite data. Exclude mismatches and log them.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

# Import logging utilities from existing API surface
from logging_utils import log_data_pairing_mismatch, log_data_pairing_mismatches_batch
from exceptions import E_PAIRING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('projects/PROJ-503-predicting-plant-defense-compound-produc/logs/verify_final_pairing.log')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path('projects/PROJ-503-predicting-plant-defense-compound-produc')
PAIRED_SAMPLES_PATH = PROJECT_ROOT / 'data' / 'processed' / 'paired_samples.csv'
EXPRESSION_MATRIX_PATH = PROJECT_ROOT / 'data' / 'processed' / 'expression_matrix.csv'
METABOLITE_MATRIX_PATH = PROJECT_ROOT / 'data' / 'processed' / 'metabolite_matrix.csv'
PAIRED_INDEX_OUTPUT_PATH = PROJECT_ROOT / 'data' / 'paired' / 'final_paired_samples.csv'
PAIRING_LOG_PATH = PROJECT_ROOT / 'logs' / 'data_pairing.json'

def load_paired_samples_index() -> Set[str]:
    """Load sample IDs from the PairedSampleIndex artifact."""
    if not PAIRED_SAMPLES_PATH.exists():
        logger.error(f"Paired samples index not found at {PAIRED_SAMPLES_PATH}")
        raise FileNotFoundError(f"Paired samples index not found at {PAIRED_SAMPLES_PATH}")
    
    sample_ids = set()
    with open(PAIRED_SAMPLES_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming the CSV has a column named 'sample_id' or similar
            # Adjust based on actual schema from T006
            sample_id = row.get('sample_id') or row.get('biosample_id') or row.get('id')
            if sample_id:
                sample_ids.add(sample_id)
    
    logger.info(f"Loaded {len(sample_ids)} samples from PairedSampleIndex")
    return sample_ids

def get_matrix_columns(file_path: Path) -> Set[str]:
    """Extract column names (sample IDs) from a wide-format matrix CSV."""
    if not file_path.exists():
        logger.error(f"Matrix file not found at {file_path}")
        raise FileNotFoundError(f"Matrix file not found at {file_path}")
    
    columns = set()
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            # Skip the first column (feature ID: gene_id or metabolite_id)
            # Assuming the first column is the identifier
            for col in reader.fieldnames[1:]:
                if col:
                    columns.add(col)
    
    logger.info(f"Found {len(columns)} samples in {file_path.name}")
    return columns

def verify_and_filter_pairs(
    paired_samples: Set[str],
    expression_columns: Set[str],
    metabolite_columns: Set[str]
) -> List[Dict[str, Any]]:
    """
    Verify that every sample in paired_samples exists in both matrices.
    Return a list of mismatches to be logged.
    """
    mismatches = []
    valid_samples = []
    
    for sample_id in paired_samples:
        has_expression = sample_id in expression_columns
        has_metabolite = sample_id in metabolite_columns
        
        if has_expression and has_metabolite:
            valid_samples.append(sample_id)
        else:
            reason = []
            if not has_expression:
                reason.append("missing_expression")
            if not has_metabolite:
                reason.append("missing_metabolite")
            
            mismatches.append({
                "sample_id": sample_id,
                "expression_source": "expression_matrix.csv" if has_expression else None,
                "metabolite_source": "metabolite_matrix.csv" if has_metabolite else None,
                "reason": "; ".join(reason)
            })
    
    return valid_samples, mismatches

def save_final_paired_samples(valid_samples: List[str]) -> None:
    """Save the final list of valid paired samples to the output CSV."""
    PAIRED_INDEX_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(PAIRED_INDEX_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id'])
        writer.writeheader()
        for sample_id in sorted(valid_samples):
            writer.writerow({'sample_id': sample_id})
    
    logger.info(f"Saved {len(valid_samples)} valid samples to {PAIRED_INDEX_OUTPUT_PATH}")

def main() -> None:
    """Main entry point for T007."""
    logger.info("Starting T007: Post-verification check for paired samples")
    
    try:
        # Load the PairedSampleIndex
        paired_samples = load_paired_samples_index()
        if not paired_samples:
            logger.warning("PairedSampleIndex is empty. Nothing to verify.")
            return

        # Load sample columns from expression matrix
        expression_columns = get_matrix_columns(EXPRESSION_MATRIX_PATH)
        
        # Load sample columns from metabolite matrix
        metabolite_columns = get_matrix_columns(METABOLITE_MATRIX_PATH)
        
        # Perform verification
        valid_samples, mismatches = verify_and_filter_pairs(
            paired_samples, expression_columns, metabolite_columns
        )
        
        # Log mismatches using the existing logging utility
        if mismatches:
            logger.warning(f"Found {len(mismatches)} mismatches. Logging them...")
            log_data_pairing_mismatches_batch(mismatches, PAIRING_LOG_PATH)
        else:
            logger.info("No mismatches found. All paired samples have both data types.")
        
        # Save the final filtered list
        save_final_paired_samples(valid_samples)
        
        # Report summary
        total_initial = len(paired_samples)
        total_final = len(valid_samples)
        total_removed = len(mismatches)
        
        logger.info(f"T007 Complete: {total_initial} initial -> {total_final} valid ({total_removed} removed)")
        
        if total_final == 0:
            logger.error("No valid paired samples remain. This may indicate a critical data issue.")
            raise E_PAIRING("No valid paired samples remain after verification.")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during verification: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()