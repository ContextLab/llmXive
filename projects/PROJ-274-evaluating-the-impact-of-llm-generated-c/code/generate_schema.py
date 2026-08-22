"""
T030a: Generate a JSON Schema based on the data model and save it to data/raw/schema_temp.json.

This script constructs a JSON Schema reflecting the expected structure of the
participant logs and study data as defined in the project's data model.
It writes the schema to data/raw/schema_temp.json and validates that the file
is valid JSON upon completion.
"""
import json
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the JSON Schema based on the project's data model for participant logs
# This schema captures the structure expected from the experiment execution
# and cleaning pipeline.
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Participant Study Logs Schema",
    "description": "Schema for raw participant logs generated during the onboarding experiment.",
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "generated_at": {"type": "string", "format": "date-time"},
                "experiment_id": {"type": "string"}
            },
            "required": ["version", "generated_at", "experiment_id"]
        },
        "participants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "participant_id": {"type": "string"},
                    "condition": {"type": "string", "enum": ["llm", "human", "none"]},
                    "repo_id": {"type": "string"},
                    "start_time": {"type": "string", "format": "date-time"},
                    "end_time": {"type": "string", "format": "date-time"},
                    "status": {"type": "string", "enum": ["completed", "failed", "abandoned"]},
                    "intervention_status": {
                        "type": ["string", "null"],
                        "enum": [None, "stop_loss", "moderator_intervention"]
                    },
                    "task_duration_seconds": {"type": ["number", "null"]},
                    "max_time_limit": {"type": ["number", "null"]},
                    "clarification_questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {"type": "string", "format": "date-time"},
                                "content": {"type": "string"},
                                "type": {"type": "string", "enum": ["keyword", "moderator-tag"]}
                            },
                            "required": ["timestamp", "content", "type"]
                        }
                    },
                    "clarification_question_count": {"type": "integer", "minimum": 0},
                    "subjective_helpfulness_rating": {"type": ["number", "null"], "minimum": 1, "maximum": 5},
                    "helpfulness_survey_text": {"type": ["string", "null"]},
                    "checksum": {"type": "string"}
                },
                "required": [
                    "participant_id", "condition", "repo_id", "start_time",
                    "status", "clarification_questions", "clarification_question_count", "checksum"
                ]
            }
        }
    },
    "required": ["metadata", "participants"]
}

def main():
    logger.info("Starting T030a: JSON Schema Generation")
    
    # Determine output path relative to project root
    # Assuming this script is run from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "schema_temp.json"

    # Ensure the directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {output_dir}")

    try:
        # Write the schema to the file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(SCHEMA, f, indent=2)
        
        logger.info(f"Schema successfully written to {output_file}")

        # Verification: Assert file exists and is valid JSON
        if not output_file.exists():
            logger.error("Verification failed: Output file does not exist.")
            sys.exit(1)

        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_schema = json.load(f)
        
        if loaded_schema != SCHEMA:
            logger.error("Verification failed: Loaded schema does not match generated schema.")
            sys.exit(1)

        logger.info("Verification passed: File exists and is valid JSON.")
        print(f"SUCCESS: Schema generated at {output_file}")

    except json.JSONDecodeError as e:
        logger.error(f"Verification failed: Invalid JSON generated - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
