import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

from config import get_config
from logging_config import get_logger
from schemas.alloy_record import AlloyRecord

logger = get_logger(__name__)

def load_raw_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load raw JSON data from a file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of records in {data_path}, got {type(data)}")
    
    return data

def verify_measurement_independence(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Verify computational independence of Poisson's ratio measurements.
    
    Excludes entries where:
    - measurement_method is 'calculated', 'derived', 'derived_from_Youngs_modulus', or missing
    - If method is missing but Young's and Bulk moduli are available, checks if Poisson's ratio
      is derived (within 1% tolerance) and excludes if so
    """
    filtered_records = []
    excluded_count = 0
    
    for i, record in enumerate(records):
        measurement_method = record.get('measurement_method')
        poisson_ratio = record.get('poissons_ratio')
        youngs_modulus = record.get('youngs_modulus_gpa')
        bulk_modulus = record.get('bulk_modulus_gpa')
        
        # Check 1: Explicit method validation
        if measurement_method in ['calculated', 'derived', 'derived_from_Youngs_modulus']:
            logger.warning(f"Record {i}: Excluded due to measurement method '{measurement_method}'")
            excluded_count += 1
            continue
        
        if measurement_method is None or measurement_method == 'unknown':
            # Check 2: Computational independence check
            if youngs_modulus is not None and bulk_modulus is not None and poisson_ratio is not None:
                # Calculate derived Poisson's ratio: ν = (3K - 2G) / (6K + 2G)
                # But we need G (Shear modulus). G = 3K(1-2ν) / (2(1+ν)) is circular.
                # Alternative: G = E / (2(1+ν)) -> derived ν from E and K?
                # Actually, we can derive ν from E and K if we assume isotropic:
                # K = E / (3(1-2ν)) -> 3K(1-2ν) = E -> 1-2ν = E/(3K) -> 2ν = 1 - E/(3K) -> ν = (1 - E/(3K))/2
                # But this is only valid if we assume the material is isotropic and we have E and K.
                # However, the task says: "if measurement_method is missing but Young's Modulus and Bulk Modulus are available, calculate derived Poisson's ratio"
                
                try:
                    # Derived ν = (3K - E) / (6K)  [from K = E / (3(1-2ν)) => 3K(1-2ν) = E => 1-2ν = E/(3K) => 2ν = 1 - E/(3K) => ν = 0.5 * (1 - E/(3K))]
                    # Let's use the standard relation: ν = (3K - 2G) / (6K + 2G) but we don't have G.
                    # From E and K: ν = (3K - E) / (6K) ? Let's check:
                    # K = E / (3(1-2ν)) => 3K(1-2ν) = E => 1-2ν = E/(3K) => 2ν = 1 - E/(3K) => ν = (1 - E/(3K))/2 = (3K - E)/(6K)
                    derived_nu = (3 * bulk_modulus - youngs_modulus) / (6 * bulk_modulus)
                    
                    reported_nu = float(poisson_ratio)
                    relative_diff = abs(derived_nu - reported_nu) / abs(reported_nu) if reported_nu != 0 else abs(derived_nu - reported_nu)
                    
                    if relative_diff <= 0.01:  # 1% tolerance
                        logger.warning(f"Record {i}: Excluded as dependent (derived Poisson's ratio matches within 1%: {relative_diff:.4f})")
                        excluded_count += 1
                        continue
                except (ZeroDivisionError, TypeError, ValueError) as e:
                    logger.warning(f"Record {i}: Could not compute derived Poisson's ratio, excluding: {e}")
                    excluded_count += 1
                    continue
            else:
                # Missing method and missing required moduli for derivation check
                logger.warning(f"Record {i}: Excluded due to missing measurement_method and insufficient data for independence check")
                excluded_count += 1
                continue
        
        filtered_records.append(record)
    
    logger.info(f"Measurement independence verification: {excluded_count} records excluded, {len(filtered_records)} retained")
    return filtered_records

def filter_monolithic_alloys(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter to monolithic aluminum alloys with non-missing required fields.
    
    Requires:
    - poissons_ratio
    - youngs_modulus_gpa
    - Cu, Mg, Si, Zn, Mn composition (atomic fractions)
    """
    filtered = []
    excluded_count = 0
    required_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    for i, record in enumerate(records):
        # Check required properties
        if record.get('poissons_ratio') is None:
            logger.debug(f"Record {i}: Excluded - missing poissons_ratio")
            excluded_count += 1
            continue
        
        if record.get('youngs_modulus_gpa') is None:
            logger.debug(f"Record {i}: Excluded - missing youngs_modulus_gpa")
            excluded_count += 1
            continue
        
        # Check required elemental compositions
        composition = record.get('composition', {})
        missing_elements = []
        for elem in required_elements:
            if elem not in composition or composition[elem] is None:
                missing_elements.append(elem)
        
        if missing_elements:
            logger.debug(f"Record {i}: Excluded - missing composition for {missing_elements}")
            excluded_count += 1
            continue
        
        filtered.append(record)
    
    logger.info(f"Monolithic alloy filtering: {excluded_count} records excluded, {len(filtered)} retained")
    return filtered

def check_major_element_sum(records: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Exclude entries where the sum of major element atomic fractions is below the threshold.
    
    Major elements are defined as Al plus the alloying elements Cu, Mg, Si, Zn, Mn.
    The sum should be >= threshold (default 0.95) for the entry to be retained.
    
    Args:
        records: List of alloy records with composition data
        threshold: Minimum sum of major element fractions (default 0.95)
    
    Returns:
        Filtered list of records meeting the threshold
    """
    filtered_records = []
    excluded_count = 0
    major_elements = ['Al', 'Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    for i, record in enumerate(records):
        composition = record.get('composition', {})
        
        # Calculate sum of major element atomic fractions
        major_sum = 0.0
        for elem in major_elements:
            if elem in composition and composition[elem] is not None:
                major_sum += float(composition[elem])
        
        # Check against threshold
        if major_sum < threshold:
            logger.warning(f"Record {i}: Excluded - major element sum ({major_sum:.4f}) < threshold ({threshold})")
            excluded_count += 1
            continue
        
        filtered_records.append(record)
    
    logger.info(f"Major element sum check: {excluded_count} records excluded, {len(filtered_records)} retained (threshold={threshold})")
    return filtered_records

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize units: convert elastic constants to GPa, calculate atomic fractions summing to unity.
    
    - Elastic constants (Young's modulus, Bulk modulus) converted to GPa if in MPa or other units
    - Atomic fractions recalculated to sum to 1.0 if they don't already
    """
    normalized_records = []
    
    for i, record in enumerate(records):
        normalized_record = record.copy()
        
        # Normalize elastic constants to GPa
        if 'youngs_modulus' in normalized_record:
            val = normalized_record['youngs_modulus']
            unit = normalized_record.get('youngs_modulus_unit', 'GPa')
            if unit == 'MPa':
                normalized_record['youngs_modulus_gpa'] = val / 1000.0
            elif unit == 'GPa':
                normalized_record['youngs_modulus_gpa'] = val
            else:
                logger.warning(f"Record {i}: Unknown unit '{unit}' for Young's modulus, assuming GPa")
                normalized_record['youngs_modulus_gpa'] = val
        
        if 'bulk_modulus' in normalized_record:
            val = normalized_record['bulk_modulus']
            unit = normalized_record.get('bulk_modulus_unit', 'GPa')
            if unit == 'MPa':
                normalized_record['bulk_modulus_gpa'] = val / 1000.0
            elif unit == 'GPa':
                normalized_record['bulk_modulus_gpa'] = val
            else:
                logger.warning(f"Record {i}: Unknown unit '{unit}' for Bulk modulus, assuming GPa")
                normalized_record['bulk_modulus_gpa'] = val
        
        # Normalize atomic fractions to sum to 1.0
        if 'composition' in normalized_record:
            composition = normalized_record['composition']
            total = sum(v for v in composition.values() if v is not None)
            
            if total > 0 and abs(total - 1.0) > 0.01:  # If not already normalized
                logger.debug(f"Record {i}: Recalculating atomic fractions (original sum: {total:.4f})")
                normalized_composition = {}
                for elem, val in composition.items():
                    if val is not None:
                        normalized_composition[elem] = val / total
                    else:
                        normalized_composition[elem] = None
                normalized_record['composition'] = normalized_composition
        
        normalized_records.append(normalized_record)
    
    logger.info(f"Unit normalization completed for {len(normalized_records)} records")
    return normalized_records

def apply_ilr_transformation(records: List[Dict[str, Any]], elements: List[str] = None) -> List[Dict[str, Any]]:
    """
    Apply Isometric Log-Ratio (ILR) transformation to compositional data.
    
    Uses the `compositional` package to transform atomic fractions of specified elements
    into ILR coordinates for use in regression models.
    
    Args:
        records: List of alloy records with composition data
        elements: List of element keys to transform (default: ['Cu', 'Mg', 'Si', 'Zn', 'Mn'])
    
    Returns:
        Records with ILR-transformed features added
    """
    if elements is None:
        elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    try:
        import compositional
    except ImportError:
        logger.error("compositional package not installed. Install with: pip install compositional")
        raise
    
    transformed_records = []
    
    for i, record in enumerate(records):
        transformed_record = record.copy()
        composition = record.get('composition', {})
        
        # Extract values for specified elements
        comp_values = []
        for elem in elements:
            val = composition.get(elem)
            if val is None or val <= 0:
                # Handle zero/negative values by replacing with small positive number
                val = 1e-10
            comp_values.append(val)
        
        # Create compositional array
        comp_array = np.array([comp_values])
        
        # Apply ILR transformation
        try:
            ilr_coords = compositional.ilr(comp_array)
            # Store ILR coordinates as separate features
            for j, coord in enumerate(ilr_coords[0]):
                transformed_record[f'ilr_{elements[j]}'] = float(coord)
        except Exception as e:
            logger.warning(f"Record {i}: ILR transformation failed: {e}")
            # Keep original record without ILR features
        
        transformed_records.append(transformed_record)
    
    logger.info(f"ILR transformation applied to {len(transformed_records)} records")
    return transformed_records

def clean_data(input_path: Path, output_path: Path) -> None:
    """
    Main data cleaning pipeline: load, verify independence, filter, normalize, and save.
    
    Pipeline steps:
    1. Load raw data from input_path
    2. Verify measurement independence (exclude calculated/derived values)
    3. Filter to monolithic alloys with required fields
    4. Check major element sum >= 0.95
    5. Normalize units (elastic constants to GPa, atomic fractions to sum to 1)
    6. Save cleaned data to output_path
    """
    logger.info(f"Starting data cleaning pipeline: {input_path} -> {output_path}")
    
    # Load raw data
    raw_data = load_raw_data(input_path)
    logger.info(f"Loaded {len(raw_data)} raw records")
    
    # Step 1: Verify measurement independence
    independent_data = verify_measurement_independence(raw_data)
    
    # Step 2: Filter monolithic alloys
    monolithic_data = filter_monolithic_alloys(independent_data)
    
    # Step 3: Check major element sum (T013)
    major_element_data = check_major_element_sum(monolithic_data, threshold=0.95)
    
    # Step 4: Normalize units
    normalized_data = normalize_units(major_element_data)
    
    # Save cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(normalized_data, f, indent=2)
    
    logger.info(f"Cleaned data saved to {output_path} ({len(normalized_data)} records)")

def run_cleaning_pipeline(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Run the full data cleaning pipeline using configuration.
    
    Reads configuration for input/output paths and runs clean_data.
    """
    cfg = get_config() if config is None else config
    
    # Determine input files (could be multiple sources)
    input_files = [
        cfg.get('data', {}).get('raw_dir', 'data/raw') / 'mp_aluminum.json',
        cfg.get('data', {}).get('raw_dir', 'data/raw') / 'nist_aluminum.json'
    ]
    
    output_file = cfg.get('data', {}).get('processed_dir', 'data/processed') / 'filtered_alloys.json'
    
    # Process each input file
    all_cleaned_data = []
    for input_file in input_files:
        if input_file.exists():
            temp_output = Path(str(output_file).replace('.json', f'_{input_file.stem}.json'))
            clean_data(input_file, temp_output)
            with open(temp_output, 'r') as f:
                all_cleaned_data.extend(json.load(f))
            temp_output.unlink()  # Remove intermediate file
        else:
            logger.warning(f"Input file not found: {input_file}")
    
    # Combine and save final output
    if all_cleaned_data:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_cleaned_data, f, indent=2)
        logger.info(f"Final cleaned data saved to {output_file} ({len(all_cleaned_data)} records)")
    else:
        logger.error("No data available for cleaning pipeline")
        raise ValueError("No input data found for cleaning pipeline")

def main():
    """Entry point for data cleaning script."""
    config = get_config()
    run_cleaning_pipeline(config)

if __name__ == "__main__":
    main()