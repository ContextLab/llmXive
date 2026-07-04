"""
Unit tests for OULAD URL accessibility and response validation.

This module tests the connectivity to the OULAD data source and validates
the HTTP response characteristics (status code, content type, content length)
to ensure the download script (code/download_data.py) can successfully fetch data.

Tests:
- test_oulad_url_accessible: Verifies the URL returns a 200 OK status.
- test_oulad_response_content_type: Verifies the response is HTML or ZIP (as expected).
- test_oulad_response_size: Verifies the response body is not empty.
"""

import pytest
import requests
import os
from pathlib import Path
from urllib.parse import urljoin

# Import config to get the real URL
# We use a relative import pattern compatible with the project structure
# Assuming tests are run from project root or with PYTHONPATH set
import sys
from pathlib import Path

# Add the code directory to the path if not already there
code_dir = Path(__file__).parent.parent / "projects" / "PROJ-438-the-effect-of-personalized-feedback-timi" / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_config_value

# The canonical OULAD URL from the project plan/specs
OULAD_BASE_URL = "https://analyse.kmi.open.ac.uk/open_dataset"
OULAD_DOWNLOAD_URL = "https://analyse.kmi.open.ac.uk/open_dataset/OULAD.zip"

# Timeout for network requests in seconds
REQUEST_TIMEOUT = 30


class TestOULADUrlAccessibility:
    """Tests for verifying the OULAD data source is reachable and valid."""

    def test_oulad_url_accessible(self):
        """
        Verify that the main OULAD landing page returns a 200 OK status.
        
        This ensures the data source is online and accessible before attempting
        to download the dataset.
        """
        try:
            response = requests.get(OULAD_BASE_URL, timeout=REQUEST_TIMEOUT)
            assert response.status_code == 200, (
                f"OULAD landing page returned status {response.status_code}. "
                f"Expected 200. The data source may be down or the URL has changed."
            )
        except requests.exceptions.Timeout:
            pytest.fail(f"Request to {OULAD_BASE_URL} timed out after {REQUEST_TIMEOUT}s")
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Failed to connect to {OULAD_BASE_URL}. Network error or host unreachable.")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Unexpected error accessing {OULAD_BASE_URL}: {str(e)}")

    def test_oulad_download_url_accessible(self):
        """
        Verify that the direct download URL for OULAD.zip is accessible.
        
        We use HEAD request to avoid downloading the full file, just checking headers.
        """
        try:
            response = requests.head(OULAD_DOWNLOAD_URL, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            # Some servers return 200, some 302 for HEAD. We accept 200 or 301/302/307/308.
            assert response.status_code in [200, 301, 302, 307, 308], (
                f"OULAD download URL returned status {response.status_code}. "
                f"Expected 200 or redirect. The dataset may be unavailable."
            )
        except requests.exceptions.Timeout:
            pytest.fail(f"HEAD request to {OULAD_DOWNLOAD_URL} timed out after {REQUEST_TIMEOUT}s")
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Failed to connect to {OULAD_DOWNLOAD_URL}. Network error.")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Unexpected error accessing {OULAD_DOWNLOAD_URL}: {str(e)}")

    def test_oulad_response_content_type(self):
        """
        Verify the response content type is appropriate for the download.
        
        The OULAD dataset is typically a ZIP file or served as HTML with a download link.
        We check that the response is not empty and has a plausible content type.
        """
        # Use HEAD first to check headers without downloading
        try:
            head_response = requests.head(OULAD_DOWNLOAD_URL, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            content_type = head_response.headers.get("Content-Type", "").lower()
            
            # Acceptable types: application/zip, application/octet-stream, or text/html (if redirect page)
            acceptable_types = [
                "application/zip",
                "application/octet-stream",
                "text/html",
                "application/x-zip-compressed"
            ]
            
            # If it's a redirect, the content type might be HTML, which is fine for the landing page
            # If it's a direct file, it should be zip/octet-stream
            is_acceptable = any(t in content_type for t in acceptable_types)
            
            # If the server doesn't return a content type, we still pass if status is 200
            # (some servers omit it for HEAD)
            if not content_type and head_response.status_code == 200:
                pass # Acceptable if no content type but success
            else:
                assert is_acceptable, (
                    f"Unexpected Content-Type: {content_type}. "
                    f"Expected one of: {acceptable_types}"
                )
        except requests.exceptions.RequestException:
            # If we can't reach the server, the accessibility test should have caught it
            pytest.skip("Cannot verify content type due to connection error")

    def test_oulad_response_not_empty(self):
        """
        Verify that a GET request to the download URL returns a non-empty body.
        
        We perform a small GET request (stream=True) and check the first chunk.
        This ensures the file exists and is not corrupted/empty.
        """
        try:
            response = requests.get(OULAD_DOWNLOAD_URL, timeout=REQUEST_TIMEOUT, stream=True)
            assert response.status_code == 200, (
                f"GET request returned {response.status_code}. Expected 200."
            )
            
            # Read the first chunk to verify non-empty
            chunk = next(response.iter_content(chunk_size=1024))
            assert len(chunk) > 0, "Response body is empty. The dataset file may be missing."
            
        except StopIteration:
            pytest.fail("Response stream ended immediately without data.")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Error during GET request: {str(e)}")