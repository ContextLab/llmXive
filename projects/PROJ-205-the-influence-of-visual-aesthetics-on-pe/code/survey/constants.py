"""
Constants for the Survey Application.
Defines schemas, stimuli lists, and Latin Square sequences.
"""
import os
from pathlib import Path

# --------------------------------------------------------------------------
# Demographic Schema
# --------------------------------------------------------------------------
DEMOGRAPHIC_SCHEMA = {
    "age": {
        "type": "integer",
        "min_value": 18,
        "max_value": 120,
        "required": True
    },
    "education": {
        "type": "string",
        "options": [
            "Less than High School",
            "High School",
            "Some College",
            "Bachelor's Degree",
            "Master's Degree",
            "Doctoral Degree"
        ],
        "required": True
    }
}

# --------------------------------------------------------------------------
# Stimuli List
# --------------------------------------------------------------------------
# The stimuli files are expected to be in code/stimuli/
STIMULI_LIST = [
    "professional",
    "minimalist",
    "low_quality",
    "neutral"
]

# --------------------------------------------------------------------------
# Latin Square Sequences
# --------------------------------------------------------------------------
# A 4x4 Latin Square ensures each stimulus appears once in each position
# and each stimulus follows every other stimulus exactly once.
# Hardcoded valid sequences for 4 conditions (A, B, C, D)
LATIN_SQUARE_SEQUENCES = [
    ["professional", "minimalist", "low_quality", "neutral"],
    ["minimalist", "low_quality", "neutral", "professional"],
    ["low_quality", "neutral", "professional", "minimalist"],
    ["neutral", "professional", "minimalist", "low_quality"]
]

# --------------------------------------------------------------------------
# Rating Scale
# --------------------------------------------------------------------------
LIKERT_SCALE = {
    "min": 1,
    "max": 7,
    "description": "1 = Very Low, 7 = Very High"
}

# --------------------------------------------------------------------------
# Minimum Ratings Required
# --------------------------------------------------------------------------
MIN_RATINGS_REQUIRED = 4
