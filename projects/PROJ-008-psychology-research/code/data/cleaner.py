"""
Data cleaning and inclusion criteria filtering module.

This module implements the logic to filter studies based on:
1. Age range (must include 6-12 years)
2. ASD diagnosis presence
3. Social skill outcome presence
"""

import logging
from typing import List, Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

# Inclusion criteria constants
MIN_AGE = 6
MAX_AGE = 12
ASD_KEYWORDS = ["asd", "autism", "autism spectrum disorder", "autistic"]
SOCIAL_OUTCOME_KEYWORDS = [
    "social", "peer", "interaction", "communication", "relationship", 
    "social skills", "social responsiveness", "social communication"
]

def _check_age_overlap(age_min: Optional[int], age_max: Optional[int]) -> bool:
    """
    Check if the study's age range overlaps with [MIN_AGE, MAX_AGE].
    
    Args:
        age_min: Minimum age of study participants
        age_max: Maximum age of study participants
        
    Returns:
        True if there is an overlap, False otherwise
    """
    if age_min is None or age_max is None:
        return False
    
    # Check if the study's age range overlaps with our target range [6, 12]
    # Overlap exists if: study_min <= target_max AND study_max >= target_min
    return age_min <= MAX_AGE and age_max >= MIN_AGE

def _has_asd_diagnosis(diagnosis_list: List[str]) -> bool:
    """
    Check if the study includes ASD diagnosis.
    
    Args:
        diagnosis_list: List of diagnosis strings from the study
        
    Returns:
        True if ASD is present, False otherwise
    """
    if not diagnosis_list:
        return False
    
    # Normalize and check for ASD keywords
    diagnosis_lower = [d.lower() for d in diagnosis_list]
    for keyword in ASD_KEYWORDS:
        if any(keyword in d for d in diagnosis_lower):
            return True
    return False

def _has_social_outcome(outcome_list: List[str]) -> bool:
    """
    Check if the study includes a social skill outcome.
    
    Args:
        outcome_list: List of outcome strings from the study
        
    Returns:
        True if a social skill outcome is present, False otherwise
    """
    if not outcome_list:
        return False
    
    # Normalize and check for social outcome keywords
    outcome_lower = [o.lower() for o in outcome_list]
    for keyword in SOCIAL_OUTCOME_KEYWORDS:
        if any(keyword in o for o in outcome_lower):
            return True
    return False

def filter_included_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter studies based on inclusion criteria:
    1. Age range must overlap with [6, 12]
    2. Must include ASD diagnosis
    3. Must include a social skill outcome
    
    Args:
        studies: List of study dictionaries with keys:
            - study_id
            - age_min
            - age_max
            - diagnosis (list of strings)
            - outcomes (list of strings)
            - source
            
    Returns:
        List of studies that meet all inclusion criteria
    """
    included = []
    excluded_count = 0
    exclusion_reasons = {
        "age": 0,
        "diagnosis": 0,
        "outcome": 0,
        "missing_data": 0
    }

    for study in studies:
        study_id = study.get("study_id", "Unknown")
        
        # Check age
        age_min = study.get("age_min")
        age_max = study.get("age_max")
        
        if not _check_age_overlap(age_min, age_max):
            logger.debug(f"Excluding {study_id}: Age range {age_min}-{age_max} does not overlap with 6-12")
            exclusion_reasons["age"] += 1
            excluded_count += 1
            continue
        
        # Check diagnosis
        diagnosis = study.get("diagnosis", [])
        if not _has_asd_diagnosis(diagnosis):
            logger.debug(f"Excluding {study_id}: No ASD diagnosis found in {diagnosis}")
            exclusion_reasons["diagnosis"] += 1
            excluded_count += 1
            continue
        
        # Check outcome
        outcomes = study.get("outcomes", [])
        if not _has_social_outcome(outcomes):
            logger.debug(f"Excluding {study_id}: No social skill outcome found in {outcomes}")
            exclusion_reasons["outcome"] += 1
            excluded_count += 1
            continue
        
        # All criteria met
        included.append(study)
        logger.debug(f"Including {study_id}")

    logger.info(f"Filtered {len(studies)} studies: {len(included)} included, {excluded_count} excluded")
    logger.info(f"Exclusion breakdown: {exclusion_reasons}")
    
    return included