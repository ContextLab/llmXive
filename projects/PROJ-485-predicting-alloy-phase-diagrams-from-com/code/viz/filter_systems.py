import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional, Set
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Defined list of complex/metastable systems to exclude from visualization
# as per US-3 Assumptions and T038 requirements.
COMPLEX_SYSTEMS: Set[str] = {
    "Fe-C",      # Iron-Carbon (metastable phases, cementite)
    "Fe-N",      # Iron-Nitrogen
    "Ti-Al",     # Titanium-Aluminum (complex intermetallics)
    "Ni-Al",     # Nickel-Aluminum (often complex at certain ratios)
    "Co-Cr",     # Cobalt-Chromium (metastable)
}

def is_complex_system(system_id: str) -> bool:
    """
    Determines if a system ID corresponds to a complex or metastable system
    that should be excluded from visualization.

    Args:
        system_id: The system identifier (e.g., "Cu-Zn", "Fe-C").

    Returns:
        True if the system is complex/metastable, False otherwise.
    """
    # Normalize to ensure case-insensitive comparison if needed, 
    # though standard format is expected to be Title-Title.
    normalized_id = system_id.strip()
    return normalized_id in COMPLEX_SYSTEMS

def filter_systems_for_visualization(system_ids: List[str]) -> List[str]:
    """
    Filters a list of system IDs, removing any that are classified as
    complex or metastable.

    Args:
        system_ids: List of system identifiers to filter.

    Returns:
        A list of system IDs suitable for visualization (simple binaries).
    """
    filtered = []
    for sid in system_ids:
        if is_complex_system(sid):
            log_warning(
                f"Excluding complex/metastable system '{sid}' from visualization.",
                code="COMPLEX_SYSTEM_EXCLUDED"
            )
        else:
            filtered.append(sid)
    return filtered

def filter_processed_data_by_system(
    data: List[Dict[str, Any]], 
    allowed_systems: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Filters a dataset list, keeping only rows belonging to allowed systems.
    If allowed_systems is None, it defaults to filtering out complex systems.

    Args:
        data: List of row dictionaries containing a 'system_id' key.
        allowed_systems: Optional list of explicit system IDs to keep.

    Returns:
        Filtered list of data rows.
    """
    if allowed_systems is None:
        # Extract unique systems from data to determine which to keep
        all_systems = {row.get('system_id') for row in data if row.get('system_id')}
        allowed_systems = filter_systems_for_visualization(list(all_systems))
    
    allowed_set = set(allowed_systems)
    return [row for row in data if row.get('system_id') in allowed_set]

def verify_exclusion(data: List[Dict[str, Any]], excluded_systems: Set[str]) -> bool:
    """
    Verifies that no rows in the data belong to the excluded systems.

    Args:
        data: List of row dictionaries.
        excluded_systems: Set of system IDs that should NOT appear in data.

    Returns:
        True if verification passes (no excluded systems found), False otherwise.
    """
    for row in data:
        sys_id = row.get('system_id')
        if sys_id in excluded_systems:
            log_error(
                f"Verification failed: Found excluded system '{sys_id}' in data.",
                code="VERIFICATION_FAILED"
            )
            return False
    return True

def run_filter_systems(
    input_path: str, 
    output_path: str, 
    excluded_systems: Optional[Set[str]] = None
) -> List[str]:
    """
    Main entry point to load data, filter out complex systems, and save the result.

    Args:
        input_path: Path to the input CSV/JSON data file.
        output_path: Path to save the filtered data.
        excluded_systems: Optional set of systems to exclude. Defaults to COMPLEX_SYSTEMS.

    Returns:
        List of system IDs included in the output.
    """
    if excluded_systems is None:
        excluded_systems = COMPLEX_SYSTEMS

    log_info(f"Loading data from {input_path}...")
    
    # Determine file type and load
    data = []
    if input_path.endswith('.json'):
        with open(input_path, 'r') as f:
            data = json.load(f)
    elif input_path.endswith('.csv'):
        import csv
        with open(input_path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    else:
        raise ValueError(f"Unsupported file format: {input_path}")

    log_info(f"Loaded {len(data)} rows.")

    # Filter
    filtered_data = filter_processed_data_by_system(data, list(set(all_systems) - excluded_systems))
    all_systems = {row.get('system_id') for row in data if row.get('system_id')}
    allowed_systems = filter_systems_for_visualization(list(all_systems))
    filtered_data = filter_processed_data_by_system(data, allowed_systems)

    log_info(f"Filtered data: {len(filtered_data)} rows remaining.")

    # Verify exclusion
    if not verify_exclusion(filtered_data, excluded_systems):
        log_error("Exclusion verification failed.", code="VERIFICATION_FAILED")
        # In a strict pipeline, we might raise here, but for T038 we just log and proceed
        # or halt depending on policy. Let's log and return.

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if output_path.endswith('.json'):
        with open(output_path, 'w') as f:
            json.dump(filtered_data, f, indent=2)
    elif output_path.endswith('.csv'):
        import csv
        if filtered_data:
            fieldnames = list(filtered_data[0].keys())
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered_data)
    else:
        raise ValueError(f"Unsupported output format: {output_path}")

    return allowed_systems

def main():
    parser = argparse.ArgumentParser(description="Filter complex systems from phase diagram data.")
    parser.add_argument('--input', type=str, required=True, help='Input data file (CSV or JSON)')
    parser.add_argument('--output', type=str, required=True, help='Output data file (CSV or JSON)')
    args = parser.parse_args()

    try:
        included_systems = run_filter_systems(args.input, args.output)
        log_info(f"Filtering complete. Included systems: {included_systems}")
        print(json.dumps({"included_systems": included_systems}))
    except Exception as e:
        log_error(f"Filtering failed: {e}", code="FILTERING_ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()