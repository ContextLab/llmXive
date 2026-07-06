"""
Verification logic for elemental properties against NIST-standard reference values.
Ensures deviation is <= 1% for atomic_radius, electronegativity, and valence_electrons.
"""
import os
import csv
import sys

# Add parent directory to path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_error, log_info, log_warning

logger = get_logger(__name__)

# NIST/JANAF Standard Reference Values (Approximate standard values for verification)
# Source: NIST Webbook / CRC Handbook of Chemistry and Physics
# Values are hardcoded here to ensure the verification logic is deterministic
# and does not rely on external network calls during the verification step itself.
REFERENCE_VALUES = {
    "Cu": {"atomic_radius_angstrom": 1.28, "electronegativity_pauling": 1.90, "valence_electrons": 1},
    "Al": {"atomic_radius_angstrom": 1.43, "electronegativity_pauling": 1.61, "valence_electrons": 3},
    "Zn": {"atomic_radius_angstrom": 1.34, "electronegativity_pauling": 1.65, "valence_electrons": 2},
    "Fe": {"atomic_radius_angstrom": 1.26, "electronegativity_pauling": 1.83, "valence_electrons": 2},
    "C":  {"atomic_radius_angstrom": 0.77, "electronegativity_pauling": 2.55, "valence_electrons": 4},
}

ALLOWED_DEVIATION_PCT = 1.0

def load_csv_data(filepath: str) -> list[dict]:
    """Load elemental properties from the CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def verify_element(element: str, actual: dict, reference: dict) -> list[str]:
    """
    Compare actual values against reference values.
    Returns a list of error messages if deviation > 1%.
    """
    errors = []
    
    # Fields to verify
    fields = [
        ("atomic_radius_angstrom", float),
        ("electronegativity_pauling", float),
        ("valence_electrons", int)
    ]

    for field_name, cast_func in fields:
        if field_name not in reference:
            continue
        
        ref_val = reference[field_name]
        try:
            actual_val = cast_func(actual.get(field_name, 0))
        except (ValueError, TypeError):
            errors.append(f"  [{element}] Invalid value for {field_name}: {actual.get(field_name)}")
            continue

        if ref_val == 0:
            if actual_val != 0:
                errors.append(f"  [{element}] {field_name}: Expected 0, got {actual_val}")
            continue

        deviation = abs(actual_val - ref_val) / abs(ref_val) * 100
        
        if deviation > ALLOWED_DEVIATION_PCT:
            errors.append(
                f"  [{element}] {field_name}: Reference={ref_val}, "
                f"Actual={actual_val}, Deviation={deviation:.2f}% "
                f"(Limit={ALLOWED_DEVIATION_PCT}%)"
            )
    
    return errors

def verify_elemental_properties(csv_path: str) -> bool:
    """
    Main verification function.
    Returns True if all elements pass the <= 1% deviation check.
    """
    log_info("Starting elemental properties verification...", module="verify_elements")
    
    try:
        data = load_csv_data(csv_path)
    except FileNotFoundError as e:
        log_error(str(e), module="verify_elements")
        return False

    all_passed = True
    total_elements = len(data)
    passed_elements = 0

    for row in data:
        element = row.get("element", "").strip()
        if not element:
            log_warning("Empty element row found, skipping.", module="verify_elements")
            continue

        if element not in REFERENCE_VALUES:
            log_warning(f"Element {element} not found in reference database. Skipping verification.", module="verify_elements")
            continue

        actual_values = {
            "atomic_radius_angstrom": row.get("atomic_radius_angstrom"),
            "electronegativity_pauling": row.get("electronegativity_pauling"),
            "valence_electrons": row.get("valence_electrons"),
        }

        ref_values = REFERENCE_VALUES[element]
        errors = verify_element(element, actual_values, ref_values)

        if errors:
            all_passed = False
            log_error(f"Verification failed for {element}:", module="verify_elements")
            for err in errors:
                log_error(err, module="verify_elements")
        else:
            passed_elements += 1
            log_info(f"Verification passed for {element}.", module="verify_elements")

    log_info(f"Verification complete. {passed_elements}/{total_elements} elements passed.", module="verify_elements")
    return all_passed

if __name__ == "__main__":
    # Default path relative to project root
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "elemental_properties.csv")
    
    # Allow override via argument
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = default_path

    print(f"Verifying: {target_path}")
    success = verify_elemental_properties(target_path)
    
    if success:
        print("RESULT: SUCCESS - All verified elements within 1% deviation.")
        sys.exit(0)
    else:
        print("RESULT: FAILURE - Deviation > 1% detected in one or more elements.")
        sys.exit(1)
