import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

from utils.logging import get_logger, log_with_context

logger = get_logger("update_checksums")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def find_artifacts() -> Dict[str, Path]:
    """Find all required artifacts in the project."""
    artifacts = {}
    
    # Define required artifact paths based on task requirements
    required_artifacts = [
        "data/processed/scheduler_trace.json",
        "data/processed/coverage_vectors.json",
        "data/processed/sensitivity_report.md",
        "data/processed/convergence_results.json",
        "data/processed/transfer_results.json",
        "data/processed/success_rate_vs_steps.png",
        "data/raw/.checksums.txt",
        "data/processed/held_out_test_set.json",
    ]
    
    for rel_path in required_artifacts:
        file_path = Path(rel_path)
        if file_path.exists():
            artifacts[rel_path] = file_path
        else:
            logger.warning(f"Artifact not found: {rel_path}")
    
    return artifacts

def generate_checksum_registry(artifacts: Dict[str, Path]) -> Dict[str, str]:
    """Generate a checksum registry for all artifacts."""
    registry = {}
    
    for rel_path, file_path in artifacts.items():
        checksum = calculate_sha256(file_path)
        registry[rel_path] = checksum
        logger.info(f"Generated checksum for {rel_path}: {checksum}")
    
    return registry

def update_checksum_file(registry: Dict[str, str], output_path: Path):
    """Write the checksum registry to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Checksum registry written to {output_path}")

def main():
    """Entry point for checksum update script."""
    logger.info("Starting artifact checksum generation")
    
    artifacts = find_artifacts()
    
    if not artifacts:
        logger.error("No artifacts found to checksum")
        sys.exit(1)
    
    registry = generate_checksum_registry(artifacts)
    
    output_path = Path("data/processed/checksum_registry.json")
    update_checksum_file(registry, output_path)
    
    logger.info("Checksum generation complete")
    sys.exit(0)

if __name__ == "__main__":
    main()
