"""
Mock Data Generator for ClinicalTrials.gov/OSF Pipeline Testing.

Generates representative mock registry responses to test the data collection,
cleaning, and extraction pipeline logic without hitting live APIs.

This module creates `data/raw/mock_registry_response.json` containing:
1. A valid study (age 8, ASD, social outcome, abstract present).
2. A valid study with missing abstract (to trigger T020 exclusion logic).
3. An invalid study (age 15, out of 6-12 range).

The JSON structure matches the expected API response format for T016.
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Define the project root relative to this file (assuming code/data/mock_data_generator.py)
# The project root is two levels up from this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = DATA_RAW_DIR / "mock_registry_response.json"

# Ensure the directory exists
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Mock Data Records
# Structure matches the fields expected by contracts/cleaned_study.schema.yaml
# and the logic in code/data/collector.py, code/data/extractor.py, etc.

mock_records = [
    {
        # Record 1: Valid study
        "id": "NCT00000001",
        "title": "Mindfulness-Based Intervention for Social Skills in Children with ASD",
        "registry": "ClinicalTrials.gov",
        "age_range": {
            "min": 8,
            "max": 10
        },
        "diagnosis": "ASD",
        "outcomes": [
            "Social Responsiveness Scale (SRS)",
            "Peer Interaction Quality",
            "Emotional Regulation"
        ],
        "abstract": {
            "text": "This study investigates the effects of a mindfulness-based intervention on social skills in children aged 8-10 with Autism Spectrum Disorder (ASD). Participants engaged in breathing exercises and body scan techniques. Results showed significant improvement in communication and peer interaction domains."
        },
        "intervention_components": [],  # To be extracted by T017a
        "delivery_format": "caregiver-mediated",
        "social_skill_domain": "mixed",  # To be extracted by T017b
        "follow_up": "3 months",
        "rater_type": "blinded",
        "blinded_assessment_flag": True
    },
    {
        # Record 2: Valid study, NO abstract (Triggers T020 exclusion if metadata missing)
        # This record has valid metadata (age, diagnosis, outcomes) but no abstract text.
        "id": "NCT00000002",
        "title": "Child-Led Mindfulness for Emotional Regulation in ASD",
        "registry": "ClinicalTrials.gov",
        "age_range": {
            "min": 9,
            "max": 12
        },
        "diagnosis": "ASD",
        "outcomes": [
            "ABC Irritability Subscale",
            "SSIS Social Skills"
        ],
        "abstract": None,  # Explicitly missing abstract
        "intervention_components": [],
        "delivery_format": "child-led",
        "social_skill_domain": "emotional regulation",
        "follow_up": "6 months",
        "rater_type": "unblinded",
        "blinded_assessment_flag": False
    },
    {
        # Record 3: Invalid study (Age 15, out of 6-12 range)
        "id": "NCT00000003",
        "title": "Mindfulness for Adolescents with ASD",
        "registry": "ClinicalTrials.gov",
        "age_range": {
            "min": 15,
            "max": 17
        },
        "diagnosis": "ASD",
        "outcomes": [
            "Peer Interaction Assessment"
        ],
        "abstract": {
            "text": "Study focusing on adolescents aged 15-17. Mindfulness techniques applied to older population."
        },
        "intervention_components": [],
        "delivery_format": "mixed",
        "social_skill_domain": "peer interaction",
        "follow_up": "3 months",
        "rater_type": "blinded",
        "blinded_assessment_flag": True
    }
]

def generate_mock_data():
    """
    Generates the mock registry response JSON file.

    Creates `data/raw/mock_registry_response.json` with the predefined records.
    This file is used by `code/data/collector.py` in CI mode.
    """
    data = {
        "total_count": len(mock_records),
        "studies": mock_records,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": "mock_generator"
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Mock data generated successfully at: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    generate_mock_data()
