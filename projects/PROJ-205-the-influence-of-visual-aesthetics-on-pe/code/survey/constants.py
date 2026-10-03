"""
Constants for the survey application.
Defines schemas, stimuli lists, and experimental design parameters.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Stimuli List (Order matters for Latin Square generation)
# These correspond to the HTML files in code/stimuli/
STEIMULI_LIST = [
    "professional",
    "minimalist",
    "low_quality",
    "neutral"
]

# Metadata Schema for CSV export
# Defines the columns and validation rules for data/raw/submissions.csv
# This schema is used by code/survey/app.py to validate and export data.
METADATA_SCHEMA = {
    "participant_id": {
        "type": "string",
        "format": "UUID4",
        "description": "Unique identifier for the participant (UUID v4)",
        "required": True
    },
    "age": {
        "type": "integer",
        "min_value": 18,
        "max_value": 120,
        "description": "Participant age in years",
        "required": True
    },
    "education": {
        "type": "string",
        "options": [
            "Less than High School",
            "High School Graduate",
            "Some College",
            "Associate Degree",
            "Bachelor's Degree",
            "Master's Degree",
            "Doctoral Degree",
            "Professional Degree"
        ],
        "description": "Highest level of education completed",
        "required": True
    },
    "timestamp": {
        "type": "string",
        "format": "ISO8601",
        "description": "Submission timestamp in ISO 8601 format",
        "required": True
    },
    "hashed_ip": {
        "type": "string",
        "description": "PBKDF2-SHA256 hash of the participant's IP address",
        "required": True
    },
    "browser_version": {
        "type": "string",
        "description": "Extracted browser name and version from User-Agent",
        "required": True
    },
    "session_duration": {
        "type": "integer",
        "description": "Session duration in seconds (calculated from start to submit)",
        "required": True
    }
}

# Latin Square Sequences (Hardcoded for reproducibility)
# A balanced Latin Square for 4 items (A, B, C, D)
# Each stimulus appears exactly once in each position across the 4 sequences.
# Sequences are generated based on participant_id modulo 4.
LATIN_SQUARE_SEQUENCES = [
    ["professional", "minimalist", "low_quality", "neutral"],
    ["minimalist", "low_quality", "neutral", "professional"],
    ["low_quality", "neutral", "professional", "minimalist"],
    ["neutral", "professional", "minimalist", "low_quality"]
]
