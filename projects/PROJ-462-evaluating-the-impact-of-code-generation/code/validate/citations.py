"""
Reference-Validator Agent for Citation Verification (Constitution Principle II)

Validates all external citations before ingestion/analysis to ensure:
- URLs are accessible and return valid content
- Data integrity via SHA-256 checksums
- Required variables are present in datasets
- All citations are properly documented with verifiable sources

This module MUST run BEFORE any data ingestion or analysis begins.
Pipeline halts if any citation fails verification.

Usage:
    from code.validate.citations import validate_citations
    result = validate_citations(citations_list)
    if not result.all_valid:
        raise RuntimeError("Citation verification failed")
"""

import hashlib
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import urllib.request
import urllib.error
import urllib.parse

# Import from existing dataset_search module (API surface provided)
sys.path.insert(0, str(Path(__file__).parent.parent))
from dataset_search import calculate_sha256, verify_url_accessible, download_dataset, check_csv_variables

# Constants
VALIDATION_REPORT_PATH = Path("data/output/citation_validation.json")
SPEC_MD_PATH = Path("specs/001-code-generation-performance-outcomes/spec.md")
REQUIRED_VARIABLES = [
    "tool_usage",
    "task_time",
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size",
]


@dataclass
class CitationValidationResult:
    """Result of validating a single citation."""

    citation_id: str
    url: str
    url_accessible: bool
    checksum_verified: bool
    expected_checksum: Optional[str]
    actual_checksum: Optional[str]
    variables_present: bool
    missing_variables: List[str]
    validation_passed: bool
    error_message: Optional[str]
    verified_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CitationValidationReport:
    """Full validation report for all citations."""

    total_citations: int
    passed_citations: int
    failed_citations: int
    all_valid: bool
    verification_timestamp: str
    results: List[CitationValidationResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_citations": self.total_citations,
            "passed_citations": self.passed_citations,
            "failed_citations": self.failed_citations,
            "all_valid": self.all_valid,
            "verification_timestamp": self.verification_timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }


def verify_url_accessible(url: str, timeout: int = 30) -> Tuple[bool, Optional[str]]:
    """
    Verify that a URL is accessible and returns a valid response.

    Args:
        url: The URL to verify
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_accessible, error_message)
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Invalid URL scheme: {parsed.scheme}"

        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if status_code == 200:
                return True, None
            else:
                return False, f"HTTP {status_code}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def verify_checksum(
    file_path: str, expected_checksum: str
) -> Tuple[bool, str]:
    """
    Verify SHA-256 checksum of a downloaded file.

    Args:
        file_path: Path to the downloaded file
        expected_checksum: Expected SHA-256 checksum (hex string)

    Returns:
        Tuple of (checksum_matches, actual_checksum)
    """
    actual = calculate_sha256(file_path)
    return actual == expected_checksum, actual


def verify_required_variables(
    file_path: str, required: List[str]
) -> Tuple[bool, List[str]]:
    """
    Verify that a CSV file contains all required variables.

    Args:
        file_path: Path to the CSV file
        required: List of required column names

    Returns:
        Tuple of (all_present, missing_columns)
    """
    available = check_csv_variables(file_path)
    missing = [col for col in required if col not in available]
    return len(missing) == 0, missing


def validate_citation(
    citation: Dict[str, Any],
    download_dir: Optional[str] = None,
) -> CitationValidationResult:
    """
    Validate a single citation entry.

    Args:
        citation: Dictionary containing citation metadata with keys:
            - id: Unique identifier for the citation
            - url: URL to the dataset
            - expected_checksum: SHA-256 checksum (optional)
            - description: Human-readable description
        download_dir: Directory to download files for validation

    Returns:
        CitationValidationResult with validation status
    """
    citation_id = citation.get("id", "unknown")
    url = citation.get("url", "")
    expected_checksum = citation.get("expected_checksum")
    description = citation.get("description", "")

    result = CitationValidationResult(
        citation_id=citation_id,
        url=url,
        url_accessible=False,
        checksum_verified=False,
        expected_checksum=expected_checksum,
        actual_checksum=None,
        variables_present=False,
        missing_variables=[],
        validation_passed=False,
        error_message=None,
        verified_at=datetime.utcnow().isoformat(),
    )

    # Step 1: Verify URL is accessible
    url_accessible, url_error = verify_url_accessible(url)
    result.url_accessible = url_accessible
    if not url_accessible:
        result.error_message = f"URL not accessible: {url_error}"
        return result

    # Step 2: Download and verify checksum if provided
    if expected_checksum and download_dir:
        try:
            local_path = download_dataset(url, download_dir)
            checksum_match, actual_checksum = verify_checksum(
                local_path, expected_checksum
            )
            result.actual_checksum = actual_checksum
            result.checksum_verified = checksum_match

            if not checksum_match:
                result.error_message = (
                    f"Checksum mismatch: expected {expected_checksum}, "
                    f"got {actual_checksum}"
                )
                return result
        except Exception as e:
            result.error_message = f"Download failed: {str(e)}"
            return result
    elif download_dir:
        # Download without checksum verification
        try:
            local_path = download_dataset(url, download_dir)
            result.actual_checksum = calculate_sha256(local_path)
            result.checksum_verified = True
        except Exception as e:
            result.error_message = f"Download failed: {str(e)}"
            return result
    else:
        result.checksum_verified = True  # Skip checksum if no download

    # Step 3: Verify required variables (if CSV)
    if download_dir and url.endswith((".csv", ".CSV")):
        try:
            local_path = download_dataset(url, download_dir)
            all_present, missing = verify_required_variables(
                local_path, REQUIRED_VARIABLES
            )
            result.variables_present = all_present
            result.missing_variables = missing

            if not all_present:
                result.error_message = (
                    f"Missing required variables: {', '.join(missing)}"
                )
                return result
        except Exception as e:
            result.error_message = f"Variable verification failed: {str(e)}"
            return result
    else:
        result.variables_present = True  # Skip if not CSV or no download

    # All validations passed
    result.validation_passed = True
    return result


def validate_citations(
    citations: List[Dict[str, Any]],
    download_dir: str = "data/raw",
) -> CitationValidationReport:
    """
    Validate all citations in the provided list.

    This is the main entry point for the Reference-Validator Agent.

    Args:
        citations: List of citation dictionaries to validate
        download_dir: Directory for temporary downloads during validation

    Returns:
        CitationValidationReport with complete validation results

    Raises:
        RuntimeError: If any citation fails verification
    """
    # Ensure download directory exists
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # Validate each citation
    results = []
    for citation in citations:
        result = validate_citation(citation, download_dir)
        results.append(result)

    # Calculate summary statistics
    passed = sum(1 for r in results if r.validation_passed)
    failed = len(results) - passed
    all_valid = failed == 0

    summary = {
        "total_citations": len(results),
        "passed_citations": passed,
        "failed_citations": failed,
        "pass_rate": passed / len(results) if results else 0.0,
        "verified_at": datetime.utcnow().isoformat(),
    }

    report = CitationValidationReport(
        total_citations=len(results),
        passed_citations=passed,
        failed_citations=failed,
        all_valid=all_valid,
        verification_timestamp=datetime.utcnow().isoformat(),
        results=results,
        summary=summary,
    )

    # Raise error if any citation failed
    if not all_valid:
        failed_ids = [r.citation_id for r in results if not r.validation_passed]
        raise RuntimeError(
            f"Citation verification failed for: {', '.join(failed_ids)}"
        )

    return report


def generate_validation_report(
    report: CitationValidationReport, output_path: str
) -> str:
    """
    Generate a JSON validation report file.

    Args:
        report: CitationValidationReport to serialize
        output_path: Path for the output JSON file

    Returns:
        Path to the generated report file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    return str(output_path)


def main():
    """
    CLI entry point for citation validation.

    Usage:
        python -m code.validate.citations --citations-file path/to/citations.json
        python -m code.validate.citations --report output.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Reference-Validator Agent for Citation Verification"
    )
    parser.add_argument(
        "--citations-file",
        type=str,
        help="Path to JSON file containing citations to validate",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=str(VALIDATION_REPORT_PATH),
        help="Path for the output validation report",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default="data/raw",
        help="Directory for temporary downloads",
    )

    args = parser.parse_args()

    if not args.citations_file:
        print("Error: --citations-file is required")
        sys.exit(1)

    # Load citations
    with open(args.citations_file, "r") as f:
        citations = json.load(f)

    # Validate
    try:
        report = validate_citations(citations, args.download_dir)
        generate_validation_report(report, args.report)

        print(f"✓ Validation complete: {report.passed_citations}/{report.total_citations} citations passed")
        print(f"Report saved to: {args.report}")
        sys.exit(0)
    except RuntimeError as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
