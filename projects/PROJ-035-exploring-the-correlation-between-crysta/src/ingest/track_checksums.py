"""
Script to track SHA-256 checksums for raw data files.

This script implements Constitution III requirements for artifact
hash tracking. It scans the data/raw/ directory, computes SHA-256
checksums for all files, and stores them in the project state file.

Usage:
    python src/ingest/track_checksums.py [--raw-dir DATA/raw] [--state STATE]

Output:
    Updates state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml
    with artifact_hashes for all raw data files.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksums import update_checksums_for_raw_data, load_artifact_hashes


def main():
    """Main entry point for checksum tracking script."""
    parser = argparse.ArgumentParser(
        description="Track SHA-256 checksums for raw data files (Constitution III)"
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=project_root / "data" / "raw",
        help="Path to raw data directory (default: data/raw)"
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=project_root / "state" / "projects" / "PROJ-035-exploring-the-correlation-between-crysta.yaml",
        help="Path to state YAML file (default: state/projects/PROJ-035-*.yaml)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display current checksums without updating"
    )
    
    args = parser.parse_args()
    
    # Ensure raw data directory exists
    if not args.raw_dir.exists():
        print(f"Warning: Raw data directory does not exist: {args.raw_dir}")
        print("Creating empty checksum entry...")
        args.raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Show current state if requested
    if args.show:
        state_data = load_artifact_hashes(args.state)
        print("Current artifact hashes:")
        if "artifact_hashes" in state_data:
            for category, hashes in state_data["artifact_hashes"].items():
                print(f"\n  {category}:")
                if isinstance(hashes, dict):
                    for file_path, hash_val in hashes.items():
                        print(f"    {file_path}: {hash_val[:16]}...")
                else:
                    print(f"    {hashes}")
        else:
            print("  No artifact hashes found.")
        return
    
    # Update checksums
    print(f"Scanning raw data directory: {args.raw_dir}")
    state_data = update_checksums_for_raw_data(args.raw_dir, args.state)
    
    # Report results
    raw_hashes = state_data.get("artifact_hashes", {}).get("raw_data", {})
    if raw_hashes:
        print(f"\nComputed checksums for {len(raw_hashes)} file(s):")
        for file_path, hash_val in raw_hashes.items():
            print(f"  {file_path}: {hash_val}")
    else:
        print("\nNo files found in raw data directory.")
    
    print(f"\nState file updated: {args.state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
