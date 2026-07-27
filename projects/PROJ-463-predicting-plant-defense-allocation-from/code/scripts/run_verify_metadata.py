"""
CLI script to run metadata verification.
"""
import sys
from pathlib import Path
from src.data.verify_metadata import main as verify_main

def main():
    """Entry point for metadata verification script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify metadata for RNA-seq studies before preprocessing'
    )
    parser.add_argument(
        '--mode',
        choices=['real', 'synthetic'],
        default='real',
        help='Mode of operation: real or synthetic'
    )
    parser.add_argument(
        '--fastq-dir',
        type=str,
        help='Directory containing FASTQ files (for real mode)'
    )
    parser.add_argument(
        '--manifest-path',
        type=str,
        help='Path to manifest file'
    )
    
    args = parser.parse_args()
    
    exit_code = verify_main(
        mode=args.mode,
        fastq_dir=args.fastq_dir,
        manifest_path=args.manifest_path
    )
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()