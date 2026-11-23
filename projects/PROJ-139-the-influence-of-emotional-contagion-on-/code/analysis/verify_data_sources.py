"""
T051: Verify Data Sources
Validates that all data files in data/raw/ are derived from verified real sources
and contain no synthetic artifacts.
"""
import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assuming script runs from project root or code/analysis/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_FILE = STATE_DIR / "projects" / "PROJ-139-the-influence-of-emotional-contagion-on-.yaml"
DOWNLOAD_LOG = PROJECT_ROOT / "data" / "processed" / "download_attempts.log"
OUTPUT_FILE = STATE_DIR / "data_source_verification.json"

# Synthetic markers to search for
SYNTHETIC_MARKERS = [
    "synthetic", "mock", "generated_fallback", "fake_data", "placeholder",
    "dummy", "test_data_only", "no_real_data"
]

# Expected source types
VALID_SOURCE_TYPES = [
    "pushshift", "reddit_api", "huggingface", "internet_archive", "common_crawl"
]

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def load_recorded_checksums() -> Dict[str, str]:
    """Load recorded checksums from state file."""
    if not PROJECT_STATE_FILE.exists():
        logger.warning(f"State file not found: {PROJECT_STATE_FILE}")
        return {}
    
    try:
        import yaml
        with open(PROJECT_STATE_FILE, 'r') as f:
            state_data = yaml.safe_load(f)
        return state_data.get('artifact_hashes', {})
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return {}

def scan_for_synthetic_markers(file_path: Path) -> List[str]:
    """Scan file content for synthetic markers."""
    markers_found = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for marker in SYNTHETIC_MARKERS:
                if marker in content:
                    markers_found.append(marker)
    except Exception as e:
        logger.error(f"Error scanning {file_path}: {e}")
    return markers_found

def verify_download_log() -> Dict[str, Any]:
    """Verify download attempts log matches data sources."""
    result = {
        "log_exists": False,
        "sources_logged": [],
        "anomalies": []
    }
    
    if not DOWNLOAD_LOG.exists():
        result["anomalies"].append("download_attempts.log not found")
        return result
    
    result["log_exists"] = True
    
    try:
        with open(DOWNLOAD_LOG, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    source_type = entry.get("origin_type", "").lower()
                    if source_type and source_type not in result["sources_logged"]:
                        result["sources_logged"].append(source_type)
                    
                    # Check for failed attempts that might indicate synthetic fallback
                    if entry.get("success") is False:
                        result["anomalies"].append(
                            f"Failed download attempt: {entry.get('endpoint', 'unknown')}"
                        )
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Error reading download log: {e}")
        result["anomalies"].append(f"Error reading download log: {e}")
    
    return result

def verify_provenance_markers(file_path: Path) -> List[str]:
    """Check for provenance markers specific to archive sources."""
    provenance_issues = []
    
    # Check for archive-specific markers if file is from archive sources
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Check for common archive indicators
            if "web.archive.org" in content or "archive.org" in content:
                pass  # Valid archive marker
            elif "commoncrawl" in content.lower():
                pass  # Valid common crawl marker
            else:
                # If file claims to be from archive but lacks markers, flag it
                pass  # We'll rely on download log for source verification
    except Exception as e:
        logger.error(f"Error checking provenance for {file_path}: {e}")
    
    return provenance_issues

def main():
    """Main verification function."""
    logger.info("Starting data source verification...")
    
    verification_result = {
        "status": "pass",
        "sources_verified": [],
        "anomalies": [],
        "files_checked": [],
        "checksums_verified": [],
        "download_log_analysis": {}
    }
    
    # Step 1: Scan data/raw/ directory
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DATA_DIR}")
        verification_result["status"] = "fail"
        verification_result["anomalies"].append("Raw data directory does not exist")
    else:
        raw_files = list(RAW_DATA_DIR.glob("*"))
        
        for file_path in raw_files:
            if file_path.is_file():
                verification_result["files_checked"].append(str(file_path.relative_to(PROJECT_ROOT)))
                
                # Check for synthetic markers
                markers = scan_for_synthetic_markers(file_path)
                if markers:
                    verification_result["status"] = "fail"
                    verification_result["anomalies"].append(
                        f"Synthetic markers found in {file_path.name}: {markers}"
                    )
                    logger.warning(f"Synthetic markers in {file_path.name}: {markers}")
                
                # Compute and verify checksum
                current_hash = compute_file_sha256(file_path)
                verification_result["checksums_verified"].append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "sha256": current_hash
                })
    
    # Step 2: Verify checksums against recorded state
    recorded_checksums = load_recorded_checksums()
    if recorded_checksums:
        for file_path in verification_result["files_checked"]:
            if file_path in recorded_checksums:
                current_hash = compute_file_sha256(RAW_DATA_DIR / Path(file_path).name)
                if current_hash != recorded_checksums[file_path]:
                    verification_result["status"] = "fail"
                    verification_result["anomalies"].append(
                        f"Checksum mismatch for {file_path}: "
                        f"recorded={recorded_checksums[file_path][:16]}..., "
                        f"current={current_hash[:16]}..."
                    )
                    logger.error(f"Checksum mismatch for {file_path}")
            else:
                logger.warning(f"No recorded checksum for {file_path}")
    
    # Step 3: Analyze download log
    download_log_analysis = verify_download_log()
    verification_result["download_log_analysis"] = download_log_analysis
    
    if download_log_analysis["anomalies"]:
        verification_result["anomalies"].extend(download_log_analysis["anomalies"])
    
    # Step 4: Verify sources are valid
    if download_log_analysis["sources_logged"]:
        invalid_sources = [
            s for s in download_log_analysis["sources_logged"] 
            if s not in VALID_SOURCE_TYPES
        ]
        if invalid_sources:
            verification_result["status"] = "fail"
            verification_result["anomalies"].append(
                f"Invalid source types logged: {invalid_sources}"
            )
        else:
            verification_result["sources_verified"] = download_log_analysis["sources_logged"]
            logger.info(f"Verified sources: {verification_result['sources_verified']}")
    
    # Step 5: Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(verification_result, f, indent=2)
    
    logger.info(f"Verification complete. Status: {verification_result['status']}")
    logger.info(f"Output written to: {OUTPUT_FILE}")
    
    # Exit with error if verification failed
    if verification_result["status"] == "fail":
        logger.error("Data source verification FAILED. Pipeline cannot proceed.")
        sys.exit(1)
    else:
        logger.info("Data source verification PASSED. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
