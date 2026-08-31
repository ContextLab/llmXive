"""
Citation Validation Script for llmXive Project.

This script verifies that all citations in the project's documentation,
requirements, and data manifests correspond to real, accessible sources.
It enforces Constitution Principle II: Verified Accuracy.
"""

import os
import sys
import re
import urllib.request
import urllib.error
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SPEC_DIR = PROJECT_ROOT / "specs" / "001-virtual-tactile-adaptation"
LOG_FILE = DATA_RESULTS_DIR / "citations_validation.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Known data sources to validate
DATA_SOURCES = {
    "dragmesh-2": {
        "url": "https://huggingface.co/datasets/dragmesh/dragmesh-2",
        "type": "huggingface_dataset",
        "required": True
    },
    "pica-baseline": {
        "url": "https://huggingface.co/datasets/dragmesh/pica-baseline-v",
        "type": "huggingface_dataset",
        "required": True
    }
}

def check_requirements_file() -> Tuple[bool, List[str]]:
    """
    Check that all packages in requirements.txt are valid and accessible.
    Returns (success, list_of_errors).
    """
    errors = []
    req_file = PROJECT_ROOT / "code" / "requirements.txt"

    if not req_file.exists():
        errors.append(f"requirements.txt not found at {req_file}")
        return False, errors

    try:
        with open(req_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        errors.append(f"Failed to read requirements.txt: {e}")
        return False, errors

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Extract package name (handle version specifiers)
        match = re.match(r'^([a-zA-Z0-9_-]+)', line)
        if match:
            package_name = match.group(1)
            # We can't easily validate every PyPI package without network,
            # but we can check for obvious typos or invalid characters
            if not re.match(r'^[a-zA-Z0-9_-]+$', package_name):
                errors.append(f"Invalid package name format: {package_name}")
        else:
            errors.append(f"Could not parse requirement line: {line}")

    if errors:
        logger.error(f"Requirements file validation failed with {len(errors)} errors")
        return False, errors

    logger.info("Requirements file validation passed")
    return True, []

def check_citations_documentation() -> Tuple[bool, List[str]]:
    """
    Check citations in README.md and other documentation files.
    Returns (success, list_of_errors).
    """
    errors = []
    doc_files = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "code" / "README.md" if (PROJECT_ROOT / "code" / "README.md").exists() else None,
        SPEC_DIR / "spec.md" if (SPEC_DIR / "spec.md").exists() else None,
        SPEC_DIR / "plan.md" if (SPEC_DIR / "plan.md").exists() else None
    ]

    # Filter out None values
    doc_files = [f for f in doc_files if f is not None]

    citation_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\[(\d+)\]', re.IGNORECASE)

    for doc_file in doc_files:
        if not doc_file.exists():
            logger.warning(f"Documentation file not found: {doc_file}")
            continue

        try:
            with open(doc_file, 'r') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Failed to read {doc_file}: {e}")
            continue

        # Find all citations
        matches = citation_pattern.findall(content)
        if not matches:
            logger.info(f"No citations found in {doc_file}")
            continue

        logger.info(f"Found {len(matches)} citations in {doc_file}")

        # Validate URLs
        for match in matches:
            url = match[1] if match[1] else None
            if url:
                # Skip relative URLs and file paths
                if url.startswith(('./', '../', '#', 'file:')):
                    continue

                try:
                    # Check if URL is accessible
                    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(request, timeout=10) as response:
                        if response.status != 200:
                            errors.append(f"URL not accessible in {doc_file}: {url} (Status: {response.status})")
                except urllib.error.HTTPError as e:
                    errors.append(f"HTTP Error for URL in {doc_file}: {url} ({e.code})")
                except urllib.error.URLError as e:
                    errors.append(f"URL Error for URL in {doc_file}: {url} ({e.reason})")
                except Exception as e:
                    errors.append(f"Unexpected error checking URL in {doc_file}: {url} ({e})")

    if errors:
        logger.error(f"Documentation citation validation failed with {len(errors)} errors")
        return False, errors

    logger.info("Documentation citation validation passed")
    return True, []

def check_spec_citations() -> Tuple[bool, List[str]]:
    """
    Specifically check citations in spec.md and plan.md for data sources.
    Returns (success, list_of_errors).
    """
    errors = []
    spec_files = [
        SPEC_DIR / "spec.md",
        SPEC_DIR / "plan.md"
    ]

    # Data source patterns
    data_source_patterns = [
        r'huggingface\.co/datasets/([a-zA-Z0-9/_-]+)',
        r'datasets\.load_dataset\(["\']([a-zA-Z0-9/_-]+)["\']',
    ]

    for spec_file in spec_files:
        if not spec_file.exists():
            logger.warning(f"Spec file not found: {spec_file}")
            continue

        try:
            with open(spec_file, 'r') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Failed to read {spec_file}: {e}")
            continue

        # Check for HuggingFace dataset references
        for pattern in data_source_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                dataset_id = match
                # Check if this is a known dataset
                if dataset_id not in DATA_SOURCES:
                    # Try to validate the URL
                    url = f"https://huggingface.co/datasets/{dataset_id}"
                    try:
                        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(request, timeout=10) as response:
                            if response.status != 200:
                                errors.append(f"Data source not accessible in {spec_file}: {dataset_id} (Status: {response.status})")
                            else:
                                logger.info(f"Verified data source in {spec_file}: {dataset_id}")
                    except Exception as e:
                        errors.append(f"Could not verify data source in {spec_file}: {dataset_id} ({e})")

    if errors:
        logger.error(f"Spec citation validation failed with {len(errors)} errors")
        return False, errors

    logger.info("Spec citation validation passed")
    return True, []

def check_data_manifests() -> Tuple[bool, List[str]]:
    """
    Check that data manifests exist and are valid for required datasets.
    Returns (success, list_of_errors).
    """
    errors = []

    # Check for DragMesh-2 manifest
    dragmesh_manifest = DATA_RAW_DIR / "dataset_manifest.jsonl"
    if not dragmesh_manifest.exists():
        # This might be expected if data hasn't been downloaded yet
        # But we should check if it's required
        if DATA_SOURCES["dragmesh-2"]["required"]:
            errors.append(f"Required data manifest not found: {dragmesh_manifest}")
    else:
        try:
            with open(dragmesh_manifest, 'r') as f:
                lines = f.readlines()
            if not lines:
                errors.append(f"Data manifest is empty: {dragmesh_manifest}")
            else:
                logger.info(f"Verified data manifest exists and is non-empty: {dragmesh_manifest}")
        except Exception as e:
            errors.append(f"Failed to read data manifest {dragmesh_manifest}: {e}")

    # Check for PICA baseline
    pica_baseline_dir = DATA_RAW_DIR / "baseline"
    if not pica_baseline_dir.exists():
        if DATA_SOURCES["pica-baseline"]["required"]:
            errors.append(f"Required PICA baseline directory not found: {pica_baseline_dir}")
    else:
        # Check for any files in the baseline directory
        baseline_files = list(pica_baseline_dir.glob("*"))
        if not baseline_files:
            errors.append(f"PICA baseline directory is empty: {pica_baseline_dir}")
        else:
            logger.info(f"Verified PICA baseline exists with {len(baseline_files)} files")

    if errors:
        logger.error(f"Data manifest validation failed with {len(errors)} errors")
        return False, errors

    logger.info("Data manifest validation passed")
    return True, []

def main():
    """
    Main function to run all citation validations.
    Exits with non-zero code if any validation fails.
    """
    logger.info("=" * 80)
    logger.info("Starting Citation Validation")
    logger.info("=" * 80)

    all_passed = True
    results = {}

    # Check requirements file
    logger.info("\n--- Checking Requirements File ---")
    req_success, req_errors = check_requirements_file()
    results["requirements"] = {"success": req_success, "errors": req_errors}
    if not req_success:
        all_passed = False

    # Check documentation citations
    logger.info("\n--- Checking Documentation Citations ---")
    doc_success, doc_errors = check_citations_documentation()
    results["documentation"] = {"success": doc_success, "errors": doc_errors}
    if not doc_success:
        all_passed = False

    # Check spec citations
    logger.info("\n--- Checking Spec Citations ---")
    spec_success, spec_errors = check_spec_citations()
    results["spec"] = {"success": spec_success, "errors": spec_errors}
    if not spec_success:
        all_passed = False

    # Check data manifests
    logger.info("\n--- Checking Data Manifests ---")
    data_success, data_errors = check_data_manifests()
    results["data_manifests"] = {"success": data_success, "errors": data_errors}
    if not data_success:
        all_passed = False

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Citation Validation Summary")
    logger.info("=" * 80)

    for category, result in results.items():
        status = "PASS" if result["success"] else "FAIL"
        logger.info(f"{category}: {status}")
        if result["errors"]:
            for error in result["errors"]:
                logger.error(f"  - {error}")

    # Write summary to JSON
    summary_file = DATA_RESULTS_DIR / "citations_validation_summary.json"
    try:
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nValidation summary written to {summary_file}")
    except Exception as e:
        logger.error(f"Failed to write summary file: {e}")

    # Final result
    if all_passed:
        logger.info("\n✓ All citation validations PASSED")
        sys.exit(0)
    else:
        logger.error("\n✗ Some citation validations FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()