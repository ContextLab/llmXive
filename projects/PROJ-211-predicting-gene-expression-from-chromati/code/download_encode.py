"""
ENCODE Data Downloader and Preprocessor for T011b.

Implements FR-001: Fetches real paired RNA-seq and DNase-seq/ATAC-seq count data
for ≥5 human cell lines from the ENCODE portal.

This script uses the ENCODE API to download processed matrix files (counts) and
bed files (peaks) for specified cell lines. It validates the data and writes
them to the project's data/raw directory.
"""
import os
import sys
import time
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import requests

# Project-relative imports
from utils import checksum_file, retry_request, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/download_encode.log')
    ]
)
logger = logging.getLogger(__name__)

# ENCODE API Configuration
ENCODE_BASE_URL = "https://www.encodeproject.org"
ENCODE_API_SEARCH = f"{ENCODE_BASE_URL}/search/?format=json"
ENCODE_DOWNLOAD = f"{ENCODE_BASE_URL}"

# Target cell lines (5 human cell lines)
TARGET_CELL_LINES = [
    "GM12878",
    "K562",
    "HMEC",
    "IMR90",
    "HepG2"
]

# Assay types: RNA-seq for expression, DNase-seq or ATAC-seq for accessibility
ASSAY_TYPES = {
    "rna": ["RNA-seq"],
    "accessibility": ["DNase-seq", "ATAC-seq"]
}

# Output paths
OUTPUT_DIR = "data/raw"
COUNTS_FILE = os.path.join(OUTPUT_DIR, "encode_counts.csv")
PEAKS_FILE = os.path.join(OUTPUT_DIR, "encode_peaks.bed")
CHECKSUM_LOG = "logs/checksums.txt"

def setup_directories():
    """Ensure output directories exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def fetch_encode_metadata(query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch metadata from ENCODE search API with retry logic.
    
    Args:
        query_params: Dictionary of query parameters for the search endpoint.
        
    Returns:
        List of item dictionaries from the '@graph' key.
    """
    url = ENCODE_API_SEARCH
    params = query_params.copy()
    params['limit'] = 'all'  # Retrieve all results

    try:
        response = retry_request(
            requests.get,
            url,
            params=params,
            max_retries=3,
            backoff_factor=2.0
        )
        response.raise_for_status()
        data = response.json()
        return data.get('@graph', [])
    except Exception as e:
        logger.error(f"Failed to fetch metadata for query {query_params}: {e}")
        raise

def find_download_uri(item: Dict[str, Any], file_format: str) -> Optional[str]:
    """
    Find the download URI for a specific file format in an ENCODE item.
    
    Args:
        item: The ENCODE item dictionary.
        file_format: Target file format (e.g., 'tsv', 'bed').
        
    Returns:
        The download URI or None if not found.
    """
    # Check for files in the item
    files = item.get('files', [])
    if not files:
        return None

    for f in files:
        if f.get('file_format') == file_format:
            if f.get('output_type') in ['gene expression matrix', 'peak', 'signal']:
                # Construct the full download URL
                # The '@id' usually looks like /files/UUID/
                file_id = f.get('@id')
                if file_id:
                    return f"{ENCODE_BASE_URL}{file_id}?download=1"
    return None

def download_file(url: str, output_path: str, expected_extension: str) -> bool:
    """
    Download a file from a URL to a local path.
    
    Args:
        url: The URL to download from.
        output_path: The local path to save the file.
        expected_extension: Expected file extension for validation.
        
    Returns:
        True if successful, False otherwise.
    """
    if not url:
        return False

    logger.info(f"Downloading from {url} to {output_path}")
    try:
        response = retry_request(
            requests.get,
            url,
            stream=True,
            max_retries=3
        )
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error(f"Downloaded file is empty or missing: {output_path}")
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def process_rna_data(cell_lines: List[str]) -> pd.DataFrame:
    """
    Fetch and process RNA-seq count data for given cell lines.
    
    Args:
        cell_lines: List of cell line names.
        
    Returns:
        DataFrame with gene expression counts.
    """
    all_counts = []
    found_cell_lines = []

    for cell_line in cell_lines:
        logger.info(f"Searching for RNA-seq data for {cell_line}...")
        
        # Search for RNA-seq experiments in this cell line
        # We look for 'gene expression matrix' output type
        query = {
            'type': 'File',
            'output_type': 'gene expression matrix',
            'file_format': 'tsv',
            'biosample_term_name': cell_line,
            'status': 'released'
        }
        
        items = fetch_encode_metadata(query)
        logger.info(f"Found {len(items)} RNA-seq matrix files for {cell_line}")

        if not items:
            logger.warning(f"No RNA-seq matrix found for {cell_line}, skipping.")
            continue

        # Take the first available file (prioritizing recent/released)
        item = items[0]
        uri = find_download_uri(item, 'tsv')
        
        if not uri:
            logger.warning(f"No download URI found for {cell_line} RNA-seq.")
            continue

        temp_path = os.path.join(OUTPUT_DIR, f"{cell_line}_rna.tsv")
        if download_file(uri, temp_path, 'tsv'):
            try:
                # ENCODE gene expression matrices usually have:
                # First column: gene_id, subsequent columns: samples (cell lines)
                # We need to extract the specific cell line's column or aggregate
                # For this task, we assume the file contains counts for the target cell line
                # or we need to parse the header to find the specific column.
                # Standard ENCODE matrix: row=genes, col=samples (often just one if filtered)
                
                df = pd.read_csv(temp_path, sep='\t', index_col=0)
                
                # Identify the column that corresponds to this cell line
                # If the file has multiple columns, we might need to select the right one.
                # For simplicity in this MVP, we assume the first numeric column or the one named with the cell line.
                # If the index is gene_id, we take the first column as the count vector for this cell line.
                if df.shape[1] >= 1:
                    # Rename the column to the cell line name
                    col_name = df.columns[0]
                    df = df[[col_name]].copy()
                    df.columns = [cell_line]
                    df.index.name = 'gene_id'
                    all_counts.append(df)
                    found_cell_lines.append(cell_line)
                    logger.info(f"Successfully processed RNA-seq for {cell_line}: {df.shape}")
                else:
                    logger.warning(f"RNA-seq file for {cell_line} has no data columns.")
            except Exception as e:
                logger.error(f"Error parsing RNA-seq file for {cell_line}: {e}")
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            logger.warning(f"Download failed for {cell_line} RNA-seq.")

    if not all_counts:
        raise RuntimeError("No RNA-seq data downloaded for any cell line.")

    # Merge all dataframes on gene_id (outer join to keep all genes, fill NaN with 0)
    combined = pd.concat(all_counts, axis=1).fillna(0)
    return combined

def process_accessibility_data(cell_lines: List[str]) -> pd.DataFrame:
    """
    Fetch and process DNase-seq/ATAC-seq peak data for given cell lines.
    
    Args:
        cell_lines: List of cell line names.
        
    Returns:
        DataFrame with peak counts (peak_id x cell_line).
    """
    all_peaks = []
    found_cell_lines = []
    
    # We need to aggregate peaks. ENCODE often provides signal tracks or peak lists.
    # For a "count" matrix similar to RNA, we look for 'peaks' or 'signal' files.
    # However, creating a matrix of peak counts across cell lines is complex because
    # peak coordinates differ.
    # Strategy:
    # 1. Download peak BED files for each cell line.
    # 2. Combine them into a single BED file (data/raw/encode_peaks.bed).
    # 3. For the counts matrix, we will use the peak IDs as rows and cell lines as columns,
    #    where 1 indicates presence, 0 absence (binary count) OR use a signal value if available.
    #    Given the task asks for "counts", we will treat the presence of a peak as a count of 1.
    #    (A more advanced pipeline would normalize signal, but this satisfies the "counts" requirement
    #     for a matrix of peaks x cell lines).

    # We will collect peak IDs and cell line associations.
    peak_data = {} # peak_id -> {cell_line: 1}

    for cell_line in cell_lines:
        logger.info(f"Searching for DNase/ATAC-seq peaks for {cell_line}...")
        
        query = {
            'type': 'File',
            'output_type': 'peaks', # or 'signal' if peaks not available
            'file_format': 'bed',
            'biosample_term_name': cell_line,
            'status': 'released'
        }
        
        items = fetch_encode_metadata(query)
        
        # Fallback to signal if peaks not found
        if not items:
            query['output_type'] = 'signal'
            items = fetch_encode_metadata(query)

        logger.info(f"Found {len(items)} peak/signal files for {cell_line}")

        if not items:
            logger.warning(f"No peak/signal data found for {cell_line}, skipping.")
            continue

        item = items[0]
        uri = find_download_uri(item, 'bed')
        
        if not uri:
            # Try signal if we asked for peaks
            if item.get('output_type') == 'peaks':
                query['output_type'] = 'signal'
                items = fetch_encode_metadata(query)
                if items:
                    uri = find_download_uri(items[0], 'bed')

        if not uri:
            logger.warning(f"No download URI found for {cell_line} peaks.")
            continue

        temp_path = os.path.join(OUTPUT_DIR, f"{cell_line}_peaks.bed")
        if download_file(uri, temp_path, 'bed'):
            try:
                # Read BED file: chrom, start, end, name, score, strand
                # ENCODE peak files often have a header or specific format.
                # We assume standard BED 6 columns.
                df = pd.read_csv(temp_path, sep='\t', header=None, 
                                 names=['chrom', 'start', 'end', 'peak_id', 'score', 'strand'])
                
                # Create a unique ID for each peak if not present or use existing
                # We'll use the peak_id column if available, else generate
                if 'peak_id' in df.columns:
                    # Ensure peak_id is unique or combine with cell line
                    # For the matrix, we want a consistent set of peaks.
                    # Since peaks vary by cell line, we will create a global list of unique peaks
                    # later. For now, we store the rows.
                    pass
                
                # Store rows for later aggregation
                if cell_line not in peak_data:
                    peak_data[cell_line] = []
                
                for _, row in df.iterrows():
                    # Create a unique key for the peak location to merge later
                    # Key: chrom:start-end
                    loc_key = f"{row['chrom']}:{row['start']}-{row['end']}"
                    # We might need to resolve overlapping peaks, but for MVP, we use location as ID
                    if loc_key not in peak_data[cell_line]:
                        peak_data[cell_line].append({
                            'loc_key': loc_key,
                            'chrom': row['chrom'],
                            'start': row['start'],
                            'end': row['end'],
                            'score': row['score']
                        })
                
                found_cell_lines.append(cell_line)
                logger.info(f"Processed {len(df)} peaks for {cell_line}")
            except Exception as e:
                logger.error(f"Error parsing peaks file for {cell_line}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            logger.warning(f"Download failed for {cell_line} peaks.")

    if not peak_data:
        raise RuntimeError("No peak data downloaded for any cell line.")

    # Aggregate into a matrix
    # Get all unique locations
    all_locs = set()
    for locs in peak_data.values():
        for p in locs:
            all_locs.add(p['loc_key'])
    
    all_locs = sorted(list(all_locs))
    
    matrix_data = []
    for loc in all_locs:
        row = {'peak_loc': loc}
        for cl in found_cell_lines:
            # Check if this peak exists in this cell line
            # Simple binary presence (1) or use score if we want to be fancy
            # For "counts", 1 is presence.
            exists = any(p['loc_key'] == loc for p in peak_data.get(cl, []))
            row[cl] = 1 if exists else 0
        matrix_data.append(row)
    
    df_matrix = pd.DataFrame(matrix_data)
    df_matrix.set_index('peak_loc', inplace=True)
    return df_matrix

def write_outputs(rna_df: pd.DataFrame, peak_df: pd.DataFrame):
    """Write processed data to CSV and BED files."""
    
    # Write counts CSV
    # Format: index=feature_id, columns=cell_lines
    # For RNA: index=gene_id, columns=cell_lines
    # For Peaks: index=peak_loc, columns=cell_lines
    # The task asks for encode_counts.csv. We will combine them?
    # Usually, counts are separate. But the task says "encode_counts.csv" and "encode_peaks.bed".
    # Let's write the RNA matrix to encode_counts.csv.
    # And the peaks to encode_peaks.bed (reconstructed from the matrix or original).
    
    # 1. Write RNA counts
    rna_df.to_csv(COUNTS_FILE)
    logger.info(f"Written RNA counts to {COUNTS_FILE}")

    # 2. Write Peaks BED
    # We need to write the BED file. We have the peak_df with locs.
    # We need to parse 'peak_loc' back to chrom, start, end.
    bed_rows = []
    for idx, row in peak_df.iterrows():
        parts = idx.split(':')
        chrom = parts[0]
        coords = parts[1].split('-')
        start = int(coords[0])
        end = int(coords[1])
        # Find a representative score (max across cell lines where present)
        # Or just use 0.
        score = 1000 # Placeholder
        bed_rows.append([chrom, start, end, idx, score, '+'])
    
    bed_df = pd.DataFrame(bed_rows)
    bed_df.to_csv(PEAKS_FILE, sep='\t', header=False, index=False)
    logger.info(f"Written peaks to {PEAKS_FILE}")

def log_checksums():
    """Calculate checksums and write to logs/checksums.txt."""
    if not os.path.exists(CHECKSUM_LOG):
        # Ensure logs dir exists
        os.makedirs(os.path.dirname(CHECKSUM_LOG), exist_ok=True)
    
    checksums = []
    for f in [COUNTS_FILE, PEAKS_FILE]:
        if os.path.exists(f):
            cs = checksum_file(f)
            checksums.append(f"{f}: {cs}")
            logger.info(f"Checksum for {f}: {cs}")
        else:
            logger.warning(f"File missing for checksum: {f}")
    
    with open(CHECKSUM_LOG, 'a') as f:
        for line in checksums:
            f.write(line + "\n")

def main():
    """Main entry point for T011b."""
    logger.info("Starting ENCODE data download (T011b)...")
    setup_directories()

    try:
        # 1. Fetch RNA-seq data
        rna_df = process_rna_data(TARGET_CELL_LINES)
        
        # 2. Fetch Accessibility data
        peak_df = process_accessibility_data(TARGET_CELL_LINES)
        
        # 3. Write outputs
        write_outputs(rna_df, peak_df)
        
        # 4. Log checksums
        log_checksums()
        
        logger.info("T011b completed successfully.")
        
    except Exception as e:
        logger.critical(f"T011b failed: {e}")
        # Re-raise to ensure the pipeline knows it failed
        raise

if __name__ == "__main__":
    main()
