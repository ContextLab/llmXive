"""
Quality Control module for filtering RNA-seq studies.

Implements logic to exclude studies with <2 biological replicates
or missing tissue metadata, and outputs a post-QC species list.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local config to ensure consistency
from src.utils.config import get_data_path

# Setup logging
logger = logging.getLogger(__name__)

def check_replicates(study_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Check if a study has at least 2 biological replicates.
    
    Args:
        study_data: Dictionary containing study metadata.
        
    Returns:
        Tuple of (is_valid, exclusion_reason).
        If valid, exclusion_reason is None.
    """
    replicates = study_data.get('replicates', 0)
    if replicates < 2:
        return False, f"Insufficient replicates: {replicates} (minimum 2 required)"
    return True, None

def check_metadata_completeness(study_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Check if a study has required tissue metadata.
    
    Args:
        study_data: Dictionary containing study metadata.
        
    Returns:
        Tuple of (is_valid, exclusion_reason).
        If valid, exclusion_reason is None.
    """
    tissue = study_data.get('tissue')
    if not tissue or tissue == 'unknown' or tissue == '':
        return False, "Missing or invalid tissue metadata"
    return True, None

def run_qc_pipeline(verification_report_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full QC pipeline on the metadata verification report.
    
    Args:
        verification_report_path: Path to the metadata verification report.
                                  If None, uses default path from config.
                                  
    Returns:
        Dictionary containing QC results and the post-QC species list.
    """
    if verification_report_path is None:
        data_path = get_data_path()
        verification_report_path = str(data_path / "processed" / "metadata_verification_report.json")
    
    input_path = Path(verification_report_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Verification report not found: {input_path}")
    
    # Load the verification report
    with open(input_path, 'r') as f:
        report = json.load(f)
    
    studies = report.get('studies', [])
    included_species = []
    excluded_studies = []
    
    for study in studies:
        accession_id = study.get('accession_id', 'unknown')
        species = study.get('species', 'unknown')
        tissue = study.get('tissue')
        replicates = study.get('replicates', 0)
        
        # Check replicates
        replicates_ok, replicate_reason = check_replicates(study)
        # Check tissue metadata
        tissue_ok, tissue_reason = check_metadata_completeness(study)
        
        if replicates_ok and tissue_ok:
            # Study passes QC
            included_species.append({
                'species': species,
                'accession_id': accession_id,
                'tissue': tissue,
                'replicates': replicates
            })
            logger.info(f"Study {accession_id} ({species}) PASSED QC")
        else:
            # Study fails QC
            reasons = []
            if not replicates_ok:
                reasons.append(replicate_reason)
            if not tissue_ok:
                reasons.append(tissue_reason)
            
            excluded_studies.append({
                'species': species,
                'accession_id': accession_id,
                'exclusion_reason': "; ".join(reasons)
            })
            logger.warning(f"Study {accession_id} ({species}) EXCLUDED: {', '.join(reasons)}")
    
    # Prepare output
    result = {
        'total_studies': len(studies),
        'included_count': len(included_species),
        'excluded_count': len(excluded_studies),
        'included_species': included_species,
        'excluded_studies': excluded_studies
    }
    
    return result

def save_post_qc_species_list(qc_results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the post-QC species list to a JSON file.
    
    Args:
        qc_results: Results dictionary from run_qc_pipeline.
        output_path: Path for the output file. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = str(data_path / "processed" / "post_qc_species_list.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Format output as list of species with exclusion reasons for excluded ones
    # and just species info for included ones
    species_list = []
    
    for item in qc_results.get('included_species', []):
        species_list.append({
            'species': item['species'],
            'accession_id': item['accession_id'],
            'status': 'included'
        })
    
    for item in qc_results.get('excluded_studies', []):
        species_list.append({
            'species': item['species'],
            'accession_id': item['accession_id'],
            'status': 'excluded',
            'exclusion_reason': item['exclusion_reason']
        })
    
    with open(output_file, 'w') as f:
        json.dump(species_list, f, indent=2)
    
    logger.info(f"Post-QC species list saved to {output_file}")
    return str(output_file)

def main():
    """
    Main entry point for the QC pipeline.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Run QC pipeline
        qc_results = run_qc_pipeline()
        
        # Log summary
        logger.info(f"QC Pipeline Complete: {qc_results['included_count']} included, "
                   f"{qc_results['excluded_count']} excluded out of {qc_results['total_studies']}")
        
        # Save post-QC species list
        output_path = save_post_qc_species_list(qc_results)
        
        return 0
        
    except Exception as e:
        logger.error(f"QC Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
