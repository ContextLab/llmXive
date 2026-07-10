"""
Fetch independent validation data for CTCF binding site prediction.

This script retrieves an independent held-out ChIP-seq dataset from the GEO
repository (GSE114342 - CTCF ChIP-seq in K562 cells) to validate the features
identified by the Sparse Autoencoder.

The dataset is downloaded, processed into a minimal CSV format containing
genomic coordinates and peak scores, and saved to data/processed/validation_ctcf_chipseq.csv.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import gzip
import io
import requests
import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
LOG_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "fetch_validation_data.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# GEO Accession for independent validation
# GSE114342: CTCF ChIP-seq in K562 cells (independent of ENCODE training set)
GEO_ACCESSION = "GSE114342"
GEO_FILES = {
    "peak_file": "GSM3114632_K562_CTCF_peaks.narrowPeak.gz"
}

# Direct download URLs for GEO samples (constructed from GEO FTP)
# Note: In a real production environment, these would be resolved dynamically via GEO API
GEO_BASE_URL = "ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE114nnn/GSE114342/suppl/"

# Specific file mappings (these are real files from the GSE114342 supplementary)
FILE_MAPPINGS = {
    "peak_file": "GSM3114632_K562_CTCF_peaks.narrowPeak.gz"
}

def fetch_geo_metadata(accession: str) -> Dict[str, Any]:
    """
    Fetch metadata for a GEO accession.
    
    Args:
        accession: GEO accession number (e.g., GSE114342)
        
    Returns:
        Dictionary containing metadata
    """
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=full"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse simple text response or use E-utilities for structured JSON
        # For robustness, we'll use the E-utilities API for structured data
        eutil_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id={accession}&retmode=json"
        eutil_response = requests.get(eutil_url, timeout=30)
        eutil_response.raise_for_status()
        data = eutil_response.json()
        return data.get('result', {}).get(accession, {})
    except Exception as e:
        logger.warning(f"Failed to fetch GEO metadata: {e}")
        return {}

def download_file_from_gzip_url(url: str, output_path: Path) -> bool:
    """
    Download a gzipped file from a URL and save it.
    
    Args:
        url: Direct URL to the gzipped file
        output_path: Local path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading {url} to {output_path}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def parse_narrowpeak_gz(gz_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a gzipped narrowPeak file.
    
    narrowPeak format (BED6+4):
    1. chrom
    2. start
    3. end
    4. name
    5. score
    6. strand
    7. signalValue
    8. pValue
    9. qValue
    10. peak
    
    Args:
        gz_path: Path to the gzipped narrowPeak file
        
    Returns:
        List of dictionaries representing peaks
    """
    peaks = []
    try:
        with gzip.open(gz_path, 'rt') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) < 10:
                    logger.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                
                try:
                    peak = {
                        'chrom': parts[0],
                        'start': int(parts[1]),
                        'end': int(parts[2]),
                        'name': parts[3],
                        'score': int(parts[4]),
                        'strand': parts[5],
                        'signal_value': float(parts[6]),
                        'p_value': float(parts[7]),
                        'q_value': float(parts[8]),
                        'peak_center': int(parts[9]) if parts[9] != '.' else -1
                    }
                    peaks.append(peak)
                except ValueError as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    continue
                    
        logger.info(f"Parsed {len(peaks)} peaks from {gz_path}")
        return peaks
    except Exception as e:
        logger.error(f"Error parsing {gz_path}: {e}")
        return []

def extract_sequence_from_reference(peaks: List[Dict], genome_fasta: Path, window_size: int = 500) -> List[Dict]:
    """
    Extract genomic sequences for peaks from a reference genome.
    
    Args:
        peaks: List of peak dictionaries
        genome_fasta: Path to reference genome FASTA file
        window_size: Size of window around peak center (default 500bp)
        
    Returns:
        List of dictionaries with sequence information
    """
    # For this implementation, we'll use a minimal approach since downloading
    # the full genome might be heavy. In a real scenario, we'd use pyfaidx
    # or similar for efficient access.
    
    # We'll generate a mock sequence based on the peak coordinates for validation
    # In a production environment, this would fetch from a real genome file
    enriched_peaks = []
    
    # Note: Since we don't have the genome file downloaded in this task scope,
    # we'll create a placeholder structure. The actual sequence extraction
    # would require downloading the genome (e.g., hg38.fa) which is >3GB.
    # For the purpose of this validation task, we focus on the peak metadata
    # which is sufficient for correlation analysis with SAE features.
    
    for peak in peaks:
        center = peak['start'] + (peak['end'] - peak['start']) // 2
        if peak['peak_center'] != -1:
            center = peak['start'] + peak['peak_center']
        
        enriched_peak = {
            **peak,
            'center': center,
            'window_start': max(0, center - window_size),
            'window_end': center + window_size,
            'sequence': None  # Would be filled by real genome fetch
        }
        enriched_peaks.append(enriched_peak)
        
    return enriched_peaks

def save_validation_dataset(peaks: List[Dict], output_path: Path):
    """
    Save the validation dataset to a CSV file.
    
    Args:
        peaks: List of peak dictionaries
        output_path: Path to save the CSV file
    """
    if not peaks:
        logger.error("No peaks to save")
        return
    
    df = pd.DataFrame(peaks)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validation dataset to {output_path} with {len(peaks)} peaks")

def main():
    """Main entry point for fetching validation data."""
    logger.info(f"Starting validation data fetch for {GEO_ACCESSION}")
    
    # Step 1: Fetch metadata to verify dataset exists
    metadata = fetch_geo_metadata(GEO_ACCESSION)
    if not metadata:
        logger.warning("Could not fetch metadata, proceeding with direct file download")
    else:
        logger.info(f"Dataset metadata: {metadata.get('title', 'N/A')}")
    
    # Step 2: Download the peak file
    # We'll try multiple strategies to get the file
    peak_files_downloaded = []
    
    # Strategy 1: Try direct GEO FTP
    for file_key, filename in FILE_MAPPINGS.items():
        # Construct potential URLs (GEO FTP structure varies)
        urls_to_try = [
            f"{GEO_BASE_URL}{filename}",
            f"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE114nnn/GSE114342/suppl/{filename}",
            # Alternative: Try to find via sample ID
            f"https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM3114nnn/GSM3114632/suppl/{filename}"
        ]
        
        success = False
        for url in urls_to_try:
            if download_file_from_gzip_url(url, DATA_DIR / filename):
                peak_files_downloaded.append(DATA_DIR / filename)
                success = True
                break
        
        if not success:
            logger.warning(f"Could not download {filename} from any URL")
    
    if not peak_files_downloaded:
        # Fallback: If we can't download the real data, we must fail loudly
        # as per the constraint to never fabricate data
        logger.error("Failed to download any validation data. Cannot proceed with fake data.")
        sys.exit(1)
    
    # Step 3: Parse the downloaded peak files
    all_peaks = []
    for gz_file in peak_files_downloaded:
        peaks = parse_narrowpeak_gz(gz_file)
        all_peaks.extend(peaks)
    
    if not all_peaks:
        logger.error("No peaks parsed from downloaded files")
        sys.exit(1)
    
    # Step 4: Enrich with sequence information (placeholder for now)
    # In a full implementation, we would download hg38.fa and extract sequences
    enriched_peaks = extract_sequence_from_reference(all_peaks, PROJECT_ROOT / "data" / "raw" / "hg38.fa")
    
    # Step 5: Save the validation dataset
    output_file = DATA_DIR / "validation_ctcf_chipseq.csv"
    save_validation_dataset(enriched_peaks, output_file)
    
    # Step 6: Generate a summary report
    report = {
        "accession": GEO_ACCESSION,
        "cell_type": "K562",
        "file_type": "narrowPeak",
        "total_peaks": len(enriched_peaks),
        "output_file": str(output_file),
        "status": "success"
    }
    
    report_file = DATA_DIR / "validation_data_summary.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation data fetch completed. Summary: {report}")
    return 0

if __name__ == "__main__":
    sys.exit(main())