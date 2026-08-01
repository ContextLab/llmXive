"""
T004: Pair samples by biological sample ID (biosample_id).

Input: CSVs from T001 (geo_expression_matrix.csv) and T002 (metabolite_matrix.csv).
Output: Logs mismatches to logs/data_pairing.json.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime

# Project root relative to this script's location (code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

# Input files from T001 and T002
EXPRESSION_FILE = DATA_RAW_DIR / "geo_expression_matrix.csv"
METABOLITE_FILE = DATA_RAW_DIR / "metabolite_matrix.csv"

# Output log file
PAIRING_LOG_FILE = LOGS_DIR / "data_pairing.json"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "pairing.log")
    ]
)
logger = logging.getLogger(__name__)

def load_samples_from_csv(file_path: Path, id_column_name: str = "biosample_id") -> Set[str]:
    """
    Load sample IDs (biosample_id) from a CSV file.
    Assumes wide format or long format where the ID column exists.
    Returns a set of unique biosample_ids found in the file.
    """
    samples = set()
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if id_column_name not in reader.fieldnames:
            raise ValueError(f"Column '{id_column_name}' not found in {file_path}. "
                             f"Available columns: {reader.fieldnames}")
        
        for row in reader:
            sample_id = row[id_column_name].strip()
            if sample_id:
                samples.add(sample_id)
    
    logger.info(f"Loaded {len(samples)} unique samples from {file_path.name}")
    return samples

def pair_samples(expression_samples: Set[str], metabolite_samples: Set[str]) -> Tuple[Set[str], List[Dict[str, Any]]]:
    """
    Identify paired samples (intersection) and log mismatches.
    
    Returns:
        paired_ids: Set of biosample_ids present in both datasets.
        mismatches: List of dicts with 'sample_id' and 'reason'.
    """
    paired_ids = expression_samples.intersection(metabolite_samples)
    mismatches = []
    
    # Samples only in expression
    only_expression = expression_samples - metabolite_samples
    for sid in sorted(only_expression):
        mismatches.append({
            "sample_id": sid,
            "reason": "present_in_expression_only"
        })
    
    # Samples only in metabolite
    only_metabolite = metabolite_samples - expression_samples
    for sid in sorted(only_metabolite):
        mismatches.append({
            "sample_id": sid,
            "reason": "present_in_metabolite_only"
        })
    
    return paired_ids, mismatches

def save_pairing_log(mismatches: List[Dict[str, Any]], output_path: Path):
    """
    Save the list of mismatches to a JSON file.
    Schema: JSON array with {sample_id, reason}.
    """
    # Add metadata header as a separate key if needed, but task asks for array
    # To be safe and extensible, we wrap it or just write the array.
    # Task spec: "Schema: JSON array with sample_id, reason"
    # We will write the array directly.
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mismatches, f, indent=2)
    logger.info(f"Saved {len(mismatches)} mismatches to {output_path}")

def main():
    logger.info("Starting sample pairing process (T004)...")
    
    try:
        # Load samples from expression matrix (T001 output)
        expression_samples = load_samples_from_csv(EXPRESSION_FILE, id_column_name="biosample_id")
        
        # Load samples from metabolite matrix (T002 output)
        metabolite_samples = load_samples_from_csv(METABOLITE_FILE, id_column_name="biosample_id")
        
        # Perform pairing
        paired_ids, mismatches = pair_samples(expression_samples, metabolite_samples)
        
        # Log statistics
        total_expression = len(expression_samples)
        total_metabolite = len(metabolite_samples)
        total_paired = len(paired_ids)
        pairing_rate = (total_paired / min(total_expression, total_metabolite)) * 100 if min(total_expression, total_metabolite) > 0 else 0.0
        
        logger.info(f"Expression samples: {total_expression}")
        logger.info(f"Metabolite samples: {total_metabolite}")
        logger.info(f"Paired samples: {total_paired}")
        logger.info(f"Pairing rate: {pairing_rate:.2f}%")
        logger.info(f"Mismatches found: {len(mismatches)}")
        
        # Save mismatches to log file
        save_pairing_log(mismatches, PAIRING_LOG_FILE)
        
        # Also save the list of paired IDs for downstream tasks (T006)
        paired_list_file = PROJECT_ROOT / "data" / "processed" / "paired_samples.csv"
        paired_list_file.parent.mkdir(parents=True, exist_ok=True)
        with open(paired_list_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["biosample_id"])
            for sid in sorted(paired_ids):
                writer.writerow([sid])
        logger.info(f"Saved {total_paired} paired sample IDs to {paired_list_file}")
        
        logger.info("T004 Pairing process completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data format error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pairing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()