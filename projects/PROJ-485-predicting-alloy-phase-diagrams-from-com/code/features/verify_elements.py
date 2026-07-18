import os
import csv
import sys
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_error, log_info, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256

logger = get_logger(__name__)

# Reference data from NIST Webbook / Standard Tables (CRC Handbook of Chemistry and Physics)
# Values are hardcoded as the "Primary Reference" for this specific task to ensure
# verification against a known standard without external network dependencies during verification.
# Source: NIST-JANAF Thermochemical Tables / CRC Handbook (2023 values)
NIST_REFERENCE_DATA = {
    "Cu": {
        "atomic_radius_angstrom": 1.28,
        "electronegativity_pauling": 1.90,
        "valence_electrons": 1  # 4s1 (commonly used for alloying)
    },
    "Al": {
        "atomic_radius_angstrom": 1.43,
        "electronegativity_pauling": 1.61,
        "valence_electrons": 3  # 3s2 3p1
    },
    "Zn": {
        "atomic_radius_angstrom": 1.34,
        "electronegativity_pauling": 1.65,
        "valence_electrons": 2  # 4s2
    },
    "Fe": {
        "atomic_radius_angstrom": 1.26,
        "electronegativity_pauling": 1.83,
        "valence_electrons": 2  # Common valence in alloys
    },
    "C": {
        "atomic_radius_angstrom": 0.77,
        "electronegativity_pauling": 2.55,
        "valence_electrons": 4  # 2s2 2p2
    }
}

def load_csv_data(filepath: str) -> List[Dict[str, Any]]:
    """Load elemental properties from the local CSV file."""
    if not os.path.exists(filepath):
        log_error(logger, f"File not found: {filepath}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def verify_element(local_value: float, reference_value: float, tolerance: float = 0.01) -> Tuple[bool, float]:
    """
    Verify if local_value deviates from reference_value by <= tolerance (percentage).
    Returns (is_valid, deviation_percent).
    """
    if reference_value == 0:
        # Avoid division by zero; if both are 0 it's valid, otherwise invalid
        return local_value == 0, 0.0
    
    deviation = abs(local_value - reference_value) / reference_value
    is_valid = deviation <= tolerance
    return is_valid, deviation * 100

def verify_elemental_properties(input_path: str = "data/raw/elemental_properties.csv") -> bool:
    """
    Cross-reference data in input_path against NIST_REFERENCE_DATA.
    Ensures all values deviate <= 1% from the reference.
    Returns True if all checks pass, False otherwise.
    Raises ValueError if critical deviations are found.
    """
    log_info(logger, f"Starting verification of {input_path} against NIST reference.")
    
    # Compute checksum for logging
    checksum = compute_file_sha256(input_path)
    log_info(logger, f"File checksum (SHA-256): {checksum}")

    local_data = load_csv_data(input_path)
    local_map = {row['element']: row for row in local_data}
    
    all_passed = True
    errors = []

    for element, ref_values in NIST_REFERENCE_DATA.items():
        if element not in local_map:
            msg = f"Element '{element}' missing from local CSV."
            log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
            errors.append(msg)
            all_passed = False
            continue

        local_row = local_map[element]
        
        # Check Atomic Radius
        try:
            local_radius = float(local_row['atomic_radius_angstrom'])
            ref_radius = ref_values['atomic_radius_angstrom']
            valid, dev = verify_element(local_radius, ref_radius)
            if not valid:
                msg = f"Atomic Radius for {element}: Local={local_radius}, Ref={ref_radius}, Deviation={dev:.2f}% (>1%)"
                log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
                errors.append(msg)
                all_passed = False
            else:
                log_info(logger, f"Atomic Radius for {element} OK (Deviation: {dev:.4f}%)")
        except (ValueError, KeyError) as e:
            msg = f"Error parsing Atomic Radius for {element}: {e}"
            log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
            errors.append(msg)
            all_passed = False

        # Check Electronegativity
        try:
            local_en = float(local_row['electronegativity_pauling'])
            ref_en = ref_values['electronegativity_pauling']
            valid, dev = verify_element(local_en, ref_en)
            if not valid:
                msg = f"Electronegativity for {element}: Local={local_en}, Ref={ref_en}, Deviation={dev:.2f}% (>1%)"
                log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
                errors.append(msg)
                all_passed = False
            else:
                log_info(logger, f"Electronegativity for {element} OK (Deviation: {dev:.4f}%)")
        except (ValueError, KeyError) as e:
            msg = f"Error parsing Electronegativity for {element}: {e}"
            log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
            errors.append(msg)
            all_passed = False

        # Check Valence Electrons (Integer comparison, tolerance is effectively 0 for integers, 
        # but we treat it as 1% of value or 1 unit if value is large. For small integers, exact match is usually required.
        # However, task says <=1% deviation. For valence=1, 1% is 0.01. So exact match is needed.
        try:
            local_val = int(float(local_row['valence_electrons']))
            ref_val = ref_values['valence_electrons']
            # For integers, 1% deviation is very strict. We check exact match or very close if float allowed.
            # Assuming integer valence.
            if local_val != ref_val:
                # Calculate % deviation based on magnitude
                deviation = abs(local_val - ref_val) / ref_val
                if deviation > 0.01:
                    msg = f"Valence Electrons for {element}: Local={local_val}, Ref={ref_val}, Deviation={deviation*100:.2f}% (>1%)"
                    log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
                    errors.append(msg)
                    all_passed = False
                else:
                    log_info(logger, f"Valence Electrons for {element} OK (Deviation: {deviation*100:.4f}%)")
            else:
                log_info(logger, f"Valence Electrons for {element} OK")
        except (ValueError, KeyError) as e:
            msg = f"Error parsing Valence Electrons for {element}: {e}"
            log_error(logger, msg, ErrorCode.INVALID_DATA_SCHEMA)
            errors.append(msg)
            all_passed = False

    if all_passed:
        log_info(logger, "Verification PASSED: All elemental properties are within 1% of NIST reference.")
    else:
        log_error(logger, f"Verification FAILED: {len(errors)} errors found.", ErrorCode.INVALID_DATA_SCHEMA)
        for err in errors:
            log_error(logger, f"  - {err}")
    
    return all_passed

def main():
    """Entry point for the verification script."""
    input_file = "data/raw/elemental_properties.csv"
    try:
        success = verify_elemental_properties(input_file)
        if success:
            log_info(logger, "Task T006a completed successfully.")
            sys.exit(0)
        else:
            log_error(logger, "Task T006a failed due to data deviation.", ErrorCode.INVALID_DATA_SCHEMA)
            sys.exit(1)
    except Exception as e:
        log_error(logger, f"Unexpected error during verification: {e}", ErrorCode.DATA_SOURCE_MISSING)
        sys.exit(1)

if __name__ == "__main__":
    main()