"""
Survey Constants Module.

Defines fixed constants for the survey application, including
metadata schema and Latin Square sequences.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Metadata Schema Definition (T069a)
# Explicitly defines columns for data export and analysis.
# browser_version and session_start_time are system-derived, not form inputs.
METADATA_SCHEMA = {
    "participant_id": {
        "type": "str",
        "description": "Unique UUID v4 for the participant",
        "required": True
    },
    "age": {
        "type": "int",
        "description": "Participant age in years",
        "required": True
    },
    "education": {
        "type": "str",
        "description": "Education level (categorical)",
        "required": True
    },
    "timestamp": {
        "type": "str",
        "description": "ISO8601 timestamp of submission",
        "required": True
    },
    "hashed_ip": {
        "type": "str",
        "description": "PBKDF2-SHA256 hash of participant IP",
        "required": True
    },
    "browser_version": {
        "type": "str",
        "description": "Extracted browser version from User-Agent header",
        "required": True
    },
    "session_start_time": {
        "type": "str",
        "description": "ISO8601 timestamp of session start (system-derived)",
        "required": True
    },
    "stimulus_id": {
        "type": "str",
        "description": "Identifier for the stimulus being rated (required for analysis)",
        "required": True
    }
}

# Latin Square Sequences (T028e)
# 4 conditions: professional, minimalist, low_quality, neutral
# Balanced design where each condition appears exactly once in each position
LATIN_SQUARE_SEQUENCES = [
    ['professional', 'minimalist', 'low_quality', 'neutral'],
    ['minimalist', 'neutral', 'professional', 'low_quality'],
    ['low_quality', 'professional', 'neutral', 'minimalist'],
    ['neutral', 'low_quality', 'minimalist', 'professional']
]

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES = 30

# Stimuli file mapping
STIMULI_FILES = {
    'professional': 'professional.html',
    'minimalist': 'minimalist.html',
    'low_quality': 'low_quality.html',
    'neutral': 'neutral.html'
}

# Likert scale options
LIKERT_OPTIONS = [1, 2, 3, 4, 5, 6, 7]
LIKERT_LABELS = {
    1: "Very Low",
    2: "Low",
    3: "Somewhat Low",
    4: "Neutral",
    5: "Somewhat High",
    6: "High",
    7: "Very High"
}
