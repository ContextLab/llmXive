"""
Data download module for plant defense compound prediction project.
Handles downloading of GEO and Metabolomics Workbench datasets.
"""
import csv
import json
import logging
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from exceptions import E_DATASET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GEO_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/"
MW_API_BASE = "https://www.metabolomicsworkbench.org/studies/"
MW_DOWNLOAD_BASE = "https://www.metabolomicsworkbench.org/data/RRCCMetadata.php"

# Study IDs
GEO_ARABIDOPSIS = "GSE21857"
GEO_SOLANUM = "GSE167633"
MW_STUDY_ID = "ST002565"

def create_session() -> requests.Session:
    """Create a requests session with appropriate headers and timeout."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; PlantDefensePipeline/1.0)'
    })
    session.timeout = 300  # 5 minutes timeout
    return session

def validate_study_accession(accession: str) -> bool:
    """Validate that an accession ID matches expected format."""
    # GEO: GSE followed by numbers
    if accession.startswith("GSE"):
        return bool(re.match(r'^GSE\d+$', accession))
    # Metabolomics Workbench: ST followed by numbers
    elif accession.startswith("ST"):
        return bool(re.match(r'^ST\d+$', accession))
    return False

def fetch_geo_series_matrix(session: requests.Session, accession: str) -> Optional[str]:
    """Fetch GEO series matrix file content."""
    # Construct URL for series matrix file
    url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:6]}/nnn/matrix/{accession}_series_matrix.txt.gz"
    try:
        # Try direct download
        response = session.get(url, timeout=300)
        if response.status_code == 200:
            return response.text
    except requests.RequestException as e:
        logger.warning(f"Direct download failed for {accession}: {e}")
    
    # Fallback: Try to get from GEO FTP
    ftp_url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:6]}/nnn/{accession}/"
    try:
        response = session.get(ftp_url, timeout=300)
        if response.status_code == 200:
            # Parse HTML to find matrix file
            import re
            pattern = rf'href="({accession}_series_matrix\.txt\.gz)"'
            match = re.search(pattern, response.text)
            if match:
                matrix_url = ftp_url + match.group(1)
                response = session.get(matrix_url, timeout=300)
                if response.status_code == 200:
                    return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch GEO data for {accession}: {e}")
    
    return None

def parse_series_matrix_header(text: str) -> Dict[str, Any]:
    """Parse header information from GEO series matrix file."""
    metadata = {}
    current_section = None
    
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('!'):
            if line.startswith('!Series_title'):
                metadata['series_title'] = line.split('=', 1)[1].strip()
            elif line.startswith('!Series_accession'):
                metadata['accession'] = line.split('=', 1)[1].strip()
            elif line.startswith('!Sample_title'):
                if 'samples' not in metadata:
                    metadata['samples'] = []
                sample_title = line.split('=', 1)[1].strip()
                metadata['samples'].append({'title': sample_title})
            elif line.startswith('!Sample_accession'):
                if 'samples' in metadata and metadata['samples']:
                    metadata['samples'][-1]['accession'] = line.split('=', 1)[1].strip()
            elif line.startswith('!Sample_characteristics_ch1'):
                if 'samples' in metadata and metadata['samples']:
                    char = line.split('=', 1)[1].strip()
                    if 'characteristics' not in metadata['samples'][-1]:
                        metadata['samples'][-1]['characteristics'] = []
                    metadata['samples'][-1]['characteristics'].append(char)
    
    return metadata

def parse_series_matrix_data(text: str) -> Tuple[List[str], List[str], List[List[float]]]:
    """Parse data section from GEO series matrix file."""
    genes = []
    samples = []
    data = []
    
    in_data = False
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('!'):
            continue
        if line.startswith('['):
            if line == '[data_matrix]':
                in_data = True
            continue
        if not in_data:
            continue
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) >= 2:
            gene_id = parts[0]
            values = []
            for val in parts[1:]:
                try:
                    values.append(float(val))
                except ValueError:
                    values.append(0.0)
            
            if not genes:  # First row defines samples
                samples = [f"sample_{i+1}" for i in range(len(values))]
            
            genes.append(gene_id)
            data.append(values)
    
    return genes, samples, data

def download_study_data(session: requests.Session, accession: str, output_dir: Path) -> Path:
    """Download GEO study data and save as zip."""
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid GEO accession format: {accession}")
    
    output_file = output_dir / f"geo_{accession}.zip"
    
    # For GEO, we'll create a zip containing the series matrix file
    matrix_text = fetch_geo_series_matrix(session, accession)
    if not matrix_text:
        raise E_DATASET(f"Failed to download GEO data for {accession}")
    
    # Create zip file
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"{accession}_series_matrix.txt", matrix_text)
    
    logger.info(f"Downloaded and saved GEO data to {output_file}")
    return output_file

def aggregate_expression_data(genes: List[str], samples: List[str], data: List[List[float]]) -> Dict[str, Any]:
    """Aggregate expression data into a structured format."""
    return {
        'genes': genes,
        'samples': samples,
        'data': data,
        'shape': (len(genes), len(samples))
    }

def save_expression_matrix(agg_data: Dict[str, Any], output_path: Path) -> Path:
    """Save expression matrix to CSV file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        header = ['gene_id'] + agg_data['samples']
        writer.writerow(header)
        
        # Write data
        for i, gene in enumerate(agg_data['genes']):
            row = [gene] + [f"{val:.6f}" for val in agg_data['data'][i]]
            writer.writerow(row)
    
    logger.info(f"Saved expression matrix to {output_path}")
    return output_path

def download_metabolite_study(accession: str, output_dir: Path) -> Path:
    """
    Download metabolite data from Metabolomics Workbench.
    
    Args:
        accession: Study accession ID (e.g., ST002565)
        output_dir: Directory to save the downloaded file
        
    Returns:
        Path to the downloaded zip file
        
    Raises:
        E_DATASET: If download fails or accession is invalid
    """
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid Metabolomics Workbench accession format: {accession}")
    
    output_file = output_dir / f"metabolomics_{accession}.zip"
    
    # Check if file already exists
    if output_file.exists():
        logger.info(f"Metabolomics data already exists at {output_file}")
        return output_file
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    session = create_session()
    
    try:
        # Step 1: Get study metadata to find analysis ID
        metadata_url = f"{MW_API_BASE}{accession}.json"
        logger.info(f"Fetching study metadata from {metadata_url}")
        
        response = session.get(metadata_url, timeout=300)
        if response.status_code != 200:
            raise E_DATASET(f"Failed to fetch study metadata for {accession}: HTTP {response.status_code}")
        
        metadata = response.json()
        
        # Extract analysis ID from metadata
        analysis_id = None
        if 'analyses' in metadata and len(metadata['analyses']) > 0:
            analysis_id = metadata['analyses'][0].get('analysis_id')
            if not analysis_id:
                # Try alternative field
                analysis_id = metadata['analyses'][0].get('id')
        
        if not analysis_id:
            raise E_DATASET(f"Could not find analysis ID for study {accession}")
        
        logger.info(f"Found analysis ID: {analysis_id}")
        
        # Step 2: Download metabolite data
        download_params = {
            'RESULT': 'RAW',
            'STUDY_ACCESSION': accession,
            'ANALYSIS_ACCESSION': analysis_id,
            'FILE_TYPE': 'TXT'
        }
        
        download_url = f"{MW_DOWNLOAD_BASE}?{requests.compat.urlencode(download_params)}"
        logger.info(f"Downloading metabolite data from {download_url}")
        
        response = session.get(download_url, timeout=600)
        if response.status_code != 200:
            raise E_DATASET(f"Failed to download metabolite data for {accession}: HTTP {response.status_code}")
        
        # Save as zip (containing the raw text file)
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"{accession}_metabolite_data.txt", response.text)
        
        logger.info(f"Successfully downloaded and saved metabolite data to {output_file}")
        return output_file
        
    except requests.RequestException as e:
        logger.error(f"Network error while downloading {accession}: {e}")
        raise E_DATASET(f"Network error downloading metabolite data for {accession}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse metadata JSON for {accession}: {e}")
        raise E_DATASET(f"Invalid metadata response for {accession}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {accession}: {e}")
        raise E_DATASET(f"Failed to download metabolite data for {accession}: {e}")

def main():
    """Main function to download metabolite data for T002a."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download metabolite data from Metabolomics Workbench')
    parser.add_argument('--study-id', default=MW_STUDY_ID, help='Metabolomics Workbench study ID')
    parser.add_argument('--output-dir', type=Path, default=Path('data/raw'), help='Output directory')
    
    args = parser.parse_args()
    
    try:
        output_path = download_metabolite_study(args.study_id, args.output_dir)
        print(f"Download completed: {output_path}")
        return 0
    except E_DATASET as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
