"""
Task T020b: Generate and Validate Data Model.

Generates `specs/001-nostalgia-cognitive-fle/data-model.yaml` based on Spec Section 5
(Entities: Participant, Stimulus, Metric) and validates consistency.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
SPECS_DIR = PROJECT_ROOT / "specs" / "001-nostalgia-cognitive-fle"
DATA_MODEL_PATH = SPECS_DIR / "data-model.yaml"

# Ensure specs directory exists
SPECS_DIR.mkdir(parents=True, exist_ok=True)

def generate_data_model() -> Dict[str, Any]:
    """
    Constructs the data model dictionary based on Spec Section 5 requirements.
    
    Entities:
    - Participant: Demographics and screening (Age, MMSE optional)
    - Stimulus: Stimulus metadata (Type, ID, Checksum)
    - Metric: Cognitive flexibility scores (WCST metrics)
    """
    data_model = {
        "version": "1.0.0",
        "description": "Data model for The Impact of Nostalgia on Cognitive Flexibility in Aging Adults",
        "entities": {
            "Participant": {
                "description": "Demographic and screening information for study participants.",
                "fields": [
                    {
                        "name": "participant_id",
                        "type": "string",
                        "required": True,
                        "description": "Unique identifier for the participant."
                    },
                    {
                        "name": "age",
                        "type": "integer",
                        "required": True,
                        "description": "Age of the participant in years. Must be >= 65 for inclusion."
                    },
                    {
                        "name": "gender",
                        "type": "string",
                        "required": False,
                        "description": "Gender of the participant."
                    },
                    {
                        "name": "education_years",
                        "type": "integer",
                        "required": False,
                        "description": "Years of formal education."
                    },
                    {
                        "name": "MMSE",
                        "type": "integer",
                        "required": False,
                        "description": "Mini-Mental State Examination score. Optional. Used for cognitive impairment screening (cutoff >= 24)."
                    }
                ]
            },
            "Stimulus": {
                "description": "Metadata regarding the stimuli presented (Nostalgia vs Control).",
                "fields": [
                    {
                        "name": "stimulus_id",
                        "type": "string",
                        "required": True,
                        "description": "Unique identifier for the stimulus item."
                    },
                    {
                        "name": "stimulus_type",
                        "type": "string",
                        "required": True,
                        "description": "Type of stimulus: 'nostalgia' or 'control'."
                    },
                    {
                        "name": "file_path",
                        "type": "string",
                        "required": True,
                        "description": "Relative path to the stimulus file."
                    },
                    {
                        "name": "checksum_sha256",
                        "type": "string",
                        "required": True,
                        "description": "SHA-256 checksum of the stimulus file for integrity verification."
                    }
                ]
            },
            "Metric": {
                "description": "Cognitive flexibility metrics derived from the Wisconsin Card Sorting Test (WCST).",
                "fields": [
                    {
                        "name": "participant_id",
                        "type": "string",
                        "required": True,
                        "description": "Foreign key linking to Participant."
                    },
                    {
                        "name": "stimulus_id",
                        "type": "string",
                        "required": True,
                        "description": "Foreign key linking to Stimulus."
                    },
                    {
                        "name": "perseverative_errors",
                        "type": "integer",
                        "required": True,
                        "description": "Number of perseverative errors made during the test."
                    },
                    {
                        "name": "categories_completed",
                        "type": "integer",
                        "required": True,
                        "description": "Number of categories successfully completed."
                    },
                    {
                        "name": "total_trials",
                        "type": "integer",
                        "required": False,
                        "description": "Total number of trials attempted."
                    }
                ]
            }
        },
        "constraints": {
            "age_inclusion": "age >= 65",
            "mmse_inclusion": "MMSE >= 24 (if MMSE data is present)",
            "stimulus_types": ["nostalgia", "control"]
        }
    }
    return data_model

def validate_against_spec(data_model: Dict[str, Any]) -> bool:
    """
    Validates the generated data model against Spec Section 5 requirements.
    
    Checks:
    1. Entities (Participant, Stimulus, Metric) exist.
    2. Specific required fields (age, stimulus_type, perseverative_errors, etc.) exist.
    3. MMSE is optional.
    """
    required_entities = ["Participant", "Stimulus", "Metric"]
    if not all(e in data_model["entities"] for e in required_entities):
        logger.error("Validation Failed: Missing required entities.")
        return False

    # Check Participant fields
    participant_fields = {f["name"] for f in data_model["entities"]["Participant"]["fields"]}
    if "age" not in participant_fields:
        logger.error("Validation Failed: 'age' missing in Participant.")
        return False
    if "MMSE" not in participant_fields:
        logger.error("Validation Failed: 'MMSE' missing in Participant (should be optional).")
        return False
    
    # Check Stimulus fields
    stimulus_fields = {f["name"] for f in data_model["entities"]["Stimulus"]["fields"]}
    if "stimulus_type" not in stimulus_fields:
        logger.error("Validation Failed: 'stimulus_type' missing in Stimulus.")
        return False

    # Check Metric fields
    metric_fields = {f["name"] for f in data_model["entities"]["Metric"]["fields"]}
    if "perseverative_errors" not in metric_fields:
        logger.error("Validation Failed: 'perseverative_errors' missing in Metric.")
        return False
    if "categories_completed" not in metric_fields:
        logger.error("Validation Failed: 'categories_completed' missing in Metric.")
        return False

    logger.info("Validation Successful: Data model matches Spec Section 5 requirements.")
    return True

def main():
    logger.info(f"Generating data model to: {DATA_MODEL_PATH}")
    
    # Generate
    model = generate_data_model()
    
    # Validate
    if not validate_against_spec(model):
        logger.error("Data model validation failed. Aborting write.")
        return 1
    
    # Write
    try:
        with open(DATA_MODEL_PATH, 'w') as f:
            yaml.dump(model, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully wrote data model to {DATA_MODEL_PATH}")
    except Exception as e:
        logger.error(f"Failed to write data model: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
