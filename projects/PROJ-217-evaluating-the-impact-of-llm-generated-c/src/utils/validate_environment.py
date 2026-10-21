"""
validate_environment.py

This script validates that the execution environment meets the requirements for the
user‑study portion of the project.  It performs the following checks:

1. All required Python packages import successfully.
2. Available RAM and free disk space are sufficient (≤ 7 GB RAM usage, ≥ 7 GB free disk).
3. A HuggingFace inference token is present and the HF inference API is reachable.
4. The Prolific API is reachable with a valid token.
5. The consent form PDF can be opened.

The script writes a detailed log to ``data/recruitment_validation.log`` and prints a
JSON line containing a ``success`` boolean to stdout.  It exits with status 0 if all
checks pass; otherwise it exits with status 1.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import psutil
import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Packages that the project relies on for later stages.
REQUIRED_PACKAGES = [
    "datasets",
    "pandas",
    "torch",
    "sentence_transformers",
    "nltk",
    "rouge_score",
    "statsmodels",
    "scipy",
    "sklearn",
    "tiktoken",
    "matplotlib",
    "textstat",
]

# Environment variable names.
HF_TOKEN_ENV = "HF_TOKEN"
PROLIFIC_TOKEN_ENV = "PROLIFIC_API_TOKEN"

# API endpoints.
HF_PING_URL = "https://api-inference.huggingface.co/ping"
PROLIFIC_PING_URL = "https://api.prolific.co/api/v1/ping"

# Resource limits.
MAX_RAM_USAGE_BYTES = 7 * 1024 ** 3          # 7 GB
MIN_FREE_DISK_BYTES = 7 * 1024 ** 3          # 7 GB

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
logger = get_logger(__name__)

def _log(message: str) -> None:
    """Append a line to the recruitment validation log."""
    log_path = paths.data("recruitment_validation.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    logger.info(message)

def _check_packages() -> bool:
    """Check that every package in REQUIRED_PACKAGES can be imported."""
    success = True
    for pkg in REQUIRED_PACKAGES:
        spec = importlib.util.find_spec(pkg)
        if spec is None:
            _log(f"[ERROR] Required package missing: {pkg}")
            success = False
        else:
            _log(f"[OK] Package importable: {pkg}")
    return success

def _check_memory() -> bool:
    """Verify that RAM usage is ≤ 7 GB."""
    vm = psutil.virtual_memory()
    used = vm.total - vm.available
    _log(f"[INFO] RAM total: {vm.total / (1024 ** 3):.2f} GB, used: {used / (1024 ** 3):.2f} GB")
    if used > MAX_RAM_USAGE_BYTES:
        _log(f"[ERROR] RAM usage exceeds {MAX_RAM_USAGE_BYTES / (1024 ** 3)} GB")
        return False
    _log("[OK] RAM usage within limits")
    return True

def _check_disk() -> bool:
    """Verify that free disk space on the project root is ≥ 7 GB."""
    root_path = Path(paths.root)
    du = psutil.disk_usage(str(root_path))
    _log(f"[INFO] Disk total: {du.total / (1024 ** 3):.2f} GB, free: {du.free / (1024 ** 3):.2f} GB")
    if du.free < MIN_FREE_DISK_BYTES:
        _log(f"[ERROR] Free disk space less than {MIN_FREE_DISK_BYTES / (1024 ** 3)} GB")
        return False
    _log("[OK] Sufficient free disk space")
    return True

def _check_hf_token() -> bool:
    """Ensure HF token exists and the inference endpoint replies."""
    token = os.getenv(HF_TOKEN_ENV)
    if not token:
        _log(f"[ERROR] Environment variable {HF_TOKEN_ENV} not set")
        return False
    _log(f"[OK] Found {HF_TOKEN_ENV}")

    try:
        resp = requests.get(
            HF_PING_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            _log("[OK] HuggingFace inference API reachable")
            return True
        else:
            _log(f"[ERROR] HF ping returned status {resp.status_code}")
            return False
    except Exception as e:
        _log(f"[ERROR] Exception during HF ping: {e}")
        return False

def _check_prolific() -> bool:
    """Ensure Prolific token exists and the API is reachable."""
    token = os.getenv(PROLIFIC_TOKEN_ENV)
    if not token:
        _log(f"[ERROR] Environment variable {PROLIFIC_TOKEN_ENV} not set")
        return False
    _log(f"[OK] Found {PROLIFIC_TOKEN_ENV}")

    try:
        resp = requests.get(
            PROLIFIC_PING_URL,
            headers={"Authorization": f"Token {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            _log("[OK] Prolific API reachable")
            return True
        else:
            _log(f"[ERROR] Prolific ping returned status {resp.status_code}")
            return False
    except Exception as e:
        _log(f"[ERROR] Exception during Prolific ping: {e}")
        return False

def _check_consent_pdf() -> bool:
    """Attempt to open the consent form PDF to ensure it is readable."""
    pdf_path = paths.data("consent_form.pdf")
    if not pdf_path.is_file():
        _log(f"[ERROR] Consent form not found at {pdf_path}")
        return False
    try:
        with open(pdf_path, "rb") as f:
            _ = f.read(10)  # read a few bytes to ensure readability
        _log("[OK] Consent form PDF is readable")
        return True
    except Exception as e:
        _log(f"[ERROR] Unable to read consent form PDF: {e}")
        return False

def main() -> None:
    """Run all checks, write the log, and emit a JSON success flag."""
    # Ensure the log file starts fresh for each run.
    log_path = paths.data("recruitment_validation.log")
    if log_path.exists():
        log_path.unlink()
    _log("=== Recruitment Environment Validation Started ===")

    checks = {
        "packages": _check_packages(),
        "memory": _check_memory(),
        "disk": _check_disk(),
        "huggingface": _check_hf_token(),
        "prolific": _check_prolific(),
        "consent_pdf": _check_consent_pdf(),
    }

    success = all(checks.values())
    _log(f"=== Validation Completed – success={success} ===")

    # Emit JSON line to stdout – this satisfies the “boolean success flag” requirement.
    print(json.dumps({"success": success}))

    # Exit with appropriate status code.
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
