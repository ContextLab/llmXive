"""
Generate and record SHA256 checksums for all raw and processed data files
in state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml

Per Constitution Principle III - Data Integrity and Reproducibility
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add code directory to path for imports
code_dir = Path(__file__).parent
project_root = code_dir.parent.parent
sys.path.insert(0, str(code_dir))

from scripts.generate_checksums import compute_file_checksum_sha256, load_state_file, save_state_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_data_files(data_dir: Path) -> List[Path]:
    """Recursively find all data files in a directory."""
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    files = []
    for ext in ['*.csv', '*.json', '*.parquet', '*.txt', '*.tsv', '*.npy', '*.pkl', '*.h5', '*.hdf5']:
        files.extend(data_dir.rglob(ext))
    return files


def generate_checksums_for_data_files(
    data_dir: Path,
    checksums: Dict[str, Any],
    category: str = "raw"
) -> int:
    """Generate checksums for all files in a data directory."""
    files = find_data_files(data_dir)
    count = 0
    
    for file_path in files:
        rel_path = str(file_path.relative_to(project_root))
        try:
            checksum = compute_file_checksum_sha256(file_path)
            file_size = file_path.stat().st_size
            
            checksums[rel_path] = {
                "sha256": checksum,
                "size_bytes": file_size,
                "category": category,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
            count += 1
            logger.info(f"  Checksummed: {rel_path} ({file_size:,} bytes)")
        except Exception as e:
            logger.error(f"  Failed to checksum {rel_path}: {e}")
    
    return count


def main():
    """Main entry point for generating data checksums."""
    logger.info("=== T014: Generate SHA256 checksums for data files ===")
    
    # Define paths
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    state_file = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
    
    # Load existing state file or create new
    if state_file.exists():
        logger.info(f"Loading existing state file: {state_file}")
        state_data = load_state_file(state_file)
    else:
        logger.info(f"Creating new state file: {state_file}")
        state_data = {
            "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "artifacts": {},
            "data_checksums": {}
        }
    
    # Initialize data_checksums section
    if "data_checksums" not in state_data:
        state_data["data_checksums"] = {}
    
    checksum_count = 0
    
    # Process raw data
    logger.info(f"\nScanning raw data directory: {data_raw_dir}")
    checksum_count += generate_checksums_for_data_files(
        data_raw_dir,
        state_data["data_checksums"],
        category="raw"
    )
    
    # Process processed data
    logger.info(f"\nScanning processed data directory: {data_processed_dir}")
    checksum_count += generate_checksums_for_data_files(
        data_processed_dir,
        state_data["data_checksums"],
        category="processed"
    )
    
    # Update metadata
    state_data["generated_at"] = datetime.utcnow().isoformat() + "Z"
    state_data["data_checksums"]["_metadata"] = {
        "total_files": checksum_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "raw_dir": str(data_raw_dir.relative_to(project_root)),
        "processed_dir": str(data_processed_dir.relative_to(project_root))
    }
    
    # Save updated state file
    logger.info(f"\nSaving state file with {checksum_count} checksums: {state_file}")
    save_state_file(state_file, state_data)
    
    logger.info("\n=== Checksum generation complete ===")
    logger.info(f"Total files checksummed: {checksum_count}")
    logger.info(f"State file updated: {state_file}")
    
    # Print summary
    logger.info("\nChecksum Summary:")
    for path, info in state_data["data_checksums"].items():
        if not path.startswith("_"):
            logger.info(f"  {path}: {info['sha256'][:16]}... ({info['size_bytes']:,} bytes)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
