import os
import logging
import json
import time
import csv
import io
from pathlib import Path
from typing import Dict, List, Any, Optional

class DataLoadingError(Exception):
    """Custom exception for data loading errors."""
    pass

def fetch_string_network(organism_id: str, confidence_threshold: int) -> Dict[str, Any]:
    """Fetches PPI network from STRING API."""
    url = f"https://string-db.org/api/json/network?species={organism_id}&confidence={confidence_threshold}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        raise DataLoadingError(f"Failed to fetch STRING network for {organism_id}: {e}")

def load_local_network(filepath: Path) -> Dict[str, Any]:
    """Loads PPI network from a local file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise DataLoadingError(f"Network file not found: {filepath}")
    except json.JSONDecodeError:
        raise DataLoadingError(f"Invalid JSON format in network file: {filepath}")

def fetch_essentiality_labels(organism_id: str) -> Dict[str, bool]:
    """Fetches gene essentiality labels from the DEG database."""
    # Attempt primary FTP URL
    ftp_url = f"ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/{organism_id}.txt"
    try:
        with io.BytesIO() as buffer:
            with requests.get(ftp_url, stream=True, timeout=10) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024):
                    buffer.write(chunk)
            buffer.seek(0)
            reader = csv.reader(io.TextIOWrapper(buffer, encoding='utf-8'), delimiter='\t')
            labels = {row[0]: bool(row[1]) for row in reader if len(row) > 1}
            return labels
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to fetch from FTP for {organism_id}: {e}. Trying API...")
        # Attempt official DEG API endpoint
        api_url = f"https://www.essentialgene.org/api/v1/organism/{organism_id}/genes"  # Replace with actual API endpoint if available
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            labels = {gene['gene_id']: gene['is_essential'] for gene in data}
            return labels
        except requests.exceptions.RequestException as e:
            raise DataLoadingError(f"Failed to fetch from API for {organism_id}: {e}")

def load_local_essentiality(filepath: Path) -> Dict[str, bool]:
    """Loads essentiality labels from a local file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise DataLoadingError(f"Essentiality file not found: {filepath}")
    except json.JSONDecodeError:
        raise DataLoadingError(f"Invalid JSON format in essentiality file: {filepath}")

def map_ids(ppi_network: Dict[str, Any], essentiality_labels: Dict[str, bool]) -> Dict[str, Any]:
    """Maps gene identifiers between PPI network and essentiality labels."""
    mapped_network = {}
    mapped_nodes = 0
    for node1, neighbors in ppi_network['nodes'].items():
        if node1 in essentiality_labels:
            mapped_network[node1] = {}
            mapped_nodes += 1
            for node2, weight in neighbors.items():
                if node2 in essentiality_labels:
                    mapped_network[node1][node2] = weight
    logging.info(f"Number of mapped nodes: {mapped_nodes}/{len(ppi_network['nodes'])}")
    return mapped_network

def load_essentiality_for_all_organisms(organisms: List[str]) -> Dict[str, Dict[str, bool]]:
    """Loads essentiality data for all organisms."""
    all_essentiality = {}
    for organism_id in organisms:
        try:
            essentiality = fetch_essentiality_labels(organism_id)
            all_essentiality[organism_id] = essentiality
        except DataLoadingError as e:
            logging.warning(f"Failed to load essentiality for {organism_id}: {e}")
    return all_essentiality

def save_essentiality_data(essentiality_data: Dict[str, Dict[str, bool]], output_path: Path) -> None:
    """Saves essentiality data to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(essentiality_data, f, indent=4)

def verify_deg_streaming_capability() -> bool:
    """
    Verifies the streaming capability of the DEG FTP dataset.
    
    Streams the first 10MB of the DEG FTP dataset.
    If the stream fails or returns fewer than 1000 lines, logs a CRITICAL warning
    and returns False to halt execution.
    
    Returns:
        bool: True if streaming verification passed, False otherwise.
    """
    import requests
    
    # Using a representative organism ID for the check. 
    # The task requires verifying the STREAMING capability of the source.
    # We use '9606' (Human) as a standard large dataset representative.
    organism_id = '9606'
    ftp_url = f"ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/{organism_id}.txt"
    
    logging.info(f"Starting DEG streaming verification for {organism_id} at {ftp_url}")
    
    try:
        # Stream the data
        with requests.get(ftp_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            
            line_count = 0
            bytes_read = 0
            max_bytes = 10 * 1024 * 1024  # 10MB
            
            # Iterate through chunks
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                
                bytes_read += len(chunk)
                
                # Process line by line within the chunk buffer
                # We need to handle partial lines across chunks
                # For simplicity in verification, we count newlines in the accumulated buffer
                # but stop once we hit the byte limit.
                
                if bytes_read >= max_bytes:
                    break
                
                # Count newlines in the current chunk to estimate lines
                # Note: This is an approximation if chunk boundaries split lines,
                # but sufficient for a "1000 lines" threshold check on a 10MB stream.
                line_count += chunk.count(b'\n')
            
            logging.info(f"Streamed {bytes_read} bytes, approx {line_count} lines.")
            
            if line_count < 1000:
                logging.critical("DEG data stream failed; verify FTP access. Returned fewer than 1000 lines.")
                return False
            
            logging.info("DEG data streaming verification PASSED.")
            return True

    except requests.exceptions.RequestException as e:
        logging.critical(f"DEG data stream failed; verify FTP access. Error: {e}")
        return False
    except Exception as e:
        logging.critical(f"Unexpected error during DEG streaming verification: {e}")
        return False

def main():
    """Entry point for T091 verification script."""
    setup_logging()
    logging.info("Running T091: Verify DEG Data Streaming Capability")
    
    success = verify_deg_streaming_capability()
    
    if not success:
        logging.critical("T091 Verification FAILED. Halting execution.")
        exit(1)
    else:
        logging.info("T091 Verification PASSED.")
        exit(0)

# Import setup_logging from utils as it is used in main
from utils import setup_logging