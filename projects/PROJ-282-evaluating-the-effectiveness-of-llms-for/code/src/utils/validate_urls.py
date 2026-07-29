"""
URL Validation Module for Dataset Manifests.

This module validates dataset URLs against the research.md manifest to ensure
data integrity and reproducibility (Constitution II). It parses the research.md
file, extracts dataset URLs, and verifies their accessibility.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import logger from existing utility
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"

# URL patterns for known datasets
DATASET_URL_PATTERNS = {
    "VulDeePecker": [
        r"https://github\.com/.*vuldeepecker.*",
        r"https://.*\.amazonaws\.com/.*vuldeepecker.*",
        r"https://.*\.com/.*vuldeepecker.*"
    ],
    "BigVul": [
        r"https://github\.com/.*bigvul.*",
        r"https://.*\.amazonaws\.com/.*bigvul.*",
        r"https://.*\.com/.*bigvul.*"
    ],
    "NIST Juliet": [
        r"https://.*\.nist\.gov/.*juliet.*",
        r"https://.*\.github\.io/.*juliet.*"
    ]
}

# Required datasets according to the project plan
REQUIRED_DATASETS = ["VulDeePecker", "BigVul"]

def parse_research_manifest(manifest_path: Path) -> Dict[str, List[str]]:
    """
    Parse research.md to extract dataset URLs.

    Args:
        manifest_path: Path to research.md file

    Returns:
        Dictionary mapping dataset names to lists of URLs found in the manifest

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        ValueError: If manifest is malformed
    """
    if not manifest_path.exists():
        logger.error(f"Research manifest not found: {manifest_path}")
        raise FileNotFoundError(f"Research manifest not found: {manifest_path}")

    dataset_urls = {}
    current_dataset = None

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for dataset sections in the manifest
        # Pattern: ### Dataset Name followed by URLs
        dataset_section_pattern = r'###\s+(.+?)\s*\n(.*?)(?=\n###|\Z)'
        matches = re.findall(dataset_section_pattern, content, re.DOTALL)

        for dataset_name, section_content in matches:
            dataset_name = dataset_name.strip()
            # Extract URLs from the section
            url_pattern = r'(https?://[^\s<>"\'\)]+)'
            urls = re.findall(url_pattern, section_content)

            if urls:
                dataset_urls[dataset_name] = urls
                logger.info(f"Found {len(urls)} URL(s) for dataset: {dataset_name}")

        # Also check for inline dataset references
        inline_pattern = r'(VulDeePecker|BigVul|NIST Juliet):\s*(https?://[^\s<>"\'\)]+)'
        inline_matches = re.findall(inline_pattern, content)
        for name, url in inline_matches:
            if name not in dataset_urls:
                dataset_urls[name] = []
            if url not in dataset_urls[name]:
                dataset_urls[name].append(url)

        if not dataset_urls:
            logger.warning("No dataset URLs found in research manifest")

        return dataset_urls

    except Exception as e:
        logger.error(f"Error parsing research manifest: {e}")
        raise

def validate_url_pattern(url: str, patterns: List[str]) -> bool:
    """
    Validate a URL against a list of regex patterns.

    Args:
        url: URL to validate
        patterns: List of regex patterns

    Returns:
        True if URL matches any pattern, False otherwise
    """
    for pattern in patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    return False

def check_url_accessibility(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Check if a URL is accessible (HEAD request).

    Args:
        url: URL to check
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_accessible, status_message)
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if status_code == 200:
                return True, f"Accessible (HTTP {status_code})"
            else:
                return False, f"Unreachable (HTTP {status_code})"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_dataset_urls(dataset_urls: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Validate all dataset URLs from the manifest.

    Args:
        dataset_urls: Dictionary of dataset names to URL lists

    Returns:
        Validation report dictionary
    """
    report = {
        "valid": True,
        "datasets": {},
        "missing_required": [],
        "errors": []
    }

    # Check for required datasets
    for dataset_name in REQUIRED_DATASETS:
        if dataset_name not in dataset_urls or not dataset_urls[dataset_name]:
            report["missing_required"].append(dataset_name)
            report["valid"] = False
            logger.error(f"Required dataset missing from manifest: {dataset_name}")

    # Validate each dataset's URLs
    for dataset_name, urls in dataset_urls.items():
        dataset_report = {
            "urls": [],
            "valid_count": 0,
            "invalid_count": 0
        }

        patterns = DATASET_URL_PATTERNS.get(dataset_name, [])

        for url in urls:
            url_report = {
                "url": url,
                "pattern_valid": False,
                "accessible": False,
                "status": ""
            }

            # Check pattern validity
            if patterns:
                url_report["pattern_valid"] = validate_url_pattern(url, patterns)
            else:
                # No specific pattern for this dataset, assume valid if it's a URL
                url_report["pattern_valid"] = url.startswith("http://") or url.startswith("https://")

            # Check accessibility
            is_accessible, status = check_url_accessibility(url)
            url_report["accessible"] = is_accessible
            url_report["status"] = status

            dataset_report["urls"].append(url_report)

            if url_report["pattern_valid"] and url_report["accessible"]:
                dataset_report["valid_count"] += 1
            else:
                dataset_report["invalid_count"] += 1
                report["valid"] = False
                report["errors"].append(f"{dataset_name}: {url} - {status}")

        report["datasets"][dataset_name] = dataset_report

    return report

def validate_urls(manifest_path: Optional[Path] = None) -> bool:
    """
    Main validation function.

    Args:
        manifest_path: Optional path to research.md (defaults to PROJECT_ROOT/research.md)

    Returns:
        True if all required datasets have valid URLs, False otherwise

    Raises:
        SystemExit: If validation fails (for CLI usage)
    """
    if manifest_path is None:
        manifest_path = RESEARCH_MD_PATH

    logger.info(f"Validating dataset URLs from: {manifest_path}")

    try:
        dataset_urls = parse_research_manifest(manifest_path)
        report = validate_dataset_urls(dataset_urls)

        # Log results
        logger.info(f"Validation complete. Valid: {report['valid']}")
        if report['missing_required']:
            logger.error(f"Missing required datasets: {', '.join(report['missing_required'])}")
        if report['errors']:
            for error in report['errors']:
                logger.error(f"Validation error: {error}")

        if not report['valid']:
            logger.error("URL validation FAILED. Required datasets are missing or inaccessible.")
            return False

        logger.info("URL validation PASSED. All required datasets are accessible.")
        return True

    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return False

def main():
    """Main entry point for CLI usage."""
    print("Dataset URL Validation Tool")
    print("=" * 50)

    success = validate_urls()

    if success:
        print("\n✓ All required dataset URLs are valid and accessible.")
        sys.exit(0)
    else:
        print("\n✗ URL validation failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
