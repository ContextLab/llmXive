"""
Verify Stimuli Checksums against the archived manifest.

This script computes the SHA-256 checksum of each loaded stimulus image
and compares it against the checksum recorded in the archive manifest
(created by T014a). It writes the verification results to
`state/artifact_hashes.json`.
"""
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Import from local project structure (consistent with T004/T005)
from src.lib.utils import compute_file_checksum
from src.metrics.load_stimuli import load_stimuli_from_archive, StimuliLoaderError
from src.config import PROJECT_ROOT, STATE_DIR, DATA_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "verify_stimuli.log")
    ]
)
logger = logging.getLogger(__name__)


def verify_stimuli(max_images: int | None = None) -> Tuple[int, int, List[Dict]]:
    """
    Verify checksums of stimuli in the local archive.

    Args:
        max_images: Optional limit on the number of images to verify.

    Returns:
        A tuple of (total_checked, passed_count, results_list).
    """
    archive_path = DATA_DIR / "stimuli" / "raw"
    manifest_path = archive_path / "manifest.json"

    if not archive_path.exists():
        raise FileNotFoundError(f"Stimuli archive not found at {archive_path}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    # Load manifest to get expected checksums
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse manifest: {e}")

    expected_checksums = {item["filename"]: item["sha256"] for item in manifest["items"]}

    # Load stimuli from the archive (re-uses T014 logic)
    try:
        stimuli = load_stimuli_from_archive(max_images=max_images)
    except StimuliLoaderError as e:
        logger.error(f"Failed to load stimuli from archive: {e}")
        raise

    results = []
    passed_count = 0
    total_checked = 0

    for img_path, img_id in stimuli:
        total_checked += 1
        
        if img_id not in expected_checksums:
            logger.warning(f"Image {img_id} not found in manifest. Skipping verification.")
            results.append({
                "image_id": img_id,
                "path": str(img_path),
                "status": "MISSING_IN_MANIFEST",
                "computed_checksum": None,
                "expected_checksum": None
            })
            continue

        expected = expected_checksums[img_id]
        
        if not img_path.exists():
            logger.error(f"Image file missing on disk: {img_path}")
            results.append({
                "image_id": img_id,
                "path": str(img_path),
                "status": "FILE_MISSING",
                "computed_checksum": None,
                "expected_checksum": expected
            })
            continue

        try:
            computed = compute_file_checksum(img_path)
        except Exception as e:
            logger.error(f"Failed to compute checksum for {img_path}: {e}")
            results.append({
                "image_id": img_id,
                "path": str(img_path),
                "status": "COMPUTE_ERROR",
                "computed_checksum": None,
                "expected_checksum": expected
            })
            continue

        if computed == expected:
          passed_count += 1
          status = "PASS"
        else:
          status = "FAIL"
          logger.error(f"Checksum mismatch for {img_id}: Expected {expected}, Got {computed}")

        results.append({
            "image_id": img_id,
            "path": str(img_path),
            "status": status,
            "computed_checksum": computed,
            "expected_checksum": expected
        })

    return total_checked, passed_count, results


def main() -> None:
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(description="Verify stimuli checksums against archive manifest.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Maximum number of images to verify (default: all)"
    )
    args = parser.parse_args()

    try:
        total, passed, results = verify_stimuli(max_images=args.limit)
        
        # Calculate summary stats
        failed = total - passed
        status = "SUCCESS" if failed == 0 else "FAILED"
        
        logger.info(f"Verification Complete: {total} checked, {passed} passed, {failed} failed.")
        
        # Prepare output artifact
        output_data = {
            "verification_status": status,
            "total_images": total,
            "passed_count": passed,
            "failed_count": failed,
            "timestamp": str(Path(__file__).stat().st_mtime), # Simple timestamp proxy
            "details": results
        }

        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        output_path = STATE_DIR / "artifact_hashes.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results written to {output_path}")

        if failed > 0:
            logger.error("One or more checksums did not match. Exiting with error code 1.")
            sys.exit(1)
        
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Critical error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
