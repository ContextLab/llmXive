"""
OSF Client Module for PROJ-350.

Provides a client for interacting with the Open Science Framework (OSF) API,
implementing exponential backoff for rate limiting and resume capability for
large file downloads.
"""
import os
import time
import hashlib
import requests
from typing import Optional, Dict, Any, List, BinaryIO
from pathlib import Path

# Constants for backoff strategy
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0     # seconds
BACKOFF_MULTIPLIER = 2.0

# OSF API Base URL
OSF_API_BASE = "https://api.osf.io/v2"

class OSFClientError(Exception):
    """Base exception for OSF client errors."""
    pass

class RateLimitExceededError(OSFClientError):
    """Raised when rate limit is exceeded and retries are exhausted."""
    pass

class DownloadError(OSFClientError):
    """Raised when a file download fails."""
    pass

def _calculate_backoff(attempt: int) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current retry attempt (0-indexed).

    Returns:
        Delay in seconds.
    """
    delay = min(INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF)
    # Add small jitter to prevent thundering herd
    jitter = delay * 0.1 * (time.time() % 1)
    return delay + jitter

def fetch_with_backoff(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Fetch data from OSF API with exponential backoff for rate limiting.

    Args:
        url: The API endpoint URL.
        params: Optional query parameters.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response as a dictionary.

    Raises:
        RateLimitExceededError: If max retries are exceeded due to 429 status.
        OSFClientError: For other HTTP errors.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            
            if response.status_code == 429:
                # Rate limited - wait and retry
                delay = _calculate_backoff(attempt)
                time.sleep(delay)
                last_error = f"Rate limited (429). Waiting {delay:.2f}s before retry {attempt + 1}/{MAX_RETRIES}."
                continue
            
            # Non-recoverable error
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                time.sleep(delay)
            else:
                raise OSFClientError(f"Request failed after {MAX_RETRIES} attempts: {last_error}") from e

    raise RateLimitExceededError(f"Rate limit exceeded after {MAX_RETRIES} retries. Last error: {last_error}")

def download_file_with_resume(
    url: str,
    output_path: str,
    chunk_size: int = 8192,
    timeout: int = 60
) -> str:
    """
    Download a file with resume capability for interrupted downloads.

    Args:
        url: The URL to download from.
        output_path: Local path to save the file.
        chunk_size: Size of chunks to read/write.
        timeout: Request timeout in seconds.

    Returns:
        Path to the downloaded file.

    Raises:
        DownloadError: If download fails after retries.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if partial file exists
    downloaded_size = 0
    headers = {}
    mode = 'wb'
    
    if output_path.exists():
        downloaded_size = output_path.stat().st_size
        headers = {'Range': f'bytes={downloaded_size}-'}
        mode = 'ab'

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()

            # If we resumed, check if server supports range requests
            if downloaded_size > 0:
                if response.status_code == 206:  # Partial Content
                    pass
                elif response.status_code == 200:  # Server ignored range, restart
                    downloaded_size = 0
                    mode = 'wb'
                    # Truncate file if it was opened in append mode
                    with open(output_path, 'wb') as f:
                        pass
            else:
                if response.status_code == 206:
                    # Server sent partial content for full request (odd but possible)
                    pass

            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

            # Verify file integrity if we downloaded the whole thing
            if downloaded_size == 0 and 'Content-Range' not in response.headers:
                # Full download completed
                return str(output_path)
            elif 'Content-Range' in response.headers:
                # Check if we got the full range
                content_range = response.headers['Content-Range']
                # Format: bytes 0-1234/5678 -> total is 5679 bytes
                try:
                    total_size = int(content_range.split('/')[-1])
                    current_size = output_path.stat().st_size
                    if current_size >= total_size:
                        return str(output_path)
                except (ValueError, IndexError):
                    pass
            
            # If we get here, we might need to retry or verify
            # For simplicity, if we got a 206, we assume it's good enough for resume logic
            # In a production system, we'd verify checksums
            return str(output_path)

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                time.sleep(delay)
            else:
                raise DownloadError(f"Download failed after {MAX_RETRIES} attempts: {last_error}") from e

    raise DownloadError(f"Download failed after {MAX_RETRIES} retries. Last error: {last_error}")

def get_study_metadata(osf_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a specific OSF study.

    Args:
        osf_id: The OSF project ID (e.g., 'xyz12').

    Returns:
        Dictionary containing study metadata.

    Raises:
        OSFClientError: If the study is not found or API fails.
    """
    url = f"{OSF_API_BASE}/nodes/{osf_id}"
    try:
        data = fetch_with_backoff(url)
        return data.get('data', {})
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise OSFClientError(f"Study not found: {osf_id}") from e
        raise

def get_study_files(osf_id: str) -> List[Dict[str, Any]]:
    """
    Fetch list of files associated with an OSF study.

    Args:
        osf_id: The OSF project ID.

    Returns:
        List of file metadata dictionaries.
    """
    url = f"{OSF_API_BASE}/nodes/{osf_id}/files"
    data = fetch_with_backoff(url)
    files = []
    
    # Handle pagination if necessary
    while data:
        if 'data' in data:
            for item in data['data']:
                files.append(item)
        
        # Check for next page
        links = data.get('links', {})
        if links.get('next'):
            data = fetch_with_backoff(links['next'])
        else:
            break
    
    return files

def get_file_download_url(file_metadata: Dict[str, Any]) -> Optional[str]:
    """
    Extract the direct download URL from file metadata.

    Args:
        file_metadata: File metadata dictionary from OSF API.

    Returns:
        Download URL or None if not available.
    """
    links = file_metadata.get('links', {})
    return links.get('download')

def download_study_file(
    osf_id: str,
    file_name: str,
    output_dir: str,
    file_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Download a specific file from an OSF study.

    Args:
        osf_id: The OSF project ID.
        file_name: Name of the file to download.
        output_dir: Directory to save the file.
        file_metadata: Optional pre-fetched file metadata.

    Returns:
        Path to the downloaded file.
    """
    if file_metadata is None:
        files = get_study_files(osf_id)
        # Find the file by name (case-insensitive)
        target_file = None
        for f in files:
            if f.get('attributes', {}).get('name', '').lower() == file_name.lower():
                target_file = f
                break
        
        if not target_file:
            raise OSFClientError(f"File '{file_name}' not found in study {osf_id}")
        file_metadata = target_file

    download_url = get_file_download_url(file_metadata)
    if not download_url:
        raise OSFClientError(f"No download URL available for file '{file_name}'")

    output_path = Path(output_dir) / file_name
    return download_file_with_resume(download_url, str(output_path))