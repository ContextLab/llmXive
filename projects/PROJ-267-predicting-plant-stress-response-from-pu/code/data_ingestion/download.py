"""
Data Ingestion: Download Module (T011)

Implements FR-001: Fetch raw data from NCBI GEO/ProteomeXchange.
- Reads explicit URLs from research.md.
- Validates domains (ncbi.nlm.nih.gov, proteomexchange.org, ebi.ac.uk).
- Downloads files to data/raw/.
- Raises ValueError if file size < 1KB or domain invalid.
"""
import os
import sys
import logging
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

# Project-relative imports
from utils.config import DATA_RAW_PATH, get_logger, log_warning, REFERENCE_VALIDATOR_THRESHOLD
from utils.checksums import compute_sha256, save_checksums

# Configure logger for this module
logger = get_logger(__name__)

# Allowed domains for data sources
ALLOWED_DOMAINS = {
    "ncbi.nlm.nih.gov",
    "proteomexchange.org",
    "ebi.ac.uk",
    "www.ncbi.nlm.nih.gov",
    "www.proteomexchange.org",
    "www.ebi.ac.uk"
}

# Minimum file size threshold (1 KB)
MIN_FILE_SIZE_BYTES = 1024

def parse_research_md_urls(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse research.md to extract URLs and associated metadata.
    
    Expected format in research.md:
    - [Source Name] (URL)
    - or simply: URL
    
    Returns a list of dicts: [{'source': str, 'url': str}, ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"research.md not found at {file_path}")

    urls = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find URLs (http/https)
    url_pattern = re.compile(r'https?://[^\s\)\]]+')
    matches = url_pattern.findall(content)

    for url in matches:
        # Clean up potential trailing punctuation
        url = url.rstrip(').,;:')
        # Determine source name if possible (simple heuristic: look before URL)
        source_name = "Unknown"
        # Try to find a bracketed name or context before the URL
        context_match = re.search(r'\[([^\]]+)\].*?(' + re.escape(url) + r')', content)
        if context_match:
            source_name = context_match.group(1).strip()
        
        urls.append({
            "source": source_name,
            "url": url
        })

    logger.info(f"Found {len(urls)} potential data URLs in {file_path}")
    return urls

def validate_domain(url: str) -> bool:
    """
    Validate that the URL belongs to an allowed domain.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Handle 'www.' prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if domain not in ALLOWED_DOMAINS:
            logger.error(f"Invalid domain: {domain} for URL: {url}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to parse domain for URL {url}: {e}")
        return False

def download_file(url: str, output_path: Path, timeout: int = 300) -> bool:
    """
    Download a file from the given URL to output_path.
    
    - Validates domain first.
    - Checks file size >= 1KB.
    - Raises ValueError on failure.
    """
    if not validate_domain(url):
        raise ValueError(f"Domain validation failed for URL: {url}")

    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Check Content-Length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            if int(content_length) < MIN_FILE_SIZE_BYTES:
                raise ValueError(f"Downloaded file size ({content_length} bytes) is less than 1KB for URL: {url}")

        # Write to disk
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify actual file size
        actual_size = output_path.stat().st_size
        if actual_size < MIN_FILE_SIZE_BYTES:
            # Clean up small file
            output_path.unlink()
            raise ValueError(f"Downloaded file size ({actual_size} bytes) is less than 1KB for URL: {url}")

        # Compute checksum
        checksum = compute_sha256(output_path)
        logger.info(f"Download complete. Size: {actual_size} bytes, SHA256: {checksum}")
        
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error downloading {url}: {e}")
        raise ValueError(f"Network error downloading {url}: {e}")
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        raise

def run_download_pipeline(research_md_path: str = "research.md") -> List[Dict[str, Any]]:
    """
    Main pipeline function to download all data sources.
    
    1. Parse URLs from research.md.
    2. Validate domains.
    3. Download files to data/raw/.
    4. Save checksums.
    """
    raw_dir = Path(DATA_RAW_PATH)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    url_list = parse_research_md_urls(research_md_path)
    results = []
    
    for item in url_list:
        url = item['url']
        source = item['source']
        
        # Generate a safe filename
        # Use the last part of the path or a hash if ambiguous
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = f"data_{hash(url) % 10000}.gz" # Fallback naming
        
        # Handle cases where filename might be empty or invalid
        if not filename or filename == '/':
            filename = f"source_{source.replace(' ', '_')}.dat"
        
        output_path = raw_dir / filename
        
        # Check if file already exists and has correct size (optional optimization)
        if output_path.exists() and output_path.stat().st_size >= MIN_FILE_SIZE_BYTES:
            logger.info(f"File {filename} already exists and is valid. Skipping download.")
            results.append({
                "source": source,
                "url": url,
                "status": "skipped",
                "path": str(output_path)
            })
            continue

        try:
            success = download_file(url, output_path)
            if success:
                results.append({
                    "source": source,
                    "url": url,
                    "status": "success",
                    "path": str(output_path)
                })
        except ValueError as e:
            # Log the error but continue with other URLs if possible
            logger.error(f"Failed to download {url}: {e}")
            results.append({
                "source": source,
                "url": url,
                "status": "failed",
                "error": str(e),
                "path": str(output_path)
            })
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            results.append({
                "source": source,
                "url": url,
                "status": "error",
                "error": str(e),
                "path": str(output_path)
            })

    # Save checksums for all successfully downloaded files
    success_files = [r['path'] for r in results if r['status'] == 'success']
    if success_files:
        save_checksums(success_files, raw_dir / "checksums.json")
        logger.info(f"Saved checksums for {len(success_files)} files.")

    return results

def main():
    """
    Entry point for the download script.
    """
    logger.info("Starting data ingestion download pipeline (T011).")
    
    # Default path relative to project root
    research_md = Path("research.md")
    if not research_md.exists():
        # Try in parent directory if run from code/
        if Path("code/research.md").exists():
            research_md = Path("code/research.md")
        else:
            logger.error("research.md not found. Cannot proceed.")
            sys.exit(1)

    results = run_download_pipeline(str(research_md))
    
    # Print summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = sum(1 for r in results if r['status'] in ['failed', 'error'])
    
    logger.info(f"Pipeline finished. Success: {success_count}, Failed: {fail_count}.")
    
    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
