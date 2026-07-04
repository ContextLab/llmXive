"""
Configuration file for Gut Microbiome-Cognitive Correlation Study.

Contains:
- Project paths
- Random seeds
- UK Biobank field IDs
- Constants for preprocessing and analysis
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed for reproducibility
RANDOM_SEED = 42

# UK Biobank Field IDs
# Microbiome-related fields (16S rRNA sequencing)
UKB_FIELD_IDS = {
    # Participant identifier
    "participant_id": "eid",
    
    # Microbiome data fields
    "microbiome_sample_date": "20400",  # Sample collection date
    "microbiome_counts": "20401",        # Raw count data (will be expanded in actual data)
    
    # Cognitive assessment fields
    "cognitive_score": "20002",          # Primary cognitive assessment score
    "cognitive_test_date": "20003",      # Test date
    
    # Confounder fields
    "age": "21003",                      # Age at assessment
    "sex": "31",                         # Sex (0: Female, 1: Male)
    "bmi": "21001",                      # Body Mass Index
    "diet_quality": "1338",              # Diet quality score
    "physical_activity": "900",          # Physical activity level
    "medication_antibiotics": "6153",    # Antibiotic medication records (ATC code J01)
    
    # Additional confounders
    "smoking_status": "20116",           # Smoking status
    "alcohol_intake": "1558",            # Alcohol intake frequency
    "education_years": "3532",           # Years of education
}

# Data paths
PATHS: Dict[str, Path] = {
    # Raw data (downloaded from UK Biobank)
    "raw_microbiome": PROJECT_ROOT / "data" / "raw" / "microbiome_16s.parquet",
    "raw_cognitive": PROJECT_ROOT / "data" / "raw" / "cognitive_assessments.parquet",
    "raw_medication": PROJECT_ROOT / "data" / "raw" / "medications.parquet",
    
    # Processed data
    "filtered_microbiome": PROJECT_ROOT / "data" / "processed" / "filtered_microbiome.parquet",
    "filtered_cognitive": PROJECT_ROOT / "data" / "processed" / "filtered_cognitive.parquet",
    "zero_replaced_counts": PROJECT_ROOT / "data" / "processed" / "zero_replaced_counts.parquet",
    "ilr_coordinates": PROJECT_ROOT / "data" / "processed" / "ilr_coordinates.parquet",
    "cohort_with_age_groups": PROJECT_ROOT / "data" / "processed" / "cohort_with_age_groups.parquet",
    
    # Results and reports
    "retention_log": PROJECT_ROOT / "data" / "processed" / "cohort_retention_log.json",
    "age_group_check": PROJECT_ROOT / "results" / "validation" / "age_group_check.json",
    "power_report": PROJECT_ROOT / "results" / "power" / "power_report.md",
    "citation_report": PROJECT_ROOT / "results" / "validation" / "instrument_citation_report.md",
    "main_effects": PROJECT_ROOT / "results" / "associations" / "main_effects.parquet",
    "interaction_effects": PROJECT_ROOT / "results" / "associations" / "interaction_effects.parquet",
    "over_control_report": PROJECT_ROOT / "results" / "sensitivity" / "over_control_report.json",
    "threshold_sweep_report": PROJECT_ROOT / "results" / "sensitivity" / "threshold_sweep_report.json",
    "manhattan_plot": PROJECT_ROOT / "results" / "plots" / "manhattan_plot.png",
}

# Preprocessing constants
ANTIBIOTIC_EXCLUSION_WINDOW_DAYS = 90  # Exclude antibiotic use within 90 days
MIN_GENUS_COUNT = 10                   # Minimum genus count for inclusion
MAX_MISSINGNESS_THRESHOLD = 0.2        # Maximum allowed missingness (20%)

# Analysis constants
ALPHA_LEVEL = 0.05                     # Significance level for hypothesis testing
BHC_METHOD = "fdr_bh"                  # Benjamini-Hochberg correction method

# Age group cutoffs (for T015.5)
AGE_GROUP_YOUNG = 50
AGE_GROUP_OLD = 70

# Memory constraints
MAX_MEMORY_GB = 7.0
BATCH_SIZE = 100000

# Logging level
LOG_LEVEL = "INFO"

# Helper function to get path by key
def get_path(key: str) -> Path:
    """Get a path from the PATHS dictionary."""
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in PATHS")
    return PATHS[key]

# Helper function to ensure directories exist
def ensure_directories():
    """Create all required directories if they don't exist."""
    for path in PATHS.values():
        path.parent.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()
