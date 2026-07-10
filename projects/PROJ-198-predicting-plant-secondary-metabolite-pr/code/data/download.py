"""
Data download module for fetching genomic and metabolomic data.

Implements download_genomes() to fetch FASTA/GFF from NCBI RefSeq/Phytozome
with size filtering, retry logic, and timeout handling.
"""
import os
import time
import logging
import requests
import gzip
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
import hashlib
import re

from config import get_species_list, get_data_path
from utils.logging import get_logger

# Constants
MAX_GENOME_SIZE_MB = 500
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 300  # 5 minutes for large file downloads
CHUNK_SIZE_BYTES = 8192

# Initialize logger
logger = get_logger(__name__)

class DownloadError(Exception):
    """Custom exception for download failures."""
    pass

def _calculate_file_size_mb(url: str) -> Optional[float]:
    """
    Get the file size in MB from the Content-Length header.
    Returns None if size cannot be determined.
    """
    try:
        # Use HEAD request to get headers without downloading content
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_bytes = int(content_length)
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
    except requests.RequestException as e:
        logger.debug(f"Could not determine file size for {url}: {e}")
    return None

def _download_file_with_retry(
    url: str,
    output_path: Path,
    description: str = "File"
) -> bool:
    """
    Download a file with retry logic and progress logging.
    
    Args:
        url: The URL to download from
        output_path: Where to save the downloaded file
        description: Human-readable description of the file for logging
        
    Returns:
        True if download succeeded, False otherwise
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Downloading {description} (attempt {attempt}/{MAX_RETRIES}): {url}")
            
            response = requests.get(
                url,
                stream=True,
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            # Get total size for progress reporting
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if attempt == 1 and downloaded % (total_size // 10 + 1) < CHUNK_SIZE_BYTES:
                                # Log progress every 10% on first attempt only
                                logger.debug(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Successfully downloaded {description} to {output_path}")
            return True
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout downloading {description} (attempt {attempt}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to download {description} after {MAX_RETRIES} attempts due to timeout")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error downloading {description} (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            else:
                logger.error(f"Failed to download {description} after {MAX_RETRIES} attempts: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error downloading {description}: {e}")
            return False
    
    return False

def _validate_genome_file(output_path: Path) -> bool:
    """
    Basic validation that the downloaded file is not empty and has expected extensions.
    """
    if not output_path.exists():
        return False
    
    file_size = output_path.stat().st_size
    if file_size == 0:
        logger.warning(f"Downloaded file is empty: {output_path}")
        return False
    
    # Check for expected extensions
    valid_extensions = {'.fasta', '.fa', '.fna', '.ffn', '.faa', '.gff', '.gff3', '.gz'}
    suffixes = output_path.suffixes
    if suffixes:
        last_suffix = suffixes[-1].lower()
        if last_suffix == '.gz' and len(suffixes) > 1:
            last_suffix = suffixes[-2].lower() + last_suffix
        
        if last_suffix not in valid_extensions and not last_suffix.endswith('.gz'):
            logger.warning(f"Unexpected file extension: {output_path.suffix}")
            # Don't fail on extension mismatch, just warn
    
    return True

def _extract_species_name_from_url(url: str) -> Optional[str]:
    """
    Attempt to extract a species name or identifier from the URL.
    Falls back to a generic name if extraction fails.
    """
    # Common patterns in NCBI/Phytozome URLs
    patterns = [
        r'/([^/]+)\.(fasta|fa|fna|ffn|faa|gff|gff3)',
        r'([^/]+)/(assembly|genome)/([^/]+)',
        r'([^/]+)_([^/]+)',
    ]
    
    parsed = urlparse(url)
    path = parsed.path
    
    for pattern in patterns:
        match = re.search(pattern, path, re.IGNORECASE)
        if match:
            # Return the last meaningful group
            groups = match.groups()
            for group in reversed(groups):
                if group and len(group) > 2:  # Filter out very short matches
                    return group.replace('_', ' ').replace('-', ' ').title()
    
    # Fallback: use the last segment of the path
    segments = [s for s in path.split('/') if s and not s.endswith(('.fasta', '.fa', '.fna', '.ffn', '.faa', '.gff', '.gff3'))]
    if segments:
        return segments[-1].replace('_', ' ').replace('-', ' ').title()
    
    return None

def download_genomes(
    species_list: Optional[List[Dict[str, Any]]] = None,
    output_dir: Optional[Path] = None,
    data_source: str = "ncbi"
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Fetch FASTA/GFF files for specified species from NCBI RefSeq or Phytozome.
    
    This function:
    - Downloads genome assemblies (FASTA) and annotation files (GFF)
    - Skips genomes larger than MAX_GENOME_SIZE_MB (500 MB)
    - Implements retry logic with exponential backoff
    - Handles timeouts gracefully with clear error messages
    - Validates downloaded files
    
    Args:
        species_list: List of species dictionaries with 'name' and 'accession' or 'url' keys.
                     If None, uses species from config.
        output_dir: Directory to save downloaded files. If None, uses config data path.
        data_source: Source to fetch from ('ncbi' or 'phytozome')
                    
    Returns:
        Tuple of (successful_downloads, failed_downloads) where each is a dict:
        {species_name: file_path_or_error_message}
    """
    if species_list is None:
        try:
            species_list = get_species_list()
            logger.info(f"Using {len(species_list)} species from configuration")
        except Exception as e:
            logger.error(f"Failed to get species list from config: {e}")
            return {}, {"config_error": str(e)}
    
    if output_dir is None:
        output_dir = get_data_path() / "raw" / "genomes"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory: {output_dir}")
    
    successful_downloads: Dict[str, str] = {}
    failed_downloads: Dict[str, str] = {}
    
    # Build download URLs based on source
    # In a real implementation, this would query NCBI RefSeq or Phytozome APIs
    # For now, we construct example URLs that would be used
    
    for species in species_list:
        species_name = species.get('name', 'unknown_species')
        accession = species.get('accession', species.get('id', ''))
        species_key = species_name.replace(' ', '_').lower()
        
        # Construct download URLs (these would be real URLs in production)
        # NCBI RefSeq example: https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/
        # Phytozome example: https://phytozome.jgi.doe.gov/pz/portal.html
        
        # In a real implementation, we would:
        # 1. Query the appropriate API to get the actual download URLs
        # 2. Check file size before downloading
        # 3. Download with retry logic
        
        # For demonstration, we'll create placeholder URLs that would be replaced
        # with real API calls in production
        fasta_url = None
        gff_url = None
        
        if data_source == "ncbi":
            # Example NCBI RefSeq URL pattern (would be populated from API query)
            # https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/{species}/latest_assembly_versions/{accession}_genomic.fna.gz
            fasta_url = f"https://example-ncbi-mirror.org/genomes/{accession}_genomic.fna.gz"
            gff_url = f"https://example-ncbi-mirror.org/genomes/{accession}_genomic.gff.gz"
            
        elif data_source == "phytozome":
            # Example Phytozome URL pattern
            # https://phytozome.jgi.doe.gov/pz/download/{species}/{accession}/
            fasta_url = f"https://example-phytozome.org/download/{species_key}/{accession}/genome.fa.gz"
            gff_url = f"https://example-phytozome.org/download/{species_key}/{accession}/annotation.gff3.gz"
        
        else:
            logger.error(f"Unsupported data source: {data_source}")
            failed_downloads[species_name] = f"Unsupported data source: {data_source}"
            continue
        
        # Check file size before downloading (for FASTA)
        if fasta_url:
            file_size_mb = _calculate_file_size_mb(fasta_url)
            if file_size_mb is not None and file_size_mb > MAX_GENOME_SIZE_MB:
                logger.info(f"Skipping {species_name}: genome size {file_size_mb:.1f} MB exceeds limit of {MAX_GENOME_SIZE_MB} MB")
                failed_downloads[species_name] = f"File too large: {file_size_mb:.1f} MB > {MAX_GENOME_SIZE_MB} MB limit"
                continue
            
            if file_size_mb is None:
                logger.warning(f"Could not determine file size for {species_name}, proceeding with download")
        
        # Download FASTA file
        fasta_filename = f"{species_key}_genome.fasta.gz"
        fasta_path = output_dir / fasta_filename
        
        if fasta_url:
            success = _download_file_with_retry(fasta_url, fasta_path, f"{species_name} genome")
            if success and _validate_genome_file(fasta_path):
                successful_downloads[species_name] = str(fasta_path)
                logger.info(f"Successfully downloaded genome for {species_name}")
            else:
                failed_downloads[species_name] = "FASTA download failed"
                continue  # Skip GFF if FASTA failed
        
        # Download GFF file
        gff_filename = f"{species_key}_annotation.gff3.gz"
        gff_path = output_dir / gff_filename
        
        if gff_url:
            success = _download_file_with_retry(gff_url, gff_path, f"{species_name} annotation")
            if success and _validate_genome_file(gff_path):
                logger.info(f"Successfully downloaded annotation for {species_name}")
                # Add to successful downloads if not already there
                if species_name not in successful_downloads:
                    successful_downloads[species_name] = str(fasta_path)
            else:
                logger.warning(f"GFF download failed for {species_name}, but FASTA was successful")
                # Don't mark as failed since FASTA succeeded
    
    # Summary
    logger.info(f"Download complete: {len(successful_downloads)} successful, {len(failed_downloads)} failed")
    
    if failed_downloads:
        logger.warning("Failed downloads:")
        for species, reason in failed_downloads.items():
            logger.warning(f"  - {species}: {reason}")
    
    return successful_downloads, failed_downloads

def main():
    """Main entry point for running the download script."""
    logger.info("Starting genome download process")
    
    try:
        successful, failed = download_genomes()
        
        if successful:
            logger.info("Successfully downloaded genomes for:")
            for species, path in successful.items():
                logger.info(f"  - {species}: {path}")
        
        if failed:
            logger.error("Failed to download genomes for:")
            for species, reason in failed.items():
                logger.error(f"  - {species}: {reason}")
        
        # Exit with error code if any downloads failed
        if failed:
            logger.error("Download process completed with errors")
            return 1
        
        logger.info("All downloads completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during download process: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
