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

def load_raw_data(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load raw JSON files from the raw data directory.
    Expects files like 'mp_aluminum.json' and 'nist_aluminum.json'.
    """
    records = []
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return records

    for json_file in raw_dir.glob("*.json"):
        logger.info(f"Loading raw data from {json_file}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    records.extend(data)
                elif isinstance(data, dict):
                    # Handle cases where data is wrapped in a key
                    records.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON in {json_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading {json_file}: {e}")

    logger.info(f"Loaded {len(records)} total raw records.")
    return records

def verify_measurement_independence(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out records where Poisson's ratio is not computationally independent.
    Excludes entries where:
    - measurement_method is 'calculated', 'derived', 'derived_from_Youngs_modulus', or missing.
    - If method is missing but Young's and Bulk modulus are present, check for derivation.
    """
    independent_records = []
    excluded_count = 0

    for record in records:
        method = record.get('measurement_method', None)
        poiss = record.get('poissons_ratio', None)
        youngs = record.get('youngs_modulus', None)
        bulk = record.get('bulk_modulus', None)

        # Check for missing or invalid method
        if method is None or method in ['calculated', 'derived', 'derived_from_Youngs_modulus', 'unknown', '']:
            logger.debug(f"Excluding record: missing or invalid measurement_method. Record: {record.get('material_id', 'N/A')}")
            excluded_count += 1
            continue

        # If method is present but we have Young's and Bulk, check for derivation
        if youngs is not None and bulk is not None and poiss is not None:
            # Poisson's ratio derived from Young's (E) and Bulk (K) is:
            # nu = (3K - E) / (6K)  =>  E = 3K(1 - 2nu) => nu = 0.5 - E/(6K)
            # Alternatively, standard relation: E = 2G(1+nu) and K = E / (3(1-2nu))
            # Derived nu from E and K: nu = (3K - E) / (6K)
            try:
                derived_nu = (3 * bulk - youngs) / (6 * bulk)
                if abs(derived_nu - poiss) / (poiss + 1e-9) < 0.01: # 1% tolerance
                    logger.warning(f"Excluding record: Poisson's ratio appears derived from E and K. Material ID: {record.get('material_id', 'N/A')}, Method: {method}")
                    excluded_count += 1
                    continue
            except ZeroDivisionError:
                logger.warning(f"Excluding record: Zero division in derived check. Material ID: {record.get('material_id', 'N/A')}")
                excluded_count += 1
                continue

        independent_records.append(record)

    logger.info(f"Measurement independence check complete. Excluded {excluded_count} records. Kept {len(independent_records)}.")
    return independent_records

def filter_monolithic_alloys(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter for monolithic alloys with:
    - Non-missing Poisson's ratio, Young's modulus.
    - Non-missing composition for Cu, Mg, Si, Zn, Mn.
    """
    filtered = []
    excluded_count = 0
    required_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']

    for record in records:
        # Check property presence
        if record.get('poissons_ratio') is None or record.get('youngs_modulus') is None:
            excluded_count += 1
            continue

        # Check composition presence
        composition = record.get('composition', {})
        missing_elements = False
        for elem in required_elements:
            if composition.get(elem) is None:
                missing_elements = True
                break

        if missing_elements:
            excluded_count += 1
            continue

        filtered.append(record)

    logger.info(f"Monolithic alloy filter complete. Excluded {excluded_count} records. Kept {len(filtered)}.")
    return filtered

def check_major_element_sum(records: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Implement exclusion logic for entries where the sum of major elemental fractions < threshold.
    Logs a warning and drops the row.
    """
    valid_records = []
    dropped_count = 0

    for record in records:
        composition = record.get('composition', {})
        # Sum the atomic fractions of the specified major elements: Cu, Mg, Si, Zn, Mn
        # We assume the composition dict contains these keys with float values.
        major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
        current_sum = 0.0
        for elem in major_elements:
            val = composition.get(elem)
            if val is not None:
                current_sum += float(val)

        if current_sum < threshold:
            logger.warning(f"Dropping record due to major element sum < {threshold}. Material ID: {record.get('material_id', 'N/A')}, Sum: {current_sum:.4f}")
            dropped_count += 1
            continue

        valid_records.append(record)

    logger.info(f"Major element sum check complete. Dropped {dropped_count} records. Kept {len(valid_records)}.")
    return valid_records

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize units:
    - Convert elastic constants to GPa (assuming input might be in MPa or other units, but spec implies standardization).
      *Assumption*: Input from MP is often in GPa, but we ensure consistency.
      If the source provides MPa, we convert. For this task, we assume the input is in GPa as per typical MP API,
      but we add a check or conversion logic if a unit field exists.
      *Refinement*: The task asks to convert to GPa. We will assume input is in GPa if not specified, or convert if 'units' field exists.
      However, to be robust, we will check for a 'units' field or standard conversion factors if the magnitude suggests MPa.
      *Simpler approach per task*: Ensure values are treated as GPa. If the raw data has a unit field, convert.
      If the raw data is from MP, it's usually GPa. We will just ensure the field exists and is numeric.
      *Correction*: The task explicitly says "convert elastic constants to GPa".
      We will assume the input is in GPa. If the source provides MPa (values > 1000 for typical metals), we divide by 1000.
      Aluminum Young's Modulus is ~70 GPa (70,000 MPa). If value > 1000, assume MPa.
    - Calculate atomic fractions summing to unity.
    """
    normalized = []

    for record in records:
        youngs = record.get('youngs_modulus')
        bulk = record.get('bulk_modulus')
        poiss = record.get('poissons_ratio')
        composition = record.get('composition', {})

        # Unit conversion for elastic constants
        # Heuristic: If Young's Modulus > 1000, assume MPa and convert to GPa.
        if youngs is not None:
            if youngs > 1000:
                record['youngs_modulus'] = youngs / 1000.0
                logger.debug(f"Converted Young's Modulus from MPa to GPa for {record.get('material_id')}")
            # Else assume GPa

        if bulk is not None:
            if bulk > 1000:
                record['bulk_modulus'] = bulk / 1000.0
                logger.debug(f"Converted Bulk Modulus from MPa to GPa for {record.get('material_id')}")

        # Normalize composition to atomic fractions summing to 1.0
        # Sum all provided composition values
        total_sum = sum(float(v) for v in composition.values() if v is not None)
        if total_sum > 0:
            new_composition = {}
            for k, v in composition.items():
                if v is not None:
                    new_composition[k] = float(v) / total_sum
                else:
                    new_composition[k] = 0.0
            record['composition'] = new_composition
        else:
            logger.warning(f"Zero total composition sum for {record.get('material_id')}, skipping normalization.")

        normalized.append(record)

    logger.info(f"Unit normalization complete. Processed {len(normalized)} records.")
    return normalized

def apply_ilr_transformation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply Isometric Log-Ratio (ILR) transformation to compositional data.
    Uses the 'compositional' package as per plan.md.
    """
    try:
        import compositional
    except ImportError:
        logger.error("compositional package not found. Install with: pip install compositional")
        raise

    ilr_records = []
    elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']

    for record in records:
        composition = record.get('composition', {})
        # Extract values in order
        vals = [composition.get(e, 0.0) for e in elements]
        vals = np.array(vals)

        # Avoid zero or negative values for log
        # Add small epsilon if necessary, though normalization should handle zeros by setting to 0?
        # compositional package usually requires strictly positive.
        # We will filter out records with zero in any of the target elements if the package requires it.
        if np.any(vals <= 0):
            # If any element is 0, we cannot take log.
            # Strategy: Replace 0 with a small value (e.g., 1e-6) relative to sum?
            # Or drop the record? The task says "monolithic alloys with non-missing...".
            # Let's assume we replace 0 with a small value to allow transformation,
            # but log a warning.
            vals[vals <= 0] = 1e-6
            logger.debug(f"Replaced zero values with 1e-6 for ILR in {record.get('material_id')}")

        # Create a Compositional object
        try:
            comp_obj = compositional.Compositional(vals)
            ilr_vals = comp_obj.ilr()
            record['ilr_features'] = ilr_vals.tolist()
            ilr_records.append(record)
        except Exception as e:
            logger.error(f"Failed ILR transformation for {record.get('material_id')}: {e}")
            continue

    logger.info(f"ILR transformation complete. Processed {len(ilr_records)} records.")
    return ilr_records

def clean_data(raw_dir: Path, processed_dir: Path, output_filename: str = "filtered_alloys.csv") -> Path:
    """
    Main cleaning pipeline:
    1. Load raw data
    2. Verify measurement independence
    3. Filter monolithic alloys
    4. Check major element sum (T013)
    5. Normalize units
    6. Apply ILR
    7. Save to CSV
    """
    logger.info("Starting data cleaning pipeline.")
    
    records = load_raw_data(raw_dir)
    if not records:
        logger.error("No raw data found to clean.")
        return processed_dir / output_filename

    records = verify_measurement_independence(records)
    records = filter_monolithic_alloys(records)
    
    # T013: Check major element sum
    records = check_major_element_sum(records, threshold=0.95)

    records = normalize_units(records)
    records = apply_ilr_transformation(records)

    # Save to CSV
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / output_filename

    if not records:
        logger.warning("No records remaining after cleaning.")
        # Create empty file with headers if needed, or just empty
        import pandas as pd
        pd.DataFrame().to_csv(output_path, index=False)
        return output_path

    # Convert to DataFrame
    import pandas as pd
    df_records = []
    for r in records:
        row = {
            'material_id': r.get('material_id'),
            'poissons_ratio': r.get('poissons_ratio'),
            'youngs_modulus': r.get('youngs_modulus'),
            'bulk_modulus': r.get('bulk_modulus'),
            'measurement_method': r.get('measurement_method'),
            'measurement_source': r.get('measurement_source')
        }
        # Flatten composition
        comp = r.get('composition', {})
        for k, v in comp.items():
            row[f'comp_{k}'] = v
        
        # Flatten ILR features
        ilr = r.get('ilr_features', [])
        for i, v in enumerate(ilr):
            row[f'ilr_{i}'] = v
        
        df_records.append(row)

    df = pd.DataFrame(df_records)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

    return output_path

def run_cleaning_pipeline():
    """
    Entry point for running the cleaning pipeline.
    """
    config = get_config()
    raw_dir = config.data_dir / "raw"
    processed_dir = config.data_dir / "processed"

    output_path = clean_data(raw_dir, processed_dir)
    return output_path

def main():
    """
    CLI entry point.
    """
    setup_logging()
    output_path = run_cleaning_pipeline()
    print(f"Pipeline complete. Output: {output_path}")

if __name__ == "__main__":
    main()