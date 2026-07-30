import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys
import json
import logging
from datetime import datetime

# Import config to get paths if needed, though we rely on relative paths here
# Import logger for consistent logging
try:
    from src.utils.logger import get_logger
except ImportError:
    # Fallback if logger not fully initialized in some contexts
    logging.basicConfig(level=logging.INFO)
    def get_logger(name): return logging.getLogger(name)

logger = get_logger(__name__)

def check_replicates(study_metadata: Dict, min_replicates: int = 2) -> Tuple[bool, str]:
    """
    Check if a study meets the minimum biological replicate requirement.

    Args:
        study_metadata: Dictionary containing study information including 'replicates'
        min_replicates: Minimum number of biological replicates required (default 2)

    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    replicates = study_metadata.get('replicates')
    if replicates is None:
        return False, "Missing replicates count in metadata"
    
    if replicates < min_replicates:
        return False, f"Insufficient biological replicates: {replicates} < {min_replicates}"
    
    return True, ""

def check_metadata_completeness(study_metadata: Dict, required_fields: List[str] = None) -> Tuple[bool, str]:
    """
    Check if all required metadata fields are present.

    Args:
        study_metadata: Dictionary containing study information
        required_fields: List of required field names (default: ['tissue'])

    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    if required_fields is None:
        required_fields = ['tissue']
    
    missing_fields = []
    for field in required_fields:
        value = study_metadata.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required metadata fields: {', '.join(missing_fields)}"
    
    return True, ""

def run_qc_pipeline(input_manifest_path: Path, output_path: Path, min_replicates: int = 2) -> Dict:
    """
    Run the full QC pipeline on studies listed in the input manifest.

    This function:
    1. Loads the input manifest (real or synthetic data)
    2. Checks each study for:
       - Minimum biological replicates (default >= 2)
       - Presence of required metadata (e.g., tissue)
    3. Excludes studies that fail any check
    4. Generates a post-QC species list
    5. Logs all exclusion reasons

    Args:
        input_manifest_path: Path to the input manifest file (JSON)
        output_path: Path where the post-QC species list will be written
        min_replicates: Minimum required biological replicates

    Returns:
        Dictionary containing QC results summary
    """
    logger.info(f"Starting QC pipeline with input manifest: {input_manifest_path}")
    
    # Load input manifest
    if not input_manifest_path.exists():
        logger.error(f"Input manifest not found: {input_manifest_path}")
        raise FileNotFoundError(f"Input manifest not found: {input_manifest_path}")
    
    with open(input_manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # Handle both single entry and list formats
    studies = manifest_data.get('studies', [manifest_data] if 'accession_id' in manifest_data else [])
    
    if not studies:
        logger.warning("No studies found in manifest")
        studies = []
    
    qc_results = []
    excluded_studies = []
    passed_studies = []
    
    for study in studies:
        accession_id = study.get('accession_id', 'unknown')
        species = study.get('species', 'unknown')
        tissue = study.get('tissue', None)
        replicates = study.get('replicates', None)
        
        logger.info(f"Processing study: {accession_id} ({species})")
        
        # Check replicates
        replicates_valid, replicates_reason = check_replicates(study, min_replicates)
        
        # Check metadata completeness (tissue is required)
        metadata_valid, metadata_reason = check_metadata_completeness(study, required_fields=['tissue'])
        
        # Determine overall validity
        if not replicates_valid or not metadata_valid:
            exclusion_reasons = []
            if not replicates_valid:
                exclusion_reasons.append(replicates_reason)
            if not metadata_valid:
                exclusion_reasons.append(metadata_reason)
            
            exclusion_reason = "; ".join(exclusion_reasons)
            
            excluded_studies.append({
                "species": species,
                "accession_id": accession_id,
                "exclusion_reason": exclusion_reason
            })
            
            logger.warning(f"Excluding study {accession_id}: {exclusion_reason}")
        else:
            passed_studies.append({
                "species": species,
                "accession_id": accession_id,
                "tissue": tissue,
                "replicates": replicates
            })
            
            logger.info(f"Study {accession_id} passed QC")
        
        # Record detailed result for this study
        qc_results.append({
            "accession_id": accession_id,
            "species": species,
            "tissue": tissue,
            "replicates": replicates,
            "replicates_valid": replicates_valid,
            "metadata_valid": metadata_valid,
            "excluded": not (replicates_valid and metadata_valid),
            "exclusion_reason": exclusion_reason if not (replicates_valid and metadata_valid) else None
        })
    
    # Generate post-QC species list (unique species that passed QC)
    passed_species = list(set([s["species"] for s in passed_studies if s["species"] != "unknown"]))
    
    # Prepare output in the required schema: { "species": <string>, "exclusion_reason": <string> }
    # Note: The schema in the task description seems to imply listing EXCLUDED species with reasons.
    # However, the task title says "post-QC species list", which usually means the INCLUDED ones.
    # Given the schema explicitly asks for "exclusion_reason", we will output the EXCLUDED studies
    # with their reasons, as that matches the schema structure provided in the task.
    # If the intent was to list included species, the schema would likely not have "exclusion_reason".
    # We will output the excluded list to match the schema exactly.
    
    post_qc_species_list = []
    for excluded in excluded_studies:
        post_qc_species_list.append({
            "species": excluded["species"],
            "exclusion_reason": excluded["exclusion_reason"]
        })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the post-QC species list (excluded studies with reasons)
    with open(output_path, 'w') as f:
        json.dump(post_qc_species_list, f, indent=2)
    
    logger.info(f"Post-QC species list (excluded studies) written to: {output_path}")
    logger.info(f"Total studies processed: {len(studies)}")
    logger.info(f"Studies passed QC: {len(passed_studies)}")
    logger.info(f"Studies excluded: {len(excluded_studies)}")
    
    return {
        "total_studies": len(studies),
        "passed_count": len(passed_studies),
        "excluded_count": len(excluded_studies),
        "passed_species": passed_species,
        "excluded_species_list": post_qc_species_list
    }

def main():
    """
    CLI entry point for the QC pipeline.
    
    Usage:
        python -m src.data.qc --input data/manifests/real_data_manifest.json --output data/processed/post_qc_species_list.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run QC pipeline on RNA-seq studies")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/manifests/real_data_manifest.json"),
        help="Path to input manifest file"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("data/processed/post_qc_species_list.json"),
        help="Path to output post-QC species list"
    )
    parser.add_argument(
        "--min-replicates", 
        type=int, 
        default=2,
        help="Minimum required biological replicates"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_qc_pipeline(
            input_manifest_path=args.input,
            output_path=args.output,
            min_replicates=args.min_replicates
        )
        
        print(json.dumps(results, indent=2))
        logger.info("QC pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"QC pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
