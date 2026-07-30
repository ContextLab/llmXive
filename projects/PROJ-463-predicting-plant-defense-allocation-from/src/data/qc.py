import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys
import json
import logging
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.config import get_data_path
from src.utils.schemas import RNASeqStudy

logger = get_logger(__name__)

def check_replicates(studies: List[Dict], min_replicates: int = 2) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter studies based on biological replicate count.
    
    Args:
        studies: List of study dictionaries containing 'replicates' key
        min_replicates: Minimum required replicates (default 2 per FR-001)
        
    Returns:
        Tuple of (included_studies, excluded_studies)
    """
    included = []
    excluded = []
    
    for study in studies:
        replicates = study.get('replicates', 0)
        species = study.get('species', 'Unknown')
        
        if replicates < min_replicates:
            excluded.append({
                'species': species,
                'accession_id': study.get('accession_id', 'Unknown'),
                'replicates': replicates,
                'exclusion_reason': f"Insufficient biological replicates: {replicates} < {min_replicates}"
            })
            logger.warning(f"Excluding study {study.get('accession_id')}: {excluded[-1]['exclusion_reason']}")
        else:
            included.append(study)
            
    return included, excluded

def check_metadata_completeness(studies: List[Dict], required_fields: List[str] = None) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter studies based on metadata completeness.
    
    Args:
        studies: List of study dictionaries
        required_fields: List of required metadata fields (default includes tissue)
        
    Returns:
        Tuple of (included_studies, excluded_studies)
    """
    if required_fields is None:
        required_fields = ['tissue', 'species', 'treatment']
        
    included = []
    excluded = []
    
    for study in studies:
        missing_fields = []
        for field in required_fields:
            value = study.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                missing_fields.append(field)
        
        if missing_fields:
            species = study.get('species', 'Unknown')
            excluded.append({
                'species': species,
                'accession_id': study.get('accession_id', 'Unknown'),
                'exclusion_reason': f"Missing required metadata fields: {', '.join(missing_fields)}"
            })
            logger.warning(f"Excluding study {study.get('accession_id')}: {excluded[-1]['exclusion_reason']}")
        else:
            included.append(study)
            
    return included, excluded

def run_qc_pipeline(input_manifest_path: Optional[Path] = None, 
                   output_path: Optional[Path] = None) -> Dict:
    """
    Run the complete QC pipeline on downloaded studies.
    
    Args:
        input_manifest_path: Path to the real data manifest or synthetic manifest
        output_path: Path to write the post-QC species list
        
    Returns:
        Dictionary containing QC results and statistics
    """
    data_path = get_data_path()
    if input_manifest_path is None:
        # Default to real data manifest if it exists, otherwise synthetic
        real_manifest = data_path / 'manifests' / 'real_data_manifest.json'
        synthetic_manifest = data_path / 'manifests' / 'synthetic_manifest.json'
        
        if real_manifest.exists():
            input_manifest_path = real_manifest
        elif synthetic_manifest.exists():
            input_manifest_path = synthetic_manifest
        else:
            raise FileNotFoundError("No data manifest found. Run download or synthetic generation first.")
    
    if output_path is None:
        output_path = data_path / 'processed' / 'post_qc_species_list.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading studies from manifest: {input_manifest_path}")
    
    with open(input_manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # Handle different manifest structures
    if 'studies' in manifest_data:
        studies = manifest_data['studies']
    elif 'entries' in manifest_data:
        # Convert manifest entries to study format
        studies = []
        for entry in manifest_data['entries']:
            study = {
                'accession_id': entry.get('accession_id', entry.get('file_name', '')),
                'species': entry.get('species', 'Unknown'),
                'tissue': entry.get('tissue', ''),
                'treatment': entry.get('treatment', ''),
                'replicates': entry.get('replicates', 1)
            }
            studies.append(study)
    else:
        # Assume flat list or single entry
        studies = [manifest_data] if isinstance(manifest_data, dict) else manifest_data
    
    total_studies = len(studies)
    logger.info(f"Found {total_studies} studies to process")
    
    # Step 1: Check replicates
    studies_after_replicates, excluded_by_replicates = check_replicates(studies)
    logger.info(f"After replicate check: {len(studies_after_replicates)} included, {len(excluded_by_replicates)} excluded")
    
    # Step 2: Check metadata completeness
    studies_after_metadata, excluded_by_metadata = check_metadata_completeness(studies_after_replicates)
    logger.info(f"After metadata check: {len(studies_after_metadata)} included, {len(excluded_by_metadata)} excluded")
    
    # Combine excluded studies
    all_excluded = excluded_by_replicates + excluded_by_metadata
    
    # Prepare output format: list of {species, exclusion_reason}
    # For included studies, we also list them with no exclusion reason
    output_list = []
    
    for study in studies_after_metadata:
        output_list.append({
            'species': study.get('species', 'Unknown'),
            'accession_id': study.get('accession_id', 'Unknown'),
            'exclusion_reason': None,
            'included': True
        })
    
    for excluded in all_excluded:
        output_list.append({
            'species': excluded['species'],
            'accession_id': excluded.get('accession_id', 'Unknown'),
            'exclusion_reason': excluded['exclusion_reason'],
            'included': False
        })
    
    # Sort by species name for consistency
    output_list.sort(key=lambda x: (x['species'], x['included']))
    
    # Write output
    output_record = {
        'generated_at': datetime.now().isoformat(),
        'source_manifest': str(input_manifest_path),
        'total_studies_processed': total_studies,
        'included_count': len(studies_after_metadata),
        'excluded_count': len(all_excluded),
        'studies': output_list
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_record, f, indent=2)
    
    logger.info(f"QC pipeline complete. Results written to: {output_path}")
    logger.info(f"Summary: {len(studies_after_metadata)} studies passed QC, {len(all_excluded)} excluded")
    
    return output_record

def main():
    """CLI entry point for QC pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run QC pipeline on RNA-seq studies')
    parser.add_argument('--input-manifest', type=Path, help='Path to input manifest file')
    parser.add_argument('--output', type=Path, help='Path to output post-QC species list')
    parser.add_argument('--min-replicates', type=int, default=2, help='Minimum required biological replicates')
    
    args = parser.parse_args()
    
    # Update global config if needed (for min_replicates)
    # Note: Currently min_replicates is hardcoded to 2 in check_replicates per spec
    
    try:
        result = run_qc_pipeline(
            input_manifest_path=args.input_manifest,
            output_path=args.output
        )
        
        print(f"QC Complete: {result['included_count']} included, {result['excluded_count']} excluded")
        return 0
        
    except Exception as e:
        logger.error(f"QC pipeline failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
