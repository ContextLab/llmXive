#!/usr/bin/env python3
"""
Generate MD5 and SHA256 checksums for HumanEval dataset files.
Records checksums in state/map.json per Constitution Principle III.

This task implements T001a from tasks.md:
- Generate MD5/SHA256 checksums for HumanEval dataset files
- Record checksums in state/map.json under data/raw/ with artifact_id, checksum, timestamp, hash fields
"""

import os
import hashlib
import json
from datetime import datetime
from pathlib import Path


def compute_file_checksums(file_path):
    """
    Compute MD5 and SHA256 checksums for a single file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        dict with 'md5' and 'sha256' hex digest strings
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
    
    return {
        'md5': md5_hash.hexdigest(),
        'sha256': sha256_hash.hexdigest()
    }


def generate_checksums_for_dataset(data_dir):
    """
    Generate checksums for all files in the dataset directory.
    
    Args:
        data_dir: Path to the data/raw directory containing HumanEval files
        
    Returns:
        list of dicts with checksum metadata for each file
    """
    checksums = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")
    
    # Find all files in the dataset directory
    for file_path in data_path.rglob('*'):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(data_path))
            checksums_data = compute_file_checksums(file_path)
            
            checksum_entry = {
                'artifact_id': f"humaneval_{relative_path.replace('/', '_').replace('.', '_')}",
                'file_path': relative_path,
                'checksum': checksums_data['sha256'],
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'hash': 'sha256',
                'artifact_type': 'dataset_file',
                'md5': checksums_data['md5']
            }
            checksums.append(checksum_entry)
    
    return checksums


def write_checksums_to_map(checksums, output_path):
    """
    Write checksum entries to state/map.json.
    
    Args:
        checksums: list of checksum entry dicts
        output_path: Path to the output state/map.json file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing map if it exists
    if output_file.exists():
        with open(output_file, 'r') as f:
            existing_map = json.load(f)
    else:
        existing_map = {'artifacts': []}
    
    # Update with new checksums for HumanEval
    existing_map['humaneval_checksums'] = checksums
    existing_map['generated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    with open(output_file, 'w') as f:
        json.dump(existing_map, f, indent=2)


def main():
    """Main entry point for checksum generation."""
    # Paths relative to project root
    data_dir = Path('data/raw')
    output_path = Path('state/map.json')
    
    print(f"Generating checksums for HumanEval dataset in {data_dir}...")
    
    try:
        checksums = generate_checksums_for_dataset(data_dir)
        
        if not checksums:
            print("WARNING: No files found in dataset directory")
            return 1
        
        write_checksums_to_map(checksums, output_path)
        
        print(f"Successfully generated checksums for {len(checksums)} files")
        print(f"Checksums written to {output_path}")
        
        # Print summary
        print("\nChecksum Summary:")
        for entry in checksums:
            print(f"  - {entry['file_path']}: {entry['checksum'][:16]}...")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T001 (download HumanEval dataset) is completed first.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to generate checksums: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
