import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from src.utils.logging import get_logger

# Constants for duration thresholds (in seconds)
NON_CI_TARGET_SECONDS = 180000  # 50 hours
CI_SUBSET_SECONDS = 3600  # 1 hour (default subset for CI)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load and parse the manifest.jsonl file.
    
    Args:
        manifest_path: Path to the manifest.jsonl file
        
    Returns:
        List of manifest entries as dictionaries
        
    Raises:
        FileNotFoundError: If manifest file does not exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
    entries = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num}: {e.msg}",
                    e.doc,
                    e.pos
                )
                
    return entries

def calculate_total_duration(entries: List[Dict[str, Any]]) -> float:
    """
    Calculate total video duration in seconds from manifest entries.
    
    Args:
        entries: List of manifest entries (each should have 'duration_seconds')
        
    Returns:
        Total duration in seconds
    """
    total = 0.0
    for entry in entries:
        if 'duration_seconds' in entry:
            total += float(entry['duration_seconds'])
        elif 'duration' in entry:
            # Handle alternative key name
            total += float(entry['duration'])
    return total

def verify_volume(manifest_path: Path, is_ci_mode: bool = False) -> Dict[str, Any]:
    """
    Verify that the generated video volume meets the required thresholds.
    
    Args:
        manifest_path: Path to the manifest.jsonl file
        is_ci_mode: If True, verify against CI subset threshold; 
                   if False, verify against 50-hour target
                   
    Returns:
        Dictionary with verification results:
        - 'success': bool indicating if verification passed
        - 'total_seconds': float of total duration found
        - 'expected_seconds': float of expected duration
        - 'entries_count': int of number of entries in manifest
        - 'message': str with detailed result message
        
    Raises:
        FileNotFoundError: If manifest file does not exist
        ValueError: If manifest is empty or invalid
    """
    logger = get_logger("verify_volume")
    
    # Load manifest
    entries = load_manifest(manifest_path)
    
    if not entries:
        raise ValueError(f"Manifest file is empty: {manifest_path}")
        
    # Calculate total duration
    total_seconds = calculate_total_duration(entries)
    
    # Determine expected threshold
    expected_seconds = CI_SUBSET_SECONDS if is_ci_mode else NON_CI_TARGET_SECONDS
    threshold_name = "CI subset" if is_ci_mode else "50-hour target"
    
    # Verification logic
    success = total_seconds >= expected_seconds
    
    result = {
        'success': success,
        'total_seconds': total_seconds,
        'expected_seconds': expected_seconds,
        'entries_count': len(entries),
        'threshold_name': threshold_name,
        'is_ci_mode': is_ci_mode
    }
    
    # Format message
    if success:
        hours = total_seconds / 3600
        result['message'] = (
            f"✓ Volume verification PASSED: {total_seconds:,.0f} seconds "
            f"({hours:.2f} hours) meets {threshold_name} ({expected_seconds:,.0f} seconds)."
        )
        logger.info(result['message'])
    else:
        hours = total_seconds / 3600
        result['message'] = (
            f"✗ Volume verification FAILED: {total_seconds:,.0f} seconds "
            f"({hours:.2f} hours) is below {threshold_name} "
            f"(expected >= {expected_seconds:,.0f} seconds)."
        )
        logger.error(result['message'])
        
    return result

def main():
    """
    CLI entry point for volume verification.
    
    Usage:
        python -m src.data_synthesis.verify_volume --manifest <path> [--ci-mode]
        
    Environment variables:
        DATA_MANIFEST_PATH: Optional default path to manifest.jsonl
        CI_MODE: Set to 'true' or '1' to enable CI mode verification
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify generated video volume against required thresholds.'
    )
    parser.add_argument(
        '--manifest', '-m',
        type=Path,
        default=os.getenv('DATA_MANIFEST_PATH', 'data/manifest.jsonl'),
        help='Path to manifest.jsonl file (default: data/manifest.jsonl)'
    )
    parser.add_argument(
        '--ci-mode',
        action='store_true',
        default=os.getenv('CI_MODE', '').lower() in ('true', '1', 'yes'),
        help='Verify against CI subset threshold (1 hour) instead of 50-hour target'
    )
    
    args = parser.parse_args()
    
    logger = get_logger("verify_volume")
    logger.info(f"Starting volume verification for: {args.manifest}")
    logger.info(f"Mode: {'CI' if args.ci_mode else 'Non-CI'}")
    
    try:
        result = verify_volume(args.manifest, is_ci_mode=args.ci_mode)
        
        if result['success']:
            print(result['message'])
            sys.exit(0)
        else:
            print(result['message'])
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"ERROR: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()
