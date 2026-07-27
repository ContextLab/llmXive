"""
Setup script to create the required directory structure for the project.
Creates data/raw/, data/processed/, data/metadata/, and initializes the
provenance.json schema file.
"""
import os
import json
from pathlib import Path


def main():
    """Create the directory structure and initialize the provenance schema."""
    # Define the project root relative to the code directory
    # The script is expected to be run from the project root or code directory
    # We assume the current working directory is the project root
    project_root = Path.cwd()

    # Define required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/metadata",
    ]

    # Create directories
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Define the provenance schema
    provenance_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Project Provenance Log",
        "description": "Tracks data generation, processing steps, and execution metadata for reproducibility.",
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Unique identifier for the project",
                "const": "PROJ-676-quantifying-the-effect-of-disorder-on-el"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of log creation"
            },
            "entries": {
                "type": "array",
                "description": "List of provenance entries for data artifacts",
                "items": {
                    "type": "object",
                    "properties": {
                        "timestamp": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task that generated this entry"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["generated", "processed", "analyzed", "stored"]
                        },
                        "input_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relative paths to input files"
                        },
                        "output_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relative paths to output files"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Key parameters used in the operation"
                        },
                        "checksums": {
                            "type": "object",
                            "description": "SHA-256 checksums for output files"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["success", "failed", "partial"]
                        }
                    },
                    "required": ["timestamp", "action", "status"]
                }
            }
        },
        "required": ["project_id", "created_at", "entries"]
    }

    # Write the schema to data/metadata/provenance.json
    provenance_path = project_root / "data/metadata/provenance.json"
    with open(provenance_path, "w", encoding="utf-8") as f:
        json.dump(provenance_schema, f, indent=2)

    print(f"Initialized provenance schema at: {provenance_path}")
    print("Directory structure setup complete.")


if __name__ == "__main__":
    main()
