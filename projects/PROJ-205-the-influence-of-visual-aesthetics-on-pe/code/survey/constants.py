"""
Constants for the survey application.
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
# Defines the columns for data/raw/submissions.csv
METADATA_SCHEMA = [
    "participant_id",
    "age",
    "education",
    "timestamp",
    "hashed_ip",
    "browser_version",
    "session_duration"
]

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
