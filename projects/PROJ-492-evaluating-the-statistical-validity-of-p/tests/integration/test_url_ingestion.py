"""
Integration test for FR-002: URL Ingestion Verification.

This test verifies that the URL ingestion pipeline (T018) correctly processes
the input URL list, handles deduplication, and produces the expected output
artifact (output/urls_deduped.csv) with valid content.

Requirement: coverage-executability-08d5764f
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Set

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.audit.ingestor import read_urls_from_csv, deduplicate_urls, write_urls_to_csv
from code.src.utils.logger import get_default_logger

logger = get_default_logger()


def load_test_urls() -> List[str]:
    """
    Loads a small, deterministic set of real URLs for testing.
    These are real, public URLs to ensure the ingestion logic handles
    standard formats correctly without fabricating data.
    """
    # Using a mix of real domains to test parsing logic
    urls = [
        "https://www.optimizely.com/optimization-glossary/ab-testing/",
        "https://vwo.com/blog/ab-testing-examples/",
        "https://www.crazyegg.com/blog/a-b-testing-examples/",
        # Duplicate to test deduplication
        "https://www.optimizely.com/optimization-glossary/ab-testing/",
        "https://www.google-analytics.com/analytics.html",
    ]
    return urls


def test_url_ingestion_deduplication():
    """
    FR-002 Verification: Ensure URL ingestion and deduplication works correctly.
    
    Steps:
    1. Create a temporary input CSV with known URLs (including duplicates).
    2. Run the ingestor's read and deduplicate functions.
    3. Verify the output count is correct (duplicates removed).
    4. Verify the output file exists at the expected path.
    5. Verify the content matches the expected unique set.
    """
    # Setup temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        input_file = input_dir / "urls.csv"
        output_file = output_dir / "urls_deduped.csv"

        # 1. Create input data
        test_urls = load_test_urls()
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url"])
            writer.writeheader()
            for url in test_urls:
                writer.writerow({"url": url})

        logger.info(f"Created test input file: {input_file}")

        # 2. Run ingestion logic
        # Read URLs
        urls, errors = read_urls_from_csv(input_file)
        assert len(errors) == 0, f"Unexpected errors reading URLs: {errors}"
        assert len(urls) == len(test_urls), "Input count mismatch"

        # Deduplicate
        unique_urls, removed_count = deduplicate_urls(urls)
        
        # 3. Verify deduplication logic
        expected_unique_count = len(set(test_urls))
        assert len(unique_urls) == expected_unique_count, \
            f"Deduplication failed: expected {expected_unique_count}, got {len(unique_urls)}"
        assert removed_count == 1, f"Expected 1 duplicate removed, got {removed_count}"

        # 4. Write output (simulating the pipeline step)
        write_urls_to_csv(unique_urls, output_file)
        
        # 5. Verify output file exists and content
        assert output_file.exists(), f"Output file {output_file} was not created"
        
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            written_urls = [row["url"] for row in reader]
        
        # Verify content matches expected unique set (order might vary, so use sets)
        written_set = set(written_urls)
        expected_set = set(unique_urls)
        
        assert written_set == expected_set, \
            f"Output content mismatch. Expected: {expected_set}, Got: {written_set}"

        logger.info(f"FR-002 Verification PASSED: Input {len(test_urls)} URLs -> Output {len(written_urls)} unique URLs.")
        return True


def main():
    """Entry point for the integration test."""
    logger.info("Starting FR-002 URL Ingestion Verification Test...")
    try:
        success = test_url_ingestion_deduplication()
        if success:
            logger.info("Test completed successfully.")
            return 0
        else:
            logger.error("Test failed.")
            return 1
    except Exception as e:
        logger.error(f"Test execution failed with exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())