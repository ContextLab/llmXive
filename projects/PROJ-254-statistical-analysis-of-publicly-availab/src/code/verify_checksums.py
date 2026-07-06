import hashlib
import json
import sys
from pathlib import Path
from utils import get_logger, setup_logging, set_deterministic_seed

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> dict:
    """Load checksum manifest from JSON file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_checksums(manifest_path: Path, data_dir: Path) -> dict:
    """Verify checksums for all files in manifest."""
    manifest = load_manifest(manifest_path)
    results = {
        "verified": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }

    for file_info in manifest.get("files", []):
        file_path = data_dir / file_info["relative_path"]
        expected_checksum = file_info["checksum"]

        if not file_path.exists():
            results["missing"] += 1
            results["details"].append({
                "file": file_info["relative_path"],
                "status": "missing",
                "expected": expected_checksum
            })
            continue

        actual_checksum = compute_sha256(file_path)
        if actual_checksum == expected_checksum:
            results["verified"] += 1
            results["details"].append({
                "file": file_info["relative_path"],
                "status": "verified",
                "checksum": actual_checksum
            })
        else:
            results["failed"] += 1
            results["details"].append({
                "file": file_info["relative_path"],
                "status": "failed",
                "expected": expected_checksum,
                "actual": actual_checksum
            })

    return results

def print_summary(results: dict) -> None:
    """Print verification summary."""
    logger = get_logger()
    logger.info(f"Verification Summary:")
    logger.info(f"  Verified: {results['verified']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Missing: {results['missing']}")

    if results["failed"] > 0 or results["missing"] > 0:
        logger.warning("Some files failed verification or are missing!")
        for detail in results["details"]:
            if detail["status"] != "verified":
                logger.warning(f"  {detail['file']}: {detail['status']}")
    else:
        logger.info("All files verified successfully!")

def main() -> int:
    """Main entry point for checksum verification."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    manifest_path = Path("data/raw/manifest.json")
    data_dir = Path("data/raw")

    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return 1

    try:
        results = verify_checksums(manifest_path, data_dir)
        print_summary(results)
        return 0 if results["failed"] == 0 and results["missing"] == 0 else 1
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
