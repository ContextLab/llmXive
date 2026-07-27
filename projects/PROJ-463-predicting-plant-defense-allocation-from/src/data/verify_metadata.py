"""
Metadata verification module for RNA-seq studies.

Verifies downloaded FASTQ files and associated metadata against FR-001 requirements
(tissue, herbivore type, replicates) BEFORE preprocessing.
"""
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from datetime import datetime
import logging

# Import from project utils
from src.utils.logger import get_logger
from src.utils.config import get_data_path
from src.utils.schemas import RNASeqStudy, DefenseAllocationIndex, HerbivoreResponseVector

# Configure logger
logger = get_logger(__name__)

# Constants
MIN_REPLICATES = 2
REQUIRED_METADATA_FIELDS = ['tissue', 'treatment', 'replicates']
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def fetch_sra_metadata(accession_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an SRA accession from NCBI E-utilities.
    
    Args:
        accession_id: SRA accession ID (e.g., SRR123456)
        retries: Number of retry attempts on failure
        
    Returns:
        Dictionary containing metadata or None if fetch fails
    """
    url = f"{NCBI_EUTILS_BASE}?db=sra&id={accession_id}&retmode=json"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'result' in data and accession_id in data['result']:
                return data['result'][accession_id]
            elif 'error' in data:
                logger.warning(f"NCBI returned error for {accession_id}: {data['error']}")
                return None
            else:
                logger.warning(f"Unexpected response format for {accession_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {accession_id}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch metadata for {accession_id} after {retries} attempts")
                return None
                
    return None

def fetch_geo_metadata(accession_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a GEO accession from NCBI E-utilities.
    
    Args:
        accession_id: GEO accession ID (e.g., GSE12345)
        retries: Number of retry attempts on failure
        
    Returns:
        Dictionary containing metadata or None if fetch fails
    """
    url = f"{NCBI_EUTILS_BASE}?db=gds&id={accession_id}&retmode=json"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'result' in data and accession_id in data['result']:
                return data['result'][accession_id]
            elif 'error' in data:
                logger.warning(f"NCBI returned error for {accession_id}: {data['error']}")
                return None
            else:
                logger.warning(f"Unexpected response format for {accession_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {accession_id}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to fetch metadata for {accession_id} after {retries} attempts")
                return None
                
    return None

def extract_required_metadata(sra_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required metadata fields from SRA metadata response.
    
    Args:
        sra_metadata: Raw metadata dictionary from NCBI
        
    Returns:
        Dictionary with extracted tissue, treatment, replicates, and other relevant fields
    """
    extracted = {
        'accession_id': sra_metadata.get('accession'),
        'tissue': None,
        'treatment': None,
        'replicates': 0,
        'species': None,
        'experiment_title': sra_metadata.get('title'),
        'experiment_description': sra_metadata.get('description'),
        'sample_attributes': {}
    }
    
    # Extract sample attributes
    sample_attrs = sra_metadata.get('sample_attributes', [])
    for attr in sample_attrs:
        tag = attr.get('tag', '').lower()
        value = attr.get('value', '')
        
        if 'tissue' in tag or 'organ' in tag:
            extracted['tissue'] = value
        elif 'treatment' in tag or 'condition' in tag or 'herbivore' in tag:
            extracted['treatment'] = value
        elif 'species' in tag or 'organism' in tag:
            extracted['species'] = value
        elif 'replicate' in tag:
            try:
                extracted['replicates'] = int(value)
            except (ValueError, TypeError):
                pass
    
    # If replicates not explicitly stated, count experiments
    if extracted['replicates'] == 0:
        experiments = sra_metadata.get('experiments', [])
        extracted['replicates'] = len(experiments)
    
    return extracted

def verify_metadata_requirements(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify that metadata meets FR-001 requirements.
    
    Args:
        metadata: Extracted metadata dictionary
        
    Returns:
        Tuple of (is_valid, list_of_exclusion_reasons)
    """
    exclusion_reasons = []
    
    # Check for tissue metadata
    if not metadata.get('tissue'):
        exclusion_reasons.append("Missing tissue metadata")
    
    # Check for treatment/herbivore type metadata
    if not metadata.get('treatment'):
        exclusion_reasons.append("Missing treatment/herbivore type metadata")
    
    # Check for minimum replicates
    if metadata.get('replicates', 0) < MIN_REPLICATES:
        exclusion_reasons.append(f"Insufficient replicates: {metadata.get('replicates', 0)} < {MIN_REPLICATES}")
    
    # Check for species metadata (important for downstream analysis)
    if not metadata.get('species'):
        exclusion_reasons.append("Missing species metadata")
    
    is_valid = len(exclusion_reasons) == 0
    return is_valid, exclusion_reasons

def verify_fastq_metadata(fastq_files: List[Path], manifest_path: Path) -> Dict[str, Any]:
    """
    Verify metadata for FASTQ files against FR-001 requirements.
    
    Args:
        fastq_files: List of FASTQ file paths
        manifest_path: Path to the data manifest JSON
        
    Returns:
        Verification report dictionary
    """
    report = {
        'verification_timestamp': datetime.now().isoformat(),
        'total_studies': 0,
        'valid_studies': 0,
        'excluded_studies': 0,
        'study_results': [],
        'summary': {
            'exclusion_reasons': {},
            'species_distribution': {},
            'tissue_distribution': {}
        }
    }
    
    # Load manifest if exists
    manifest_data = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse manifest: {e}")
    
    # Process each FASTQ file
    for fastq_file in fastq_files:
        study_result = {
            'fastq_file': str(fastq_file),
            'accession_id': None,
            'is_valid': False,
            'metadata': {},
            'exclusion_reasons': []
        }
        
        # Extract accession ID from filename
        accession_id = fastq_file.stem
        if accession_id.startswith('SRR') or accession_id.startswith('GSM') or accession_id.startswith('GSE'):
            study_result['accession_id'] = accession_id
        else:
            # Try to find in manifest
            for entry in manifest_data.get('entries', []):
                if entry.get('file_name') == fastq_file.name:
                    study_result['accession_id'] = entry.get('accession_id')
                    break
        
        if not study_result['accession_id']:
            study_result['exclusion_reasons'].append("Could not determine accession ID")
            study_result['is_valid'] = False
        else:
            # Fetch metadata from NCBI
            metadata = fetch_sra_metadata(study_result['accession_id'])
            
            if not metadata:
                study_result['exclusion_reasons'].append("Failed to fetch metadata from NCBI")
            else:
                # Extract required fields
                extracted_metadata = extract_required_metadata(metadata)
                study_result['metadata'] = extracted_metadata
                
                # Verify requirements
                is_valid, exclusion_reasons = verify_metadata_requirements(extracted_metadata)
                study_result['is_valid'] = is_valid
                study_result['exclusion_reasons'] = exclusion_reasons
                
                # Update summary statistics
                if is_valid:
                    report['valid_studies'] += 1
                    
                    # Track species distribution
                    species = extracted_metadata.get('species', 'Unknown')
                    report['summary']['species_distribution'][species] = report['summary']['species_distribution'].get(species, 0) + 1
                    
                    # Track tissue distribution
                    tissue = extracted_metadata.get('tissue', 'Unknown')
                    report['summary']['tissue_distribution'][tissue] = report['summary']['tissue_distribution'].get(tissue, 0) + 1
                else:
                    report['excluded_studies'] += 1
                    for reason in exclusion_reasons:
                        report['summary']['exclusion_reasons'][reason] = report['summary']['exclusion_reasons'].get(reason, 0) + 1
        
        report['study_results'].append(study_result)
        report['total_studies'] += 1
    
    return report

def verify_synthetic_metadata(synthetic_manifest_path: Path) -> Dict[str, Any]:
    """
    Verify synthetic metadata against schema.
    
    Args:
        synthetic_manifest_path: Path to synthetic manifest JSON
        
    Returns:
        Verification report dictionary
    """
    report = {
        'verification_timestamp': datetime.now().isoformat(),
        'mode': 'synthetic',
        'total_studies': 0,
        'valid_studies': 0,
        'excluded_studies': 0,
        'study_results': [],
        'summary': {
            'exclusion_reasons': {},
            'species_distribution': {},
            'tissue_distribution': {}
        }
    }
    
    if not synthetic_manifest_path.exists():
        logger.error(f"Synthetic manifest not found: {synthetic_manifest_path}")
        report['exclusion_reasons']['missing_manifest'] = 1
        return report
    
    try:
        with open(synthetic_manifest_path, 'r') as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse synthetic manifest: {e}")
        report['exclusion_reasons']['invalid_manifest'] = 1
        return report
    
    # Verify synthetic entries
    entries = manifest_data.get('entries', [])
    if not entries:
        # Check if it's a single entry format
        if manifest_data.get('source_type') == 'synthetic':
            entries = [manifest_data]
    
    for entry in entries:
        study_result = {
            'accession_id': entry.get('accession_id'),
            'is_valid': True,
            'metadata': {},
            'exclusion_reasons': []
        }
        
        # Validate schema fields
        required_fields = ['accession_id', 'species', 'tissue', 'treatment', 'replicates']
        missing_fields = [field for field in required_fields if not entry.get(field)]
        
        if missing_fields:
            study_result['is_valid'] = False
            study_result['exclusion_reasons'].append(f"Missing required fields: {', '.join(missing_fields)}")
            report['excluded_studies'] += 1
            for field in missing_fields:
                reason = f"Missing {field}"
                report['summary']['exclusion_reasons'][reason] = report['summary']['exclusion_reasons'].get(reason, 0) + 1
        else:
            # Check replicates
            if entry.get('replicates', 0) < MIN_REPLICATES:
                study_result['is_valid'] = False
                study_result['exclusion_reasons'].append(f"Insufficient replicates: {entry.get('replicates')} < {MIN_REPLICATES}")
                report['excluded_studies'] += 1
                reason = f"Insufficient replicates"
                report['summary']['exclusion_reasons'][reason] = report['summary']['exclusion_reasons'].get(reason, 0) + 1
            else:
                report['valid_studies'] += 1
                study_result['metadata'] = {
                    'species': entry.get('species'),
                    'tissue': entry.get('tissue'),
                    'treatment': entry.get('treatment'),
                    'replicates': entry.get('replicates')
                }
                
                # Update distributions
                species = entry.get('species', 'Unknown')
                report['summary']['species_distribution'][species] = report['summary']['species_distribution'].get(species, 0) + 1
                
                tissue = entry.get('tissue', 'Unknown')
                report['summary']['tissue_distribution'][tissue] = report['summary']['tissue_distribution'].get(tissue, 0) + 1
        
        report['study_results'].append(study_result)
        report['total_studies'] += 1
    
    return report

def main(mode: str = 'real', fastq_dir: Optional[str] = None, manifest_path: Optional[str] = None) -> int:
    """
    Main function to run metadata verification.
    
    Args:
        mode: 'real' or 'synthetic'
        fastq_dir: Directory containing FASTQ files (for real mode)
        manifest_path: Path to manifest file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    data_path = get_data_path()
    
    if mode == 'synthetic':
        logger.info("Running metadata verification in synthetic mode")
        synthetic_manifest_path = Path(data_path) / 'synthetic' / 'synthetic_manifest.json'
        if manifest_path:
            synthetic_manifest_path = Path(manifest_path)
        
        report = verify_synthetic_metadata(synthetic_manifest_path)
    else:
        logger.info("Running metadata verification in real mode")
        
        # Determine FASTQ directory
        if fastq_dir:
            raw_dir = Path(fastq_dir)
        else:
            raw_dir = Path(data_path) / 'raw'
        
        # Find FASTQ files
        fastq_files = list(raw_dir.glob('*.fastq.gz')) + list(raw_dir.glob('*.fq.gz'))
        
        if not fastq_files:
            logger.warning("No FASTQ files found in raw directory")
            # Try processed directory as fallback
            processed_dir = Path(data_path) / 'processed'
            fastq_files = list(processed_dir.glob('*.fastq.gz')) + list(processed_dir.glob('*.fq.gz'))
        
        if not fastq_files:
            logger.error("No FASTQ files found in any expected directory")
            return 1
        
        # Determine manifest path
        if manifest_path:
            manifest_file = Path(manifest_path)
        else:
            manifest_file = Path(data_path) / 'manifests' / 'real_data_manifest.json'
            if not manifest_file.exists():
                manifest_file = Path(data_path) / 'manifests' / 'synthetic_manifest.json'
        
        report = verify_fastq_metadata(fastq_files, manifest_file)
    
    # Write report
    output_dir = Path(data_path) / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'metadata_verification_report.json'
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Metadata verification report written to {output_path}")
    
    # Print summary
    logger.info(f"Total studies: {report['total_studies']}")
    logger.info(f"Valid studies: {report['valid_studies']}")
    logger.info(f"Excluded studies: {report['excluded_studies']}")
    
    if report['excluded_studies'] > 0:
        logger.warning(f"Exclusion reasons: {json.dumps(report['summary']['exclusion_reasons'], indent=2)}")
    
    return 0 if report['valid_studies'] > 0 else 1

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify metadata for RNA-seq studies')
    parser.add_argument('--mode', choices=['real', 'synthetic'], default='real',
                      help='Mode of operation: real or synthetic')
    parser.add_argument('--fastq-dir', type=str, help='Directory containing FASTQ files')
    parser.add_argument('--manifest-path', type=str, help='Path to manifest file')
    
    args = parser.parse_args()
    
    sys.exit(main(
        mode=args.mode,
        fastq_dir=args.fastq_dir,
        manifest_path=args.manifest_path
    ))
