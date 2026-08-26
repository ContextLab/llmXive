"""
Generate a JSON Schema based on the data model defined in data-model.md.
This script reads the specification and outputs a valid JSON Schema file.
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

def main():
    # Define paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    project_root = Path(__file__).parent.parent
    specs_dir = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c"
    contracts_dir = project_root / "contracts"
    
    # Ensure contracts directory exists
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = contracts_dir / "dataset.schema.json"
    
    logger.info(f"Generating JSON Schema for data model...")
    logger.info(f"Output path: {output_path}")

    # Construct the JSON Schema based on specs/001-evaluating-the-impact-of-llm-generated-c/data-model.md
    # The schema represents the union of all entities for validation purposes
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "LLM Generated Code Documentation Study Dataset",
        "description": "Schema for the combined dataset of Repositories, Participants, TaskSessions, and ClarificationQuestions.",
        "type": "object",
        "properties": {
            "repository": {
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Unique identifier (UUID)",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "GitHub URL"
                    },
                    "commit_hash": {
                        "type": "string",
                        "description": "Pinned commit SHA",
                        "pattern": "^[a-f0-9]{40}$"
                    },
                    "condition": {
                        "type": "string",
                        "enum": ["llm_docs", "human_docs", "no_docs"],
                        "description": "Experimental condition"
                    },
                    "loc": {
                        "type": "integer",
                        "description": "Lines of Code"
                    },
                    "cc": {
                        "type": "integer",
                        "description": "Cyclomatic Complexity"
                    },
                    "doc_quality_score": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Documentation quality score"
                    },
                    "generated_docs_path": {
                        "type": "string",
                        "description": "Relative path to generated Markdown"
                    }
                },
                "required": ["repo_id", "url", "commit_hash", "condition", "loc", "cc", "doc_quality_score"]
            },
            "participant": {
                "type": "object",
                "properties": {
                    "participant_id": {
                        "type": "string",
                        "description": "Anonymized UUID",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "condition": {
                        "type": "string",
                        "enum": ["llm_docs", "human_docs", "no_docs"],
                        "description": "Assigned experimental condition"
                    },
                    "demographics": {
                        "type": ["object", "null"],
                        "properties": {
                            "age": {"type": "integer"},
                            "experience_level": {"type": "string"}
                        },
                        "description": "Optional demographic data"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "completed", "dropped_out"],
                        "description": "Current status of the participant"
                    },
                    "consent_timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 consent timestamp"
                    }
                },
                "required": ["participant_id", "condition", "status", "consent_timestamp"]
            },
            "task_session": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique UUID",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "participant_id": {
                        "type": "string",
                        "description": "Foreign key to Participant"
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Foreign key to Repository"
                    },
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 start time"
                    },
                    "end_time": {
                        "type": ["string", "null"],
                        "format": "date-time",
                        "description": "ISO 8601 end time or null if incomplete"
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Calculated duration"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["completed", "failed", "stopped"],
                        "description": "Session status"
                    },
                    "max_time_flag": {
                        "type": "boolean",
                        "description": "True if stopped at 45m limit"
                    },
                    "helpfulness_rating": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Subjective rating 1-5"
                    }
                },
                "required": ["session_id", "participant_id", "repo_id", "start_time", "duration_seconds", "status", "max_time_flag"]
            },
            "clarification_question": {
                "type": "object",
                "properties": {
                    "question_id": {
                        "type": "string",
                        "description": "Unique UUID",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Foreign key to TaskSession"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp"
                    },
                    "content": {
                        "type": "string",
                        "description": "Text of the question"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["clarification", "moderator_action"],
                        "description": "Type of event"
                    }
                },
                "required": ["question_id", "session_id", "timestamp", "content", "type"]
            }
        },
        "required": ["repository", "participant", "task_session", "clarification_question"]
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        logger.info(f"Successfully wrote schema to {output_path}")
        
        # Verify the file is valid JSON by reading it back
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)
        logger.info("Verification: Output file is valid JSON.")
        
    except Exception as e:
        logger.error(f"Failed to write or verify schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()