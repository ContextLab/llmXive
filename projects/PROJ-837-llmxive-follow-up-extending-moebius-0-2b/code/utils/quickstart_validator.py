"""
Quickstart validation utilities for the llmXive pipeline.

This module provides functions to:
- Compute file hashes
- Check directory existence
- Validate artifacts
- Generate checksum manifests
"""
import os
import sys
import json
import hashlib
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_path, get_mode
from utils.logger import get_logger, log_error, log_fatal

logger = get_logger(__name__)

def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> Optional[str]:
    """Compute the hash of a file."""
    path = Path(filepath)
    if not path.exists():
        log_error(f"File not found for hashing: {filepath}")
        return None
    
    try:
        hash_obj = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        log_error(f"Hash computation failed for {filepath}: {e}")
        return None

def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists."""
    path = Path(dirpath)
    return path.is_dir()

def validate_artifact(filepath: str, required: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate that an artifact exists.
    
    Returns:
        Tuple of (exists, error_message)
    """
    path = Path(filepath)
    if not path.exists():
        if required:
            return False, f"Required artifact missing: {filepath}"
        return False, f"Optional artifact missing: {filepath}"
    return True, None

def run_quickstart_validation() -> Dict[str, Any]:
    """
    Run validation of all required artifacts for the quickstart.
    
    Returns:
        A dictionary with validation results.
    """
    results = {
        'mode': get_mode(),
        'artifacts': {},
        'directories': {},
        'overall_status': 'PASS'
    }
    
    # Define required artifacts
    artifacts = [
        'data/annotations/decoupled_scores.csv',
        'data/annotations/human_scores.csv',
        'data/results/proxy_validation.json',
        'data/results/permutation_test.json',
        'data/results/ablation_report.json',
        'data/results/latency_raw.csv',
        'data/results/evaluation_report.json'
    ]
    
    # Define required directories
    directories = [
        'data/raw',
        'data/processed',
        'data/annotations',
        'data/results',
        'code/models',
        'code/training',
        'code/eval'
    ]
    
    # Validate artifacts
    for artifact in artifacts:
        exists, error = validate_artifact(artifact)
        results['artifacts'][artifact] = {
            'exists': exists,
            'error': error
        }
        if not exists and artifact in [a for a in artifacts if 'required' in a]:
            results['overall_status'] = 'FAIL'
    
    # Validate directories
    for directory in directories:
        exists = check_directory_exists(directory)
        results['directories'][directory] = exists
        if not exists:
            results['overall_status'] = 'FAIL'
    
    return results

def generate_checksum_manifest(output_path: str) -> bool:
    """Generate a checksum manifest for all artifacts."""
    artifacts = [
        'data/annotations/decoupled_scores.csv',
        'data/annotations/human_scores.csv',
        'data/results/proxy_validation.json',
        'data/results/permutation_test.json',
        'data/results/ablation_report.json',
        'data/results/latency_raw.csv',
        'data/results/evaluation_report.json'
    ]
    
    manifest = {
        'generated_at': str(Path().resolve()),
        'hashes': {}
    }
    
    for artifact in artifacts:
        hash_val = compute_file_hash(artifact)
        if hash_val:
            manifest['hashes'][artifact] = hash_val
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest generated: {output_path}")
    return True

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description='Quickstart validation for llmXive')
    parser.add_argument('--mode', type=str, choices=['validate', 'manifest'],
                      default='validate', help='Validation mode')
    parser.add_argument('--output', type=str, required=False,
                      help='Output path for manifest (required for manifest mode)')
    
    args = parser.parse_args()
    
    if args.mode == 'validate':
        results = run_quickstart_validation()
        print(json.dumps(results, indent=2))
        if results['overall_status'] == 'FAIL':
            sys.exit(1)
    elif args.mode == 'manifest':
        if not args.output:
            parser.error("Manifest mode requires --output")
        success = generate_checksum_manifest(args.output)
        if not success:
            sys.exit(1)
    else:
        parser.error(f"Unknown mode: {args.mode}")

if __name__ == '__main__':
    main()