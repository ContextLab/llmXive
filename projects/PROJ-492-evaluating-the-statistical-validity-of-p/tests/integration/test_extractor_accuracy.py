"""
Integration test for FR-002: Extractor Accuracy Verification.

This test asserts that extracted fields exist for > 95% of valid pages.
It runs the extraction pipeline on a set of real URLs (from data/raw or a
provided list) and validates the completeness of the resulting ABTestSummary
objects.

Requirements:
- FR-002: Extracted fields must exist for > 95% of valid pages.
- SC-001: Extraction accuracy >= 95%.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.fetcher import fetch_urls_batch
from code.src.audit.ingestor import read_urls_from_csv
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Configuration
EXPECTED_COMPLETENESS_THRESHOLD = 0.95
INPUT_URLS_FILE = "data/input/urls.csv"
RAW_DATA_DIR = "data/raw"
EXTRACTED_OUTPUT_FILE = "data/extracted/summaries.json"

# Define required fields for a "valid" summary per FR-002
# These are the core fields that must be present for the statistical reconstruction
# to proceed. Missing these indicates a failed extraction.
REQUIRED_FIELDS: Set[str] = {
    "url",
    "domain",
    "baseline_conversion_rate",
    "variant_conversion_rate",
    "baseline_sample_size",
    "variant_sample_size",
    "p_value",
    "effect_size",
    "outcome_type"
}

def _get_valid_pages(extracted_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter summaries that represent valid pages (i.e., not a parsing error).
    A page is considered 'valid' if it was successfully parsed and contains
    at least a URL.
    """
    valid = []
    for summary in extracted_summaries:
        # If we have a URL, we assume the page was fetched and attempted to be parsed.
        # If extraction failed completely, the extractor usually logs an error
        # and might not produce a record, or produces one with specific error flags.
        # Here we consider any record with a URL as a 'valid page' attempt.
        if summary.get("url"):
            valid.append(summary)
    return valid

def _calculate_completeness(valid_summaries: List[Dict[str, Any]]) -> float:
    """
    Calculate the percentage of valid pages that contain all required fields.
    """
    if not valid_summaries:
        return 0.0

    complete_count = 0
    for summary in valid_summaries:
        has_all_fields = all(field in summary and summary[field] is not None
                             for field in REQUIRED_FIELDS)
        if has_all_fields:
            complete_count += 1

    return complete_count / len(valid_summaries)

@pytest.mark.integration
def test_extractor_accuracy():
    """
    FR-002 Verification: Run the extractor on available data and assert
    that extracted fields exist for > 95% of valid pages.
    """
    # Ensure paths exist
    urls_path = project_root / INPUT_URLS_FILE
    if not urls_path.exists():
        pytest.fail(f"Input URLs file not found: {urls_path}. "
                    "Please run T018 (ingestor) to populate data/input/urls.csv "
                    "or ensure data/raw contains fetched HTML files.")

    # 1. Load URLs
    logger.info(f"Reading URLs from {urls_path}")
    url_list = read_urls_from_csv(urls_path)
    if not url_list:
        pytest.fail("No URLs found in input file.")

    # 2. Fetch HTML (if not already present)
    # We rely on T019 having run, but we ensure data exists here.
    raw_dir = project_root / RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Check if we have enough fetched HTML files
    html_files = list(raw_dir.glob("*.html"))
    if not html_files:
        logger.warning("No HTML files found in data/raw. Attempting to fetch.")
        # Fetching might fail in CI without network, so we catch it.
        try:
            fetch_urls_batch(url_list, raw_dir)
            html_files = list(raw_dir.glob("*.html"))
        except Exception as e:
            pytest.fail(f"Failed to fetch URLs: {e}. "
                        "Ensure network is available or data/raw is pre-populated.")

    # 3. Run Extraction
    extracted_dir = project_root / "data" / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    output_path = extracted_dir / "summaries.json"

    logger.info(f"Running extraction on {len(html_files)} HTML files.")
    try:
        summaries = extract_all(html_files)
        write_summaries_to_json(summaries, output_path)
    except Exception as e:
        pytest.fail(f"Extraction failed: {e}")

    if not summaries:
        pytest.fail("Extraction produced no summaries.")

    # 4. Validate Completeness
    valid_pages = _get_valid_pages(summaries)
    completeness = _calculate_completeness(valid_pages)

    logger.info(f"Total summaries: {len(summaries)}")
    logger.info(f"Valid pages: {len(valid_pages)}")
    logger.info(f"Completeness rate: {completeness:.2%}")

    # Assert against threshold
    if completeness < EXPECTED_COMPLETENESS_THRESHOLD:
        # Collect details for debugging
        missing_fields_list = []
        for s in valid_pages:
            missing = [f for f in REQUIRED_FIELDS if f not in s or s[f] is None]
            if missing:
                missing_fields_list.append({"url": s.get("url"), "missing": missing})

        pytest.fail(
            f"Extractor accuracy check FAILED. "
            f"Required completeness: > {EXPECTED_COMPLETENESS_THRESHOLD:.0%}, "
            f"Actual: {completeness:.2%}. "
            f"Sample of failures: {missing_fields_list[:5]}"
        )

    assert completeness >= EXPECTED_COMPLETENESS_THRESHOLD, (
        f"Extractor accuracy check FAILED. "
        f"Required: > {EXPECTED_COMPLETENESS_THRESHOLD:.0%}, Got: {completeness:.2%}"
    )

if __name__ == "__main__":
    # Allow running as a script for quick verification
    pytest.main([__file__, "-v", "-s"])