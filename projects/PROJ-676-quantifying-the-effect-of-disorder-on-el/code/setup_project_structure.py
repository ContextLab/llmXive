"""
Project Initialization Script for PROJ-676.

This script creates the required directory structure and initializes the
provenance schema file for the project.

Directories created:
- code/
- data/raw/
- data/processed/
- data/metadata/
- tests/
- docs/
- specs/

Files created:
- data/metadata/provenance.json (schema definition)
"""
import os
import json
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The task specifies paths relative to the project root:
    # projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/
    # We assume this script runs from that root.
    project_root = Path(".")
    
    # Define the required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "specs"
    ]
    
    created_dirs = []
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create the provenance schema file
    provenance_path = project_root / "data" / "metadata" / "provenance.json"
    
    if not provenance_path.exists():
        # Define the schema structure for provenance tracking
        # This aligns with T006b requirements for logging
        schema = {
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
        
        # Initialize with current timestamp
        from datetime import datetime
        schema["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        with open(provenance_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"Created provenance schema: {provenance_path}")
    else:
        print(f"Provenance schema already exists: {provenance_path}")
    
    print("\nProject structure initialization complete.")
    print(f"Created {len(created_dirs)} new directories.")

if __name__ == "__main__":
    main()
