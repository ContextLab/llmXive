"""
Data Ingestion and Harmonization Module.
Handles fetching, cleaning, unit conversion, and validation of polymer blend data.
"""
import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
import hashlib
import csv
import io

# Ensure code directory is in path for relative imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, setup_logging
from utils.seeds import set_deterministic_seed
from utils.ingest_utils import (
    celsius_to_kelvin,
    pascal_to_gpa,
    validate_weight_fractions,
    is_valid_smiles,
    parse_smiles_to_mol
)
from utils.schema_validator import load_schema, validate_output_file
from utils.checksum import compute_file_checksum
import config

# Initialize Logger
setup_logging()
logger = get_logger(__name__)

# Set deterministic seed
set_deterministic_seed(config.RANDOM_SEED)

# Constants
DATA_RAW_DIR = config.DATA_RAW_DIR
DATA_PROCESSED_DIR = config.DATA_PROCESSED_DIR
DATA_OUTPUT_DIR = config.DATA_OUTPUT_DIR
TOLERANCE_SENSITIVITY_REPORT_PATH = config.TOLERANCE_SENSITIVITY_REPORT_PATH
DATA_QUALITY_REPORT_PATH = config.DATA_QUALITY_REPORT_PATH
WEIGHT_FRACTION_TOLERANCES = config.WEIGHT_FRACTION_TOLERANCES

# Ensure output directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_data(source_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load raw data from a CSV file or simulate a fetch if no path is provided.
    For this task, we assume data is already downloaded to data/raw/ or fetch from a known public source.
    Since T019b requires real data and T014 failed previously on unspecified sources,
    we will attempt to load from a specific expected file or raise an error.

    In a real pipeline, this would call the API fetcher. Here we assume the data
    has been placed in data/raw/polymer_blend_data.csv by T020 (or similar).
    If not present, we raise a FileNotFoundError to fail loudly as per constraints.
    """
    # Check for expected file
    expected_file = DATA_RAW_DIR / "polymer_blend_data.csv"
    
    if not expected_file.exists():
        # Try to find any csv in raw dir
        csv_files = list(DATA_RAW_DIR.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                f"No raw data found in {DATA_RAW_DIR}. "
                "Please ensure T020 has downloaded data or place 'polymer_blend_data.csv' there."
            )
        # Use the first found CSV
        source_path = csv_files[0]
        logger.info(f"Using found CSV: {source_path}")
    else:
        source_path = expected_file

    records = []
    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean and parse basic types
            cleaned_row = {}
            for k, v in row.items():
                if v == '' or v is None:
                    cleaned_row[k] = None
                else:
                    # Try to convert numbers
                    try:
                        if '.' in v:
                            cleaned_row[k] = float(v)
                        else:
                            cleaned_row[k] = int(v)
                    except ValueError:
                        cleaned_row[k] = v
            records.append(cleaned_row)
    
    logger.info(f"Loaded {len(records)} records from {source_path}")
    return records


def harmonize_units(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert units to standard SI (Kelvin, GPa).
    """
    if record is None:
        return record
    
    # Convert Tg from Celsius to Kelvin if present and not already in K
    if 'Tg' in record and record['Tg'] is not None:
        # Assume input is Celsius if < 200 (heuristic) or based on schema
        # For robustness, we assume the raw data comes in Celsius as per typical datasets
        # If the value is > 0 and < 300, treat as Celsius.
        val = record['Tg']
        if isinstance(val, (int, float)) and 0 < val < 300:
            record['Tg_K'] = celsius_to_kelvin(val)
        else:
            record['Tg_K'] = val # Assume already K or invalid
    
    # Convert Modulus from Pa to GPa if present
    if 'Modulus' in record and record['Modulus'] is not None:
        val = record['Modulus']
        if isinstance(val, (int, float)):
            # Assume input is Pa if > 1000
            if val > 1000:
                record['Modulus_GPa'] = pascal_to_gpa(val)
            else:
                record['Modulus_GPa'] = val # Assume already GPa
    
    return record


def run_harmonization(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply unit harmonization to a batch of records.
    """
    return [harmonize_units(r) for r in records]


def validate_smiles_batch(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Validate SMILES strings and return valid records and indices of invalid ones.
    """
    valid_records = []
    invalid_indices = []
    
    for i, record in enumerate(records):
        smiles = record.get('SMILES')
        if smiles and is_valid_smiles(smiles):
            valid_records.append(record)
        else:
            invalid_indices.append(i)
            logger.debug(f"Invalid SMILES at index {i}: {smiles}")
    
    return valid_records, invalid_indices


def validate_weight_fractions_batch(records: List[Dict[str, Any]], tolerance: float = 0.02) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Validate weight fractions sum to 1.0 within a given tolerance.
    Returns valid records and indices of invalid ones.
    """
    valid_records = []
    invalid_indices = []
    
    for i, record in enumerate(records):
        # Extract weight fractions. Assuming keys like 'w1', 'w2' or 'weight_fraction_1'
        # We'll look for keys containing 'weight' or 'w' and numeric suffixes
        w_values = []
        for key, val in record.items():
            if isinstance(val, (int, float)) and ('weight' in key.lower() or (key.startswith('w') and len(key) > 1)):
                w_values.append(val)
        
        if not w_values:
            # If no weight fractions found, we might skip or count as invalid depending on policy
            # For now, if no weights, we assume it's a pure polymer (valid if only 1 component)
            # But strict validation requires weights. Let's mark as invalid if no weights found.
            invalid_indices.append(i)
            continue

        if validate_weight_fractions(w_values, tolerance):
            valid_records.append(record)
        else:
            invalid_indices.append(i)
            logger.debug(f"Weight fraction sum invalid at index {i}: {w_values}, sum={sum(w_values)}")
    
    return valid_records, invalid_indices


def run_tolerance_sensitivity_sweep(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run validation with different weight-fraction tolerance thresholds.
    Logs impact on valid record counts and pass rate percentage per threshold.
    Output: tolerance_sensitivity_report.json
    """
    logger.info(f"Starting weight-fraction tolerance sensitivity sweep with thresholds: {WEIGHT_FRACTION_TOLERANCES}")
    
    results = {
        "thresholds": [],
        "total_records": len(records),
        "sweep_details": []
    }
    
    for tol in WEIGHT_FRACTION_TOLERANCES:
        valid_records, invalid_indices = validate_weight_fractions_batch(records, tolerance=tol)
        pass_rate = (len(valid_records) / len(records) * 100) if len(records) > 0 else 0.0
        
        detail = {
            "tolerance": tol,
            "valid_count": len(valid_records),
            "invalid_count": len(invalid_indices),
            "pass_rate_percent": round(pass_rate, 2)
        }
        
        results["sweep_details"].append(detail)
        logger.info(f"Tolerance {tol}: {len(valid_records)} valid ({pass_rate:.2f}%)")
    
    # Write report
    with open(TOLERANCE_SENSITIVITY_REPORT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved sensitivity report to {TOLERANCE_SENSITIVITY_REPORT_PATH}")
    return results


def generate_data_quality_report(records: List[Dict[str, Any]], 
                                 invalid_smiles_indices: List[int], 
                                 invalid_weight_indices: List[int],
                                 tolerance_results: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive data quality report.
    """
    report = {
        "total_records": len(records),
        "invalid_smiles_count": len(invalid_smiles_indices),
        "invalid_weight_fractions_count": len(invalid_weight_indices),
        "valid_records_count": len(records) - len(invalid_smiles_indices) - len(invalid_weight_indices), # Simplified overlap
        "sensitivity_analysis": tolerance_results
    }
    
    with open(DATA_QUALITY_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved data quality report to {DATA_QUALITY_REPORT_PATH}")
    return report


def main():
    """
    Main entry point for the ingestion pipeline.
    """
    logger.info("Starting Data Ingestion Pipeline (T019b: Sensitivity Sweep)")
    
    try:
        # 1. Load Raw Data
        raw_records = load_raw_data()
        if not raw_records:
            logger.warning("No records loaded. Exiting.")
            return
        
        # 2. Harmonize Units
        harmonized_records = run_harmonization(raw_records)
        
        # 3. Validate SMILES
        valid_smiles_records, invalid_smiles_indices = validate_smiles_batch(harmonized_records)
        
        # 4. Run Tolerance Sensitivity Sweep (T019b specific)
        tolerance_results = run_tolerance_sensitivity_sweep(valid_smiles_records)
        
        # 5. Select a specific tolerance for final validation (e.g., 0.02)
        final_tolerance = 0.02
        final_valid_records, final_invalid_weight_indices = validate_weight_fractions_batch(
            valid_smiles_records, tolerance=final_tolerance
        )
        
        # 6. Generate Quality Report
        generate_data_quality_report(
            raw_records, 
            invalid_smiles_indices, 
            final_invalid_weight_indices,
            tolerance_results
        )
        
        # 7. Save Final Processed Data (for downstream tasks)
        final_output_path = DATA_PROCESSED_DIR / "processed_polymer_data.csv"
        with open(final_output_path, 'w', newline='', encoding='utf-8') as f:
            if final_valid_records:
                writer = csv.DictWriter(f, fieldnames=final_valid_records[0].keys())
                writer.writeheader()
                writer.writerows(final_valid_records)
        
        logger.info(f"Pipeline complete. Processed data saved to {final_output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()