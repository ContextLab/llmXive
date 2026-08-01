import logging
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import get_config
from logging_config import get_logger
from schemas.alloy_record import AlloyRecord

logger = get_logger(__name__)

def load_raw_data(raw_path: Path) -> List[Dict[str, Any]]:
    """Load raw JSON data from disk."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_path}")
    
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        raise ValueError(f"Unexpected data format in {raw_path}")

def apply_schema_validation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate records against AlloyRecord schema (T010)."""
    valid_records = []
    required_fields = ['poisson_ratio', 'young_modulus', 'composition', 'measurement_method']
    
    for i, record in enumerate(records):
        missing = [f for f in required_fields if f not in record or record[f] is None]
        if missing:
            logger.warning(f"Record {i} missing required fields: {missing}, skipping")
            continue
        
        # Validate measurement_method presence and non-null (T010)
        if record['measurement_method'] is None:
            logger.warning(f"Record {i} has null measurement_method, skipping")
            continue
        
        valid_records.append(record)
    
    logger.info(f"Schema validation passed for {len(valid_records)} of {len(records)} records")
    return valid_records

def apply_independence_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out derived measurement methods (T014)."""
    kept = []
    excluded_count = 0
    
    derived_values = {'Derived', 'calculated_from_Youngs_modulus', 'calculated'}
    allowed_values = {'Ultrasonic', 'Independent', 'Direct Measurement'}
    
    # Ensure log directory exists
    log_path = Path("data/logs")
    log_path.mkdir(parents=True, exist_ok=True)
    independence_log = log_path / "independence_check.log"
    
    with open(independence_log, 'w') as log_file:
        for record in records:
            method = record.get('measurement_method', '')
            
            if method in derived_values:
                excluded_count += 1
                log_file.write(f"Excluded: Derived measurement_method '{method}'\n")
                continue
            elif method in allowed_values or method not in derived_values:
                # Keep if not explicitly derived (allows for other valid methods)
                kept.append(record)
            else:
                # Unknown method - log and keep for now, or exclude?
                # Per spec: only exclude specific derived values
                kept.append(record)
    
    metrics = {
        "kept": len(kept),
        "excluded_derived": excluded_count
    }
    
    metrics_path = Path("data/logs/independence_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Independence filter: kept {len(kept)}, excluded {excluded_count}")
    return kept

def apply_monolithic_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter for monolithic alloys with required properties (T011)."""
    filtered = []
    required_elements = {'Cu', 'Mg', 'Si', 'Zn', 'Mn'}
    
    for record in records:
        if record.get('poisson_ratio') is None:
            continue
        if record.get('young_modulus') is None:
            continue
        
        composition = record.get('composition', {})
        if not isinstance(composition, dict):
            continue
        
        # Check if all required elements are present (even if 0)
        if not all(elem in composition for elem in required_elements):
            continue
        
        filtered.append(record)
    
    logger.info(f"Monolithic filter: {len(filtered)} records remaining")
    return filtered

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize units to GPa and atomic fractions (T012)."""
    normalized = []
    
    for record in records:
        new_record = record.copy()
        
        # Convert Young's modulus to GPa if needed
        ym = new_record.get('young_modulus', 0)
        ym_unit = new_record.get('young_modulus_unit', 'GPa')
        if ym_unit == 'MPa':
            new_record['young_modulus'] = ym / 1000.0
            new_record['young_modulus_unit'] = 'GPa'
        
        # Normalize composition to atomic fractions
        composition = new_record.get('composition', {})
        total = sum(composition.values()) if composition else 0
        
        if total > 0:
            new_composition = {k: v / total for k, v in composition.items()}
            new_record['composition'] = new_composition
        else:
            new_record['composition'] = {k: 0.0 for k in composition.keys()}
        
        normalized.append(new_record)
    
    logger.info(f"Unit normalization completed for {len(normalized)} records")
    return normalized

def apply_major_element_filter(records: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Exclude entries where major element sum < threshold (T013)."""
    filtered = []
    major_elements = {'Al', 'Cu', 'Mg', 'Si', 'Zn', 'Mn'}
    
    for record in records:
        composition = record.get('composition', {})
        major_sum = sum(composition.get(elem, 0) for elem in major_elements)
        
        if major_sum < threshold:
            logger.warning(f"Dropping record: major element sum {major_sum:.4f} < {threshold}")
            continue
        
        filtered.append(record)
    
    logger.info(f"Major element filter: {len(filtered)} records remaining")
    return filtered

def run_cleaning_pipeline(raw_path: Path, output_path: Path) -> pd.DataFrame:
    """Run the full cleaning pipeline (T010, T014, T011, T012, T013, T018)."""
    
    # Step 1: Load raw data
    logger.info("Loading raw data...")
    records = load_raw_data(raw_path)
    
    # Step 2: Schema validation (T010)
    logger.info("Applying schema validation...")
    records = apply_schema_validation(records)
    
    # Step 3: Independence filter (T014)
    logger.info("Applying independence filter...")
    records = apply_independence_filter(records)
    
    # Step 4: Monolithic filter (T011)
    logger.info("Applying monolithic filter...")
    records = apply_monolithic_filter(records)
    
    # Step 5: Normalize units (T012)
    logger.info("Normalizing units...")
    records = normalize_units(records)
    
    # Step 6: Major element filter (T013)
    logger.info("Applying major element filter...")
    records = apply_major_element_filter(records)
    
    # Step 7: Final validation and output (T018)
    logger.info("Performing final validation...")
    
    if len(records) == 0:
        logger.error("CRITICAL: No valid entries found after filtering. Pipeline halted.")
        raise RuntimeError("CRITICAL: No valid entries found after filtering. Pipeline halted.")
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Handle small sample size warning (T018)
    if len(df) < 50:
        logger.warning(f"Sample size < 50: Limiting model complexity per plan.md Assumptions")
        # Note: max_depth=5 is handled in modeling.py, not here
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as Parquet (T018 requirement)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Pipeline completed. Output written to: {output_path}")
    logger.info(f"Total rows: {len(df)}")
    
    # Verify file creation
    if not output_path.exists():
        raise RuntimeError(f"Failed to create output file: {output_path}")
    
    return df

def main():
    """Main entry point for direct execution."""
    config = get_config()
    raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
    output_path = Path(config.data_processed_dir) / "alloys_clean.parquet"
    
    try:
        df = run_cleaning_pipeline(raw_path, output_path)
        print(f"Success: {len(df)} records processed")
    except Exception as e:
        print(f"Error: {e}")
        raise
