import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.utils.config import get_data_path

# Configure logger
logger = logging.getLogger(__name__)

def check_replicates(study: Dict[str, Any], min_replicates: int = 2) -> Tuple[bool, Optional[str]]:
    """
    Check if a study has sufficient biological replicates.
    
    Args:
        study: Dictionary containing study metadata
        min_replicates: Minimum number of replicates required (default: 2)
        
    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    replicates = study.get('replicates')
    if replicates is None:
        return False, "Missing replicate count"
    
    if replicates < min_replicates:
        return False, f"Insufficient replicates: {replicates} < {min_replicates}"
    
    return True, None

def check_metadata_completeness(study: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Check if a study has all required metadata fields.
    
    Args:
        study: Dictionary containing study metadata
        
    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    required_fields = ['species', 'tissue', 'treatment']
    
    for field in required_fields:
        value = study.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False, f"Missing or empty metadata field: {field}"
    
    return True, None

def run_qc_pipeline(verification_report_path: Path) -> Dict[str, Any]:
    """
    Run the full QC pipeline on the metadata verification report.
    
    Args:
        verification_report_path: Path to the metadata verification report
        
    Returns:
        Dictionary containing QC results
    """
    if not verification_report_path.exists():
        raise FileNotFoundError(f"Verification report not found: {verification_report_path}")
    
    with open(verification_report_path, 'r') as f:
        report = json.load(f)
    
    included_species = []
    exclusions = []
    
    studies = report.get('studies', [])
    
    for study in studies:
        accession_id = study.get('accession_id')
        species = study.get('species')
        exclusion_reason = study.get('exclusion_reason')
        
        # If already excluded in verification, add to exclusions
        if exclusion_reason is not None:
            exclusions.append({
                'species': species,
                'reason': exclusion_reason
            })
            logger.warning(f"Excluding study {accession_id} ({species}): {exclusion_reason}")
            continue
        
        # Check replicates
        is_valid_replicates, replicate_reason = check_replicates(study)
        if not is_valid_replicates:
            exclusions.append({
                'species': species,
                'reason': replicate_reason
            })
            logger.warning(f"Excluding study {accession_id} ({species}): {replicate_reason}")
            continue
        
        # Check metadata completeness
        is_valid_metadata, metadata_reason = check_metadata_completeness(study)
        if not is_valid_metadata:
            exclusions.append({
                'species': species,
                'reason': metadata_reason
            })
            logger.warning(f"Excluding study {accession_id} ({species}): {metadata_reason}")
            continue
        
        # Study passed all QC checks
        included_species.append(species)
        logger.info(f"Including study {accession_id} ({species})")
    
    return {
        'included_species': included_species,
        'exclusions': exclusions
    }

def save_post_qc_species_list(qc_results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the post-QC species list to a JSON file.
    
    Args:
        qc_results: Dictionary containing QC results
        output_path: Path to save the output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(qc_results, f, indent=2)
    
    logger.info(f"Saved post-QC species list to {output_path}")

def main() -> int:
    """
    Main entry point for the QC pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Define paths
        data_dir = get_data_path()
        verification_report_path = data_dir / 'processed' / 'metadata_verification_report.json'
        output_path = data_dir / 'processed' / 'post_qc_species_list.json'
        
        logger.info(f"Reading verification report from {verification_report_path}")
        
        # Run QC pipeline
        qc_results = run_qc_pipeline(verification_report_path)
        
        # Save results
        save_post_qc_species_list(qc_results, output_path)
        
        # Log summary
        included_count = len(qc_results['included_species'])
        excluded_count = len(qc_results['exclusions'])
        logger.info(f"QC complete: {included_count} species included, {excluded_count} excluded")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in verification report: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during QC: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
