import os
import sys
import subprocess
import hashlib
import shutil
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Import local utilities to ensure dependency chain
from src.utils.config import get_project_root, get_config
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.validate_urls import validate_dataset_urls, parse_research_manifest

# Configure logger for this module
logger = get_logger("download")

# Constants
TIMEOUT_SECONDS = 30
SCOPE_DEVIATION_LOG_PATH = "data/logs/scope_deviation.log"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    if not file_path.exists():
        return False
    actual = compute_sha256(file_path)
    return actual.lower() == expected_checksum.lower()

def download_via_wget(url: str, dest_path: Path, timeout: int = TIMEOUT_SECONDS) -> bool:
    """Download file using wget."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["wget", "--timeout", str(timeout), "-O", str(dest_path), url]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Downloaded {url} to {dest_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Wget failed for {url}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("wget not found in PATH. Please install wget.")
        return False

def clone_via_git(repo_url: str, dest_dir: Path, timeout: int = TIMEOUT_SECONDS) -> bool:
    """Clone repository using git."""
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    cmd = ["git", "clone", "--depth", "1", "--timeout", str(timeout), repo_url, str(dest_dir)]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Cloned {repo_url} to {dest_dir}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed for {repo_url}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("git not found in PATH. Please install git.")
        return False

def log_scope_deviation(source: str, error: str, fallback: str) -> None:
    """Log a scope deviation event to the designated log file."""
    log_dir = Path(get_project_root()) / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / SCOPE_DEVIATION_LOG_PATH
    
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": source,
        "error": error,
        "fallback": fallback
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(event) + "\n")
    logger.warning(f"Scope deviation logged: {source} -> {fallback} due to {error}")

def fetch_nist_juliet_c() -> Tuple[bool, Optional[Path]]:
    """
    Attempt to fetch the official NIST Juliet repository for C/C++.
    Primary Mandate: NIST Juliet for C/C++.
    Returns (success, path_to_data).
    """
    # NIST Juliet C/C++ repository URL (verified source)
    nist_repo = "https://github.com/codeseclab/Juliet_C_TestSuite.git"
    dest_dir = Path(get_project_root()) / "data" / "raw" / "juliet_c"
    
    logger.info(f"Attempting to fetch NIST Juliet C repository: {nist_repo}")
    try:
        # Try git clone with timeout
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--timeout", str(TIMEOUT_SECONDS), nist_repo, str(dest_dir)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 10
        )
        if result.returncode == 0:
            logger.info("Successfully cloned NIST Juliet C repository.")
            return True, dest_dir
        else:
            raise Exception(result.stderr)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        error_msg = str(e)
        logger.warning(f"NIST Juliet C fetch failed: {error_msg}")
        return False, None

def fetch_bigvul_c() -> Tuple[bool, Optional[Path]]:
    """
    Fallback: Fetch BigVul dataset for C code.
    """
    # BigVul dataset URL (verified source)
    bigvul_repo = "https://github.com/fpv-ibm/BigVul.git"
    dest_dir = Path(get_project_root()) / "data" / "raw" / "bigvul_c"
    
    logger.info(f"Attempting to fetch BigVul C repository: {bigvul_repo}")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--timeout", str(TIMEOUT_SECONDS), bigvul_repo, str(dest_dir)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 10
        )
        if result.returncode == 0:
            logger.info("Successfully cloned BigVul C repository.")
            return True, dest_dir
        else:
            raise Exception(result.stderr)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        error_msg = str(e)
        logger.error(f"BigVul C fetch failed: {error_msg}")
        return False, None

def fetch_vuldeepecker_python() -> Tuple[bool, Optional[Path]]:
    """
    Fetch VulDeePecker dataset for Python code.
    """
    # VulDeePecker dataset URL (verified source)
    vuldeepecker_repo = "https://github.com/zhongjiajie/VulDeePecker.git"
    dest_dir = Path(get_project_root()) / "data" / "raw" / "vuldeepecker_python"
    
    logger.info(f"Attempting to fetch VulDeePecker Python repository: {vuldeepecker_repo}")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--timeout", str(TIMEOUT_SECONDS), vuldeepecker_repo, str(dest_dir)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 10
        )
        if result.returncode == 0:
            logger.info("Successfully cloned VulDeePecker Python repository.")
            return True, dest_dir
        else:
            raise Exception(result.stderr)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        error_msg = str(e)
        logger.error(f"VulDeePecker Python fetch failed: {error_msg}")
        return False, None

def fetch_bigvul_js() -> Tuple[bool, Optional[Path]]:
    """
    Fetch BigVul dataset for JavaScript code.
    """
    # BigVul dataset URL (verified source)
    bigvul_repo = "https://github.com/fpv-ibm/BigVul.git"
    dest_dir = Path(get_project_root()) / "data" / "raw" / "bigvul_js"
    
    logger.info(f"Attempting to fetch BigVul JavaScript repository: {bigvul_repo}")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--timeout", str(TIMEOUT_SECONDS), bigvul_repo, str(dest_dir)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 10
        )
        if result.returncode == 0:
            logger.info("Successfully cloned BigVul JavaScript repository.")
            return True, dest_dir
        else:
            raise Exception(result.stderr)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
        error_msg = str(e)
        logger.error(f"BigVul JavaScript fetch failed: {error_msg}")
        return False, None

def validate_dataset(dataset_name: str, path: Path) -> bool:
    """Validate that a dataset directory contains expected files."""
    if not path.exists():
        logger.error(f"Dataset path does not exist: {path}")
        return False
    
    # Basic validation: check if directory is not empty
    files = list(path.glob("*"))
    if not files:
        logger.error(f"Dataset directory is empty: {path}")
        return False
    
    logger.info(f"Dataset validated: {dataset_name} at {path}")
    return True

def download_all_datasets() -> Dict[str, Any]:
    """
    Orchestrate the download of all required datasets.
    Implements the fallback logic for NIST Juliet -> BigVul for C.
    Returns a dictionary of results.
    """
    results = {
        "nist_juliet_c": {"success": False, "path": None},
        "bigvul_c": {"success": False, "path": None},
        "vuldeepecker_python": {"success": False, "path": None},
        "bigvul_js": {"success": False, "path": None}
    }
    
    log_stage_start("download_all_datasets")
    
    # 1. Fetch VulDeePecker (Python) - Independent
    logger.info("Step 1: Fetching VulDeePecker (Python)...")
    success, path = fetch_vuldeepecker_python()
    results["vuldeepecker_python"]["success"] = success
    results["vuldeepecker_python"]["path"] = str(path) if path else None
    if success:
        validate_dataset("vuldeepecker_python", path)
    
    # 2. Fetch BigVul (JavaScript) - Independent
    logger.info("Step 2: Fetching BigVul (JavaScript)...")
    success, path = fetch_bigvul_js()
    results["bigvul_js"]["success"] = success
    results["bigvul_js"]["path"] = str(path) if path else None
    if success:
        validate_dataset("bigvul_js", path)
    
    # 3. Fetch NIST Juliet (C/C++) - Primary Mandate
    logger.info("Step 3: Attempting to fetch NIST Juliet (C/C++)...")
    success, path = fetch_nist_juliet_c()
    
    if success:
        results["nist_juliet_c"]["success"] = True
        results["nist_juliet_c"]["path"] = str(path)
        validate_dataset("nist_juliet_c", path)
    else:
        # Fallback Logic: Log Scope Deviation and switch to BigVul for C
        logger.warning("NIST Juliet fetch failed. Switching to BigVul for C code.")
        log_scope_deviation(
            source="NIST Juliet",
            error="Fetch failed (HTTP 404, timeout, or network error)",
            fallback="BigVul C"
        )
        
        # Attempt BigVul C
        logger.info("Attempting fallback: Fetching BigVul (C)...")
        success_c, path_c = fetch_bigvul_c()
        results["bigvul_c"]["success"] = success_c
        results["bigvul_c"]["path"] = str(path_c) if path_c else None
        
        if success_c:
            logger.info("BigVul C fallback successful.")
            validate_dataset("bigvul_c", path_c)
        else:
            logger.error("Both NIST Juliet and BigVul C fetches failed.")
            # Fail loudly if ALL sources fail
            raise RuntimeError(
                "CRITICAL FAILURE: Unable to fetch C/C++ dataset. "
                "Both NIST Juliet (primary) and BigVul (fallback) failed. "
                "Pipeline cannot proceed without real data."
            )
    
    # Final Check: Ensure at least one C source is available
    if not results["nist_juliet_c"]["success"] and not results["bigvul_c"]["success"]:
        raise RuntimeError("CRITICAL FAILURE: No C dataset available.")
    
    log_stage_complete("download_all_datasets")
    return results

def main():
    """Entry point for the download script."""
    logger.info("Starting dataset download pipeline (T011).")
    
    # Validate URLs first (Dependency: T005)
    try:
        logger.info("Validating dataset URLs from research manifest...")
        validate_dataset_urls()
        logger.info("URL validation successful.")
    except Exception as e:
        logger.error(f"URL validation failed: {e}")
        raise RuntimeError("URL validation failed. Cannot proceed with download.")
    
    try:
        results = download_all_datasets()
        logger.info("Dataset download pipeline completed successfully.")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        return 0
    except Exception as e:
        logger.error(f"Download pipeline failed: {e}")
        log_stage_failure("download_all_datasets", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
