import os
import sys
import json
import glob
import hashlib
from typing import List, Dict, Any, Tuple

# Add project root to path to allow imports from code/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.renderer import validate_ascii_grid, validate_grid_bounds, validate_grid_coordinates
from code.logger import get_logger, configure_global_logging

logger = get_logger(__name__)

def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return calculate_levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def load_ascii_file(filepath: str) -> str:
    """Load and return the content of an ASCII file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ASCII file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and return the content of a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_ascii_consistency(ascii_content: str) -> Tuple[bool, str]:
    """
    Validate that the ASCII grid is consistent.
    Returns (is_valid, error_message).
    """
    lines = ascii_content.strip().split('\n')
    if not lines:
        return False, "Empty ASCII content"

    # Validate bounds
    is_valid, msg = validate_grid_bounds(lines)
    if not is_valid:
        return False, f"Bounds validation failed: {msg}"

    # Validate coordinates
    is_valid, msg = validate_grid_coordinates(lines)
    if not is_valid:
        return False, f"Coordinates validation failed: {msg}"

    # Validate grid structure
    is_valid, msg = validate_ascii_grid(lines)
    if not is_valid:
        return False, f"Grid validation failed: {msg}"

    return True, "Valid"

def cross_validate_ascii_json(ascii_content: str, json_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Cross-validate ASCII grid against JSON event log.
    Returns (is_valid, error_message).
    """
    # Extract grid from JSON if present
    if 'grid' in json_data:
        json_grid = json_data['grid']
        # Convert JSON grid to string for comparison
        json_grid_str = '\n'.join([''.join(row) for row in json_grid])
        ascii_grid_str = ascii_content.strip()

        # Calculate Levenshtein distance
        distance = calculate_levenshtein_distance(json_grid_str, ascii_grid_str)

        if distance != 0:
            return False, f"Levenshtein distance between ASCII and JSON grid is {distance} (expected 0)"

    return True, "Valid"

def validate_files(ascii_path: str, json_path: str) -> Dict[str, Any]:
    """
    Validate a pair of ASCII and JSON files.
    Returns validation result dictionary.
    """
    result = {
        'ascii_file': ascii_path,
        'json_file': json_path,
        'valid': True,
        'errors': [],
        'warnings': []
    }

    try:
        ascii_content = load_ascii_file(ascii_path)
        json_data = load_json_file(json_path)
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"File loading error: {str(e)}")
        return result

    # Validate ASCII consistency
    is_valid, msg = validate_ascii_consistency(ascii_content)
    if not is_valid:
        result['valid'] = False
        result['errors'].append(f"ASCII validation error: {msg}")
    else:
        result['warnings'].append("ASCII validation passed")

    # Cross-validate ASCII and JSON
    is_valid, msg = cross_validate_ascii_json(ascii_content, json_data)
    if not is_valid:
        result['valid'] = False
        result['errors'].append(f"Cross-validation error: {msg}")
    else:
        result['warnings'].append("Cross-validation passed")

    return result

def generate_validation_report(ascii_dir: str, json_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a validation report for all ASCII/JSON file pairs.
    """
    report = {
        'summary': {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'overall_valid': True
        },
        'files': []
    }

    # Find all ASCII files
    ascii_files = glob.glob(os.path.join(ascii_dir, '*.ascii'))
    json_files = glob.glob(os.path.join(json_dir, '*.json'))

    # Create a mapping of base names to files
    ascii_map = {os.path.splitext(os.path.basename(f))[0]: f for f in ascii_files}
    json_map = {os.path.splitext(os.path.basename(f))[0]: f for f in json_files}

    # Find matching pairs
    common_bases = set(ascii_map.keys()) & set(json_map.keys())

    if not common_bases:
        report['summary']['overall_valid'] = False
        report['errors'] = ["No matching ASCII/JSON file pairs found"]
        return report

    for base in sorted(common_bases):
        ascii_path = ascii_map[base]
        json_path = json_map[base]

        validation_result = validate_files(ascii_path, json_path)
        report['files'].append(validation_result)
        report['summary']['total_files'] += 1

        if validation_result['valid']:
            report['summary']['valid_files'] += 1
        else:
            report['summary']['invalid_files'] += 1
            report['summary']['overall_valid'] = False

    # Write report to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    return report

def main():
    """Main entry point for the validator."""
    # Default paths
    ascii_dir = os.path.join(PROJECT_ROOT, 'data', 'processed')
    json_dir = os.path.join(PROJECT_ROOT, 'data', 'processed')
    output_path = os.path.join(PROJECT_ROOT, 'results', 'validation_report.json')

    # Check if directories exist
    if not os.path.exists(ascii_dir):
        logger.error(f"ASCII directory not found: {ascii_dir}")
        sys.exit(1)

    if not os.path.exists(json_dir):
        logger.error(f"JSON directory not found: {json_dir}")
        sys.exit(1)

    # Generate report
    report = generate_validation_report(ascii_dir, json_dir, output_path)

    # Print summary
    print(f"Validation Summary:")
    print(f"  Total files: {report['summary']['total_files']}")
    print(f"  Valid files: {report['summary']['valid_files']}")
    print(f"  Invalid files: {report['summary']['invalid_files']}")
    print(f"  Overall valid: {report['summary']['overall_valid']}")

    if not report['summary']['overall_valid']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
