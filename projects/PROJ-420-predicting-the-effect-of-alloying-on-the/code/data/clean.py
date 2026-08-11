"""Data cleaning module for alloy records."""
import sys
import logging
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from compositional import ilr, ilr_inv
from periodictable import elements
from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
logger = setup_logging()
if logger is None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def setup_paths():
    """Setup data paths."""
    config = get_config()
    return {
        'raw_dir': config.data_raw_dir,
        'processed_dir': config.data_processed_dir,
        'logs_dir': config.data_logs_dir,
        'results_dir': config.results_dir,
        'models_dir': config.models_dir
    }

def log_exclusion(step: str, count: int, reason: str, log_file: Optional[Path] = None):
    """
    Log exclusion records to a CSV file.
    
    Args:
        step: The processing step where exclusion occurred
        count: Number of records excluded
        reason: Reason for exclusion
        log_file: Path to the log file (optional, uses default if None)
    """
    if log_file is None:
        config = get_config()
        log_file = config.data_logs_dir / "exclusion_log.txt"
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to CSV file
    file_exists = log_file.exists() and log_file.stat().st_size > 0
    
    with open(log_file, 'a') as f:
        if not file_exists:
            f.write("step,count,reason\n")
        f.write(f"{step},{count},{reason}\n")
    
    logger.info(f"Logged exclusion: step={step}, count={count}, reason={reason}")

def validate_raw_record_fields(record: Dict[str, Any]) -> bool:
    """
    Validate that a raw record contains all required fields.
    
    Required fields:
    - poisson_ratio
    - young_modulus
    - composition (with at least Cu, Mg, Si, Zn, Mn)
    - measurement_method (or can be inferred)
    
    Returns:
        True if all required fields are present, False otherwise
    """
    required_fields = ['poisson_ratio', 'young_modulus', 'composition']
    
    for field in required_fields:
        if field not in record or record[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Check composition has required elements
    composition = record.get('composition', {})
    required_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    for element in required_elements:
        if element not in composition:
            logger.warning(f"Missing required element in composition: {element}")
            return False
    
    return True

def normalize_raw_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw record data to standard format.
    
    Handles field name differences (e.g., 'nu' -> 'poisson_ratio')
    and ensures consistent structure.
    """
    normalized = record.copy()
    
    # Map field names
    field_mappings = {
        'nu': 'poisson_ratio',
        'youngs_modulus': 'young_modulus',
        'E': 'young_modulus',
        'elements': 'composition'
    }
    
    for old_name, new_name in field_mappings.items():
        if old_name in normalized and new_name not in normalized:
            normalized[new_name] = normalized.pop(old_name)
    
    return normalized

def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for monolithic alloys only.
    
    Definition: alloy_type == 'monolithic' OR is_composite == False OR composite_fraction == 0.0
    
    Priority: Check alloy_type first, then is_composite, then composite_fraction.
    If neither field exists, the record is excluded.
    """
    mask = pd.Series([False] * len(df), index=df.index)
    
    # Check alloy_type
    if 'alloy_type' in df.columns:
        mask |= (df['alloy_type'] == 'monolithic')
    
    # Check is_composite
    if 'is_composite' in df.columns:
        mask |= (df['is_composite'] == False)
    
    # Check composite_fraction
    if 'composite_fraction' in df.columns:
        mask |= (df['composite_fraction'] == 0.0)
    
    # If no filter columns exist, exclude all
    if not mask.any():
        logger.warning("No monolithic filter columns found, excluding all records")
        return pd.DataFrame()
    
    filtered_df = df[mask].copy()
    excluded_count = len(df) - len(filtered_df)
    
    if excluded_count > 0:
        log_exclusion("monolithic_filter", excluded_count, "Not monolithic alloy")
    
    return filtered_df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units for young_modulus and composition.
    
    - young_modulus: Convert from MPa to GPa if needed
    - composition: Convert from wt% to at% using atomic weights
    """
    normalized_df = df.copy()
    
    # Convert young_modulus to GPa if in MPa (assume values > 1000 are in MPa)
    if 'young_modulus' in normalized_df.columns:
        normalized_df['young_modulus'] = np.where(
            normalized_df['young_modulus'] > 1000,
            normalized_df['young_modulus'] / 1000.0,
            normalized_df['young_modulus']
        )
    
    # Convert composition from wt% to at%
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    al_atomic_weight = elements.Al.mass
    
    if 'composition' in normalized_df.columns:
        def convert_wt_to_at(composition_dict):
            """Convert weight percent to atomic percent."""
            if not isinstance(composition_dict, dict):
                return composition_dict
            
            # Calculate atomic fractions
            atomic_fractions = {}
            total_atoms = 0.0
            
            # First, calculate atoms for each element
            for element, wt_percent in composition_dict.items():
                if element in major_elements or element == 'Al':
                  atomic_weight = getattr(elements, element, None)
                  if atomic_weight:
                      atomic_weight = atomic_weight.mass
                  else:
                      # Fallback atomic weights
                      atomic_weights = {'Al': 26.98, 'Cu': 63.55, 'Mg': 24.31, 
                                    'Si': 28.09, 'Zn': 65.38, 'Mn': 54.94}
                      atomic_weight = atomic_weights.get(element, 27.0)
                  
                  atoms = wt_percent / atomic_weight
                  atomic_fractions[element] = atoms
                  total_atoms += atoms
            
            # Normalize to atomic fractions
            if total_atoms > 0:
                for element in atomic_fractions:
                    atomic_fractions[element] /= total_atoms
            
            return atomic_fractions
        
        normalized_df['composition'] = normalized_df['composition'].apply(convert_wt_to_at)
    
    return normalized_df

def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out entries where major element sum < 0.95.
    
    Calculation: major_sum = sum(Cu, Mg, Si, Zn, Mn) in atomic fractions
    Al balance = 1.0 - major_sum
    If major_sum < 0.95, exclude row with log warning.
    """
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    mask = pd.Series([True] * len(df), index=df.index)
    
    excluded_count = 0
    
    for idx, row in df.iterrows():
        composition = row.get('composition', {})
        if not isinstance(composition, dict):
            mask[idx] = False
            excluded_count += 1
            continue
        
        major_sum = sum(composition.get(elem, 0.0) for elem in major_elements)
        
        if major_sum < 0.95:
            mask[idx] = False
            excluded_count += 1
    
    filtered_df = df[mask].copy()
    
    if excluded_count > 0:
        log_exclusion("major_element_filter", excluded_count, "Major element sum < 0.95")
    
    return filtered_df

def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for records with valid measurement_method.
    
    If measurement_method is missing, attempt to infer from source metadata.
    If inference is impossible, EXCLUDE the record immediately.
    
    Regex: Use VALID_MEASUREMENT_METHODS from config
    """
    config = get_config()
    valid_method_pattern = re.compile(config.VALID_MEASUREMENT_METHODS, re.IGNORECASE)
    
    mask = pd.Series([True] * len(df), index=df.index)
    excluded_count = 0
    
    for idx, row in df.iterrows():
        method = row.get('measurement_method', None)
        
        if method is None or pd.isna(method):
            # Attempt to infer from source
            source = row.get('source', '').lower()
            inferred = False
            
            # Heuristic inference based on source
            if 'nist' in source.lower():
                # NIST typically uses ultrasonic methods
                method = 'Ultrasonic'
                inferred = True
            elif 'materialsproject' in source.lower():
                # Materials Project typically uses DFT calculations
                method = 'Direct'
                inferred = True
            
            if not inferred:
                # Cannot infer, exclude record
                mask[idx] = False
                excluded_count += 1
                log_exclusion("independence_filter", 1, "inference_failed")
                continue
        
        # Check if method matches valid pattern
        if not valid_method_pattern.search(str(method)):
            mask[idx] = False
            excluded_count += 1
            log_exclusion("independence_filter", 1, f"invalid_method:{method}")
    
    filtered_df = df[mask].copy()
    
    return filtered_df

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ILR (Isometric Log-Ratio) transformation to compositional data.
    
    Uses fixed order ['Cu', 'Mg', 'Si', 'Zn', 'Mn'] for reproducibility.
    """
    transformed_df = df.copy()
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    def apply_ilr_to_composition(composition_dict):
        """Apply ILR transformation to a single composition."""
        if not isinstance(composition_dict, dict):
            return composition_dict
        
        # Extract values in fixed order
        values = [composition_dict.get(elem, 0.0) for elem in major_elements]
        
        # Ensure all values are non-negative and sum to 1
        values = [max(0.0, v) for v in values]
        total = sum(values)
        if total > 0:
            values = [v / total for v in values]
        else:
            # Fallback if all zeros
            values = [0.2] * 5
        
        try:
            # Apply ILR transformation
            ilr_result = ilr(np.array(values).reshape(1, -1))
            return {f'ilr_{i}': float(ilr_result[0, i]) for i in range(5)}
        except Exception as e:
            logger.warning(f"ILR transformation failed: {e}")
            return {f'ilr_{i}': 0.0 for i in range(5)}
    
    # Apply transformation to each row
    ilr_columns = transformed_df['composition'].apply(apply_ilr_to_composition)
    
    # Expand ILR columns
    for i in range(5):
        transformed_df[f'ilr_{i}'] = ilr_columns.apply(lambda x: x.get(f'ilr_{i}', 0.0))
    
    return transformed_df

def run_cleaning_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None):
    """
    Run the full data cleaning pipeline.
    
    Steps:
    1. Load raw data
    2. Validate raw record fields
    3. Normalize raw data
    4. Apply monolithic filter
    5. Normalize units
    6. Apply major element filter
    7. Apply independence filter
    8. Apply ILR transformation
    9. Save cleaned data
    
    Args:
        input_path: Path to raw data file
        output_path: Path to save cleaned data
    """
    config = get_config()
    
    if input_path is None:
        input_path = config.data_raw_dir / "alloys_raw.json"
    
    if output_path is None:
        output_path = config.data_processed_dir / "alloys_clean.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting cleaning pipeline from {input_path}")
    
    # Load raw data
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            raw_data = json.load(f)
        df = pd.DataFrame(raw_data)
    elif input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(df)} raw records")
    
    # Validate and normalize
    valid_records = []
    for idx, row in df.iterrows():
        record = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
        normalized = normalize_raw_data(record)
        if validate_raw_record_fields(normalized):
            valid_records.append(normalized)
        else:
            log_exclusion("validation", 1, "missing_required_fields")
    
    df = pd.DataFrame(valid_records)
    logger.info(f"After validation: {len(df)} records")
    
    # Apply filters
    df = apply_monolithic_filter(df)
    logger.info(f"After monolithic filter: {len(df)} records")
    
    df = normalize_units(df)
    logger.info(f"After unit normalization: {len(df)} records")
    
    df = apply_major_element_filter(df)
    logger.info(f"After major element filter: {len(df)} records")
    
    df = apply_independence_filter(df)
    logger.info(f"After independence filter: {len(df)} records")
    
    # Apply ILR transformation
    df = apply_ilr_transformation(df)
    logger.info(f"After ILR transformation: {len(df)} records")
    
    # Final validation
    if len(df) < 50:
        error_msg = f"Insufficient data after filtering (<50 entries): {len(df)}"
        logger.error(error_msg)
        log_exclusion("final_validation", 0, error_msg)
        raise ValueError(error_msg)
    
    # Save cleaned data
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} cleaned records to {output_path}")
    
    # Log final exclusion summary
    exclusion_log_path = config.data_logs_dir / "exclusion_log.txt"
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            lines = f.readlines()
        logger.info(f"Exclusion log has {len(lines)} entries")
    
    return df

def main():
    """Main entry point for data cleaning."""
    parser = argparse.ArgumentParser(description="Clean alloy data")
    parser.add_argument('--input', type=str, help='Input data file path')
    parser.add_argument('--output', type=str, help='Output data file path')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    try:
        run_cleaning_pipeline(input_path, output_path)
        logger.info("Data cleaning completed successfully")
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        raise

if __name__ == "__main__":
    main()
