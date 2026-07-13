"""
Initialize the scheduler trace file with schema documentation.

This script creates the initial empty trace file and writes a schema
reference to the project's data directory.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

# Import from sibling modules
from utils.scheduler_trace_schema import SCHEMA_DEFINITION, get_schema_description

def initialize_trace_file(output_path: Path) -> None:
    """
    Initialize the scheduler trace file.

    Creates an empty JSONL file and writes a schema header comment
    (as a JSON object) to document the expected format.

    Args:
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the file with an initial schema definition entry
    # This ensures the file exists and documents the expected format
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write a metadata entry describing the schema
        schema_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "schema_definition",
            "data": {
                "version": "1.0",
                "description": get_schema_description(),
                "schema": SCHEMA_DEFINITION
            }
        }
        f.write(json.dumps(schema_entry) + '\n')

    print(f"Initialized scheduler trace file at: {output_path}")
    print(f"Schema version: 1.0")
    print(f"Expected format: JSONL (one JSON object per line)")

def main() -> None:
    """Main entry point for the script."""
    project_root = Path(__file__).resolve().parent.parent.parent
    output_path = project_root / "data" / "processed" / "scheduler_trace.json"

    initialize_trace_file(output_path)

if __name__ == "__main__":
    main()
