import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import logging
from urllib.parse import urlparse
import hashlib
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
EXTERNAL_DIR = DATA_DIR / "external"
VERIFICATION_LOG_PATH = DATA_DIR / "verification_log.json"

# Security constraints
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
ALLOWED_EXTENSIONS = {'.csv', '.json', '.yaml', '.yml', '.txt', '.parquet'}
ALLOWED_HOSTS = {
    'figshare.com',
    'zenodo.org',
    'github.com',
    'raw.githubusercontent.com',
    'nist.gov',
    'mofdb.org'
}

def sanitize_url(url: str) -> str:
    """
    Sanitize and validate the input URL.
    Prevents SSRF, path traversal, and injection attacks.
    """
    if not isinstance(url, str):
        raise ValueError("URL must be a string")

    # Remove whitespace and control characters
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    # Check for null bytes or dangerous characters
    if '\x00' in url or any(c in url for c in ['\n', '\r', '\t']):
        raise ValueError("URL contains invalid characters")

    # Validate URL format
    parsed = urlparse(url)
    
    if not parsed.scheme:
        raise ValueError("URL must include a scheme (http/https)")
    
    if parsed.scheme not in ('http', 'https'):
        raise ValueError("Only HTTP and HTTPS schemes are allowed")

    # Validate hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a valid hostname")

    # Check against allowlist
    if not any(hostname.endswith(host) for host in ALLOWED_HOSTS):
        raise ValueError(f"Hostname '{hostname}' is not in the allowed list")

    # Normalize and return
    return url

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection.
    """
    if not isinstance(filename, str):
        raise ValueError("Filename must be a string")

    # Remove path separators and control characters
    filename = filename.replace('\\', '/').split('/')[-1]
    filename = filename.replace('\x00', '').strip()

    if not filename:
        raise ValueError("Filename cannot be empty after sanitization")

    # Check extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension '{ext}' is not allowed")

    # Check for dangerous patterns
    if '..' in filename or filename.startswith('.'):
        raise ValueError("Filename contains invalid path components")

    return filename

def write_verification_log(
    status: str,
    source: str,
    details: str,
    timestamp: Optional[datetime] = None,
    file_hash: Optional[str] = None,
    error: Optional[str] = None
) -> Path:
    """
    Write a verification log entry to verification_log.json.
    Creates the file if it doesn't exist, appends if it does.
    """
    if timestamp is None:
        timestamp = datetime.now()

    log_entry = {
        "timestamp": timestamp.isoformat(),
        "status": status,
        "source": source,
        "details": details,
        "file_hash": file_hash,
        "error": error
    }

    # Ensure directory exists
    VERIFICATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read existing logs or create new list
    if VERIFICATION_LOG_PATH.exists():
        try:
            with open(VERIFICATION_LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = [logs]
        except (json.JSONDecodeError, IOError):
            logger.warning("Corrupted verification log, creating new one")
            logs = []
    else:
        logs = []

    # Append new entry
    logs.append(log_entry)

    # Write back with formatting
    with open(VERIFICATION_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    logger.info(f"Verification log written: {VERIFICATION_LOG_PATH}")
    return VERIFICATION_LOG_PATH

def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def attempt_nist_fetch(url: str, output_filename: str) -> bool:
    """
    Attempt to fetch data from NIST or similar trusted source.
    Returns True on success, False on failure.
    """
    try:
        # Sanitize inputs
        sanitized_url = sanitize_url(url)
        sanitized_filename = sanitize_filename(output_filename)
        output_path = EXTERNAL_DIR / sanitized_filename

        logger.info(f"Attempting fetch from: {sanitized_url}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Stream download with size limit
        headers = {'User-Agent': 'llmXive-Downloader/1.0'}
        response = requests.get(sanitized_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        total_size = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        logger.error("Download exceeded size limit")
                        output_path.unlink()
                        raise ValueError("File size exceeds maximum allowed")

        # Verify file integrity
        file_hash = calculate_file_hash(output_path)
        logger.info(f"Downloaded successfully. Size: {total_size} bytes, Hash: {file_hash}")

        # Write success log
        write_verification_log(
            status="SUCCESS",
            source="NIST",
            details=f"Fetched {sanitized_filename}",
            file_hash=file_hash
        )

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during NIST fetch: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="NIST",
            details=f"Failed to fetch {output_filename}",
            error=str(e)
        )
        return False
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="NIST",
            details="Input validation failed",
            error=str(e)
        )
        return False
    except Exception as e:
        logger.error(f"Unexpected error during NIST fetch: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="NIST",
            details="Unexpected error",
            error=str(e)
        )
        return False

def attempt_fallback_fetch(url: str, output_filename: str) -> bool:
    """
    Fallback fetch mechanism for when primary source fails.
    Validates URL and attempts download with stricter checks.
    """
    try:
        # Sanitize inputs
        sanitized_url = sanitize_url(url)
        sanitized_filename = sanitize_filename(output_filename)
        output_path = EXTERNAL_DIR / sanitized_filename

        logger.info(f"Attempting fallback fetch from: {sanitized_url}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Additional check for known malicious patterns in path
        if re.search(r'//', sanitized_url.split('://')[1]):
            raise ValueError("Suspicious URL path structure detected")

        headers = {'User-Agent': 'llmXive-Downloader/1.0'}
        response = requests.get(sanitized_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type and not sanitized_filename.endswith('.html'):
            logger.warning("Received HTML content for non-HTML request")
            # Allow it but log warning

        total_size = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        logger.error("Download exceeded size limit")
                        output_path.unlink()
                        raise ValueError("File size exceeds maximum allowed")

        file_hash = calculate_file_hash(output_path)
        logger.info(f"Fallback fetch successful. Size: {total_size} bytes, Hash: {file_hash}")

        write_verification_log(
            status="SUCCESS",
            source="FALLBACK",
            details=f"Fetched {sanitized_filename} via fallback",
            file_hash=file_hash
        )

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during fallback fetch: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="FALLBACK",
            details=f"Failed to fetch {output_filename} via fallback",
            error=str(e)
        )
        return False
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="FALLBACK",
            details="Input validation failed",
            error=str(e)
        )
        return False
    except Exception as e:
        logger.error(f"Unexpected error during fallback fetch: {str(e)}")
        write_verification_log(
            status="FAILURE",
            source="FALLBACK",
            details="Unexpected error",
            error=str(e)
        )
        return False

def main():
    """
    Main entry point for the download module.
    Demonstrates security-hardened fetching with verification logging.
    """
    logger.info("Starting download module with security hardening")

    # Test case 1: Valid NIST fetch attempt (will likely fail if URL doesn't exist)
    test_url = "https://figshare.com/ndownloader/files/12345678"  # Example valid structure
    test_filename = "test_data.csv"
    
    logger.info(f"Testing with URL: {test_url}")
    
    # Attempt primary fetch
    success = attempt_nist_fetch(test_url, test_filename)
    
    if not success:
        logger.info("Primary fetch failed, attempting fallback")
        # In a real scenario, we might try a different URL
        # For this demo, we just log the attempt
    
    # Test case 2: Invalid URL (should be caught by sanitization)
    invalid_url = "javascript:alert('xss')"
    try:
        sanitize_url(invalid_url)
        logger.error("Should have raised an exception for invalid URL")
    except ValueError as e:
        logger.info(f"Correctly rejected invalid URL: {e}")
    
    # Test case 3: Path traversal attempt
    malicious_filename = "../../../etc/passwd.csv"
    try:
        sanitize_filename(malicious_filename)
        logger.error("Should have raised an exception for path traversal")
    except ValueError as e:
        logger.info(f"Correctly rejected malicious filename: {e}")

    logger.info("Download module security tests completed")

if __name__ == "__main__":
    main()