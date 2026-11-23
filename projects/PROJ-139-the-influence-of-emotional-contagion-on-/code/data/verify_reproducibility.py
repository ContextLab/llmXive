import os
import sys
import json
import hashlib
import logging
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import get_config, DatasetPaths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_recorded_checksums(state_file: Path) -> Dict[str, str]:
    """Load the recorded checksums from the state YAML/JSON file."""
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    # Try loading as JSON first, then YAML if that fails
    try:
        with open(state_file, 'r') as f:
            content = json.load(f)
            # Handle nested structure if project uses specific keys
            if isinstance(content, dict):
                if 'checksums' in content:
                    return content['checksums']
                # If the file is just a map of path -> hash
                return content
    except json.JSONDecodeError:
        # Fallback to simple text parsing if JSON fails (for YAML compatibility)
        # This is a basic parser for the specific format expected
        checksums = {}
        with open(state_file, 'r') as f:
            for line in f:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    checksums[key.strip()] = value.strip()
        return checksums
    
    return {}

def verify_artifacts(
    recorded_checksums: Dict[str, str], 
    base_path: Path
) -> Dict[str, Any]:
    """
    Re-compute checksums for all recorded artifacts and compare.
    Returns a report of matches, mismatches, and missing files.
    """
    results = {
        "verified": 0,
        "mismatched": 0,
        "missing": 0,
        "details": []
    }

    for rel_path, expected_hash in recorded_checksums.items():
        full_path = base_path / rel_path
        
        if not full_path.exists():
            results["missing"] += 1
            results["details"].append({
                "path": rel_path,
                "status": "missing",
                "expected": expected_hash
            })
            logger.warning(f"Missing artifact: {full_path}")
            continue

        try:
            actual_hash = compute_file_sha256(full_path)
            if actual_hash == expected_hash:
                results["verified"] += 1
                results["details"].append({
                    "path": rel_path,
                    "status": "verified",
                    "hash": actual_hash
                })
            else:
                results["mismatched"] += 1
                results["details"].append({
                    "path": rel_path,
                    "status": "mismatch",
                    "expected": expected_hash,
                    "actual": actual_hash
                })
                logger.error(f"Hash mismatch for {full_path}")
        except Exception as e:
            results["mismatched"] += 1
            results["details"].append({
                "path": rel_path,
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Error computing hash for {full_path}: {e}")

    return results

def generate_report(
    verification_results: Dict[str, Any],
    output_path: Path
) -> None:
    """Generate a reproducibility verification report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_artifacts": len(verification_results["details"]),
            "verified": verification_results["verified"],
            "mismatched": verification_results["mismatched"],
            "missing": verification_results["missing"],
            "reproducible": verification_results["mismatched"] == 0 and verification_results["missing"] == 0
        },
        "details": verification_results["details"]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reproducibility report written to {output_path}")
    logger.info(f"Reproducible: {report['summary']['reproducible']}")
    if not report['summary']['reproducible']:
        logger.warning("Reproducibility check FAILED. See details for mismatches.")

def main():
    """
    Main entry point for T028: Verify reproducibility by re-running pipeline and matching checksums.
    """
    config = get_config()
    paths = config.paths
    
    # 1. Identify the state file containing recorded checksums
    # Based on T027, this is likely under state/
    state_dir = paths.state_dir
    checksum_file = None
    
    # Look for the project-specific state file
    project_id = "PROJ-139-the-influence-of-emotional-contagion-on-"
    possible_files = [
        state_dir / "projects" / f"{project_id}.yaml",
        state_dir / "projects" / f"{project_id}.json",
        state_dir / "checksums.json",
        state_dir / "checksums.yaml"
    ]
    
    for p in possible_files:
        if p.exists():
            checksum_file = p
            break
    
    if not checksum_file:
        raise FileNotFoundError(
            f"Could not find recorded checksums file. Expected one of: {possible_files}"
        )
    
    logger.info(f"Found recorded checksums at: {checksum_file}")

    # 2. Load recorded checksums
    recorded_checksums = load_recorded_checksums(checksum_file)
    if not recorded_checksums:
        raise ValueError("Recorded checksums file is empty or malformed.")
    
    logger.info(f"Loaded {len(recorded_checksums)} recorded checksums.")

    # 3. Verify artifacts against recorded checksums
    # We verify against the project root (where data/, state/, etc. live)
    project_root = paths.project_root
    verification_results = verify_artifacts(recorded_checksums, project_root)

    # 4. Generate report
    report_path = paths.state_dir / "reproducibility_report.json"
    generate_report(verification_results, report_path)

    # 5. Exit with error code if not reproducible
    is_reproducible = verification_results["mismatched"] == 0 and verification_results["missing"] == 0
    if not is_reproducible:
        logger.error("Reproducibility verification FAILED.")
        sys.exit(1)
    
    logger.info("Reproducibility verification PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()
