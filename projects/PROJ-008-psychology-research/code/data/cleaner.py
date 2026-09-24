"""
Data cleaning module for US1.
Validates study records against inclusion criteria and cleans data.
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

# Inclusion criteria constants
VALID_AGE_MIN = 6
VALID_AGE_MAX = 12
VALID_DIAGNOSIS = 'ASD'
VALID_OUTCOMES = ['SRS-2', 'ABC', 'SSIS', 'PEP-3', 'Social Skills Rating System',
                  'Autism Behavior Checklist', 'Social Skills Improvement System',
                  'Preschool Evaluation Scale']

EXCLUDED_LOG_PATH = 'data/raw/excluded_studies.log'


def validate_age(age: Any) -> bool:
    """
    Validate age is within 6-12 range.

    Args:
        age: Age value (int or string)

    Returns:
        True if valid, False otherwise
    """
    try:
        age_int = int(age)
        return VALID_AGE_MIN <= age_int <= VALID_AGE_MAX
    except (ValueError, TypeError):
        return False


def validate_asd_diagnosis(diagnosis: Any) -> bool:
    """
    Validate diagnosis is ASD.

    Args:
        diagnosis: Diagnosis string

    Returns:
        True if ASD, False otherwise
    """
    if not diagnosis:
        return False
    return str(diagnosis).upper() == VALID_DIAGNOSIS.upper()


def validate_outcomes(outcomes: Any) -> bool:
    """
    Validate outcomes contain recognized social skill measures.

    Args:
        outcomes: List or string of outcomes

    Returns:
        True if at least one valid outcome found, False otherwise
    """
    if not outcomes:
        return False

    if isinstance(outcomes, str):
        outcomes_list = [outcomes]
    else:
        outcomes_list = outcomes

    for outcome in outcomes_list:
        if outcome in VALID_OUTCOMES:
            return True

    return False


def filter_included_studies(studies: List[Dict[str, Any]], log_path: str = EXCLUDED_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Filter studies based on inclusion criteria.

    Args:
        studies: List of study records
        log_path: Path to exclusion log file

    Returns:
        List of included studies
    """
    included = []
    excluded_count = 0

    for study in studies:
        study_id = study.get('id', 'unknown')
        reasons = []

        # Validate age
        if 'age' in study:
            age = study['age']
            if isinstance(age, dict):
                # Handle age_range object
                min_age = age.get('min', age.get('min_age'))
                max_age = age.get('max', age.get('max_age'))
                if min_age is not None and not validate_age(min_age):
                    reasons.append(f"Age min {min_age} out of range")
                if max_age is not None and not validate_age(max_age):
                    reasons.append(f"Age max {max_age} out of range")
            elif not validate_age(age):
                reasons.append(f"Age {age} out of range")

        # Validate diagnosis
        diagnosis = study.get('diagnosis')
        if not validate_asd_diagnosis(diagnosis):
            reasons.append(f"Diagnosis {diagnosis} not ASD")

        # Validate outcomes
        outcomes = study.get('outcomes')
        if not validate_outcomes(outcomes):
            reasons.append(f"No valid social skill outcomes")

        # Check for abstract if metadata insufficient
        if not study.get('abstract_text') and not study.get('abstract'):
            # Check if we have enough metadata
            if 'age' not in study or not study.get('diagnosis'):
                reasons.append("INSUFFICIENT_METADATA_NO_ABSTRACT")

        if reasons:
            excluded_count += 1
            for reason in reasons:
                log_excluded_study(study_id, reason, log_path)
            logger.warning(f"Excluded study {study_id}: {reasons}")
        else:
            included.append(study)

    logger.info(f"Filtered {excluded_count} studies, {len(included)} included")
    return included


def handle_multi_arm_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Handle multi-arm studies by splitting control groups proportionally.

    Args:
        studies: List of study records

    Returns:
        List of processed study records
    """
    processed = []

    for study in studies:
        # Check if this is a multi-arm study
        arms = study.get('arms', [])
        if len(arms) > 2:
            # Multi-arm study found
            logger.info(f"Processing multi-arm study: {study.get('id')}")
            # Logic to split control group would go here
            # For now, we pass through with a flag
            study['is_multi_arm'] = True
        else:
            study['is_multi_arm'] = False

        processed.append(study)

    return processed


def clean_studies(studies: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Main cleaning pipeline: filter and process studies.

    Args:
        studies: List of raw study records

    Returns:
        DataFrame of cleaned studies
    """
    # Filter included studies
    included = filter_included_studies(studies)

    # Handle multi-arm studies
    processed = handle_multi_arm_studies(included)

    # Convert to DataFrame
    df = pd.DataFrame(processed)

    # Ensure required columns exist
    required_cols = ['id', 'title', 'registry', 'age_range', 'diagnosis',
                    'outcomes', 'intervention_components', 'delivery_format',
                    'social_skill_domain', 'rater_type', 'blinded_assessment_flag']

    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    return df


def log_excluded_study(study_id: str, reason: str, log_path: str = EXCLUDED_LOG_PATH):
    """
    Log an excluded study to the exclusion log.

    Args:
        study_id: Study identifier
        reason: Reason for exclusion
        log_path: Path to log file
    """
    log_entry = {
        'study_id': study_id,
        'reason': reason,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    log_path_obj = Path(log_path)
    log_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

    logger.info(f"Excluded study {study_id}: {reason}")


def main():
    """Main entry point for cleaner module."""
    logger.info("Cleaner module loaded successfully")
    pass


if __name__ == '__main__':
    main()
