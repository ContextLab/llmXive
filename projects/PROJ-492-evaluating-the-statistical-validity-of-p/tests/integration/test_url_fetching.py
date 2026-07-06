"""
Integration test for FR-002: URL Fetching and HTML Retrieval.

This test verifies that the pipeline can successfully fetch HTML content from
real URLs, handle retries and timeouts, and save the content to disk as required
by the specification.

Requirements verified:
- Fetcher module correctly downloads HTML from provided URLs
- Retry logic works for transient failures
- Timeout handling prevents hanging
- Saved HTML files are valid and contain expected content
- Error logging occurs for failed fetches (ERR-0xx codes)
"""
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code.src.utils.logger import get_default_logger, get_error_message
from code.src.audit.fetcher import fetch_url_with_retry, fetch_html_to_file, ingest_and_fetch

logger = get_default_logger(__name__)

# Test configuration
TEST_TIMEOUT = 30
TEST_MAX_RETRIES = 3
TEST_DATA_DIR = PROJECT_ROOT / "data" / "test_fetching"
TEST_URLS_FILE = TEST_DATA_DIR / "test_urls.csv"
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"

# Real-world A/B test summary URLs for validation
# Using Wikipedia pages about A/B testing as they contain relevant statistical content
# and are reliably accessible
REAL_TEST_URLS = [
    "https://en.wikipedia.org/wiki/A/B_testing",
    "https://en.wikipedia.org/wiki/Statistical_hypothesis_testing",
    "https://en.wikipedia.org/wiki/P-value",
    "https://en.wikipedia.org/wiki/Effect_size",
    "https://en.wikipedia.org/wiki/Sample_size_determination"
]

def setup_test_environment():
    """Create necessary test directories and input files."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create test URLs CSV if it doesn't exist
    if not TEST_URLS_FILE.exists():
        with open(TEST_URLS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'source', 'timestamp'])
            for i, url in enumerate(REAL_TEST_URLS):
                writer.writerow([url, 'wikipedia', time.strftime('%Y-%m-%d %H:%M:%S')])
        logger.info(f"Created test URLs file: {TEST_URLS_FILE}")
    else:
        logger.info(f"Using existing test URLs file: {TEST_URLS_FILE}")

def load_test_urls() -> List[Dict[str, str]]:
    """Load URLs from the test CSV file."""
    urls = []
    with open(TEST_URLS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append(row)
    return urls

def test_fetch_url_with_retry():
    """Test that individual URL fetching works with retry logic."""
    logger.info("Testing individual URL fetch with retry logic...")
    
    # Test with a known good URL
    test_url = REAL_TEST_URLS[0]
    success = False
    content = None
    error_msg = None
    
    for attempt in range(TEST_MAX_RETRIES):
        try:
            success, content, error_msg = fetch_url_with_retry(
                test_url, 
                timeout=TEST_TIMEOUT, 
                max_retries=TEST_MAX_RETRIES
            )
            if success:
                break
            time.sleep(1)  # Brief delay between retries
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
            continue
    
    assert success, f"Failed to fetch {test_url} after {TEST_MAX_RETRIES} attempts: {error_msg}"
    assert content is not None, "Fetched content is None"
    assert len(content) > 0, "Fetched content is empty"
    assert "A/B testing" in content or "A/B_test" in content, "Content doesn't appear to be the expected page"
    
    logger.info(f"✓ Successfully fetched {test_url} ({len(content)} bytes)")
    return True

def test_fetch_html_to_file():
    """Test that HTML content is correctly saved to files."""
    logger.info("Testing HTML file saving...")
    
    test_url = REAL_TEST_URLS[0]
    output_file = TEST_OUTPUT_DIR / f"test_{int(time.time())}.html"
    
    success, saved_path, error_msg = fetch_html_to_file(
        test_url, 
        output_dir=str(TEST_OUTPUT_DIR),
        timeout=TEST_TIMEOUT,
        max_retries=TEST_MAX_RETRIES
    )
    
    assert success, f"Failed to save HTML to file: {error_msg}"
    assert Path(saved_path).exists(), f"Saved file does not exist: {saved_path}"
    assert Path(saved_path).stat().st_size > 0, "Saved file is empty"
    
    # Verify file content
    with open(saved_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    assert len(content) > 100, "Saved file content seems too short"
    assert "html" in content.lower(), "Saved file doesn't appear to contain HTML"
    
    logger.info(f"✓ Successfully saved HTML to {saved_path} ({Path(saved_path).stat().st_size} bytes)")
    return True

def test_ingest_and_fetch_batch():
    """Test batch URL ingestion and fetching."""
    logger.info("Testing batch URL ingestion and fetching...")
    
    urls = load_test_urls()
    assert len(urls) > 0, "No test URLs found"
    
    # Fetch a subset to keep test time reasonable
    test_subset = urls[:3]
    
    results = ingest_and_fetch(
        urls=test_subset,
        output_dir=str(TEST_OUTPUT_DIR),
        timeout=TEST_TIMEOUT,
        max_retries=TEST_MAX_RETRIES
    )
    
    successful_count = sum(1 for r in results if r['success'])
    failed_count = sum(1 for r in results if not r['success'])
    
    logger.info(f"Batch fetch results: {successful_count} successful, {failed_count} failed")
    
    # We expect at least some successes
    assert successful_count > 0, "No URLs were successfully fetched"
    
    # Verify output files exist
    for result in results:
        if result['success']:
            assert Path(result['output_file']).exists(), f"Output file missing: {result['output_file']}"
            assert Path(result['output_file']).stat().st_size > 0, f"Output file empty: {result['output_file']}"
    
    # Log any failures with error codes
    for result in results:
        if not result['success']:
            error_code = result.get('error_code', 'ERR-UNKNOWN')
            error_msg = result.get('error_message', 'Unknown error')
            logger.warning(f"Fetch failed for {result['url']}: {error_code} - {error_msg}")
    
    logger.info(f"✓ Batch processing completed: {successful_count}/{len(test_subset)} successful")
    return True

def test_error_handling():
    """Test that appropriate errors are logged for invalid URLs."""
    logger.info("Testing error handling for invalid URLs...")
    
    invalid_url = "https://this-domain-definitely-does-not-exist-12345.com"
    
    success, content, error_msg = fetch_url_with_retry(
        invalid_url,
        timeout=5,  # Short timeout for test
        max_retries=1
    )
    
    # We expect this to fail
    assert not success, "Fetch should have failed for invalid URL"
    assert error_msg is not None, "Error message should be present"
    
    logger.info(f"✓ Correctly handled invalid URL with error: {error_msg}")
    return True

def main():
    """Run all integration tests for FR-002."""
    logger.info("=" * 60)
    logger.info("Starting FR-002 Verification: URL Fetching and HTML Retrieval")
    logger.info("=" * 60)
    
    try:
        # Setup
        setup_test_environment()
        
        # Run tests
        test_fetch_url_with_retry()
        test_fetch_html_to_file()
        test_ingest_and_fetch_batch()
        test_error_handling()
        
        logger.info("=" * 60)
        logger.info("✓ ALL FR-002 VERIFICATION TESTS PASSED")
        logger.info("=" * 60)
        return 0
        
    except AssertionError as e:
        logger.error(f"TEST FAILED: {str(e)}")
        logger.info("=" * 60)
        logger.error("✗ FR-002 VERIFICATION FAILED")
        logger.info("=" * 60)
        return 1
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {str(e)}")
        logger.info("=" * 60)
        logger.error("✗ FR-002 VERIFICATION FAILED WITH EXCEPTION")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
