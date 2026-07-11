"""
ENCODE Data Download and Processing Module.

Implements FR-001: Fetch real paired RNA-seq and DNase-seq/ATAC-seq count data
for human cell lines from the ENCODE portal.
"""
import os
import sys
import time
import logging
import json
import csv
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/download_encode.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ENCODE_BASE_URL = "https://www.encodeproject.org"
ENCODE_API_URL = f"{ENCODE_BASE_URL}/search/?format=json"
CELL_LINES = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
OUTPUT_COUNTS = "data/raw/encode_counts.csv"
OUTPUT_PEAKS = "data/raw/encode_peaks.bed"
OUTPUT_CHECKSUMS = "logs/checksums.txt"

def setup_directories():
    """Ensure required output directories exist."""
    dirs = ["data/raw", "logs"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Directory ensured: {d}")

def get_session_with_retry():
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_encode_metadata(cell_line: str, assay_type: str) -> List[Dict[str, Any]]:
    """
    Fetch metadata for a specific cell line and assay type from ENCODE.

    Args:
        cell_line: Cell line name (e.g., "GM12878")
        assay_type: Assay type (e.g., "rna-seq", "dnase-seq", "atac-seq")

    Returns:
        List of experiment metadata dictionaries.
    """
    params = {
        "type": "Experiment",
        "assay_term_name": assay_type,
        "organism.name": "Human",
        "biosample.term_name": cell_line,
        "status": "released",
        "limit": "100"
    }

    session = get_session_with_retry()
    url = f"{ENCODE_API_URL}&{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    logger.info(f"Fetching metadata for {cell_line} {assay_type}...")
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        logger.info(f"Found {len(items)} experiments for {cell_line} {assay_type}")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata for {cell_line} {assay_type}: {e}")
        return []

def find_download_uri(experiment: Dict[str, Any], file_type: str) -> Optional[str]:
    """
    Find the download URI for a specific file type in an experiment.

    Args:
        experiment: Experiment metadata dictionary.
        file_type: Desired file type (e.g., "counts", "bed").

    Returns:
        Download URI or None if not found.
    """
    for file_obj in experiment.get("files", []):
        if file_obj.get("file_type") == file_type and file_obj.get("status") == "available":
            if "download_uri" in file_obj:
                return file_obj["download_uri"]
            # Construct URI if not present
            accession = file_obj.get("accession", "")
            return f"{ENCODE_BASE_URL}{file_obj.get('@id', '')}"
    return None

def download_file(uri: str, output_path: str, expected_rows: int = None) -> bool:
    """
    Download a file from ENCODE to the specified path.

    Args:
        uri: Download URI.
        output_path: Local path to save the file.
        expected_rows: Optional expected row count for validation.

    Returns:
        True if download successful, False otherwise.
    """
    session = get_session_with_retry()
    logger.info(f"Downloading from {uri} to {output_path}...")
    
    try:
        # Handle relative URIs
        if not uri.startswith("http"):
            uri = f"{ENCODE_BASE_URL}{uri}"
        
        response = session.get(uri, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded: {output_path} ({os.path.getsize(output_path)} bytes)")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def process_rna_data(experiments: List[Dict[str, Any]], cell_line: str) -> Tuple[List[List[str]], List[str]]:
    """
    Process RNA-seq data: download counts and prepare matrix.

    Args:
        experiments: List of experiment metadata.
        cell_line: Cell line name.

    Returns:
        Tuple of (data_rows, headers)
    """
    rows = []
    headers = ["gene_id", "gene_name", "chrom", "start", "end", "strand", "cell_line", "counts"]
    
    # Try to find a counts file
    for exp in experiments:
        uri = find_download_uri(exp, "counts")
        if uri:
            temp_path = f"temp_{cell_line}_counts.tsv"
            if download_file(uri, temp_path):
                # Parse TSV counts file
                try:
                    with open(temp_path, 'r') as f:
                        reader = csv.reader(f, delimiter='\t')
                        header = next(reader, None)
                        # Assume standard ENCODE format: gene_id, gene_name, chr, start, end, strand, count
                        for row in reader:
                            if len(row) >= 7:
                                gene_id = row[0]
                                gene_name = row[1]
                                chrom = row[2]
                                start = row[3]
                                end = row[4]
                                strand = row[5]
                                count = row[6]
                                rows.append([gene_id, gene_name, chrom, start, end, strand, cell_line, count])
                    os.remove(temp_path)
                    break
                except Exception as e:
                    logger.error(f"Error parsing counts file for {cell_line}: {e}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    return rows, headers

def process_accessibility_data(experiments: List[Dict[str, Any]], cell_line: str) -> Tuple[List[List[str]], List[str]]:
    """
    Process DNase/ATAC-seq data: download peak files and prepare BED.

    Args:
        experiments: List of experiment metadata.
        cell_line: Cell line name.

    Returns:
        Tuple of (data_rows, headers)
    """
    rows = []
    headers = ["chrom", "start", "end", "peak_id", "cell_line", "score"]
    
    # Try to find a bed file
    for exp in experiments:
        # Try multiple file types
        for ftype in ["bed", "narrowPeak", "broadPeak"]:
            uri = find_download_uri(exp, ftype)
            if uri:
                temp_path = f"temp_{cell_line}_peaks.bed"
                if download_file(uri, temp_path):
                    try:
                        with open(temp_path, 'r') as f:
                            for idx, line in enumerate(f):
                                parts = line.strip().split('\t')
                                if len(parts) >= 3:
                                    chrom = parts[0]
                                    start = parts[1]
                                    end = parts[2]
                                    peak_id = f"{cell_line}_peak_{idx}"
                                    score = parts[4] if len(parts) > 4 else "0"
                                    rows.append([chrom, start, end, peak_id, cell_line, score])
                        os.remove(temp_path)
                        break
                    except Exception as e:
                        logger.error(f"Error parsing peaks file for {cell_line}: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
    
    return rows, headers

def write_counts_csv(all_data: List[List[str]], headers: List[str], output_path: str):
    """Write RNA-seq counts to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_data)
    logger.info(f"Wrote counts to {output_path}")

def write_peaks_bed(all_data: List[List[str]], headers: List[str], output_path: str):
    """Write peaks to BED file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Write only the first 3 columns for BED format compliance, plus optional metadata
        for row in all_data:
            f.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[5]}\n")
    logger.info(f"Wrote peaks to {output_path}")

def log_checksums(file_paths: List[str], checksum_log: str):
    """Calculate and log checksums for output files."""
    with open(checksum_log, 'a') as log_file:
        for path in file_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    content = f.read()
                    checksum = hashlib.sha256(content).hexdigest()
                    log_file.write(f"{path}: {checksum}\n")
                    logger.info(f"Checksum for {path}: {checksum}")
            else:
                logger.warning(f"File not found for checksum: {path}")

def main():
    """Main entry point for ENCODE data download."""
    logger.info("Starting ENCODE data download for FR-001")
    setup_directories()

    all_counts_data = []
    all_counts_headers = None
    all_peaks_data = []
    all_peaks_headers = None

    # Process each cell line
    for cell_line in CELL_LINES:
        logger.info(f"Processing cell line: {cell_line}")
        
        # Fetch RNA-seq data
        rna_experiments = fetch_encode_metadata(cell_line, "rna-seq")
        if rna_experiments:
            data, headers = process_rna_data(rna_experiments, cell_line)
            all_counts_data.extend(data)
            if all_counts_headers is None:
                all_counts_headers = headers
        
        # Fetch DNase/ATAC-seq data
        dnase_experiments = fetch_encode_metadata(cell_line, "dnase-seq")
        atac_experiments = fetch_encode_metadata(cell_line, "atac-seq")
        
        exps = dnase_experiments + atac_experiments
        if exps:
            data, headers = process_accessibility_data(exps, cell_line)
            all_peaks_data.extend(data)
            if all_peaks_headers is None:
                all_peaks_headers = headers

    # Write outputs
    if all_counts_data and all_counts_headers:
        write_counts_csv(all_counts_data, all_counts_headers, OUTPUT_COUNTS)
    else:
        logger.warning("No RNA-seq data collected")

    if all_peaks_data and all_peaks_headers:
        write_peaks_bed(all_peaks_data, all_peaks_headers, OUTPUT_PEAKS)
    else:
        logger.warning("No accessibility data collected")

    # Log checksums
    output_files = []
    if os.path.exists(OUTPUT_COUNTS):
        output_files.append(OUTPUT_COUNTS)
    if os.path.exists(OUTPUT_PEAKS):
        output_files.append(OUTPUT_PEAKS)
    
    if output_files:
        log_checksums(output_files, OUTPUT_CHECKSUMS)
    
    logger.info("ENCODE data download completed")

if __name__ == "__main__":
    main()