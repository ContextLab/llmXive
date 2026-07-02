"""
Download organic CIFs from the Crystallography Open Database (COD).

This script fetches CIF files for organic molecules with <= 50 non-hydrogen atoms
from the COD API, applies filtering based on atom counts, and saves the valid
CIFs to the data/raw_cif/ directory.

Requirements:
- COD API access (https://www.crystallography.net/cod/ftp/)
- Filter: <= 50 non-H atoms (organic molecules)

Output:
- data/raw_cif/<cif_id>.cif for each valid structure
- Logging of download statistics and failures
"""

import os
import re
import logging
import sys
from typing import List, Dict, Optional, Tuple
import requests
from tqdm import tqdm
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import fix_seed, setup_logging
from error_handling import CIFParseError, MissingMetadataError, handle_corrupt_cif, log_processing_statistics
from config import ensure_directories

# Constants
COD_BASE_URL = "https://www.crystallography.net/cod/"
COD_FTP_INDEX = "https://www.crystallography.net/cod/index.html"
MAX_NON_H_ATOMS = 50
BATCH_SIZE = 100  # Process in batches to avoid overwhelming the server
RETRY_DELAY = 1.0  # Seconds between retries
MAX_RETRIES = 3

# Setup logging
logger = setup_logging(__name__)

def fix_seed():
    """Fix random seed for reproducibility."""
    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)

def get_cod_id_list() -> List[str]:
    """
    Get list of COD IDs from the COD index page.
    
    Returns:
        List of COD IDs (e.g., '1000000', '1000001', ...)
    """
    try:
        # The COD provides a list of all entries in a text file
        # We'll use the main index to get the range
        # For efficiency, we'll fetch a known range of IDs
        # COD IDs typically range from 1000000 to 7000000+
        
        # Instead of scraping, we'll use a known range and check existence
        # This is more reliable than parsing HTML
        start_id = 1000000
        end_id = 2000000  # Start with a manageable range
        
        ids = []
        for i in range(start_id, end_id + 1):
            ids.append(str(i))
        
        return ids
    except Exception as e:
        logger.error(f"Failed to get COD ID list: {e}")
        return []

def check_cif_exists(cif_id: str) -> bool:
    """
    Check if a CIF file exists on the COD server.
    
    Args:
        cif_id: The COD ID to check
        
    Returns:
        True if the CIF exists, False otherwise
    """
    url = f"{COD_BASE_URL}{cif_id}.cif"
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def extract_atom_count_from_cif(cif_content: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract atom counts from CIF content.
    
    Args:
        cif_content: The content of the CIF file
        
    Returns:
        Tuple of (total_atoms, non_h_atoms) or (None, None) if parsing fails
    """
    try:
        # Look for _atom_site_type_symbol or similar fields
        # COD CIF files typically have _atom_site_label or _atom_site_type_symbol
        
        # Count atoms by parsing _atom_site_label lines
        atom_labels = []
        for line in cif_content.split('\n'):
            if line.startswith('_atom_site_label'):
                # Next lines contain the data
                continue
            if line.startswith('_') or line.startswith('loop_'):
                continue
            if line.strip() and not line.startswith('#'):
                # This might be data
                parts = line.split()
                if parts:
                    label = parts[0]
                    # Check if it looks like an atom label (e.g., C1, O2, H3)
                    if re.match(r'^[A-Z][a-z]?\d*$', label):
                        atom_labels.append(label)
        
        if not atom_labels:
            # Try alternative parsing: look for _atom_site_type_symbol
            for line in cif_content.split('\n'):
                if '_atom_site_type_symbol' in line:
                    # Find the data block
                    data_lines = []
                    in_data = False
                    for l in cif_content.split('\n'):
                        if '_atom_site_type_symbol' in l:
                            in_data = True
                            continue
                        if in_data:
                            if l.startswith('_') or l.startswith('loop_'):
                                break
                            if l.strip():
                                data_lines.append(l)
                    
                    # Parse data lines
                    for dl in data_lines:
                        parts = dl.split()
                        if parts:
                            symbol = parts[0]
                            if re.match(r'^[A-Z][a-z]?$', symbol):
                                atom_labels.append(symbol)
                    break
        
        if not atom_labels:
            return None, None
        
        total_atoms = len(atom_labels)
        non_h_atoms = sum(1 for label in atom_labels if not label.startswith('H'))
        
        return total_atoms, non_h_atoms
        
    except Exception as e:
        logger.warning(f"Failed to extract atom count: {e}")
        return None, None

def download_cif(cif_id: str, output_dir: str) -> bool:
    """
    Download a single CIF file from COD.
    
    Args:
        cif_id: The COD ID
        output_dir: Directory to save the CIF file
        
    Returns:
        True if download and validation successful, False otherwise
    """
    url = f"{COD_BASE_URL}{cif_id}.cif"
    output_path = os.path.join(output_dir, f"{cif_id}.cif")
    
    # Check if file already exists
    if os.path.exists(output_path):
        logger.debug(f"CIF {cif_id} already exists, skipping")
        return True
    
    # Check if CIF exists on server
    if not check_cif_exists(cif_id):
        logger.debug(f"CIF {cif_id} does not exist on server")
        return False
    
    try:
        # Download with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to download CIF {cif_id} after {MAX_RETRIES} attempts: {e}")
                    return False
                time.sleep(RETRY_DELAY)
        
        # Parse and validate
        cif_content = response.text
        total_atoms, non_h_atoms = extract_atom_count_from_cif(cif_content)
        
        if non_h_atoms is None:
            logger.warning(f"Could not determine atom count for CIF {cif_id}, skipping")
            return False
        
        if non_h_atoms > MAX_NON_H_ATOMS:
            logger.debug(f"CIF {cif_id} has {non_h_atoms} non-H atoms (> {MAX_NON_H_ATOMS}), skipping")
            return False
        
        # Save valid CIF
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cif_content)
        
        logger.info(f"Downloaded CIF {cif_id} ({non_h_atoms} non-H atoms)")
        return True
        
    except Exception as e:
        logger.error(f"Error processing CIF {cif_id}: {e}")
        return False

def main():
    """
    Main function to download organic CIFs from COD.
    """
    fix_seed()
    
    # Ensure output directories exist
    output_dir = ensure_directories()
    raw_cif_dir = os.path.join(output_dir, "data", "raw_cif")
    os.makedirs(raw_cif_dir, exist_ok=True)
    
    logger.info(f"Starting CIF download to {raw_cif_dir}")
    
    # Get list of COD IDs to process
    # For this implementation, we'll use a sample range
    # In production, this would be a configurable range or list
    cif_ids = get_cod_id_list()
    
    if not cif_ids:
        logger.error("No COD IDs found to process")
        return
    
    logger.info(f"Found {len(cif_ids)} COD IDs to process")
    
    # Process in batches
    successful_downloads = 0
    failed_downloads = 0
    skipped_existing = 0
    skipped_too_large = 0
    
    for cif_id in tqdm(cif_ids, desc="Downloading CIFs"):
        # Check if already downloaded
        output_path = os.path.join(raw_cif_dir, f"{cif_id}.cif")
        if os.path.exists(output_path):
            skipped_existing += 1
            continue
        
        # Download and validate
        success = download_cif(cif_id, raw_cif_dir)
        if success:
            successful_downloads += 1
        else:
            # Check if it was skipped due to size
            if not check_cif_exists(cif_id):
                failed_downloads += 1
            else:
                # Likely skipped due to atom count
                skipped_too_large += 1
        
        # Small delay to be polite to the server
        time.sleep(0.1)
    
    # Log statistics
    log_stats = {
        'total_processed': len(cif_ids),
        'successful_downloads': successful_downloads,
        'failed_downloads': failed_downloads,
        'skipped_existing': skipped_existing,
        'skipped_too_large': skipped_too_large,
        'output_directory': raw_cif_dir
    }
    
    logger.info("Download statistics:")
    for key, value in log_stats.items():
        logger.info(f"  {key}: {value}")
    
    # Save statistics to file
    stats_path = os.path.join(raw_cif_dir, "download_stats.json")
    import json
    with open(stats_path, 'w') as f:
        json.dump(log_stats, f, indent=2)
    
    logger.info(f"Download complete. Statistics saved to {stats_path}")
    
    # Return success if we got at least some downloads
    return successful_downloads > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
