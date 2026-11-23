import os
import sys
import logging
import re
import requests
from pathlib import Path
from typing import List, Tuple, Optional

# Local imports based on API surface
from utils.logging_config import get_logger, log_warning
from utils.config import get_data_path, get_project_root

logger = get_logger(__name__)

# Allowed domains for data fetching
ALLOWED_DOMAINS = [
    'ncbi.nlm.nih.gov',
    'proteomexchange.org',
    'ebi.ac.uk',
    'www.ebi.ac.uk',
    'figshare.com',
    'dataverse.harvard.edu',
    'zenodo.org'
]

def parse_research_md_urls() -> List[Tuple[str, str]]:
    """
    Parses research.md to extract data source URLs and their descriptions.
    Returns a list of (url, description) tuples.
    """
    project_root = get_project_root()
    research_md_path = project_root / 'research.md'
    
    if not research_md_path.exists():
        raise FileNotFoundError(f"research.md not found at {research_md_path}")

    urls = []
    current_desc = ""
    
    with open(research_md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_data_section = False
    for line in lines:
        line_stripped = line.strip()
        
        # Detect section start
        if line_stripped.startswith('#') and 'Data' in line_stripped:
            in_data_section = True
            continue
        
        if in_data_section:
            if line_stripped.startswith('#'):
                in_data_section = False
                continue
            
            # Look for URLs
            url_match = re.search(r'(https?://[^\s\)]+)', line)
            if url_match:
                url = url_match.group(1)
                # Clean up markdown links if present
                if url.startswith('http'):
                    # Extract description from the line if available
                    desc = line.replace(url, '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').strip()
                    if not desc:
                        desc = url.split('/')[-1]
                    urls.append((url, desc))
                    logger.info(f"Found URL: {url}")
    
    if not urls:
        raise ValueError("No valid data URLs found in research.md")
        
    return urls

def validate_domain(url: str) -> bool:
    """
    Validates that the URL belongs to an allowed domain.
    Raises ValueError if the domain is not allowed.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if not domain:
            raise ValueError(f"Could not extract domain from URL: {url}")
        
        is_allowed = any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
        
        if not is_allowed:
            raise ValueError(f"Domain '{domain}' is not in the allowed list: {ALLOWED_DOMAINS}")
        
        logger.info(f"Domain validation passed for: {domain}")
        return True
    except Exception as e:
        logger.error(f"Domain validation failed: {e}")
        raise

def download_file(url: str, dest_dir: Optional[Path] = None) -> Path:
    """
    Downloads a file from a validated URL.
    
    STRICT ERROR HANDLING:
    - No try/except blocks that catch network errors and return synthetic data.
    - No fallback to mock data.
    - Any failure to fetch real data results in an immediate, loud Exception.
    
    Args:
        url: The URL to download from.
        dest_dir: Directory to save the file. Defaults to data/raw/.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        ValueError: If URL is invalid or domain not allowed.
        requests.exceptions.RequestException: If the download fails (network error, 404, etc.).
        RuntimeError: If file size is < 1KB.
    """
    # Validate domain first
    validate_domain(url)
    
    if dest_dir is None:
        dest_dir = get_data_path() / 'raw'
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Derive filename from URL
    filename = url.split('/')[-1].split('?')[0]
    if not filename:
        filename = f"downloaded_file_{int(time.time())}"
    
    dest_path = dest_dir / filename
    
    logger.info(f"Downloading {url} to {dest_path}")
    
    try:
        # Stream the download to handle large files
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()  # This raises HTTPError for bad responses (4xx, 5xx)
        
        # Check content length if available
        content_length = response.headers.get('content-length')
        if content_length:
            logger.info(f"Expected file size: {int(content_length)} bytes")
        
        # Write to file
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify file size
        file_size = dest_path.stat().st_size
        if file_size < 1024:
            # Clean up the small file
            dest_path.unlink()
            raise RuntimeError(f"Downloaded file size ({file_size} bytes) is less than 1KB. Data source may be empty or invalid.")
        
        logger.info(f"Successfully downloaded {filename} ({file_size} bytes)")
        return dest_path
        
    except requests.exceptions.Timeout:
        logger.error(f"Download timed out for {url}")
        raise
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection failed for {url}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for {url}")
        raise
    except Exception as e:
        # Re-raise any other unexpected errors loudly
        logger.error(f"Unexpected error during download: {e}")
        raise

def run_download_pipeline() -> List[Path]:
    """
    Orchestrates the download of all data sources listed in research.md.
    
    Returns:
        List of paths to downloaded files.
    
    Raises:
        Exception: If any download fails. No synthetic fallback is performed.
    """
    logger.info("Starting download pipeline")
    urls = parse_research_md_urls()
    downloaded_files = []
    
    for url, desc in urls:
        try:
            file_path = download_file(url)
            downloaded_files.append(file_path)
        except Exception as e:
            # Log the specific failure but do NOT fallback to synthetic data
            logger.error(f"Failed to download {desc}: {e}")
            # Re-raise to halt the pipeline as per strict error handling requirements
            raise e
    
    logger.info(f"Download pipeline completed. {len(downloaded_files)} files downloaded.")
    return downloaded_files

def main():
    """Entry point for the download script."""
    try:
        files = run_download_pipeline()
        print(f"Successfully downloaded {len(files)} files:")
        for f in files:
            print(f"  - {f}")
    except Exception as e:
        logger.error(f"Download pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()