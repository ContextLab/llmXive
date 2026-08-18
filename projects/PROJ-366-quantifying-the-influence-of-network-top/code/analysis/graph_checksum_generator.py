import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import get_config, get_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_graph_files(graph_dir: Path) -> List[Path]:
    """Find all graph pickle files in the directory."""
    if not graph_dir.exists():
        logger.error(f"Graph directory does not exist: {graph_dir}")
        return []
    
    files = list(graph_dir.glob("graph_*.pkl"))
    logger.info(f"Found {len(files)} graph files in {graph_dir}")
    return sorted(files)

def generate_checksums_for_graphs(graph_files: List[Path], algorithm: str = 'sha256') -> Dict[str, str]:
    """Generate checksums for a list of graph files."""
    checksums = {}
    for file_path in graph_files:
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            checksums[file_path.name] = checksum
            logger.info(f"Checksum for {file_path.name}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise
    return checksums

def save_checksum_manifest(checksums: Dict[str, str], output_path: Path, algorithm: str = 'sha256'):
    """Save the checksum manifest to a JSON file."""
    manifest = {
        "checksums": checksums,
        "algorithm": algorithm,
        "generated_at": datetime.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest saved to {output_path}")

def main():
    """Main entry point for generating graph checksums."""
    config = get_config()
    paths = get_paths()
    
    graph_dir = paths['processed_graphs']
    output_file = paths['checksums_file']
    
    logger.info(f"Processing graph directory: {graph_dir}")
    
    graph_files = find_graph_files(graph_dir)
    if not graph_files:
        logger.error("No graph files found. Exiting.")
        sys.exit(1)
    
    checksums = generate_checksums_for_graphs(graph_files)
    
    if not checksums:
        logger.error("Failed to generate any checksums. Exiting.")
        sys.exit(1)
    
    save_checksum_manifest(checksums, output_file)
    
    logger.info("Graph checksum generation completed successfully.")

if __name__ == "__main__":
    main()
