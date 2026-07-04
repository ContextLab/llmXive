"""
Validate URLs for CodeSearchNet and Defects4J datasets before download.

This script checks the accessibility of the primary download URLs for the
required datasets. It exits with code 0 if all URLs are reachable, or code 1
if any URL is unreachable, printing specific error details.
"""
import sys
import time
import urllib.request
import urllib.error
from typing import List, Tuple

# Configuration: Real, public URLs for the datasets
# CodeSearchNet: GitHub release of the processed dataset
CODESEARCHNET_URL = "https://github.com/code-search-net/CodeSearchNet/archive/master.zip"

# Defects4J: Official website download link
DEFECTS4J_URL = "https://github.com/rjust/defects4j/releases/download/v2.0.0/defects4j-2.0.0.tar.gz"

# Connection timeout in seconds
TIMEOUT = 10


def check_url(url: str, timeout: int = TIMEOUT) -> Tuple[bool, str]:
    """
    Check if a URL is accessible by attempting a HEAD request.
    
    Args:
        url: The URL to check.
        timeout: Connection timeout in seconds.
        
    Returns:
        Tuple of (is_accessible, status_message)
    """
    try:
        # Use a request with method 'HEAD' if supported, otherwise 'GET' with no body read
        # urllib.request does not support HEAD directly in all Python versions easily without custom opener,
        # so we do a GET but stop reading after headers if possible, or just a fast fetch.
        # For robustness with large files, we just try to open and check headers.
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True, f"OK (HTTP {response.status})"
            else:
                return False, f"Unexpected status code: {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"


def main():
    """
    Main entry point to validate all dataset URLs.
    """
    urls_to_check = [
        ("CodeSearchNet", CODESEARCHNET_URL),
        ("Defects4J", DEFECTS4J_URL),
    ]

    print("Starting URL validation for dataset sources...")
    print("-" * 60)

    all_passed = True
    results: List[Tuple[str, bool, str]] = []

    for name, url in urls_to_check:
        print(f"Checking {name}...")
        print(f"  URL: {url}")
        
        start_time = time.time()
        success, message = check_url(url)
        elapsed = time.time() - start_time

        status = "PASS" if success else "FAIL"
        print(f"  Status: {status} ({message}) [{elapsed:.2f}s]")
        print("-" * 60)

        results.append((name, success, message))
        if not success:
            all_passed = False

    print("\nSummary:")
    if all_passed:
        print("  All dataset URLs are reachable.")
        print("  Proceeding to download is safe.")
        sys.exit(0)
    else:
        print("  One or more dataset URLs are unreachable.")
        print("  Please check your network connection or the URL configuration.")
        print("\nFailed checks:")
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()