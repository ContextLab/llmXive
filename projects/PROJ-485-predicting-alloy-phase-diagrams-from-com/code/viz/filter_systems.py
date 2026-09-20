"""
Filter systems to exclude complex/metastable systems (e.g., Fe-C) from visualization.
Implements T038: Exclude complex/metastable systems from visualization.

Constraint: Visualization must be limited to 'simple binary systems' (e.g., Cu-Zn, Al-Cu).
Verification: Assert Fe-C is not in the generated plots list.
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional, Set

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

# Define the list of complex/metastable systems to exclude
# Based on US-3 Assumptions and domain knowledge of alloy phase diagrams
COMPLEX_SYSTEMS = {
    "Fe-C",      # Iron-Carbon (metastable cementite formation)
    "Fe-N",      # Iron-Nitrogen (metastable nitrides)
    "Ti-C",      # Titanium-Carbon (complex carbides)
    "Ti-N",      # Titanium-Nitrogen (complex nitrides)
    "W-C",       # Tungsten-Carbon (complex carbides)
    "Cr-C",      # Chromium-Carbon (complex carbides)
    "Mo-C",      # Molybdenum-Carbon (complex carbides)
    "V-C",       # Vanadium-Carbon (complex carbides)
    "Nb-C",      # Niobium-Carbon (complex carbides)
    "Ta-C",      # Tantalum-Carbon (complex carbides)
}

# Define allowed simple binary systems (explicit whitelist for safety)
ALLOWED_SIMPLE_SYSTEMS = {
    "Cu-Zn",
    "Al-Cu",
    "Cu-Al",
    "Zn-Cu",
    "Al-Zn",
    "Zn-Al",
    "Fe-Ni",
    "Ni-Fe",
    "Cu-Ni",
    "Ni-Cu",
    "Al-Mg",
    "Mg-Al",
}

logger = get_logger(__name__)


def is_complex_system(system_id: str) -> bool:
    """
    Check if a system ID represents a complex/metastable system.
    
    Args:
        system_id: System identifier (e.g., "Fe-C", "Cu-Zn")
        
    Returns:
        True if the system is complex/metastable, False otherwise
    """
    # Normalize the system ID for comparison
    normalized_id = system_id.strip().upper()
    
    # Check against explicit complex systems list
    for complex_sys in COMPLEX_SYSTEMS:
        if normalized_id == complex_sys.upper():
            return True
    
    # If we have an explicit whitelist, only allow those
    if ALLOWED_SIMPLE_SYSTEMS:
        for allowed_sys in ALLOWED_SIMPLE_SYSTEMS:
            if normalized_id == allowed_sys.upper():
                return False
        # If not in whitelist, treat as complex/unknown
        return True
    
    # Default: assume simple unless explicitly complex
    return False


def filter_systems_for_visualization(
    systems: List[str],
    exclude_list: Optional[Set[str]] = None,
    include_list: Optional[Set[str]] = None
) -> List[str]:
    """
    Filter a list of system IDs to exclude complex/metastable systems.
    
    Args:
        systems: List of system IDs to filter
        exclude_list: Optional explicit set of systems to exclude
        include_list: Optional explicit set of systems to include (whitelist)
        
    Returns:
        Filtered list of system IDs (only simple binary systems)
    """
    filtered_systems = []
    excluded_systems = []
    
    # Merge exclude lists
    final_exclude_list = COMPLEX_SYSTEMS.copy()
    if exclude_list:
        final_exclude_list.update(exclude_list)
    
    for system_id in systems:
        normalized_id = system_id.strip()
        
        # Check if explicitly excluded
        if normalized_id.upper() in {s.upper() for s in final_exclude_list}:
            excluded_systems.append(normalized_id)
            log_warning(
                f"Excluding complex/metastable system: {normalized_id}",
                code=ErrorCode.DATA_SOURCE_MISSING
            )
            continue
        
        # Check if explicitly included (whitelist mode)
        if include_list:
            if normalized_id.upper() in {s.upper() for s in include_list}:
                filtered_systems.append(normalized_id)
            else:
                excluded_systems.append(normalized_id)
                log_warning(
                    f"Excluding system not in whitelist: {normalized_id}",
                    code=ErrorCode.DATA_SOURCE_MISSING
                )
        else:
            # Use default complex system detection
            if not is_complex_system(normalized_id):
                filtered_systems.append(normalized_id)
            else:
                excluded_systems.append(normalized_id)
                log_warning(
                    f"Excluding complex/metastable system: {normalized_id}",
                    code=ErrorCode.DATA_SOURCE_MISSING
                )
    
    log_info(
        f"Filtered systems: {len(filtered_systems)} included, {len(excluded_systems)} excluded",
        code=None
    )
    
    return filtered_systems


def filter_processed_data_by_system(
    data: List[Dict[str, Any]],
    allowed_systems: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter processed data rows to only include allowed systems.
    
    Args:
        data: List of data dictionaries with 'system_id' or 'system' key
        allowed_systems: List of system IDs to keep
        
    Returns:
        Filtered list of data dictionaries
    """
    allowed_set = {s.upper().strip() for s in allowed_systems}
    filtered_data = []
    excluded_count = 0
    
    for row in data:
        # Try different possible keys for system identifier
        system_id = None
        for key in ['system_id', 'system', 'alloy_system', 'binary_system']:
            if key in row and row[key]:
                system_id = str(row[key]).upper().strip()
                break
        
        if system_id and system_id in allowed_set:
            filtered_data.append(row)
        else:
            excluded_count += 1
    
    log_info(
        f"Filtered data: {len(filtered_data)} rows kept, {excluded_count} rows excluded",
        code=None
    )
    
    return filtered_data


def verify_exclusion(
    systems: List[str],
    forbidden_systems: Set[str] = None
) -> bool:
    """
    Verify that forbidden systems are not present in the list.
    
    Args:
        systems: List of system IDs to verify
        forbidden_systems: Set of system IDs that must not be present
        
    Returns:
        True if verification passes, False otherwise
    """
    if forbidden_systems is None:
        forbidden_systems = COMPLEX_SYSTEMS
    
    forbidden_upper = {s.upper() for s in forbidden_systems}
    present_forbidden = []
    
    for system_id in systems:
        if system_id.upper() in forbidden_upper:
            present_forbidden.append(system_id)
    
    if present_forbidden:
        log_error(
            f"Forbidden systems found in visualization list: {present_forbidden}",
            code=ErrorCode.INVALID_DATA_SCHEMA
        )
        return False
    
    log_info(
        f"Verification passed: No forbidden systems found in {len(systems)} systems",
        code=None
    )
    return True


def run_filter_systems(
    input_systems: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    exclude_complex: bool = True
) -> List[str]:
    """
    Main entry point for filtering systems.
    
    Args:
        input_systems: Optional list of system IDs to filter
        output_file: Optional path to write filtered systems
        exclude_complex: Whether to exclude complex systems (default: True)
        
    Returns:
        Filtered list of system IDs
    """
    if input_systems is None:
        # Default test case: include Fe-C to verify exclusion
        input_systems = ["Cu-Zn", "Al-Cu", "Fe-C", "Cu-Al", "Fe-N", "Ni-Fe"]
    
    log_info(f"Input systems: {input_systems}", code=None)
    
    if exclude_complex:
        filtered = filter_systems_for_visualization(input_systems)
    else:
        filtered = input_systems
    
    # Verify exclusion of complex systems
    if exclude_complex:
        if not verify_exclusion(filtered):
            log_error(
                "Verification failed: Complex systems found in filtered output",
                code=ErrorCode.INVALID_DATA_SCHEMA
            )
            raise ValueError("Complex systems found in filtered output")
    
    # Write to output file if specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(filtered, f, indent=2)
        log_info(f"Filtered systems written to {output_file}", code=None)
    
    log_info(f"Output systems: {filtered}", code=None)
    return filtered


def main():
    """Command-line interface for system filtering."""
    parser = argparse.ArgumentParser(
        description="Filter complex/metastable systems from visualization candidates"
    )
    parser.add_argument(
        "--input",
        type=str,
        nargs="*",
        help="System IDs to filter (e.g., Cu-Zn Fe-C Al-Cu)"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="JSON file containing list of system IDs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/artifacts/filtered_systems.json",
        help="Output JSON file for filtered systems"
    )
    parser.add_argument(
        "--exclude-complex",
        action="store_true",
        default=True,
        help="Exclude complex/metastable systems (default: True)"
    )
    
    args = parser.parse_args()
    
    # Load input systems
    input_systems = None
    if args.input:
        input_systems = args.input
    elif args.input_file:
        if os.path.exists(args.input_file):
            with open(args.input_file, 'r') as f:
                input_systems = json.load(f)
        else:
            log_error(f"Input file not found: {args.input_file}", code=ErrorCode.DATA_SOURCE_MISSING)
            sys.exit(1)
    
    # Run filtering
    try:
        filtered = run_filter_systems(
            input_systems=input_systems,
            output_file=args.output,
            exclude_complex=args.exclude_complex
        )
        log_info(f"Successfully filtered {len(filtered)} systems", code=None)
    except Exception as e:
        log_error(f"Failed to filter systems: {str(e)}", code=ErrorCode.INVALID_DATA_SCHEMA)
        sys.exit(1)


if __name__ == "__main__":
    main()
