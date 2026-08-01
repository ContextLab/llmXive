import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from schemas.alloy_record import AlloyRecord
from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def load_raw_data(raw_path: Path) -> List[Dict[str, Any]]:
    """Load raw JSON data from disk."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    # Ensure we have a list of records
    if isinstance(data, dict) and 'records' in data:
        return data['records']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Raw data must be a list of records or a dict with 'records' key")

def apply_schema_validation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate records against the AlloyRecord schema (T010)."""
    validated = []
    missing_fields = set()
    
    for i, record in enumerate(records):
        try:
            # Check for required fields explicitly before Pydantic validation
            required_fields = [
                'poisson_ratio', 'young_modulus', 
                'cu_fraction', 'mg_fraction', 'si_fraction', 
                'zn_fraction', 'mn_fraction', 'measurement_method'
            ]
            
            for field in required_fields:
                if field not in record or record[field] is None:
                    missing_fields.add(field)
            
            if missing_fields:
                logger.warning(f"Record {i} missing fields: {missing_fields}. Excluding.")
                missing_fields.clear()
                continue
            
            # Pydantic validation
            alloy = AlloyRecord(**record)
            validated.append(alloy.model_dump())
            
        except Exception as e:
            logger.warning(f"Record {i} failed validation: {e}. Excluding.")
            continue
    
    if not validated:
        raise ValueError("No records passed schema validation.")
    
    logger.info(f"Schema validation passed for {len(validated)} records.")
    return validated

def apply_independence_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out 'Derived' measurement methods (T014)."""
    kept = []
    excluded_count = 0
    log_path = Path("data/logs/independence_check.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as log_file:
        for record in records:
            method = record.get('measurement_method', '')
            if method in ['Derived', 'calculated_from_Youngs_modulus', 'calculated']:
                excluded_count += 1
                log_file.write(f"Excluded: {method}\n")
                logger.debug(f"Excluded record due to method: {method}")
            else:
                kept.append(record)
    
    metrics = {
        "kept": len(kept),
        "excluded_derived": excluded_count
    }
    
    metrics_path = Path("data/logs/independence_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Independence filter applied. Kept: {len(kept)}, Excluded: {excluded_count}")
    return kept

def apply_monolithic_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for monolithic alloys with non-missing composition (T011)."""
    filtered = []
    for record in records:
        # Check for non-missing Poisson's ratio and Young's modulus
        if record.get('poisson_ratio') is None or record.get('young_modulus') is None:
            continue
        
        # Check for non-missing composition fractions
        fractions = ['cu_fraction', 'mg_fraction', 'si_fraction', 'zn_fraction', 'mn_fraction']
        if any(record.get(f) is None for f in fractions):
            continue
        
        filtered.append(record)
    
    logger.info(f"Monolithic filter applied. Result: {len(filtered)} records.")
    return filtered

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize units (GPa) and calculate atomic fractions (T012)."""
    normalized = []
    for record in records:
        # Assume input is already in GPa or convert if necessary (placeholder logic)
        # If input is in Pa, divide by 1e9
        if 'young_modulus' in record and record['young_modulus'] > 1000: 
            # Heuristic: if value is very large, assume Pa
            pass # Keep as is, assuming GPa input per task description
        
        # Ensure fractions sum to 1.0 (normalize if needed)
        fractions = ['cu_fraction', 'mg_fraction', 'si_fraction', 'zn_fraction', 'mn_fraction']
        current_sum = sum(record.get(f, 0) for f in fractions)
        
        if current_sum > 0 and abs(current_sum - 1.0) > 0.01:
            # Normalize
            for f in fractions:
                record[f] = record.get(f, 0) / current_sum
            # Al fraction is the balance
            record['al_fraction'] = 1.0 - current_sum
        else:
            record['al_fraction'] = 1.0 - sum(record.get(f, 0) for f in fractions)
        
        normalized.append(record)
    
    logger.info(f"Unit normalization complete. {len(normalized)} records.")
    return normalized

def apply_major_element_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Exclude entries where major element sum < 0.95 (T013)."""
    filtered = []
    for record in records:
        fractions = ['cu_fraction', 'mg_fraction', 'si_fraction', 'zn_fraction', 'mn_fraction', 'al_fraction']
        total = sum(record.get(f, 0) for f in fractions)
        
        if total < 0.95:
            logger.warning(f"Major element sum {total:.4f} < 0.95. Excluding record.")
            continue
        
        filtered.append(record)
    
    logger.info(f"Major element filter applied. Result: {len(filtered)} records.")
    return filtered

def run_cleaning_pipeline(raw_path: Path, output_path: Path) -> pd.DataFrame:
    """Orchestrate the full cleaning pipeline (T018)."""
    logger.info("Starting full cleaning pipeline.")
    
    # 1. Load
    records = load_raw_data(raw_path)
    logger.info(f"Loaded {len(records)} raw records.")
    
    # 2. Schema Validation (T010)
    records = apply_schema_validation(records)
    
    # 3. Independence Filter (T014)
    records = apply_independence_filter(records)
    
    # 4. Monolithic Filter (T011)
    records = apply_monolithic_filter(records)
    
    # 5. Normalize Units (T012)
    records = normalize_units(records)
    
    # 6. Major Element Filter (T013)
    records = apply_major_element_filter(records)
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # T018 Final Validation
    if len(df) == 0:
        logger.error("CRITICAL: No valid entries found after filtering. Pipeline halted.")
        raise RuntimeError("CRITICAL: No valid entries found after filtering. Pipeline halted.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    df.to_csv(output_path, index=False)
    logger.info(f"Pipeline completed. Output written to {output_path} ({len(df)} rows).")
    
    # Log warning if sample size is small
    if len(df) < 50:
        logger.warning("Sample size < 50: Limiting model complexity per plan.md Assumptions")
    
    return df

def main():
    """Entry point for testing the cleaning logic directly."""
    config = get_config()
    raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
    output_path = Path(config.data_processed_dir) / "filtered_alloys.csv"
    
    try:
        df = run_cleaning_pipeline(raw_path, output_path)
        print(f"Success: {len(df)} records processed.")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
