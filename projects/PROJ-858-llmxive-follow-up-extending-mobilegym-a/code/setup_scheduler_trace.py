"""
Task T011: Initialize data/processed/scheduler_trace.json schema and directory structure.

This script ensures the data/processed/ directory exists and initializes
the scheduler_trace.json file with the required schema structure.
The schema is derived from the project's requirements for tracking
scheduler decisions, metrics, and state coverage transitions.
"""
import json
import os
import sys
from datetime import datetime, timezone

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.logging import get_task_logger, log_task_start, log_task_complete, log_error
from utils.constants import get_coverage_vector_dimensions, get_semantic_proxies

logger = get_task_logger(__name__)

PROCESSED_DIR = os.path.join(project_root, "data", "processed")
TRACE_FILE = os.path.join(PROCESSED_DIR, "scheduler_trace.json")

def ensure_processed_directory():
    """Create data/processed directory if it doesn't exist."""
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        logger.info(f"Created directory: {PROCESSED_DIR}")
    else:
        logger.info(f"Directory already exists: {PROCESSED_DIR}")

def initialize_trace_schema():
    """
    Initialize the scheduler_trace.json file with the required schema.
    
    The schema includes:
    - metadata: version, created_at, schema_version
    - entries: list of scheduler decision records
    - Each entry contains:
      - timestamp: ISO 8601 timestamp
      - session_id: unique session identifier
      - batch_id: unique batch identifier
      - phase: current curriculum phase (1 or 2)
      - selected_tasks: list of selected task parameters
      - coverage_vector: current binary state coverage vector
      - metrics_triggered: list of metrics that triggered selection
      - selection_reason: explanation of why tasks were chosen
      - fallback_used: boolean indicating if fallback logic was used
      - entropy_value: entropy of the selection (if applicable)
    """
    # Get dynamic values from constants
    coverage_dims = get_coverage_vector_dimensions()
    semantic_proxies = get_semantic_proxies()
    
    # Create initial schema structure
    trace_schema = {
        "metadata": {
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
            "description": "Scheduler trace for State-Guided Curriculum",
            "coverage_vector_dimensions": coverage_dims,
            "semantic_proxies": semantic_proxies
        },
        "entries": []
    }
    
    return trace_schema

def write_trace_file(trace_data):
    """Write the trace data to the JSON file."""
    with open(TRACE_FILE, 'w', encoding='utf-8') as f:
        json.dump(trace_data, f, indent=2, default=str)
    logger.info(f"Initialized scheduler trace file: {TRACE_FILE}")

def main():
    """Main entry point for T011."""
    log_task_start("T011", "Initialize scheduler_trace.json schema and directory")
    
    try:
        # Step 1: Ensure data/processed directory exists
        ensure_processed_directory()
        
        # Step 2: Initialize the schema
        trace_data = initialize_trace_schema()
        
        # Step 3: Write the file
        write_trace_file(trace_data)
        
        log_task_complete("T011", "scheduler_trace.json initialized successfully")
        print(f"SUCCESS: {TRACE_FILE} created with schema initialization.")
        return 0
        
    except Exception as e:
        log_error("T011", str(e))
        print(f"FAILED: Could not initialize scheduler_trace.json: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
