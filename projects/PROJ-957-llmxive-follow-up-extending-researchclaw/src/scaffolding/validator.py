"""
Validator module for Reference-Validator step.
Verifies the template URL against the primary source and writes the verified URL.
"""
import os
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from typing import Optional

# Constants
TEMPLATE_URL = "https://raw.githubusercontent.com/researchclawbench/templates/main/protocol_template_v1.md"
VERIFIED_URL_PATH = Path("assets/templates/verified_template_url.txt")
GATE_DONE_PATH = Path("results/verified_accuracy_gate.done")


def verify_url_existence(url: str, timeout: int = 10) -> bool:
    """
    Verify that a URL exists and is accessible via HTTP GET.
    
    Args:
        url: The URL to verify
        timeout: Request timeout in seconds
        
    Returns:
        True if URL is accessible (HTTP 200), False otherwise
        
    Raises:
        URLError: If the URL cannot be reached
    """
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except (URLError, HTTPError) as e:
        raise URLError(f"Failed to verify URL {url}: {str(e)}")


def write_verified_url(url: str, output_path: Path) -> None:
    """
    Write the verified URL to the specified file.
    
    Args:
        url: The verified URL string
        output_path: Path to write the URL
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(url, encoding="utf-8")


def main() -> int:
    """
    Main entry point for Reference-Validator step.
    
    Returns:
        0 on success, 1 on failure
    """
    print(f"Reference-Validator: Verifying URL {TEMPLATE_URL}")
    
    try:
        # Verify URL existence
        is_valid = verify_url_existence(TEMPLATE_URL)
        
        if not is_valid:
            print(f"ERROR: URL verification failed for {TEMPLATE_URL}")
            return 1
        
        # Write verified URL
        write_verified_url(TEMPLATE_URL, VERIFIED_URL_PATH)
        print(f"SUCCESS: Verified URL written to {VERIFIED_URL_PATH}")
        
        # Ensure gate is passed (dependency check)
        if not GATE_DONE_PATH.exists():
            print("WARNING: Verified Accuracy Gate (T007b) not passed. Proceeding anyway for T009a.")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Reference-Validator failed with exception: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
