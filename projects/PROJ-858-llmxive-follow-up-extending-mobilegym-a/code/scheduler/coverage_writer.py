"""
Coverage Writer Module

Writes aggregated coverage vectors to data/processed/coverage_vectors.json
and manages checksums for reproducibility.
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from utils.logging import get_logger, log_with_context
from scheduler.state_coverage import aggregate_coverage_vectors

logger = get_logger(__name__)


def load_aggregated_vectors(source_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load aggregated coverage vectors from a source file or generate them.
    
    If source_path is provided, loads from that file.
    Otherwise, attempts to load from the default location or generates from raw rollouts.
    
    Args:
        source_path: Optional path to load vectors from.
        
    Returns:
        List of aggregated coverage vector dictionaries.
        
    Raises:
        FileNotFoundError: If source file doesn't exist and no raw data is available.
    """
    if source_path:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('vectors', [])
    
    # Default path for aggregated vectors (from T026 processing)
    default_path = Path("data/processed/aggregated_vectors.json")
    if default_path.exists():
        with open(default_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('vectors', [])
    
    # If no aggregated file exists, we need to process raw rollouts
    # This assumes T025/T026 have run and produced raw rollout data
    raw_rollouts_path = Path("data/raw/rollouts.json")
    if not raw_rollouts_path.exists():
        raise FileNotFoundError(
            "No aggregated vectors found and no raw rollouts available. "
            "Please run state_coverage.py first to generate rollouts."
        )
    
    logger.info(f"Loading raw rollouts from {raw_rollouts_path} for aggregation")
    with open(raw_rollouts_path, 'r', encoding='utf-8') as f:
        rollouts = json.load(f)
    
    # Aggregate the vectors
    aggregated = aggregate_coverage_vectors(rollouts)
    return aggregated


def write_coverage_vectors(vectors: List[Dict[str, Any]], output_path: str) -> str:
    """
    Write coverage vectors to a JSON file with metadata.
    
    Args:
        vectors: List of coverage vector dictionaries.
        output_path: Path to write the JSON file.
        
    Returns:
        Path to the written file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "total_vectors": len(vectors),
        "schema": "coverage_vector_v1"
    }
    
    output_data = {
        "metadata": metadata,
        "vectors": vectors
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully wrote {len(vectors)} coverage vectors to {output_path}")
    return str(output_file)


def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_checksum_file(artifact_path: str, checksum_registry_path: str = "data/raw/.checksums.txt") -> None:
    """
    Update the checksum registry with the new artifact's checksum.
    
    Args:
        artifact_path: Path to the artifact file.
        checksum_registry_path: Path to the checksum registry file.
    """
    checksum = calculate_file_checksum(artifact_path)
    filename = os.path.basename(artifact_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    registry_entry = f"{filename}: {checksum} (generated at {timestamp})\n"
    
    # Append to registry
    with open(checksum_registry_path, 'a', encoding='utf-8') as f:
        f.write(registry_entry)
    
    logger.info(f"Updated checksum registry: {filename} -> {checksum[:16]}...")


def main():
    """
    Main entry point for writing coverage vectors.
    
    Reads aggregated vectors, writes to data/processed/coverage_vectors.json,
    and updates checksums.
    """
    logger.info("Starting coverage vector write process")
    
    # Configuration
    output_path = "data/processed/coverage_vectors.json"
    checksum_registry = "data/raw/.checksums.txt"
    
    try:
        # Load aggregated vectors
        vectors = load_aggregated_vectors()
        
        if not vectors:
            logger.warning("No coverage vectors found to write")
            return
        
        logger.info(f"Loaded {len(vectors)} coverage vectors")
        
        # Write to file
        written_path = write_coverage_vectors(vectors, output_path)
        
        # Calculate and record checksum
        update_checksum_file(written_path, checksum_registry)
        
        logger.info("Coverage vector write process completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
