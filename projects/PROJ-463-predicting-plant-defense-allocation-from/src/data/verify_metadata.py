"""
Metadata verification for downloaded FASTQ files.

Verifies that downloaded files match FR-001 requirements:
- Tissue type is present and valid
- Herbivore type is present
- Replicates are sufficient (>= 2)

Fetches metadata from NCBI E-utilities using accession IDs.
"""
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from urllib.parse import urlencode

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_config
from src.utils.schemas import ManifestEntry, DataManifest
from src.data.download import fetch_sra_accession_info

logger = get_logger(__name__)

# FR-001 Required metadata fields
REQUIRED_METADATA_FIELDS = {
    'tissue': ['leaf', 'root', 'stem', 'flower', 'seed', 'whole_plant', 'inflorescence'],
    'herbivore_type': ['chewing', 'sucking', 'phloem_feeder', 'xylem_feeder', 'leaf_miner', 'leaf_taster', 'stem_borer', 'root_feeder', 'none', 'control'],
}

MIN_REPLICATES = 2

def fetch_sra_metadata(accession_id: str, retries: int = 3, backoff: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an SRA accession from NCBI E-utilities.
    
    Args:
        accession_id: The SRA accession ID (e.g., SRR123456)
        retries: Number of retry attempts
        backoff: Backoff time between retries in seconds
        
    Returns:
        Dictionary containing metadata, or None if fetch fails
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    params = {
        'db': 'sra',
        'id': accession_id,
        'retmode': 'json'
    }
    
    for attempt in range(retries):
        try:
            url = f"{base_url}?{urlencode(params)}"
            logger.info(f"Fetching metadata for {accession_id} (attempt {attempt + 1}/{retries})")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'result' in data and accession_id in data['result']:
                result = data['result'][accession_id]
                logger.debug(f"Successfully fetched metadata for {accession_id}")
                return result
            else:
                logger.warning(f"No result found for {accession_id} in response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {accession_id}: {e}")
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
            else:
                logger.error(f"Failed to fetch metadata for {accession_id} after {retries} attempts")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {accession_id}: {e}")
            return None
    
    return None

def extract_required_metadata(sra_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required metadata fields from SRA metadata.
    
    Args:
        sra_metadata: Raw metadata from NCBI SRA
        
    Returns:
        Dictionary with extracted fields: tissue, herbivore_type, sample_title, etc.
    """
    extracted = {
        'accession_id': sra_metadata.get('accession', ''),
        'sample_title': sra_metadata.get('title', ''),
        'tissue': None,
        'herbivore_type': None,
        'organism': sra_metadata.get('organism', ''),
        'platform': sra_metadata.get('platform', ''),
        'library_strategy': sra_metadata.get('library_strategy', ''),
        'library_source': sra_metadata.get('library_source', ''),
        'attributes': {}
    }
    
    # Extract attributes from the metadata
    attributes = sra_metadata.get('attributes', [])
    
    for attr in attributes:
        key = attr.get('key', '').lower()
        value = attr.get('value', '')
        
        # Map common attribute names to our required fields
        if key in ['tissue', 'tissue_type', 'plant_tissue']:
            extracted['tissue'] = value.lower().strip()
        elif key in ['herbivore_type', 'herbivore', 'feeding_type', 'damage_type']:
            extracted['herbivore_type'] = value.lower().strip()
        elif key in ['organism', 'species']:
            extracted['organism'] = value
        else:
            extracted['attributes'][key] = value
    
    # If tissue/herbivore not found in standard keys, check sample title
    if not extracted['tissue']:
        title = extracted['sample_title'].lower()
        for tissue_type in REQUIRED_METADATA_FIELDS['tissue']:
            if tissue_type in title:
                extracted['tissue'] = tissue_type
                break
    
    if not extracted['herbivore_type']:
        title = extracted['sample_title'].lower()
        for herb_type in REQUIRED_METADATA_FIELDS['herbivore_type']:
            if herb_type in title:
                extracted['herbivore_type'] = herb_type
                break
    
    return extracted

def verify_metadata_requirements(extracted_metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify that extracted metadata meets FR-001 requirements.
    
    Args:
        extracted_metadata: Metadata extracted from SRA
        
    Returns:
        Tuple of (is_valid, list_of_failure_reasons)
    """
    failures = []
    
    # Check tissue
    tissue = extracted_metadata.get('tissue')
    if not tissue:
        failures.append("Missing tissue metadata")
    elif tissue not in REQUIRED_METADATA_FIELDS['tissue']:
        failures.append(f"Tissue '{tissue}' not in allowed list: {REQUIRED_METADATA_FIELDS['tissue']}")
    
    # Check herbivore type
    herbivore_type = extracted_metadata.get('herbivore_type')
    if not herbivore_type:
        failures.append("Missing herbivore_type metadata")
    elif herbivore_type not in REQUIRED_METADATA_FIELDS['herbivore_type']:
        failures.append(f"Herbivore type '{herbivore_type}' not in allowed list: {REQUIRED_METADATA_FIELDS['herbivore_type']}")
    
    return len(failures) == 0, failures

def verify_fastq_metadata(fastq_files: List[Path], manifest_path: Path) -> Dict[str, Any]:
    """
    Verify metadata for all FASTQ files against FR-001 requirements.
    
    Args:
        fastq_files: List of paths to FASTQ files to verify
        manifest_path: Path to the manifest file containing accession IDs
        
    Returns:
        Verification report dictionary
    """
    report = {
        'verification_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_files': len(fastq_files),
        'verified_files': [],
        'failed_files': [],
        'excluded_studies': [],
        'summary': {
            'total_verified': 0,
            'total_failed': 0,
            'total_excluded': 0
        }
    }
    
    # Load manifest to get accession IDs
    try:
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
            manifest_entries = manifest_data.get('entries', [])
    except FileNotFoundError:
        logger.error(f"Manifest file not found: {manifest_path}")
        report['error'] = f"Manifest file not found: {manifest_path}"
        return report
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        report['error'] = f"Invalid JSON in manifest: {e}"
        return report
    
    # Create mapping of accession_id to manifest entry
    accession_map = {}
    for entry in manifest_entries:
        accession_id = entry.get('accession_id')
        if accession_id:
            accession_map[accession_id] = entry
    
    # Track studies and their samples for replicate checking
    study_samples = {}
    
    for fastq_file in fastq_files:
        # Extract accession ID from filename (e.g., SRR123456_R1.fastq.gz)
        filename = fastq_file.name
        parts = filename.split('_')
        if len(parts) < 2:
            logger.warning(f"Cannot extract accession ID from filename: {filename}")
            report['failed_files'].append({
                'file': str(fastq_file),
                'reason': 'Invalid filename format'
            })
            report['summary']['total_failed'] += 1
            continue
        
        accession_id = parts[0]
        
        # Get manifest entry
        manifest_entry = accession_map.get(accession_id)
        if not manifest_entry:
            logger.warning(f"No manifest entry found for {accession_id}")
            report['failed_files'].append({
                'file': str(fastq_file),
                'reason': 'No manifest entry found'
            })
            report['summary']['total_failed'] += 1
            continue
        
        # Fetch metadata from NCBI
        sra_metadata = fetch_sra_metadata(accession_id)
        if not sra_metadata:
            logger.error(f"Failed to fetch metadata for {accession_id}")
            report['failed_files'].append({
                'file': str(fastq_file),
                'accession_id': accession_id,
                'reason': 'Failed to fetch metadata from NCBI'
            })
            report['summary']['total_failed'] += 1
            continue
        
        # Extract required fields
        extracted = extract_required_metadata(sra_metadata)
        
        # Verify requirements
        is_valid, failures = verify_metadata_requirements(extracted)
        
        # Track by study (using organism or sample title as study identifier)
        study_id = extracted.get('organism', 'unknown')
        if study_id not in study_samples:
            study_samples[study_id] = []
        study_samples[study_id].append({
            'accession_id': accession_id,
            'file': str(fastq_file),
            'is_valid': is_valid,
            'failures': failures,
            'metadata': extracted
        })
        
        if is_valid:
            report['verified_files'].append({
                'file': str(fastq_file),
                'accession_id': accession_id,
                'tissue': extracted.get('tissue'),
                'herbivore_type': extracted.get('herbivore_type'),
                'organism': extracted.get('organism')
            })
            report['summary']['total_verified'] += 1
        else:
            report['failed_files'].append({
                'file': str(fastq_file),
                'accession_id': accession_id,
                'failures': failures,
                'metadata': extracted
            })
            report['summary']['total_failed'] += 1
    
    # Check replicates per study
    for study_id, samples in study_samples.items():
        valid_samples = [s for s in samples if s['is_valid']]
        if len(valid_samples) < MIN_REPLICATES:
            # Mark all samples in this study as excluded
            excluded_reason = f"Insufficient replicates: {len(valid_samples)} < {MIN_REPLICATES}"
            report['excluded_studies'].append({
                'study_id': study_id,
                'valid_samples': len(valid_samples),
                'reason': excluded_reason,
                'sample_accessions': [s['accession_id'] for s in valid_samples]
            })
            # Move valid samples from verified to excluded
            for sample in valid_samples:
                for verified in report['verified_files']:
                    if verified['accession_id'] == sample['accession_id']:
                        report['verified_files'].remove(verified)
                        break
                sample['excluded'] = True
                sample['exclusion_reason'] = excluded_reason
                report['failed_files'].append({
                    'file': sample['file'],
                    'accession_id': sample['accession_id'],
                    'reason': excluded_reason
                })
                report['summary']['total_verified'] -= 1
                report['summary']['total_excluded'] += 1
    
    report['summary']['total_failed'] = len(report['failed_files'])
    
    logger.info(f"Metadata verification complete: {report['summary']['total_verified']} verified, "
               f"{report['summary']['total_failed']} failed, {report['summary']['total_excluded']} excluded")
    
    return report

def main():
    """Main entry point for metadata verification."""
    config = get_config()
    data_path = Path(config.get_data_path())
    raw_dir = data_path / 'raw'
    processed_dir = data_path / 'processed'
    manifests_dir = data_path / 'manifests'
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all FASTQ files in raw directory
    fastq_files = list(raw_dir.glob('*_R1.fastq.gz')) + list(raw_dir.glob('*_R2.fastq.gz'))
    
    if not fastq_files:
        logger.warning("No FASTQ files found in data/raw/")
        print("No FASTQ files found. Please run T011 (download.py) first.")
        sys.exit(0)
    
    # Find manifest file
    manifest_files = list(manifests_dir.glob('*_manifest.json'))
    if not manifest_files:
        logger.error("No manifest file found in data/manifests/")
        print("No manifest file found. Please run T011 (download.py) first.")
        sys.exit(1)
    
    # Use the first manifest found (or combine if multiple)
    manifest_path = manifest_files[0]
    logger.info(f"Using manifest: {manifest_path}")
    
    # Run verification
    report = verify_fastq_metadata(fastq_files, manifest_path)
    
    # Write report to processed directory
    output_path = processed_dir / 'metadata_verification_report.json'
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report written to: {output_path}")
    print(f"Metadata verification complete. Report saved to: {output_path}")
    
    # Return exit code based on results
    if report['summary']['total_verified'] == 0:
        logger.error("No files passed metadata verification!")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
