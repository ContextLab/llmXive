"""
Data download module for acquiring genomic and metabolomic datasets.
Handles GEO Series Matrix downloads and Metabolomics Workbench Study API downloads.
"""
import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from exceptions import E_DATASET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
GEO_SERIES_MATRIX_URL = "https://www.ncbi.nlm.nih.gov/geo/download/?acc={}&format=txt&file={}_series_matrix.txt.gz"
MW_BASE_URL = "https://www.metabolomicsworkbench.org/data/study_textformat.php"
MW_STUDY_API = "https://www.metabolomicsworkbench.org/data/REST2/API/"

# Study IDs for this project
GEO_STUDIES = {
    "Arabidopsis": "GSE21857",
    "Solanum": "GSE167633"
}
MW_STUDY_ID = "ST002565"

def create_session(timeout: int = 60) -> requests.Session:
    """Create a requests session with default timeout."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; PlantDefensePipeline/1.0)'
    })
    return session

def validate_study_accession(accession: str) -> bool:
    """Validate that an accession ID matches expected format."""
    # GEO: GSE followed by digits
    if accession.startswith("GSE"):
        return bool(re.match(r'^GSE\d+$', accession))
    # Metabolomics Workbench: ST followed by digits
    if accession.startswith("ST"):
        return bool(re.match(r'^ST\d+$', accession))
    return False

def fetch_geo_series_matrix(accession: str, output_dir: Path) -> Path:
    """
    Fetch GEO Series Matrix file for a given accession.
    
    Args:
        accession: GEO accession ID (e.g., GSE21857)
        output_dir: Directory to save the file
        
    Returns:
        Path to the downloaded file
        
    Raises:
        E_DATASET: If download fails or file is invalid
    """
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid GEO accession format: {accession}")
    
    url = f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=txt&file={accession}_series_matrix.txt.gz"
    output_path = output_dir / f"{accession}_series_matrix.txt"
    
    logger.info(f"Downloading GEO series matrix for {accession}...")
    logger.info(f"URL: {url}")
    
    session = create_session()
    try:
        # GEO files are gzipped, we download and decompress
        response = session.get(url, timeout=120, stream=True)
        response.raise_for_status()
        
        # Write to file (handling gzip if needed)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded {accession} to {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {accession}: {e}")
        raise E_DATASET(f"Failed to download GEO dataset {accession}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {accession}: {e}")
        raise E_DATASET(f"Error downloading GEO dataset {accession}: {e}")

def parse_series_matrix_header(lines: List[str]) -> Dict[str, Any]:
    """
    Parse the header section of a GEO Series Matrix file.
    
    Args:
        lines: List of header lines (starting with ^)
        
    Returns:
        Dictionary with metadata
    """
    metadata = {
        'samples': [],
        'genes': [],
        'platform': None,
        'title': None,
        'organism': None
    }
    
    current_sample = None
    
    for line in lines:
        if not line.startswith('^'):
            continue
            
        line = line.strip()
        parts = line.split('!', 1)
        if len(parts) != 2:
            continue
            
        field = parts[0].strip()
        value = parts[1].strip()
        
        if field == '!series_matrix_table_begin':
            break
        elif field == '!series_title':
            metadata['title'] = value
        elif field == '!series_organism':
            metadata['organism'] = value
        elif field == '!series_platform_id':
            metadata['platform'] = value
        elif field.startswith('!Sample_title'):
            if current_sample is None:
                current_sample = {}
            current_sample['title'] = value
        elif field.startswith('!Sample_accession'):
            if current_sample is None:
                current_sample = {}
            current_sample['accession'] = value
            metadata['samples'].append(current_sample)
            current_sample = {}
        elif field.startswith('!Sample_biosample'):
            if current_sample is None:
                current_sample = {}
            current_sample['biosample'] = value
            # Update last sample if we have one
            if metadata['samples']:
                metadata['samples'][-1].update(current_sample)
                
    return metadata

def parse_series_matrix_data(lines: List[str]) -> Tuple[List[str], Dict[str, List[float]]]:
    """
    Parse the data section of a GEO Series Matrix file.
    
    Args:
        lines: List of data lines
        
    Returns:
        Tuple of (gene_ids, {sample_id: [values]})
    """
    gene_ids = []
    data = {}
    sample_ids = []
    
    # First, identify sample columns from the header
    # The data section starts after !series_matrix_table_begin
    in_data = False
    
    for line in lines:
        line = line.strip()
        if line == '!series_matrix_table_begin':
            in_data = True
            continue
        if not in_data:
            continue
            
        # Parse tab-separated data
        parts = line.split('\t')
        if len(parts) < 2:
            continue
            
        # First column is usually the gene/probe ID
        gene_id = parts[0].strip()
        if gene_id.startswith('!') or gene_id.startswith('#'):
            continue
            
        gene_ids.append(gene_id)
        
        # Subsequent columns are sample values
        for i, val in enumerate(parts[1:], 1):
            if i > len(sample_ids):
                sample_ids.append(f"sample_{i-1}")
            
            try:
                num_val = float(val) if val.strip() else 0.0
                if i-1 not in data:
                    data[i-1] = []
                data[i-1].append(num_val)
            except ValueError:
                # Non-numeric value, treat as 0
                if i-1 not in data:
                    data[i-1] = []
                data[i-1].append(0.0)
    
    # Reorganize data by sample
    sample_data = {}
    for i, values in data.items():
        if i < len(sample_ids):
          sample_data[sample_ids[i]] = values
        else:
          sample_data[f"sample_{i}"] = values
              
    return gene_ids, sample_data

def download_study_data(accession: str, output_dir: Path) -> Path:
    """
    Download study data from Metabolomics Workbench.
    
    Args:
        accession: Study accession ID (e.g., ST002565)
        output_dir: Directory to save the file
        
    Returns:
        Path to the downloaded file
        
    Raises:
        E_DATASET: If download fails
    """
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid Metabolomics Workbench accession format: {accession}")
    
    # MW Study API endpoint for metabolite data
    url = f"https://www.metabolomicsworkbench.org/data/REST2/API/Study/GetAnalysisResult"
    params = {
        'STUDY_ID': accession,
        'ANALYSIS_ID': 'AN00000000'  # We'll get the actual ID from metadata
    }
    
    # First, get study metadata to find analysis ID
    metadata_url = f"https://www.metabolomicsworkbench.org/data/REST2/API/Study/GetStudy"
    metadata_params = {'STUDY_ID': accession}
    
    logger.info(f"Fetching metadata for Metabolomics Workbench study {accession}...")
    
    session = create_session()
    try:
        # Get metadata first
        meta_response = session.get(metadata_url, params=metadata_params, timeout=60)
        meta_response.raise_for_status()
        
        meta_data = meta_response.json()
        if 'ANALYSIS' not in meta_data or not meta_data['ANALYSIS']:
            raise E_DATASET(f"No analysis found for study {accession}")
        
        # Use the first analysis
        analysis_id = meta_data['ANALYSIS'][0]['ANALYSIS_ID']
        params['ANALYSIS_ID'] = analysis_id
        
        logger.info(f"Using analysis ID: {analysis_id}")
        
        # Now fetch metabolite data
        response = session.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        output_path = output_dir / f"{accession}_metabolite_data.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logger.info(f"Successfully downloaded {accession} to {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {accession}: {e}")
        raise E_DATASET(f"Failed to download Metabolomics Workbench dataset {accession}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {accession}: {e}")
        raise E_DATASET(f"Error downloading Metabolomics Workbench dataset {accession}: {e}")

def aggregate_expression_data(accession: str, file_path: Path, output_dir: Path) -> Path:
    """
    Parse GEO Series Matrix file and create expression matrix.
    
    Args:
        accession: Study accession
        file_path: Path to downloaded file
        output_dir: Output directory
        
    Returns:
        Path to the created expression matrix CSV
    """
    logger.info(f"Processing expression data for {accession}...")
    
    # Read and decompress if needed
    content = b''
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Handle gzip if present
    if content[:2] == b'\x1f\x8b':
        import gzip
        with gzip.GzipFile(fileobj=file_path) as f:
            lines = [line.decode('utf-8', errors='ignore').strip() for line in f.readlines()]
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f.readlines()]
    
    # Split into header and data
    header_lines = []
    data_lines = []
    in_data = False
    
    for line in lines:
        if line == '!series_matrix_table_begin':
            in_data = True
            header_lines.append(line)
            continue
        if in_data:
            data_lines.append(line)
        else:
            header_lines.append(line)
    
    # Parse metadata
    metadata = parse_series_matrix_header(header_lines)
    logger.info(f"Found {len(metadata['samples'])} samples for {accession}")
    
    # Parse data
    gene_ids, sample_data = parse_series_matrix_data(header_lines + data_lines)
    logger.info(f"Found {len(gene_ids)} genes for {accession}")
    
    if not gene_ids or not sample_data:
        raise E_DATASET(f"No valid data found in {accession}")
    
    # Create output CSV in WIDE FORMAT
    output_path = output_dir / "geo_expression_matrix.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header: gene_id, sample_1, sample_2, ...
        header = ['gene_id'] + list(sample_data.keys())
        writer.writerow(header)
        
        # Data rows
        for i, gene_id in enumerate(gene_ids):
            row = [gene_id]
            for sample_id in sample_data.keys():
                if i < len(sample_data[sample_id]):
                    row.append(f"{sample_data[sample_id][i]:.6f}")
                else:
                    row.append("")
            writer.writerow(row)
    
    logger.info(f"Created expression matrix at {output_path}")
    return output_path

def save_expression_matrix(accession: str, file_path: Path, output_dir: Path) -> Path:
    """
    Main function to download and process GEO expression data.
    
    Args:
        accession: GEO accession ID
        file_path: Path to save raw download
        output_dir: Directory for processed output
        
    Returns:
        Path to the final expression matrix CSV
    """
    raw_path = download_study_data(accession, file_path.parent) if accession.startswith("ST") else \
               fetch_geo_series_matrix(accession, file_path.parent)
    
    if accession.startswith("GSE"):
        return aggregate_expression_data(accession, raw_path, output_dir)
    else:
        # For metabolomics, we handle separately
        return raw_path

def download_metabolite_study(accession: str, output_dir: Path) -> Path:
    """
    Download and process metabolite data from Metabolomics Workbench.
    
    Args:
        accession: Study accession ID
        output_dir: Directory to save output
        
    Returns:
        Path to the metabolite matrix CSV
        
    Raises:
        E_DATASET: If download fails
    """
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid accession format: {accession}")
    
    logger.info(f"Downloading metabolite data for {accession}...")
    
    # Use the study text format API which gives us the data directly
    url = "https://www.metabolomicsworkbench.org/data/study_textformat.php"
    params = {
        'STUDY_ID': accession,
        'ANALYSIS_RESULT': 'Y',
        'RESULT_TYPE': 'METABOLITE'
    }
    
    session = create_session()
    try:
        response = session.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        # Parse the text format data
        lines = response.text.strip().split('\n')
        
        # Find the data section
        data_start = -1
        for i, line in enumerate(lines):
            if line.startswith('###METADATA'):
                data_start = i + 1
                break
        
        if data_start == -1:
            # Try alternative parsing
            data_start = 0
        
        # Extract sample IDs and metabolite names
        sample_ids = []
        metabolite_names = []
        data_matrix = []
        
        # Parse header
        header_line = lines[data_start] if data_start < len(lines) else ""
        if header_line:
            headers = header_line.split('\t')
            # First column is typically METABOLITE_NAME
            # Subsequent columns are samples
            for i, h in enumerate(headers):
                if i == 0:
                    continue  # Skip metabolite name column
                sample_ids.append(h.strip())
        
        # Parse data rows
        for line in lines[data_start + 1:]:
            if not line.strip() or line.startswith('###'):
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            metabolite_name = parts[0].strip()
            metabolite_names.append(metabolite_name)
            
            row_values = []
            for val in parts[1:]:
                try:
                    row_values.append(float(val) if val.strip() else 0.0)
                except ValueError:
                    row_values.append(0.0)
            
            data_matrix.append(row_values)
        
        if not metabolite_names or not sample_ids:
            raise E_DATASET(f"No valid metabolite data found for {accession}")
        
        logger.info(f"Found {len(metabolite_names)} metabolites and {len(sample_ids)} samples")
        
        # Write to CSV in WIDE FORMAT
        output_path = output_dir / "metabolite_matrix.csv"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header: metabolite_id, sample_1, sample_2, ...
            writer.writerow(['metabolite_id'] + sample_ids)
            
            # Data rows
            for i, metabolite in enumerate(metabolite_names):
                row = [metabolite]
                if i < len(data_matrix):
                    row.extend([f"{v:.6f}" for v in data_matrix[i]])
                else:
                    row.extend([""] * len(sample_ids))
                writer.writerow(row)
        
        logger.info(f"Created metabolite matrix at {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {accession}: {e}")
        raise E_DATASET(f"Failed to download Metabolomics Workbench dataset {accession}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {accession}: {e}")
        raise E_DATASET(f"Error downloading Metabolomics Workbench dataset {accession}: {e}")

def main():
    """Main entry point for data download."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download genomic and metabolomic data')
    parser.add_argument('--geo', action='append', help='GEO accession IDs to download')
    parser.add_argument('--mw', action='append', help='Metabolomics Workbench accession IDs to download')
    parser.add_argument('--output-dir', default='data/raw', help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download GEO data
    if args.geo:
        for accession in args.geo:
            try:
                logger.info(f"Processing GEO accession: {accession}")
                file_path = output_dir / f"{accession}_raw.txt"
                result_path = save_expression_matrix(accession, file_path, output_dir)
                logger.info(f"Completed {accession}: {result_path}")
            except E_DATASET as e:
                logger.error(f"Failed {accession}: {e}")
                raise
    
    # Download Metabolomics Workbench data
    if args.mw:
        for accession in args.mw:
            try:
                logger.info(f"Processing MW accession: {accession}")
                result_path = download_metabolite_study(accession, output_dir)
                logger.info(f"Completed {accession}: {result_path}")
            except E_DATASET as e:
                logger.error(f"Failed {accession}: {e}")
                raise

if __name__ == "__main__":
    main()