"""
Script to verify data integrity using SHA-256 checksums.

This script can be used to:
1. Generate checksums for a directory of files
2. Save checksums to a JSON file
3. Verify files against stored checksums
4. Generate a report of verification results
"""
import argparse
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checksum import (
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_against_checksums
)
from utils.logging import setup_logging, get_logger, info, error, warning

def main():
    parser = argparse.ArgumentParser(
        description="Verify data integrity using SHA-256 checksums"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate checksums for files in a directory"
    )
    gen_parser.add_argument(
        "directory",
        type=str,
        help="Directory containing files to checksum"
    )
    gen_parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output path for checksum JSON file"
    )
    gen_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=True,
        help="Include subdirectories (default: True)"
    )
    gen_parser.add_argument(
        "--extensions", "-e",
        type=str,
        nargs="+",
        help="File extensions to include (e.g., .csv .nii)"
    )
    
    # Verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify files against stored checksums"
    )
    verify_parser.add_argument(
        "directory",
        type=str,
        help="Directory containing files to verify"
    )
    verify_parser.add_argument(
        "--checksums", "-c",
        type=str,
        required=True,
        help="Path to checksum JSON file"
    )
    verify_parser.add_argument(
        "--report", "-r",
        type=str,
        help="Optional path to save verification report (JSON)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level="INFO")
    logger = get_logger(__name__)
    
    if args.command == "generate":
        directory = Path(args.directory)
        if not directory.exists():
            error(f"Directory not found: {directory}")
            sys.exit(1)
            
        logger.info(f"Generating checksums for: {directory}")
        
        extensions = None
        if args.extensions:
            # Ensure extensions start with a dot
            extensions = [
                ext if ext.startswith(".") else f".{ext}"
                for ext in args.extensions
            ]
            
        checksums = compute_directory_checksums(
            directory,
            recursive=args.recursive,
            extensions=extensions
        )
        
        if not checksums:
            warning("No files found to checksum")
            sys.exit(0)
            
        save_checksums(checksums, args.output)
        info(f"Successfully generated checksums for {len(checksums)} files")
        
    elif args.command == "verify":
        directory = Path(args.directory)
        checksums_path = Path(args.checksums)
        
        if not directory.exists():
            error(f"Directory not found: {directory}")
            sys.exit(1)
            
        if not checksums_path.exists():
            error(f"Checksum file not found: {checksums_path}")
            sys.exit(1)
            
        logger.info(f"Verifying files in: {directory}")
        logger.info(f"Using checksums from: {checksums_path}")
        
        try:
            checksums = load_checksums(checksums_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            error(f"Failed to load checksums: {e}")
            sys.exit(1)
            
        results = verify_directory_against_checksums(directory, checksums)
        
        # Calculate summary
        total = len(results)
        valid = sum(1 for v in results.values() if v)
        invalid = total - valid
        
        if invalid == 0:
            info(f"✓ All {total} files verified successfully")
        else:
            error(f"✗ {invalid}/{total} files failed verification")
            
            # List failed files
            failed_files = [k for k, v in results.items() if not v]
            for f in failed_files:
                warning(f"  - {f}")
                
        # Save report if requested
        if args.report:
            report = {
                "directory": str(directory),
                "checksums_file": str(checksums_path),
                "total_files": total,
                "valid": valid,
                "invalid": invalid,
                "results": results
            }
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            info(f"Verification report saved to: {args.report}")
            
        sys.exit(0 if invalid == 0 else 1)
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
