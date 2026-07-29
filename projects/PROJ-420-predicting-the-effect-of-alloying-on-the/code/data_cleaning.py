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
    """Load raw JSON data extracted from OpenML."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from {raw_path}")
    return data

def apply_schema_validation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T010: Validate that required fields exist in the schema.
    Checks for field presence, not value validity.
    """
    required_fields = [
        'poissons_ratio', 'youngs_modulus', 
        'cu', 'mg', 'si', 'zn', 'mn'
    ]
    
    validated = []
    missing_fields_log = []
    
    for i, record in enumerate(records):
        missing = [f for f in required_fields if f not in record]
        if missing:
            missing_fields_log.append(f"Record {i}: missing fields {missing}")
            # Per T010: If required field missing in schema, raise error
            raise ValueError(f"Schema validation failed. Missing required fields: {missing}")
        validated.append(record)
    
    if missing_fields_log:
        logger.warning("Schema validation issues found (logged): " + "; ".join(missing_fields_log[:5]))
    
    logger.info(f"Schema validation passed for {len(validated)} records")
    return validated

def apply_independence_filter(records: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    T014: Filter based on measurement_method (FR-009).
    - Missing/Null: Include, log warning
    - Derived/Calculated: Exclude, log warning
    - Independent/Ultrasonic: Keep
    """
    kept = []
    excluded_derived = 0
    included_missing = 0
    
    log_path = Path(get_config().data_logs_dir) / "independence_check.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as log_file:
        for record in records:
            method = record.get('measurement_method')
            
            if method is None:
                # Missing field
                included_missing += 1
                record['measurement_source'] = 'unknown'
                kept.append(record)
                log_file.write(f"[WARNING] Missing measurement_method, assuming independent\n")
                continue
            
            method_str = str(method).lower().strip()
            
            if method_str in ['missing', 'null', '']:
                # Null value
                included_missing += 1
                record['measurement_source'] = 'unknown'
                kept.append(record)
                log_file.write(f"[WARNING] Null measurement_method, assuming independent\n")
                continue
            
            if 'derived' in method_str or 'calculated_from_youngs' in method_str:
                # Exclude derived
                excluded_derived += 1
                log_file.write(f"[EXCLUDED] Derived measurement_method: '{method}'\n")
                continue
            
            if 'ultrasonic' in method_str or 'independent' in method_str:
                # Keep independent
                record['measurement_source'] = method
                kept.append(record)
                continue
            
            # Default: if not clearly derived, keep but mark unknown if ambiguous
            record['measurement_source'] = method
            kept.append(record)
    
    metrics = {
        "kept": len(kept),
        "excluded_derived": excluded_derived,
        "included_missing": included_missing
    }
    
    metrics_path = Path(get_config().data_processed_dir) / "independence_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Independence filter: kept={metrics['kept']}, excluded_derived={metrics['excluded_derived']}, included_missing={metrics['included_missing']}")
    return kept, metrics

def apply_monolithic_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T011: Filter for monolithic alloys with non-missing values.
    """
    filtered = []
    for record in records:
        # Check for non-missing Poisson's ratio, Young's modulus, and compositions
        if record.get('poissons_ratio') is None or record.get('youngs_modulus') is None:
            continue
        
        comps = ['cu', 'mg', 'si', 'zn', 'mn']
        if any(record.get(c) is None for c in comps):
            continue
        
        filtered.append(record)
    
    logger.info(f"Monolithic filter: {len(records)} -> {len(filtered)}")
    return filtered

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T012: Normalize units (GPa) and calculate atomic fractions.
    """
    normalized = []
    for record in records:
        new_record = record.copy()
        
        # Convert Young's modulus to GPa if in MPa
        ym = new_record.get('youngs_modulus', 0)
        if ym > 1000: # Assuming MPa if > 1000
            new_record['youngs_modulus'] = ym / 1000.0
        
        # Calculate atomic fractions
        # Assuming input is atomic % or weight % that needs normalization
        # The spec says "calculate atomic fractions summing to unity"
        # We assume the input columns are atomic percentages (0-100) or fractions (0-1)
        # If they are percentages, divide by 100. If they are already fractions, ensure sum is 1.
        
        comps = ['cu', 'mg', 'si', 'zn', 'mn']
        comp_values = [new_record.get(c, 0) for c in comps]
        
        total = sum(comp_values)
        if total == 0:
            logger.warning(f"Zero composition sum for record, skipping normalization")
            continue
        
        # Normalize to sum to 1 (atomic fraction)
        for i, c in enumerate(comps):
            new_record[c] = comp_values[i] / total
        
        # Add Al balance
        new_record['al'] = 1.0 - total
        normalized.append(new_record)
    
    logger.info(f"Unit normalization complete: {len(normalized)} records")
    return normalized

def apply_major_element_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T013: Exclude entries where major element sum < 0.95.
    """
    filtered = []
    dropped_count = 0
    
    for record in records:
        # Sum of Cu, Mg, Si, Zn, Mn (already normalized atomic fractions)
        major_sum = sum(record.get(c, 0) for c in ['cu', 'mg', 'si', 'zn', 'mn'])
        
        if major_sum < 0.95:
            dropped_count += 1
            logger.warning(f"Dropped record with major element sum {major_sum:.4f} < 0.95")
            continue
        
        filtered.append(record)
    
    logger.info(f"Major element filter: {len(records)} -> {len(filtered)} (dropped {dropped_count})")
    return filtered

def run_cleaning_pipeline(raw_path: Optional[Path] = None, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    T017: Orchestrate the full cleaning pipeline.
    Order: T010 -> T014 -> T011 -> T012 -> T013
    """
    config = get_config()
    if raw_path is None:
        raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
    if output_path is None:
        output_path = Path(config.data_processed_dir) / "filtered_alloys.csv"
    
    # Ensure output directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting cleaning pipeline...")
    
    # T010: Schema Validation
    records = load_raw_data(raw_path)
    records = apply_schema_validation(records)
    
    # T014: Independence Filter
    records, metrics = apply_independence_filter(records)
    
    # T011: Monolithic Filter
    records = apply_monolithic_filter(records)
    
    # T012: Unit Normalization
    records = normalize_units(records)
    
    # T013: Major Element Filter
    records = apply_major_element_filter(records)
    
    if len(records) == 0:
        raise RuntimeError("CRITICAL: No valid entries found after cleaning. Pipeline halted.")
    
    # Convert to DataFrame and save
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Pipeline complete. Output saved to {output_path} with {len(df)} rows.")
    return df

def main():
    """CLI entry point for cleaning pipeline."""
    logger.info("Running data cleaning pipeline (T017)...")
    try:
        df = run_cleaning_pipeline()
        logger.info("Cleaning pipeline finished successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
