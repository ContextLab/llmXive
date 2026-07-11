"""
Data cleaning and inclusion criteria filtering module.

This module implements the logic to filter studies based on:
1. Age range (must include 6-12 years)
2. ASD diagnosis presence
3. Social skill outcome presence
4. Multi-arm study handling (splitting control groups)
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

def _split_control_group(study: Dict[str, Any], n_arms: int) -> List[Dict[str, Any]]:
    """
    Split a multi-arm study's control group proportionally.
    
    When a study has multiple intervention arms sharing a single control group,
    we split the control group's N and variance proportionally to avoid
    double-counting in meta-analysis.
    
    Args:
        study: A study dictionary containing arm information
        n_arms: Total number of intervention arms in the study
        
    Returns:
        List of modified study dictionaries, one per intervention arm,
        with adjusted control group statistics.
        
    Reference: Borenstein et al. (2009) Introduction to Meta-Analysis,
               Chapter 17: Multiple treatment arms
    """
    arms = study.get("arms", [])
    if not arms:
        logger.warning(f"Study {study.get('study_id')} has no arms defined, skipping split")
        return [study]
    
    # Identify control and intervention arms
    intervention_arms = [a for a in arms if a.get("type", "").lower() == "intervention"]
    control_arms = [a for a in arms if a.get("type", "").lower() == "control"]
    
    if len(intervention_arms) == 0 or len(control_arms) == 0:
        # No splitting needed if only one type of arm or no control
        return [study]
    
    if len(intervention_arms) == 1:
        # Only one intervention arm, no splitting needed
        return [study]
    
    # Calculate split factor: 1 / number of intervention arms
    # This distributes the control group N and variance across comparisons
    split_factor = 1.0 / len(intervention_arms)
    
    split_studies = []
    
    for i, int_arm in enumerate(intervention_arms):
        # Create a copy of the study for this specific comparison
        split_study = study.copy()
        
        # Create a new arms list with only the current intervention arm
        # and a modified control arm
        new_arms = [int_arm.copy()]
        
        # Split each control arm proportionally
        for ctrl_arm in control_arms:
            split_ctrl = ctrl_arm.copy()
            
            # Split sample size
            if "n" in split_ctrl and split_ctrl["n"]:
                split_ctrl["n"] = int(round(split_ctrl["n"] * split_factor))
                if split_ctrl["n"] < 1:
                    split_ctrl["n"] = 1  # Ensure at least 1 participant
            
            # Split variance (standard deviation remains the same, 
            # but we adjust the standard error implicitly through N)
            # Note: For meta-analysis, we typically keep SD constant
            # and adjust N, which affects the standard error calculation
            
            new_arms.append(split_ctrl)
        
        split_study["arms"] = new_arms
        split_study["study_id"] = f"{study.get('study_id', '')}_arm{i+1}"
        
        split_studies.append(split_study)
        logger.debug(
            f"Split control group for {study.get('study_id')}: "
            f"created {len(intervention_arms)} comparisons with split factor {split_factor}"
        )
    
    return split_studies

def handle_multi_arm_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process multi-arm studies by splitting control groups.
    
    When a study has multiple intervention arms sharing a single control group,
    this function splits the control group proportionally to create independent
    comparisons, preventing double-counting in meta-analysis.
    
    Args:
        studies: List of study dictionaries that have already passed inclusion criteria
        
    Returns:
        List of studies with multi-arm studies split into separate comparisons
    """
    processed_studies = []
    multi_arm_count = 0
    
    for study in studies:
        study_id = study.get("study_id", "Unknown")
        arms = study.get("arms", [])
        
        if not arms:
            # No arms defined, keep as is
            processed_studies.append(study)
            continue
        
        # Count intervention arms
        intervention_arms = [a for a in arms if a.get("type", "").lower() == "intervention"]
        
        if len(intervention_arms) > 1:
            # Multi-arm study: split control group
            split_studies = _split_control_group(study, len(intervention_arms))
            processed_studies.extend(split_studies)
            multi_arm_count += 1
            logger.info(
                f"Split multi-arm study {study_id} into {len(split_studies)} comparisons"
            )
        else:
            # Single intervention arm, no splitting needed
            processed_studies.append(study)
    
    logger.info(
        f"Processed {len(studies)} studies: "
        f"{multi_arm_count} multi-arm studies split into {len(processed_studies)} total comparisons"
    )
    
    return processed_studies

def filter_included_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter studies based on inclusion criteria:
    1. Age range must overlap with [6, 12]
    2. Must include ASD diagnosis
    3. Must include a social skill outcome
    4. Handle multi-arm studies by splitting control groups
    
    Args:
        studies: List of study dictionaries with keys:
            - study_id
            - age_min
            - age_max
            - diagnosis (list of strings)
            - outcomes (list of strings)
            - arms (list of arm dictionaries with type, n, mean, sd, etc.)
            - source
            
    Returns:
        List of studies that meet all inclusion criteria, with multi-arm
        studies split into separate comparisons
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
    
    # Handle multi-arm studies
    if included:
        included = handle_multi_arm_studies(included)
    
    return included