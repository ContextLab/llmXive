"""
Initialize the scheduler trace file with the correct schema.

This script creates `data/processed/scheduler_trace.json` containing
the schema definition and an empty entries array, ready for logging.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from utils.scheduler_trace_schema import SCHEMA_DEFINITION

def initialize_trace_file(output_path: Path) -> None:
    """
    Initialize the trace file with the schema and empty entries.
    
    Args:
        output_path: The path where the trace file should be written.
    """
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    trace_data = {
        "schema_version": SCHEMA_DEFINITION["properties"]["schema_version"]["const"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": []
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trace_data, f, indent=2, ensure_ascii=False)
    
    print(f"Initialized scheduler trace schema at: {output_path}")

def main():
    """Main entry point."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    output_path = root_dir / "data" / "processed" / "scheduler_trace.json"
    initialize_trace_file(output_path)

if __name__ == "__main__":
    main()
