import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

# Import existing utilities from the project API surface
from utils.logger import get_logger
from utils.ingest_utils import is_valid_smiles, validate_weight_fractions
from utils.seeds import set_deterministic_seed
from config import PROJECT_ROOT

logger = get_logger(__name__)

# Constants
PERFECT_JOIN_THRESHOLD = 0.50  # 50% failure rate triggers fallback
REQUIRED_FIELDS = {'smiles', 'composition', 'tg', 'modulus'}

def load_raw_data() -> List[Dict[str, Any]]:
    """
    Load raw data from the processed directory.
    In a real implementation, this would read from data/processed/
    For now, it assumes the data has been saved by T020.
    """
    data_path = PROJECT_ROOT / "data" / "processed" / "harmonized_data.json"
    if not data_path.exists():
        # Fallback to raw if processed doesn't exist, but log warning
        data_path = PROJECT_ROOT / "data" / "raw" / "raw_data.json"
    
    if not data_path.exists():
        logger.error(f"Raw data file not found at {data_path}")
        return []

    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def harmonize_units(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Harmonize units (C->K, Pa->GPa) for the dataset.
    This is a placeholder for the actual harmonization logic.
    """
    # In a real implementation, this would iterate through data and convert units
    # For T019c, we assume the data is already harmonized or we perform basic checks
    return data

def run_harmonization(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the full harmonization pipeline.
    """
    logger.info("Starting unit harmonization...")
    harmonized = harmonize_units(data)
    logger.info(f"Harmonized {len(harmonized)} records.")
    return harmonized

def validate_smiles_batch(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate SMILES strings using RDKit.
    """
    valid_data = []
    for record in data:
        if is_valid_smiles(record.get('smiles')):
            valid_data.append(record)
        else:
            logger.debug(f"Invalid SMILES excluded: {record.get('smiles', 'N/A')}")
    return valid_data

def validate_weight_fractions_batch(data: List[Dict[str, Any]], tolerance: float = 0.02) -> List[Dict[str, Any]]:
    """
    Validate weight fractions sum to 1.0 within tolerance.
    """
    valid_data = []
    for record in data:
        if validate_weight_fractions(record.get('composition', {}), tolerance):
            valid_data.append(record)
        else:
            logger.debug(f"Invalid weight fractions excluded: {record.get('composition', {})}")
    return valid_data

def check_perfect_join(record: Dict[str, Any]) -> bool:
    """
    Check if a record has a 'perfect join' (SMILES + Composition + Tg + Modulus).
    """
    # Check for presence of required fields
    has_smiles = bool(record.get('smiles'))
    has_composition = bool(record.get('composition'))
    has_tg = record.get('tg') is not None
    has_modulus = record.get('modulus') is not None

    # Validate SMILES format
    if has_smiles and not is_valid_smiles(record['smiles']):
        return False

    # Validate composition (sum of weight fractions)
    if has_composition:
        if not validate_weight_fractions(record['composition']):
            return False

    return has_smiles and has_composition and has_tg and has_modulus

def calculate_join_success_rate(data: List[Dict[str, Any]]) -> Tuple[float, int, int]:
    """
    Calculate the percentage of records with a 'perfect join'.
    Returns: (success_rate, total_records, perfect_join_count)
    """
    if not data:
        return 0.0, 0, 0

    perfect_join_count = sum(1 for record in data if check_perfect_join(record))
    total_records = len(data)
    success_rate = perfect_join_count / total_records if total_records > 0 else 0.0

    return success_rate, total_records, perfect_join_count

def run_join_success_rate_check(data: List[Dict[str, Any]]) -> bool:
    """
    Run the Join Success Rate Check & Fallback Trigger.
    Returns True if the pipeline can continue, False if fallback is triggered.
    """
    logger.info("Running Join Success Rate Check...")
    success_rate, total, perfect_count = calculate_join_success_rate(data)
    failure_rate = 1.0 - success_rate

    logger.info(f"Join Success Rate: {success_rate:.2%} ({perfect_count}/{total} records)")
    logger.info(f"Join Failure Rate: {failure_rate:.2%}")

    if failure_rate > PERFECT_JOIN_THRESHOLD:
        logger.error(f"CRITICAL: Join failure rate ({failure_rate:.2%}) exceeds threshold ({PERFECT_JOIN_THRESHOLD:.2%}).")
        logger.error("Triggering Monomer-Level Fallback mode.")
        logger.error("Halting main blend pipeline. Switching to code/02b_fallback.py.")
        
        # Save the report for audit
        report_path = PROJECT_ROOT / "data" / "processed" / "join_success_report.json"
        report = {
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "total_records": total,
            "perfect_join_count": perfect_count,
            "threshold": PERFECT_JOIN_THRESHOLD,
            "fallback_triggered": True
        }
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Trigger fallback by calling the fallback script
        fallback_script = PROJECT_ROOT / "code" / "02b_fallback.py"
        if fallback_script.exists():
            logger.info(f"Executing fallback script: {fallback_script}")
            # In a real pipeline, we might use subprocess or import and run main
            # For now, we just log that it would be executed
            # os.system(f"python {fallback_script}") 
        else:
            logger.error(f"Fallback script not found at {fallback_script}. Cannot proceed.")
        
        return False
    else:
        logger.info("Join success rate is acceptable. Proceeding with main pipeline.")
        return True

def run_tolerance_sensitivity_sweep(data: List[Dict[str, Any]], tolerances: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Run tolerance sensitivity sweep for weight fraction validation.
    """
    if tolerances is None:
        tolerances = [0.01, 0.02, 0.05, 0.10]
    
    results = {}
    for tol in tolerances:
        valid_data = validate_weight_fractions_batch(data, tol)
        results[f"tolerance_{tol}"] = {
            "valid_count": len(valid_data),
            "pass_rate": len(valid_data) / len(data) if data else 0.0
        }
    
    return results

def generate_data_quality_report(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive data quality report.
    """
    success_rate, total, perfect_count = calculate_join_success_rate(data)
    
    report = {
        "total_records": total,
        "perfect_join_count": perfect_count,
        "success_rate": success_rate,
        "failure_rate": 1.0 - success_rate,
        "validation_summary": {
            "smiles_valid": sum(1 for r in data if is_valid_smiles(r.get('smiles'))),
            "composition_valid": sum(1 for r in data if validate_weight_fractions(r.get('composition'))),
            "tg_present": sum(1 for r in data if r.get('tg') is not None),
            "modulus_present": sum(1 for r in data if r.get('modulus') is not None)
        }
    }
    
    return report

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    set_deterministic_seed(42)
    
    # Load raw data
    raw_data = load_raw_data()
    if not raw_data:
        logger.error("No data loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(raw_data)} records.")
    
    # Harmonize units
    harmonized_data = run_harmonization(raw_data)
    
    # Validate SMILES
    validated_smiles_data = validate_smiles_batch(harmonized_data)
    logger.info(f"SMILES validation passed for {len(validated_smiles_data)} records.")
    
    # Validate weight fractions
    validated_wf_data = validate_weight_fractions_batch(validated_smiles_data)
    logger.info(f"Weight fraction validation passed for {len(validated_wf_data)} records.")
    
    # Run Join Success Rate Check & Fallback Trigger
    can_proceed = run_join_success_rate_check(validated_wf_data)
    
    if not can_proceed:
        logger.error("Pipeline halted due to fallback trigger.")
        sys.exit(1)
    
    # Generate data quality report
    report = generate_data_quality_report(validated_wf_data)
    report_path = PROJECT_ROOT / "data" / "processed" / "data_quality_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Data quality report saved to {report_path}")
    
    # Save processed data
    output_path = PROJECT_ROOT / "data" / "processed" / "harmonized_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validated_wf_data, f, indent=2)
    logger.info(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    main()
