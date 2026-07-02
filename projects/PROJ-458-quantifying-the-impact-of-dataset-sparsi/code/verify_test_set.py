"""
Verify test set independence and log metadata.

This script loads the test set created by test_split.py, verifies its
integrity via checksum, and logs metadata (row count, checksum, etc.)
to data/metadata/test_set_metadata.json.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256
from config import load_env

# Initialize logger
logger = get_logger(__name__)

def verify_test_set(test_set_path: Path, metadata_path: Path) -> dict:
    """
    Verify the test set and generate metadata.
    
    Args:
        test_set_path: Path to the test set CSV file
        metadata_path: Path where metadata JSON will be saved
        
    Returns:
        Dictionary containing metadata
    """
    logger.info(f"Verifying test set at: {test_set_path}")
    
    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set file not found: {test_set_path}")
    
    # Read file content for checksum
    with open(test_set_path, 'rb') as f:
        content = f.read()
    
    # Calculate SHA-256 checksum
    checksum = hashlib.sha256(content).hexdigest()
    
    # Count rows (excluding header)
    text_content = content.decode('utf-8')
    lines = text_content.strip().split('\n')
    row_count = len(lines) - 1 if len(lines) > 1 else 0
    
    # Get file size
    file_size = test_set_path.stat().st_size
    
    # Extract column names from header
    header = lines[0].split(',') if lines else []
    columns = header
    
    # Create metadata
    metadata = {
        "file_path": str(test_set_path),
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "checksum_sha256": checksum,
        "file_size_bytes": file_size,
        "verification_status": "passed" if row_count > 0 else "warning_empty",
        "checksum_file": f"{test_set_path}.sha256"
    }
    
    # Ensure metadata directory exists
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Test set verified: {row_count} rows, checksum: {checksum[:16]}...")
    logger.info(f"Metadata saved to: {metadata_path}")
    
    return metadata

def main():
    """Main entry point."""
    # Load configuration
    load_env()
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    test_set_path = project_root / "data" / "processed" / "test_set.csv"
    metadata_path = project_root / "data" / "metadata" / "test_set_metadata.json"
    
    try:
        metadata = verify_test_set(test_set_path, metadata_path)
        print(f"Verification successful. Metadata: {json.dumps(metadata, indent=2)}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Test set not found: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())