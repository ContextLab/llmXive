"""
Data validation schemas for the gut microbiome and circadian rhythm project.

This module defines the expected data structures for the merged cohort dataset,
matching the contracts/dataset.schema.yaml specification.
"""
from typing import Dict, Any, List

# Schema definition for the merged cohort dataset
# Matches contracts/dataset.schema.yaml
COHORT_SCHEMA: Dict[str, Dict[str, Any]] = {
    "participant_id": {
        "type": str,
        "nullable": False,
        "description": "Unique participant identifier from American Gut Project/Open Humans"
    },
    "shannon": {
        "type": float,
        "nullable": False,
        "description": "Shannon diversity index (alpha diversity)"
    },
    "simpson": {
        "type": float,
        "nullable": False,
        "description": "Simpson diversity index (alpha diversity)"
    },
    "bray_curtis": {
        "type": float,
        "nullable": False,
        "description": "Bray-Curtis dissimilarity (beta diversity metric)"
    },
    "sleep_duration": {
        "type": float,
        "nullable": False,
        "description": "Average sleep duration in hours"
    },
    "sleep_quality": {
        "type": float,
        "nullable": False,
        "description": "Sleep quality score (0-100)"
    },
    "chronotype": {
        "type": str,
        "nullable": False,
        "description": "Chronotype classification (morning/evening/intermediate)"
    },
    "age": {
        "type": float,
        "nullable": True,
        "description": "Participant age in years"
    },
    "bmi": {
        "type": float,
        "nullable": True,
        "description": "Body Mass Index"
    },
    "antibiotic_history": {
        "type": str,
        "nullable": True,
        "description": "Antibiotic use history (yes/no/unknown)"
    },
    "diet_type": {
        "type": str,
        "nullable": True,
        "description": "Diet classification (e.g., omnivore, vegetarian, vegan)"
    },
    "medication_use": {
        "type": str,
        "nullable": True,
        "description": "Current medication use status"
    }
}

# Required columns for the merged cohort (non-nullable fields)
REQUIRED_COLUMNS: List[str] = [
    "participant_id",
    "shannon",
    "simpson",
    "bray_curtis",
    "sleep_duration",
    "sleep_quality",
    "chronotype"
]

# Optional columns that may be imputed or have missing values
OPTIONAL_COLUMNS: List[str] = [
    "age",
    "bmi",
    "antibiotic_history",
    "diet_type",
    "medication_use"
]

def get_schema() -> Dict[str, Dict[str, Any]]:
    """
    Returns the complete schema definition for the merged cohort.
    
    Returns:
        Dict[str, Dict[str, Any]]: Schema mapping column names to their
        type and constraint definitions.
    """
    return COHORT_SCHEMA

def get_required_columns() -> List[str]:
    """
    Returns the list of columns that must be present and non-null.
    
    Returns:
        List[str]: List of required column names.
    """
    return REQUIRED_COLUMNS.copy()

def get_optional_columns() -> List[str]:
    """
    Returns the list of columns that may contain missing values.
    
    Returns:
        List[str]: List of optional column names.
    """
    return OPTIONAL_COLUMNS.copy()