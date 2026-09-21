"""
Utility module for file and directory checksum operations.
Provides CLI interface for checksum management.
"""
import sys
import argparse
from pathlib import Path
import json

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import compute_file_checksum, compute_directory_checksum, save_checksums, load_checksums, verify_checksums
from utils import setup_logger, PipelineError

logger = setup_logger(__name__)

def compute_checksums_for_directory(directory: Path, output_file: Path = None) -> list:
    """
    Compute checksums for all files and subdirectories in a directory.
    
    Args:
        directory: Path to the directory to process
        output_file: Optional path to save checksums to JSON file
        
    Returns:
        List of checksum dictionaries
    """
    if not directory.exists():
        raise PipelineError(f"Directory does not exist: {directory}")
    
    checksums = []
    
    # Process files
    for item in sorted(directory.rglob("*")):
        if item.is_file():
            checksum = compute_file_checksum(item)
            checksums.append({
                "path": str(item.relative_to(project_root)),
                "checksum": checksum,
                "type": "file"
            })
            logger.debug(f"Computed file checksum: {item.name}")
        elif item.is_dir():
            # Skip directories with .gitkeep only (empty directories)
            gitkeep = item / ".gitkeep"
            if not (item.exists() and not any(f for f in item.iterdir() if f != gitkeep)):
                checksum = compute_directory_checksum(item)
                checksums.append({
                    "path": str(item.relative_to(project_root)),
                    "checksum": checksum,
                    "type": "directory"
                })
                logger.debug(f"Computed directory checksum: {item.name}")
    
    if output_file:
        save_checksums(checksums, output_file)
        logger.info(f"Saved {len(checksums)} checksums to {output_file}")
    
    return checksums

def verify_all_checksums(checksum_file: Path) -> bool:
    """
    Verify all checksums against a stored checksum file.
    
    Args:
        checksum_file: Path to the JSON file containing checksums
        
    Returns:
        True if all checksums match, False otherwise
    """
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False
    
    try:
        results = verify_checksums(checksum_file)
        all_passed = all(r["valid"] for r in results)
        
        for result in results:
            status = "✓" if result["valid"] else "✗"
            logger.info(f"{status} {result['path']}: {result['message']}")
        
        return all_passed
    except Exception as e:
        logger.error(f"Error verifying checksums: {e}")
        return False

def main() -> int:
    """Main entry point for checksum utility CLI."""
    parser = argparse.ArgumentParser(
        description="Data checksum utility for verifying data integrity"
    )
    parser.add_argument(
        "command",
        choices=["compute", "verify"],
        help="Command to execute: compute or verify"
    )
    parser.add_argument(
        "-d", "--directory",
        type=Path,
        default=project_root / "data",
        help="Directory to process (default: data/)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=project_root / "data" / "checksums.json",
        help="Output file for checksums (default: data/checksums.json)"
    )
    parser.add_argument(
        "-c", "--checksum-file",
        type=Path,
        default=project_root / "data" / "checksums.json",
        help="Checksum file for verification (default: data/checksums.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")

    try:
        if args.command == "compute":
          if not args.directory.exists():
              logger.error(f"Directory not found: {args.directory}")
              return 1
          compute_checksums_for_directory(args.directory, args.output)
          return 0
        elif args.command == "verify":
          success = verify_all_checksums(args.checksum_file)
          return 0 if success else 1
        else:
          parser.print_help()
          return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())