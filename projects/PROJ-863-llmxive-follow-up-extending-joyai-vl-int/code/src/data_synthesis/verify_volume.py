import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from src.utils.logging import get_logger


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the manifest.jsonl file and return its parsed content.
    
    Args:
        manifest_path: Path to the manifest.jsonl file
        
    Returns:
        Parsed manifest data as a dictionary
        
    Raises:
        FileNotFoundError: If manifest file does not exist
        json.JSONDecodeError: If manifest file is not valid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            raise ValueError(f"Manifest file is empty: {manifest_path}")
        # Handle JSONL format (one JSON object per line)
        lines = content.split('\n')
        if len(lines) == 1:
            return json.loads(lines[0])
        else:
            # If multiple lines, return list of records
            return [json.loads(line) for line in lines]


def calculate_total_duration(manifest_data: Any) -> float:
    """
    Calculate the total video duration in seconds from manifest data.
    
    Args:
        manifest_data: Parsed manifest data (dict or list of dicts)
        
    Returns:
        Total duration in seconds
        
    Note:
        Handles both single manifest entry and JSONL format with multiple entries.
        Summing duration_seconds field from each entry.
    """
    total_seconds = 0.0
    
    if isinstance(manifest_data, dict):
        # Single manifest entry
        entries = [manifest_data]
    elif isinstance(manifest_data, list):
        # JSONL format with multiple entries
        entries = manifest_data
    else:
        raise ValueError(f"Unexpected manifest data type: {type(manifest_data)}")
    
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"Manifest entry is not a dictionary: {entry}")
        
        # Extract duration - try common field names
        duration = entry.get('duration_seconds') or entry.get('duration') or entry.get('total_seconds', 0)
        if isinstance(duration, (int, float)):
            total_seconds += float(duration)
        elif isinstance(duration, str):
            # Try to parse string duration
            try:
                total_seconds += float(duration)
            except ValueError:
                pass
                
    return total_seconds


def verify_volume(manifest_path: Path, ci_mode: bool = False, ci_threshold_seconds: float = 3600.0) -> Dict[str, Any]:
    """
    Verify that the generated video volume meets the requirements.
    
    Args:
        manifest_path: Path to the manifest.jsonl file
        ci_mode: If True, verify against CI threshold (default 1 hour)
        ci_threshold_seconds: Duration threshold for CI mode (default 3600 seconds)
        
    Returns:
        Dictionary with verification results:
            - 'success': bool indicating if verification passed
            - 'total_seconds': float total duration found
            - 'required_seconds': float required duration
            - 'message': str human-readable result message
            
    Raises:
        FileNotFoundError: If manifest file does not exist
        ValueError: If manifest is invalid or verification fails
    """
    logger = get_logger("verify_volume")
    
    # Load manifest
    logger.info(f"Loading manifest from: {manifest_path}")
    manifest_data = load_manifest(manifest_path)
    
    # Calculate total duration
    total_seconds = calculate_total_duration(manifest_data)
    
    # Determine required threshold
    if ci_mode:
        required_seconds = ci_threshold_seconds
        mode_str = "CI"
    else:
        required_seconds = 180000.0  # 50 hours = 180,000 seconds
        mode_str = "Non-CI"
    
    logger.info(f"Verification mode: {mode_str}, Required: {required_seconds}s, Found: {total_seconds}s")
    
    # Verify threshold
    success = total_seconds >= required_seconds
    
    if success:
        message = f"SUCCESS: {mode_str} verification passed. Total duration: {total_seconds:.2f}s ({total_seconds/3600:.2f} hours) >= {required_seconds}s ({required_seconds/3600:.2f} hours)"
        logger.info(message)
    else:
        message = f"FAILURE: {mode_str} verification failed. Total duration: {total_seconds:.2f}s ({total_seconds/3600:.2f} hours) < {required_seconds}s ({required_seconds/3600:.2f} hours)"
        logger.error(message)
    
    return {
        'success': success,
        'total_seconds': total_seconds,
        'required_seconds': required_seconds,
        'message': message
    }


def main():
    """
    Command-line entry point for volume verification.
    
    Usage:
        python src/data_synthesis/verify_volume.py [--ci] [--threshold SECONDS] [manifest_path]
        
    Defaults:
        manifest_path: data/manifest.jsonl
        ci_mode: False (Non-CI mode, requires 50 hours)
        ci_threshold_seconds: 3600.0 (1 hour for CI mode)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify video generation volume meets requirements'
    )
    parser.add_argument(
        'manifest_path',
        nargs='?',
        default='data/manifest.jsonl',
        help='Path to manifest.jsonl file (default: data/manifest.jsonl)'
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Enable CI mode (verify against smaller threshold)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=3600.0,
        help='Duration threshold in seconds for CI mode (default: 3600.0)'
    )
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest_path)
    
    try:
        result = verify_volume(manifest_path, ci_mode=args.ci, ci_threshold_seconds=args.threshold)
        
        print(f"\n{'='*60}")
        print(f"Volume Verification Results")
        print(f"{'='*60}")
        print(f"Mode: {'CI' if args.ci else 'Non-CI'}")
        print(f"Total Duration: {result['total_seconds']:.2f} seconds ({result['total_seconds']/3600:.2f} hours)")
        print(f"Required Duration: {result['required_seconds']:.2f} seconds ({result['required_seconds']/3600:.2f} hours)")
        print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
        print(f"Message: {result['message']}")
        print(f"{'='*60}\n")
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()