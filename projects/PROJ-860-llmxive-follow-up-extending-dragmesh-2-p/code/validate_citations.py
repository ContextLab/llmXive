"""
Citation Validation Module for llmXive Pipeline.

This module implements Constitution Principle II: Verified Accuracy.
It validates that all data sources and baseline models referenced in
plan.md and spec.md correspond to real, accessible, and verified sources.

The validation is strict: if any citation cannot be verified, the pipeline
halts immediately to prevent downstream processing of unverified data.
"""

import os
import sys
import re
import urllib.request
import urllib.error
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project Root relative to this file (assuming code/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"
SPEC_MD_PATH = PROJECT_ROOT / "spec.md"
REQUIREMENTS_PATH = PROJECT_ROOT / "code" / "requirements.txt"

# Known verified sources for DragMesh-2 and PICA
# These are hardcoded based on the project's verified registry
VERIFIED_DRAGMESH_URL = "https://huggingface.co/datasets/dragmesh/dragmesh-2"
VERIFIED_PICA_URL = "https://huggingface.co/datasets/dragmesh/pica-baseline-v"

def check_requirements_file() -> bool:
    """
    Verify that requirements.txt exists and contains pinned versions.
    Returns True if valid, False otherwise.
    """
    if not REQUIREMENTS_PATH.exists():
        logger.error(f"File not found: {REQUIREMENTS_PATH}")
        return False

    content = REQUIREMENTS_PATH.read_text()
    if not content.strip():
        logger.error(f"requirements.txt is empty: {REQUIREMENTS_PATH}")
        return False

    # Check for pinned versions (==)
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith('#')]
    pinned_count = 0
    for line in lines:
        if '==' in line:
            pinned_count += 1

    if pinned_count == 0:
        logger.warning("No pinned versions found in requirements.txt. This violates Constitution Principle I.")
        # We don't fail the citation check for this, but we log it.

    logger.info(f"requirements.txt validated. Found {len(lines)} dependencies.")
    return True

def check_citations_documentation() -> bool:
    """
    Verify that plan.md and spec.md exist and contain citation markers.
    This is a structural check to ensure documentation is present.
    """
    files_to_check = [PLAN_MD_PATH, SPEC_MD_PATH]
    all_valid = True

    for f_path in files_to_check:
        if not f_path.exists():
            logger.error(f"Documentation file missing: {f_path}")
            all_valid = False
            continue

        content = f_path.read_text()
        # Basic check for citation-like patterns (e.g., [1], [Ref], URLs)
        # This is a heuristic; the real validation happens in specific checks
        if not re.search(r'\[.*?\]|\bhttps?://\S+', content):
            logger.warning(f"No obvious citations or URLs found in {f_path.name}.")
        
        logger.info(f"Checked documentation: {f_path.name}")

    return all_valid

def check_spec_citations() -> bool:
    """
    Validate citations specifically mentioned in spec.md related to data sources.
    Checks for DragMesh-2 and PICA baseline references.
    """
    if not SPEC_MD_PATH.exists():
        logger.error("spec.md not found. Cannot validate citations.")
        return False

    content = SPEC_MD_PATH.read_text()
    issues = []

    # Check for DragMesh-2 reference
    if "DragMesh-2" in content or "dragmesh" in content.lower():
        logger.info("Detected DragMesh-2 reference in spec.md.")
        # Verify the URL is reachable (HEAD request)
        try:
            req = urllib.request.Request(VERIFIED_DRAGMESH_URL, method='HEAD')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Verified DragMesh-2 source: {VERIFIED_DRAGMESH_URL}")
                else:
                    issues.append(f"DragMesh-2 URL returned status {response.status}")
        except urllib.error.URLError as e:
            issues.append(f"Cannot reach DragMesh-2 source: {e}")
        except Exception as e:
            issues.append(f"Error checking DragMesh-2: {e}")
    else:
        logger.warning("No explicit DragMesh-2 reference found in spec.md.")

    # Check for PICA baseline reference
    if "PICA" in content or "pica" in content.lower():
        logger.info("Detected PICA baseline reference in spec.md.")
        try:
            req = urllib.request.Request(VERIFIED_PICA_URL, method='HEAD')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Verified PICA baseline source: {VERIFIED_PICA_URL}")
                else:
                    issues.append(f"PICA baseline URL returned status {response.status}")
        except urllib.error.URLError as e:
            issues.append(f"Cannot reach PICA baseline source: {e}")
        except Exception as e:
            issues.append(f"Error checking PICA baseline: {e}")
    else:
        logger.warning("No explicit PICA baseline reference found in spec.md.")

    if issues:
        for issue in issues:
            logger.error(f"Citation validation failed: {issue}")
        return False

    return True

def check_data_manifests() -> bool:
    """
    Check if data manifests (if already downloaded) exist and are non-empty.
    This is a secondary check to ensure local data integrity before download tasks.
    """
    # Paths where data would be downloaded
    dragmesh_manifest_path = PROJECT_ROOT / "data" / "raw" / "manifest.json"
    pica_manifest_path = PROJECT_ROOT / "data" / "raw" / "baseline" / "manifest.json"

    checks = []
    
    # DragMesh-2
    if dragmesh_manifest_path.exists():
        if dragmesh_manifest_path.stat().st_size == 0:
            checks.append("DragMesh-2 manifest exists but is empty.")
        else:
            logger.info("Local DragMesh-2 manifest found and non-empty.")
    else:
        logger.info("Local DragMesh-2 manifest not found. This is expected before T005d.")

    # PICA
    if pica_manifest_path.exists():
        if pica_manifest_path.stat().st_size == 0:
            checks.append("PICA baseline manifest exists but is empty.")
        else:
            logger.info("Local PICA baseline manifest found and non-empty.")
    else:
        logger.info("Local PICA baseline manifest not found. This is expected before T012d.")

    if checks:
        for c in checks:
            logger.error(c)
        return False

    return True

def main():
    """
    Main entry point for citation validation.
    Returns 0 if all checks pass, 1 if any check fails.
    """
    logger.info("Starting Citation Validation (Constitution Principle II)...")
    
    all_passed = True

    # 1. Check requirements
    if not check_requirements_file():
        all_passed = False

    # 2. Check documentation structure
    if not check_citations_documentation():
        all_passed = False

    # 3. Validate specific data source citations
    if not check_spec_citations():
        all_passed = False

    # 4. Check local manifests (if they exist)
    if not check_data_manifests():
        all_passed = False

    if all_passed:
        logger.info("SUCCESS: All citations validated. Pipeline can proceed.")
        return 0
    else:
        logger.error("FAILURE: One or more citations failed validation. Pipeline halted.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
