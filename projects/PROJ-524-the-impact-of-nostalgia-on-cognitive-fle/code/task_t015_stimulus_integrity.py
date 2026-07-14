"""
Task T015: Stimulus File Integrity Check

Implements stimulus file integrity check:
1. Fetch canonical checksum from dataset's metadata.json or GitHub release asset.
2. Compare against local file SHA-256.
3. Log mismatch as ERR_STIMULUS_CORRUPT.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from config import get_config, get_env_str, ensure_dirs
from utils import setup_logging, compute_sha256, log_info, log_warning, log_error, get_timestamp

# Constants
STIMULUS_SUBDIR = "stimuli"
METADATA_FILENAME = "metadata.json"
CHECKSUM_KEY = "stimulus_checksum"  # Expected key in metadata.json
LOG_FILE = "data/processed/stimulus_integrity_log.json"
GITHUB_RELEASE_URL = "https://github.com/example/nostalgia-cognitive-flexibility/releases/download/v1.0.0/metadata.json"


def fetch_canonical_checksum_from_metadata(metadata_path: Path) -> Optional[str]:
    """
    Fetch canonical checksum from local metadata.json if it exists.
    """
    if not metadata_path.exists():
        log_warning(f"Metadata file not found at {metadata_path}. Cannot fetch checksum.")
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if CHECKSUM_KEY in metadata:
            return metadata[CHECKSUM_KEY]
        else:
            log_warning(f"Checksum key '{CHECKSUM_KEY}' not found in metadata.json.")
            return None
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse metadata.json: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error reading metadata.json: {e}")
        return None


def fetch_canonical_checksum_from_github() -> Optional[str]:
    """
    Fallback: Fetch canonical checksum from GitHub release metadata.
    Requires 'requests' library.
    """
    try:
        import requests
        log_info(f"Attempting to fetch checksum from GitHub release: {GITHUB_RELEASE_URL}")
        
        response = requests.get(GITHUB_RELEASE_URL, timeout=10)
        response.raise_for_status()
        
        metadata = response.json()
        if CHECKSUM_KEY in metadata:
            return metadata[CHECKSUM_KEY]
        else:
            log_warning(f"Checksum key '{CHECKSUM_KEY}' not found in GitHub metadata.")
            return None
    except ImportError:
        log_error("The 'requests' library is required to fetch checksums from GitHub. Please install it.")
        return None
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to fetch checksum from GitHub: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error fetching checksum from GitHub: {e}")
        return None


def compute_local_checksum(stimulus_path: Path) -> Optional[str]:
    """
    Compute SHA-256 checksum of the local stimulus file.
    """
    if not stimulus_path.exists():
        log_error(f"Stimulus file not found at {stimulus_path}. Cannot compute checksum.")
        return None

    try:
        return compute_sha256(stimulus_path)
    except Exception as e:
        log_error(f"Failed to compute SHA-256 for {stimulus_path}: {e}")
        return None


def check_integrity(
    project_root: Path,
    stimulus_filename: str = "nostalgia_stimuli_v1.zip"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Main integrity check logic.
    
    Returns:
        Tuple[bool, Dict]: (is_valid, report_dict)
    """
    stimulus_dir = project_root / "data" / STIMULUS_SUBDIR
    metadata_path = project_root / "data" / STIMULUS_SUBDIR / METADATA_FILENAME
    stimulus_path = stimulus_dir / stimulus_filename

    report = {
        "timestamp": get_timestamp(),
        "stimulus_file": str(stimulus_path),
        "metadata_file": str(metadata_path),
        "canonical_source": None,
        "canonical_checksum": None,
        "local_checksum": None,
        "status": "UNKNOWN",
        "error": None
    }

    # 1. Compute local checksum
    local_checksum = compute_local_checksum(stimulus_path)
    report["local_checksum"] = local_checksum

    if local_checksum is None:
        report["status"] = "FAIL_FILE_NOT_FOUND"
        log_error(f"Stimulus integrity check FAILED: File not found at {stimulus_path}")
        return False, report

    # 2. Fetch canonical checksum
    canonical_checksum = fetch_canonical_checksum_from_metadata(metadata_path)
    
    if canonical_checksum:
        report["canonical_source"] = "local_metadata"
        report["canonical_checksum"] = canonical_checksum
    else:
        log_info("Local metadata checksum not found. Attempting GitHub fallback.")
        canonical_checksum = fetch_canonical_checksum_from_github()
        if canonical_checksum:
            report["canonical_source"] = "github_release"
            report["canonical_checksum"] = canonical_checksum
        else:
            report["status"] = "FAIL_NO_CANONICAL"
            log_error("Stimulus integrity check FAILED: Could not fetch canonical checksum from any source.")
            return False, report

    # 3. Compare
    if local_checksum == canonical_checksum:
        report["status"] = "PASS"
        log_info(f"Stimulus integrity check PASSED. Checksum: {local_checksum}")
        return True, report
    else:
        report["status"] = "FAIL_MISMATCH"
        report["error"] = "ERR_STIMULUS_CORRUPT"
        log_error(f"ERR_STIMULUS_CORRUPT: Checksum mismatch for {stimulus_filename}")
        log_error(f"  Expected: {canonical_checksum}")
        log_error(f"  Found:    {local_checksum}")
        return False, report


def save_report(report: Dict[str, Any], output_path: Path):
    """
    Save the integrity check report to a JSON file.
    """
    ensure_dirs([output_path.parent])
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    log_info(f"Integrity report saved to {output_path}")


def main():
    """
    Entry point for the script.
    """
    # Setup logging
    logger = setup_logging("task_t015", log_level=logging.INFO)
    
    # Get configuration
    config = get_config()
    project_root = Path(config.get("project_root", "."))
    
    # Determine stimulus filename from config or default
    stimulus_filename = get_env_str("STIMULUS_FILENAME", "nostalgia_stimuli_v1.zip")
    
    log_info(f"Starting stimulus integrity check for: {stimulus_filename}")
    
    is_valid, report = check_integrity(project_root, stimulus_filename)
    
    # Save report
    output_path = Path(project_root) / "data" / "processed" / "stimulus_integrity_log.json"
    save_report(report, output_path)
    
    if not is_valid:
        log_error("Stimulus integrity check completed with errors. See log for details.")
        # Exit with non-zero code to indicate failure
        return 1
    
    log_info("Stimulus integrity check completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
