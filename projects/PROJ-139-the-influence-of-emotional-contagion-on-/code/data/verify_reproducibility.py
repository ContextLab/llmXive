"""
Reproducibility Verification Script (T028)

This script verifies that the pipeline is reproducible by:
1. Loading the previously recorded artifact checksums from state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml
2. Re-computing the SHA-256 checksums for all recorded artifacts in the current state.
3. Comparing the new checksums against the recorded ones.
4. Writing a verification report to data/processed/reproducibility_report.json.

If any checksums do not match, the script raises a RuntimeError to fail loudly.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

from config.settings import get_config, DatasetPaths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact file not found for checksum verification: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {e}")

def load_recorded_checksums(config: Any) -> Dict[str, str]:
    """Load the checksums recorded in the project state YAML."""
    state_file = config.project_state_file
    if not os.path.exists(state_file):
        raise FileNotFoundError(f"Project state file not found: {state_file}")
    
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    
    # The checksums are expected to be in state_data['artifact_checksums']
    # Based on T027 description: "Update state/projects/...yaml with a map of file paths to SHA-256 hashes"
    checksums = state_data.get('artifact_checksums', {})
    if not checksums:
        logger.warning("No artifact checksums found in state file. Verification cannot proceed.")
        return {}
    
    return checksums

def verify_artifacts(recorded_checksums: Dict[str, str], base_path: Path) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """
    Verify current artifacts against recorded checksums.
    Returns:
      - matches: dict of path -> current_hash for matching files
      - mismatches: dict of path -> (old_hash, new_hash)
      - missing: list of paths that are missing
    """
    matches = {}
    mismatches = {}
    missing = []

    for rel_path, expected_hash in recorded_checksums.items():
        full_path = base_path / rel_path
        
        if not full_path.exists():
            missing.append(rel_path)
            logger.warning(f"Missing artifact: {full_path}")
            continue

        current_hash = compute_file_sha256(full_path)
        
        if current_hash == expected_hash:
            matches[rel_path] = current_hash
            logger.info(f"Verified: {rel_path}")
        else:
            mismatches[rel_path] = (expected_hash, current_hash)
            logger.error(f"Mismatch detected for {rel_path}")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Found:    {current_hash}")

    return matches, mismatches, missing

def generate_report(
    matches: Dict[str, str],
    mismatches: Dict[str, Tuple[str, str]],
    missing: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """Generate the reproducibility report."""
    total = len(matches) + len(mismatches) + len(missing)
    success = len(mismatches) == 0 and len(missing) == 0

    report = {
        "status": "success" if success else "failed",
        "total_artifacts_checked": total,
        "verified_count": len(matches),
        "mismatch_count": len(mismatches),
        "missing_count": len(missing),
        "details": {
            "verified": list(matches.keys()),
            "mismatches": {k: {"expected": v[0], "found": v[1]} for k, v in mismatches.items()},
            "missing": missing
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    config = get_config()
    paths = config.paths
    
    logger.info("Starting reproducibility verification (T028)...")
    
    # 1. Load recorded checksums
    try:
        recorded_checksums = load_recorded_checksums(config)
        if not recorded_checksums:
            raise RuntimeError("No checksums recorded. Run T027 first to record artifact hashes.")
    except Exception as e:
        logger.error(f"Failed to load recorded checksums: {e}")
        raise

    # 2. Verify artifacts
    matches, mismatches, missing = verify_artifacts(recorded_checksums, Path("."))

    # 3. Generate report
    output_path = paths.processed_dir / "reproducibility_report.json"
    report = generate_report(matches, mismatches, missing, output_path)

    # 4. Fail loudly if verification failed
    if report["status"] == "failed":
        error_msg = f"Reproducibility verification FAILED. Mismatches: {len(mismatches)}, Missing: {len(missing)}. See {output_path} for details."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Reproducibility verification PASSED. {len(matches)} artifacts verified. Report saved to {output_path}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
