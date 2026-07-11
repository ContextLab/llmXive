"""
Download resistance gene reference data from the Comprehensive Antibiotic Resistance Database (CARD).

This module fetches the latest resistance gene sequences and metadata from CARD's 
programmatically accessible API to support mechanism-blind filtering and feature extraction.

Output: data/raw/card_reference_data.json (or .fasta depending on requirements)
"""
import os
import sys
import logging
import time
import json
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger
from utils.config import get_config_value, get_paths

# Constants
CARD_API_URL = "https://card.mcmaster.ca/api/data"
CARD_API_VERSION = "3.2.9"  # Latest stable version as of 2024
CARD_DOWNLOAD_URL = "https://card.mcmaster.ca/latest/data"
CARD_ARO_DATA_URL = "https://card.mcmaster.ca/api/3.2.9/aro.json"

logger = get_logger(__name__)

def fetch_card_metadata(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch resistance gene metadata from CARD API.
    
    Args:
        version: CARD version string (e.g., "3.2.9"). Uses latest if None.
        
    Returns:
        Dictionary containing resistance gene metadata including:
        - gene identifiers
        - resistance mechanisms
        - antibiotic classes
        - sequence data (if available)
        
    Raises:
        requests.RequestException: If API call fails
        ValueError: If response format is unexpected
    """
    if version is None:
        # Try to get latest version from config or use default
        version = get_config_value("card_version") or CARD_API_VERSION
        
    url = f"{CARD_ARO_DATA_URL}?version={version}"
    
    logger.info(f"Fetching CARD data from: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if "ARO" not in data:
            raise ValueError("Unexpected CARD API response format: missing 'ARO' key")
            
        logger.info(f"Successfully fetched {len(data['ARO'])} resistance gene entries")
        return data
        
    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching CARD data. API may be unreachable.")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching CARD data: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CARD API response as JSON: {e}")
        raise

def filter_resistance_genes(
    card_data: Dict[str, Any],
    antibiotic_classes: Optional[List[str]] = None,
    mechanisms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Filter CARD data based on antibiotic classes or resistance mechanisms.
    
    Args:
        card_data: Full CARD ARO data dictionary
        antibiotic_classes: List of antibiotic class names to filter by
        mechanisms: List of resistance mechanism types to filter by
        
    Returns:
        Filtered CARD data dictionary
    """
    if not card_data or "ARO" not in card_data:
        logger.warning("No valid CARD data provided for filtering")
        return card_data
        
    aro_entries = card_data["ARO"]
    filtered_entries = {}
    
    for entry_id, entry_data in aro_entries.items():
        # Extract relevant fields
        antibiotic_class = entry_data.get("antibiotic", [])
        mechanism = entry_data.get("resistance_mechanism", "")
        
        # Check if entry matches criteria
        match_class = (
            antibiotic_classes is None or 
            any(ac in antibiotic_class for ac in antibiotic_classes)
        )
        
        match_mechanism = (
            mechanisms is None or 
            mechanism in mechanisms
        )
        
        if match_class and match_mechanism:
            filtered_entries[entry_id] = entry_data
            
    logger.info(f"Filtered CARD data: {len(filtered_entries)} entries remain "
               f"(from {len(aro_entries)} total)")
               
    return {
        **card_data,
        "ARO": filtered_entries
    }

def extract_gene_sequences(card_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract nucleotide sequences from CARD data.
    
    Args:
        card_data: CARD ARO data dictionary
        
    Returns:
        Dictionary mapping gene IDs to nucleotide sequences
    """
    sequences = {}
    
    if "ARO" not in card_data:
        logger.warning("No ARO data found in CARD response")
        return sequences
        
    for entry_id, entry_data in card_data["ARO"].items():
        sequence = entry_data.get("sequence", "")
        if sequence:
            sequences[entry_id] = sequence
            
    logger.info(f"Extracted {len(sequences)} gene sequences from CARD data")
    return sequences

def save_card_data(
    card_data: Dict[str, Any],
    output_path: Path,
    include_sequences: bool = True
) -> None:
    """
    Save CARD data to a JSON file.
    
    Args:
        card_data: CARD data dictionary to save
        output_path: Path to output file
        include_sequences: Whether to include sequence data in output
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for serialization
    data_to_save = card_data.copy()
    
    if not include_sequences and "ARO" in data_to_save:
        # Remove sequence data to reduce file size
        for entry_id, entry_data in data_to_save["ARO"].items():
            if "sequence" in entry_data:
                del entry_data["sequence"]
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved CARD data to: {output_path}")
    except IOError as e:
        logger.error(f"Failed to save CARD data to {output_path}: {e}")
        raise

def download_card_fasta(output_path: Path) -> None:
    """
    Download CARD resistance gene sequences in FASTA format.
    
    This function fetches the CARD database in FASTA format for use with
    tools like ARIBA or BLAST.
    
    Args:
        output_path: Path where FASTA file will be saved
    """
    # CARD provides a direct FASTA download link
    fasta_url = "https://card.mcmaster.ca/latest/data"
    
    logger.info(f"Downloading CARD FASTA from: {fasta_url}")
    
    try:
        response = requests.get(fasta_url, timeout=120, stream=True)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        logger.info(f"Successfully downloaded CARD FASTA to: {output_path}")
        logger.info(f"File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download CARD FASTA: {e}")
        raise

def main() -> int:
    """
    Main entry point for CARD data download.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Load configuration
        paths = get_paths()
        raw_data_dir = paths.get("raw_data_dir", Path("data/raw"))
        
        # Determine output paths
        json_output = raw_data_dir / "card_reference_data.json"
        fasta_output = raw_data_dir / "card_reference_sequences.fasta"
        
        logger.info("Starting CARD resistance gene data download")
        
        # Fetch metadata and gene information
        card_data = fetch_card_metadata()
        
        # Optionally filter by antibiotic classes from config
        antibiotic_classes = get_config_value("target_antibiotic_classes")
        if antibiotic_classes:
            card_data = filter_resistance_genes(card_data, antibiotic_classes=antibiotic_classes)
        
        # Save JSON metadata
        save_card_data(card_data, json_output, include_sequences=True)
        
        # Download FASTA sequences (optional but recommended for ARIBA)
        if not fasta_output.exists():
            download_card_fasta(fasta_output)
        else:
            logger.info(f"FASTA file already exists at {fasta_output}, skipping download")
        
        logger.info("CARD data download completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Card data download failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
