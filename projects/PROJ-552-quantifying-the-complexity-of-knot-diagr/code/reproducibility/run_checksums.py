"""
Run checksum recording for all data files and generate documentation.

This script implements T045: Record checksums in data/ directory and document
in docs/reproducibility/checksums.md (per FR-007).

It uses the checksums.py module (created in T044) to:
1. Find all data files in data/ directory
2. Compute SHA-256 checksums for each file
3. Record checksums in data/checksums.json and data/checksums.csv
4. Generate documentation in docs/reproducibility/checksums.md
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reproducibility.checksums import (
    find_data_files,
    record_checksums,
    write_checksums_json,
    write_checksums_csv,
    write_checksums_documentation,
    main as checksums_main
)
from reproducibility.logs import log_operation, get_logger

logger = get_logger()

def run_checksum_recording():
    """
    Execute checksum recording for all data files.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Log operation start
        log_operation(
            operation="checksum_recording",
            input_file="data/",
            output_file="data/checksums.json, docs/reproducibility/checksums.md",
            parameters={"recursive": True, "algorithm": "sha256"},
            status="started"
        )
        
        # Define paths
        data_dir = project_root / "data"
        docs_dir = project_root / "docs" / "reproducibility"
        
        # Ensure directories exist
        data_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all data files
        print(f"Finding data files in {data_dir}...")
        data_files = find_data_files(data_dir)
        
        if not data_files:
            print("No data files found. Creating empty checksums record.")
            data_files = []
        else:
            print(f"Found {len(data_files)} data files:")
            for f in data_files:
                print(f"  - {f}")
        
        # Record checksums
        print("\nComputing SHA-256 checksums...")
        checksum_records = record_checksums(data_files)
        
        # Write checksums to JSON
        json_path = data_dir / "checksums.json"
        print(f"\nWriting checksums to {json_path}...")
        write_checksums_json(checksum_records, json_path)
        
        # Write checksums to CSV
        csv_path = data_dir / "checksums.csv"
        print(f"Writing checksums to {csv_path}...")
        write_checksums_csv(checksum_records, csv_path)
        
        # Generate documentation
        md_path = docs_dir / "checksums.md"
        print(f"\nGenerating documentation at {md_path}...")
        write_checksums_documentation(
            checksum_records=checksum_records,
            output_path=md_path,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Log operation success
        log_operation(
            operation="checksum_recording",
            input_file="data/",
            output_file=f"data/checksums.json, docs/reproducibility/checksums.md",
            parameters={"file_count": len(data_files)},
            status="completed"
        )
        
        print("\n✓ Checksum recording completed successfully!")
        print(f"  - JSON record: {json_path}")
        print(f"  - CSV record: {csv_path}")
        print(f"  - Documentation: {md_path}")
        
        return True
        
    except Exception as e:
        log_operation(
            operation="checksum_recording",
            input_file="data/",
            output_file="N/A",
            parameters={"error": str(e)},
            status="failed"
        )
        print(f"\n✗ Checksum recording failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    success = run_checksum_recording()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
