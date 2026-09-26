"""
Data cleaner module for validating and filtering study data.

Implements validation logic for age range, ASD diagnosis, outcomes,
and blinding status as per US1 requirements.
"""
import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from code.utils.logging import get_logger

logger = get_logger(__name__)

def validate_age(study: Dict[str, Any]) -> bool:
    """
    Validate that the study age range is within 6-12 years.
    
    Args:
        study: Study record dictionary
        
    Returns:
        True if age range is valid (6-12), False otherwise
    """
    age_range = study.get('age_range', {})
    if not age_range:
        return False
    
    min_age = age_range.get('min')
    max_age = age_range.get('max')
    
    if min_age is None or max_age is None:
        return False
    
    return 6 <= min_age <= 12 and 6 <= max_age <= 12

def validate_asd_diagnosis(study: Dict[str, Any]) -> bool:
    """
    Validate that the study diagnosis is ASD.
    
    Args:
        study: Study record dictionary
        
    Returns:
        True if diagnosis is ASD, False otherwise
    """
    diagnosis = study.get('diagnosis', '')
    return diagnosis == 'ASD'

def validate_outcomes(study: Dict[str, Any]) -> bool:
    """
    Validate that the study has social skill outcomes.
    
    Checks if any outcome contains 'social skill' (case-insensitive)
    or matches known validated measure patterns (SRS, ABC, SSIS, PEP).
    
    Args:
        study: Study record dictionary
        
    Returns:
        True if valid social skill outcomes found, False otherwise
    """
    outcomes = study.get('outcomes', [])
    if not outcomes:
        return False
    
    # Check for 'social skill' phrase (case-insensitive)
    for outcome in outcomes:
        if 'social skill' in outcome.lower():
            return True
    
    # Check for known validated measures
    known_measures = ['srs', 'abc', 'ssis', 'pep']
    for outcome in outcomes:
        outcome_lower = outcome.lower()
        for measure in known_measures:
            if measure in outcome_lower:
                return True
    
    return False

def validate_blinding_status(study: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and validate blinding status from study metadata.
    
    Identifies if a study reports blinded vs. unblinded raters.
    If both are reported, flags as 'mixed'.
    
    Args:
        study: Study record dictionary
        
    Returns:
        Dictionary with 'rater_type' and 'blinded_assessment_flag'
    """
    rater_type = study.get('rater_type', 'unknown')
    blinded_flag = study.get('blinded_assessment_flag')
    
    # Validate rater_type is one of the allowed values
    valid_rater_types = ['blinded', 'unblinded', 'mixed', 'unknown']
    if rater_type not in valid_rater_types:
        # Attempt to infer from blinded_flag if available
        if blinded_flag is True:
            rater_type = 'blinded'
        elif blinded_flag is False:
            rater_type = 'unblinded'
        else:
            rater_type = 'unknown'
    
    # Ensure blinded_assessment_flag is boolean
    if blinded_flag is None:
        if rater_type == 'blinded':
            blinded_flag = True
        elif rater_type == 'unblinded':
            blinded_flag = False
        else:
            blinded_flag = None  # Unknown
    
    return {
        'rater_type': rater_type,
        'blinded_assessment_flag': blinded_flag
    }

def log_excluded_study(study_id: str, reason: str, log_path: Path) -> None:
    """
    Log an excluded study to the excluded studies log file.
    
    Args:
        study_id: ID of the excluded study
        reason: Reason for exclusion
        log_path: Path to the exclusion log file
    """
    log_entry = {
        'study_id': study_id,
        'reason': reason,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to log file (JSONL format)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"Excluded study {study_id}: {reason}")

def filter_included_studies(studies: List[Dict[str, Any]], exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """
    Filter studies based on inclusion criteria.
    
    Includes studies that:
    - Have valid age range (6-12)
    - Have ASD diagnosis
    - Have valid social skill outcomes
    
    Excluded studies are logged to the exclusion log.
    
    Args:
        studies: List of study records
        exclusion_log_path: Path to the exclusion log file
        
    Returns:
        List of included studies
    """
    included = []
    
    for study in studies:
        study_id = study.get('id', 'unknown')
        
        # Validate age
        if not validate_age(study):
            log_excluded_study(study_id, 'INVALID_AGE_RANGE', exclusion_log_path)
            continue
        
        # Validate diagnosis
        if not validate_asd_diagnosis(study):
            log_excluded_study(study_id, 'INVALID_DIAGNOSIS', exclusion_log_path)
            continue
        
        # Validate outcomes
        if not validate_outcomes(study):
            log_excluded_study(study_id, 'INVALID_OUTCOME', exclusion_log_path)
            continue
        
        included.append(study)
    
    logger.info(f"Filtered studies: {len(included)} included, {len(studies) - len(included)} excluded")
    return included

def handle_multi_arm_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Handle multi-arm studies by splitting control groups proportionally.
    
    For studies with multiple treatment arms sharing a control group,
    the control group sample size is divided proportionally.
    
    Args:
        studies: List of study records
        
    Returns:
        List of processed study records
    """
    processed = []
    
    for study in studies:
        # Check if study has multiple arms
        arms = study.get('arms', [])
        if len(arms) <= 1:
            processed.append(study)
            continue
        
        # Find control group
        control_arm = None
        treatment_arms = []
        
        for arm in arms:
            arm_type = arm.get('type', '').lower()
            if 'control' in arm_type or 'placebo' in arm_type:
                control_arm = arm
            else:
                treatment_arms.append(arm)
        
        if control_arm and len(treatment_arms) > 1:
            # Split control group proportionally
            n_control = control_arm.get('n', 0)
            n_per_arm = n_control // len(treatment_arms)
            
            # Create separate records for each treatment arm
            for treatment_arm in treatment_arms:
                new_study = study.copy()
                new_study['arm'] = treatment_arm
                new_study['control_n'] = n_per_arm
                processed.append(new_study)
        else:
            processed.append(study)
    
    return processed

def clean_studies(studies: List[Dict[str, Any]], exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """
    Main cleaning function that applies all validation and processing steps.
    
    Args:
        studies: List of study records
        exclusion_log_path: Path to the exclusion log file
        
    Returns:
        List of cleaned and validated study records
    """
    # Filter by inclusion criteria
    included = filter_included_studies(studies, exclusion_log_path)
    
    # Handle multi-arm studies
    processed = handle_multi_arm_studies(included)
    
    # Add blinding status to each study
    for study in processed:
        blinding_info = validate_blinding_status(study)
        study['rater_type'] = blinding_info['rater_type']
        study['blinded_assessment_flag'] = blinding_info['blinded_assessment_flag']
    
    return processed

def main():
    """
    Main entry point for the data cleaner script.
    
    Reads raw study data, applies cleaning/validation, and writes
    cleaned data to CSV format.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean and validate study data')
    parser.add_argument('--input', type=str, required=True, 
                      help='Input directory containing raw study data')
    parser.add_argument('--output', type=str, required=True,
                      help='Output directory for cleaned data')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find raw data files
    raw_files = list(input_path.glob('*.json'))
    if not raw_files:
        logger.error(f"No JSON files found in {input_path}")
        return
    
    # Load all studies
    all_studies = []
    for raw_file in raw_files:
        with open(raw_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_studies.extend(data)
            elif isinstance(data, dict):
                all_studies.append(data)
    
    logger.info(f"Loaded {len(all_studies)} studies from {len(raw_files)} files")
    
    # Define exclusion log path
    exclusion_log_path = input_path / 'excluded_studies.log'
    
    # Clean studies
    cleaned_studies = clean_studies(all_studies, exclusion_log_path)
    
    # Write cleaned data to CSV
    output_file = output_path / 'cleaned_studies.csv'
    
    if cleaned_studies:
        df = pd.DataFrame(cleaned_studies)
        df.to_csv(output_file, index=False)
        logger.info(f"Wrote {len(cleaned_studies)} cleaned studies to {output_file}")
    else:
        # Create empty CSV with expected columns
        columns = ['id', 'title', 'registry', 'age_range', 'diagnosis', 
                  'outcomes', 'intervention_components', 'delivery_format',
                  'social_skill_domain', 'follow_up', 'abstract_text',
                  'rater_type', 'blinded_assessment_flag']
        df = pd.DataFrame(columns=columns)
        df.to_csv(output_file, index=False)
        logger.warning(f"No studies passed validation. Created empty CSV at {output_file}")

if __name__ == '__main__':
    main()
