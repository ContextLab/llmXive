"""
Constants for the survey application.
"""

# Latin Square Matrix for stimulus presentation order
# Each row is a balanced permutation of the 4 conditions
LATIN_SQUARE_MATRIX = [
    ["Professional", "Minimalist", "Low-Quality", "Neutral"],
    ["Minimalist", "Low-Quality", "Neutral", "Professional"],
    ["Low-Quality", "Neutral", "Professional", "Minimalist"],
    ["Neutral", "Professional", "Minimalist", "Low-Quality"]
]

# Minimum number of stimuli required for valid submission
MIN_STIMULI = 4

# Demographic input schema
DEMOGRAPHIC_SCHEMA = {
    "age": {
        "type": "integer",
        "min_value": 18,
        "max_value": 120,
        "description": "Age in years"
    },
    "education": {
        "type": "string",
        "options": [
            "Less than High School",
            "High School Diploma",
            "Some College",
            "Associate Degree",
            "Bachelor's Degree",
            "Master's Degree",
            "Doctoral Degree"
        ],
        "description": "Highest level of education completed"
    }
}

# CSV export schema definition
CSV_SCHEMA = {
    "participant_id": {
        "type": "string",
        "description": "Unique UUID for the participant"
    },
    "stimulus_id": {
        "type": "string",
        "description": "Identifier for the stimulus condition"
    },
    "credibility": {
        "type": "integer",
        "min_value": 1,
        "max_value": 7,
        "description": "Credibility rating (1-7)"
    },
    "professionalism": {
        "type": "integer",
        "min_value": 1,
        "max_value": 7,
        "description": "Professionalism rating (1-7)"
    },
    "timestamp": {
        "type": "string",
        "description": "ISO format timestamp of submission"
    },
    "hashed_ip": {
        "type": "string",
        "description": "SHA-256 hash of participant IP address"
    },
    "age": {
        "type": "integer",
        "description": "Participant age"
    },
    "education": {
        "type": "string",
        "description": "Education level text"
    },
    "duplicate_flag": {
        "type": "string",
        "options": ["YES", "NO"],
        "description": "Flag indicating duplicate IP"
    },
    "session_status": {
        "type": "string",
        "options": ["active", "timeout"],
        "description": "Status of the session"
    },
    "submission_status": {
        "type": "string",
        "options": ["complete", "incomplete"],
        "description": "Status of the submission"
    }
}
