"""
Citation Validation Gate Implementation.

This module enforces the Citation Validation Gate as per the project plan.
It validates bibliographic references by checking:
1. URL reachability (HTTP 200 OK)
2. Checksum verification (if provided in metadata)
3. Title overlap (semantic similarity check against expected source)

Usage:
    python src/utils/validate_citations.py --input data/raw/citations.yaml --output data/derived/validation_report.json
"""

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 10  # seconds
MAX_TITLE_SIMILARITY = 0.85  # Threshold for title overlap check
USER_AGENT = "llmXive-CitationValidator/1.0"

@dataclass
class Citation:
    """Represents a single citation entry."""
    id: str
    url: str
    expected_title: str
    checksum: Optional[str] = None  # SHA256 or MD5
    checksum_algorithm: str = "sha256"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of validating a single citation."""
    citation_id: str
    url: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

def load_citations(filepath: Path) -> List[Citation]:
    """Load citations from a YAML file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Citation file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError("Citation file must contain a list of citations")

    citations = []
    for item in data:
        try:
            citation = Citation(
                id=item.get('id'),
                url=item.get('url'),
                expected_title=item.get('title'),
                checksum=item.get('checksum'),
                checksum_algorithm=item.get('checksum_algorithm', 'sha256'),
                metadata=item.get('metadata', {})
            )
            citations.append(citation)
        except Exception as e:
            logger.error(f"Failed to parse citation: {e}")
            continue

    return citations

def check_url_reachability(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[bool, Optional[str]]:
    """
    Check if the URL is reachable and returns a valid response.

    Returns:
        Tuple of (is_reachable, error_message)
    """
    try:
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"

        headers = {"User-Agent": USER_AGENT}
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)

        # If HEAD fails, try GET (some servers block HEAD)
        if response.status_code == 405:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            # Consume only enough to verify status
            response.iter_lines()

        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def verify_checksum(url: str, expected_checksum: str, algorithm: str = "sha256") -> Tuple[bool, Optional[str]]:
    """
    Download the file and verify its checksum.

    Note: This downloads the full file, so use with caution for large files.
    For large files, consider streaming and partial verification if supported.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT * 10, stream=True)
        response.raise_for_status()

        hash_obj = hashlib.new(algorithm)
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                hash_obj.update(chunk)

        computed_checksum = hash_obj.hexdigest()

        if computed_checksum.lower() == expected_checksum.lower():
            return True, None
        else:
            return False, f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}"

    except Exception as e:
        return False, f"Checksum verification failed: {str(e)}"

def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate a simple similarity score between two titles.
    Uses a normalized word overlap approach.

    Returns:
        Float between 0.0 and 1.0
    """
    if not title1 or not title2:
        return 0.0

    # Normalize titles: lowercase, remove punctuation, split into words
    def normalize(text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return set(text.split())

    words1 = normalize(title1)
    words2 = normalize(title2)

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0

def fetch_title_from_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    Attempt to extract the title from the URL content.
    Supports HTML (meta tags) and some PDF/text formats.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()

        if 'text/html' in content_type:
            # Parse HTML for title
            html_content = response.text
            # Simple regex for <title> tag
            match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
            # Fallback to meta title
            match = re.search(r'<meta[^>]+name=["\']title["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        elif 'application/pdf' in content_type:
            # For PDFs, we might need a library like PyPDF2, but for now return None
            # to avoid heavy dependencies. The caller can handle this case.
            logger.warning(f"PDF title extraction not implemented for {url}")
            return None

        return None

    except Exception as e:
        logger.debug(f"Failed to fetch title from {url}: {e}")
        return None

def validate_citation(citation: Citation) -> ValidationResult:
    """
    Validate a single citation against all gate criteria.
    """
    errors = []
    warnings = []
    details = {}
    is_valid = True

    # 1. URL Reachability
    logger.info(f"Checking reachability for {citation.url}")
    reachable, error = check_url_reachability(citation.url)
    details['url_reachable'] = reachable
    if not reachable:
        errors.append(f"URL not reachable: {error}")
        is_valid = False

    # 2. Checksum Verification (if provided)
    if citation.checksum:
        logger.info(f"Verifying checksum for {citation.url}")
        checksum_valid, error = verify_checksum(
            citation.url,
            citation.checksum,
            citation.checksum_algorithm
        )
        details['checksum_verified'] = checksum_valid
        if not checksum_valid:
            errors.append(f"Checksum verification failed: {error}")
            is_valid = False
    else:
        details['checksum_verified'] = None
        warnings.append("No checksum provided, skipping verification")

    # 3. Title Overlap
    if citation.expected_title:
        logger.info(f"Checking title overlap for {citation.url}")
        fetched_title = fetch_title_from_url(citation.url)
        details['fetched_title'] = fetched_title

        if fetched_title:
            similarity = calculate_title_similarity(citation.expected_title, fetched_title)
            details['title_similarity'] = similarity

            if similarity < MAX_TITLE_SIMILARITY:
                warnings.append(
                    f"Title similarity low ({similarity:.2f}): "
                    f"Expected '{citation.expected_title[:50]}...', "
                    f"Got '{fetched_title[:50]}...'"
                )
                # We treat low similarity as a warning, not a hard failure,
                # as titles might be abbreviated or formatted differently.
                # However, if it's extremely low, we might flag it.
                if similarity < 0.3:
                    errors.append(f"Title mismatch: expected '{citation.expected_title}', got '{fetched_title}'")
                    is_valid = False
        else:
            warnings.append("Could not fetch title from URL for comparison")

    return ValidationResult(
        citation_id=citation.id,
        url=citation.url,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        details=details
    )

def validate_all_citations(citations: List[Citation]) -> List[ValidationResult]:
    """Validate all citations in the list."""
    results = []
    for i, citation in enumerate(citations):
        logger.info(f"Validating citation {i+1}/{len(citations)}: {citation.id}")
        result = validate_citation(citation)
        results.append(result)
    return results

def generate_report(results: List[ValidationResult], output_path: Path) -> None:
    """Generate a JSON report of validation results."""
    report = {
        "summary": {
            "total_citations": len(results),
            "valid_count": sum(1 for r in results if r.is_valid),
            "invalid_count": sum(1 for r in results if not r.is_valid),
            "validity_rate": sum(1 for r in results if r.is_valid) / len(results) if results else 0.0
        },
        "results": [
            {
                "citation_id": r.citation_id,
                "url": r.url,
                "is_valid": r.is_valid,
                "errors": r.errors,
                "warnings": r.warnings,
                "details": r.details
            }
            for r in results
        ]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate citations for the Citation Validation Gate."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to the input YAML file containing citations."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("data/derived/citation_validation_report.json"),
        help="Path to the output JSON report."
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Timeout in seconds for HTTP requests."
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading citations from {args.input}")
        citations = load_citations(args.input)

        if not citations:
            logger.warning("No valid citations found in the input file.")
            # Still generate an empty report
            generate_report([], args.output)
            return

        logger.info(f"Validating {len(citations)} citations...")
        results = validate_all_citations(citations)

        logger.info("Generating report...")
        generate_report(results, args.output)

        # Exit with error code if any citation is invalid
        invalid_count = sum(1 for r in results if not r.is_valid)
        if invalid_count > 0:
            logger.error(f"Validation failed for {invalid_count} citation(s).")
            sys.exit(1)
        else:
            logger.info("All citations validated successfully.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
