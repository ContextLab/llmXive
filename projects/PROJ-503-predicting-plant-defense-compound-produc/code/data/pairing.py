import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# Import custom exceptions as defined in the project API surface
from exceptions import E_PAIRING

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path relative to the script execution context
# Assuming scripts are run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_samples_from_csv(file_path: Path) -> Set[str]:
    """
    Load sample IDs (biosample_ids) from a CSV file.
    Expects a CSV with a header containing 'biosample_id' or similar.
    For this task, we assume the paired_index.csv from T004 contains the list.
    If the input is the raw expression/metabolite matrices, we need to parse headers.
    
    Based on T004 output: `data/processed/paired_index.csv` likely contains sample IDs.
    If the input is the raw wide-format matrix, the columns (after gene_id) are sample IDs.
    
    For T005, we are validating the pairing rate against the output of T004.
    T004 output `data/processed/paired_index.csv` should contain the matched pairs.
    However, the task says: "Verify FR-009... if <95% of samples have matched... pairs".
    This implies we need to compare the TOTAL expression samples vs the PAIRED samples.
    
    Inputs:
    - expression_matrix_path: The raw expression matrix (T001 output) to get total expression samples.
    - metabolite_matrix_path: The raw metabolite matrix (T002 output) to get total metabolite samples.
    - paired_index_path: The output of T004 (paired_index.csv) containing the valid paired samples.
    
    Wait, T004 output `data/processed/paired_index.csv` is the result of pairing.
    The task T005 requires calculating the pairing rate: (Number of Paired Samples) / (Total Expression Samples).
    If this rate < 0.95, raise E_PAIRING.
    
    Let's assume T004 produces a file listing the valid paired sample IDs.
    We need to know the total count of expression samples to calculate the rate.
    The expression matrix is in `data/raw/geo_expression_matrix.csv`.
    The metabolite matrix is in `data/raw/metabolite_matrix.csv`.
    
    Refining inputs for this function:
    1. Load all sample IDs from Expression Matrix (columns 1..end).
    2. Load all sample IDs from Metabolite Matrix (columns 1..end).
    3. Load the list of paired sample IDs from T004 output (or re-calculate if T004 output is just the index).
    
    Actually, T004 description says: "Output: `data/processed/paired_index.csv`".
    T005 depends on T004. So we read `data/processed/paired_index.csv`.
    But `paired_index.csv` might just be the list of *paired* samples.
    To get the rate, we need the denominator: Total Expression Samples.
    
    Let's define the function to accept the paths to the raw matrices and the paired index.
    """
    samples = set()
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Check if it's a wide format matrix (has gene_id column) or a simple list
        fieldnames = reader.fieldnames
        if not fieldnames:
            return samples
        
        if 'gene_id' in fieldnames or 'metabolite_id' in fieldnames:
            # Wide format: samples are columns excluding the ID column
            # Assuming first column is ID, rest are samples
            sample_columns = [col for col in fieldnames if col != 'gene_id' and col != 'metabolite_id']
            for col in sample_columns:
                # Just add column name as sample ID
                samples.add(col)
        elif 'sample_id' in fieldnames:
            # Simple list format
            for row in reader:
                samples.add(row['sample_id'])
        else:
            # Fallback: assume first column is ID, rest are samples? Or just all non-empty cells?
            # Let's assume wide format if 'gene_id' not found but multiple columns exist
            # If it's a 1-column file with IDs
            if len(fieldnames) == 1:
                for row in reader:
                    samples.add(row[fieldnames[0]])
            else:
                # Assume wide format, first col is ID
                sample_columns = fieldnames[1:]
                for col in sample_columns:
                    samples.add(col)
                    
    return samples

def extract_biosample_ids_from_expression(expression_path: Path) -> Dict[str, str]:
    """
    Extract biosample IDs from the expression matrix if the columns are biosample IDs.
    In the context of T001/T002, the columns are sample IDs which should correspond to biosample IDs.
    Returns a dict mapping column_name -> biosample_id (usually same as column_name).
    """
    # This is a simplified extraction. In a real scenario, we might map accession to biosample.
    # For T005, we assume the column names in the wide matrix ARE the sample IDs to be paired.
    samples = load_samples_from_csv(expression_path)
    return {s: s for s in samples}

def extract_biosample_ids_from_metabolite(metabolite_path: Path) -> Dict[str, str]:
    """
    Extract biosample IDs from the metabolite matrix.
    """
    samples = load_samples_from_csv(metabolite_path)
    return {s: s for s in samples}

def pair_samples(expression_samples: Set[str], metabolite_samples: Set[str]) -> Tuple[Set[str], List[Dict[str, Any]]]:
    """
    Calculate the intersection of expression and metabolite samples.
    Returns (paired_samples, mismatches_log).
    """
    paired = expression_samples.intersection(metabolite_samples)
    mismatches = []
    
    for s in expression_samples:
        if s not in metabolite_samples:
            mismatches.append({
                "sample_id": s,
                "source": "expression",
                "reason": "missing_in_metabolite"
            })
    for s in metabolite_samples:
        if s not in expression_samples:
            mismatches.append({
                "sample_id": s,
                "source": "metabolite",
                "reason": "missing_in_expression"
            })
    
    return paired, mismatches

def calculate_pairing_rate(paired_count: int, total_expression_count: int) -> float:
    """
    Calculate the pairing rate.
    Rate = Paired / Total Expression Samples.
    """
    if total_expression_count == 0:
        return 0.0
    return paired_count / total_expression_count

def save_paired_index(paired_samples: Set[str], output_path: Path) -> None:
    """
    Save the list of paired sample IDs to a CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id'])
        writer.writeheader()
        for s in sorted(paired_samples):
            writer.writerow({'sample_id': s})

def run_pairing_validation(
    expression_matrix_path: Path,
    metabolite_matrix_path: Path,
    paired_index_path: Path,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Main validation logic for T005.
    
    1. Load all expression sample IDs.
    2. Load all metabolite sample IDs.
    3. Calculate the intersection (paired).
    4. Calculate pairing rate = len(paired) / len(expression).
    5. If rate < threshold, raise E_PAIRING.
    6. Save the paired index if successful.
    7. Log mismatches if any.
    """
    logger.info(f"Starting pairing validation for {expression_matrix_path} and {metabolite_matrix_path}")
    
    # Load samples
    try:
        expression_samples = load_samples_from_csv(expression_matrix_path)
        metabolite_samples = load_samples_from_csv(metabolite_matrix_path)
    except Exception as e:
        logger.error(f"Failed to load sample lists: {e}")
        raise
    
    if not expression_samples:
        logger.error("No expression samples found.")
        raise E_PAIRING("No expression samples found to validate pairing.")
    
    # Calculate pairing
    paired_samples, mismatches = pair_samples(expression_samples, metabolite_samples)
    
    total_expression = len(expression_samples)
    total_paired = len(paired_samples)
    rate = calculate_pairing_rate(total_paired, total_expression)
    
    logger.info(f"Total Expression Samples: {total_expression}")
    logger.info(f"Total Metabolite Samples: {len(metabolite_samples)}")
    logger.info(f"Paired Samples: {total_paired}")
    logger.info(f"Pairing Rate: {rate:.4f} ({rate*100:.2f}%)")
    
    # Check threshold
    if rate < threshold:
        error_msg = (
            f"Pairing rate {rate:.4f} is below the required threshold of {threshold}. "
            f"Aborting with E-PAIRING. "
            f"Expression samples: {total_expression}, Paired: {total_paired}."
        )
        logger.error(error_msg)
        
        # Log mismatches to logs/data_pairing.json
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "data_pairing.json"
        
        existing_mismatches = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_mismatches = json.load(f)
            except json.JSONDecodeError:
                existing_mismatches = []
        
        existing_mismatches.extend(mismatches)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_mismatches, f, indent=2)
        
        raise E_PAIRING(error_msg)
    
    # If passed, save the paired index
    paired_index_path.parent.mkdir(parents=True, exist_ok=True)
    save_paired_index(paired_samples, paired_index_path)
    
    logger.info(f"Pairing validation successful. Rate: {rate:.4f}. Saved to {paired_index_path}")
    
    return {
        "total_expression": total_expression,
        "total_metabolite": len(metabolite_samples),
        "paired": total_paired,
        "rate": rate,
        "threshold": threshold,
        "status": "passed"
    }

def main():
    """
    Entry point for the pairing validation script.
    """
    # Define paths based on project structure
    expression_path = PROJECT_ROOT / "data" / "raw" / "geo_expression_matrix.csv"
    metabolite_path = PROJECT_ROOT / "data" / "raw" / "metabolite_matrix.csv"
    paired_index_path = PROJECT_ROOT / "data" / "processed" / "paired_index.csv"
    
    # Threshold from FR-009
    threshold = 0.95
    
    try:
        result = run_pairing_validation(
            expression_matrix_path=expression_path,
            metabolite_matrix_path=metabolite_path,
            paired_index_path=paired_index_path,
            threshold=threshold
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except E_PAIRING as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during pairing validation")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()