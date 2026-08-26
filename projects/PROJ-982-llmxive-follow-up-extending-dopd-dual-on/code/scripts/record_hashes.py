"""
Script to record checksums of artifacts.
"""
import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.checksum import compute_file_hash, compute_directory_hash

def main():
    parser = argparse.ArgumentParser(description='Record artifact checksums')
    parser.add_argument('--input-dir', type=str, default='data/raw',
                        help='Directory to hash')
    parser.add_argument('--output-file', type=str, default='data/processed/checksums.json',
                        help='Output file for checksums')
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: Directory not found: {args.input_dir}")
        sys.exit(1)

    print(f"Computing checksums for: {args.input_dir}")

    # Compute directory hash
    dir_hash = compute_directory_hash(args.input_dir)

    # Compute individual file hashes
    file_hashes = {}
    for root, dirs, files in os.walk(args.input_dir):
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, args.input_dir)
            file_hash = compute_file_hash(filepath)
            file_hashes[rel_path] = file_hash

    # Prepare output
    checksum_data = {
        'metadata': {
            'input_directory': args.input_dir,
            'timestamp': datetime.now().isoformat(),
            'directory_hash': dir_hash
        },
        'file_hashes': file_hashes
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    # Save checksums
    with open(args.output_file, 'w') as f:
        json.dump(checksum_data, f, indent=2)

    print(f"Checksums saved to: {args.output_file}")
    print(f"Directory hash: {dir_hash}")
    print(f"Number of files hashed: {len(file_hashes)}")

if __name__ == '__main__':
    main()