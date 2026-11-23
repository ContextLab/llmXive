"""
Scheduler Trace Schema Definitions.

Defines the structure and validation rules for the scheduler trace JSON file.
This file is used by T011 to initialize the schema and by T018 to log metrics.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Schema version for traceability
SCHEMA_VERSION = "1.0.0"

# Schema definition matching the requirements for T011 and T018
# This structure supports logging of scheduler decisions and metrics triggers
SCHEMA_DEFINITION = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Scheduler Trace",
    "description": "A log of scheduler decisions, metrics triggers, and state transitions.",
    "type": "object",
    "properties": {
        "schema_version": {
            "type": "string",
            "const": SCHEMA_VERSION,
            "description": "Version of the trace schema"
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp when the trace file was created"
        },
        "entries": {
            "type": "array",
            "description": "List of trace entries",
            "items": {
                "type": "object",
                "required": ["timestamp", "event_type", "data"],
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp of the event"
                    },
                    "event_type": {
                        "type": "string",
                        "enum": [
                            "scheduler_start",
                            "scheduler_step",
                            "metrics_triggered",
                            "fallback_triggered",
                            "batch_selected",
                            "error"
                        ],
                        "description": "Type of event being logged"
                    },
                    "data": {
                        "type": "object",
                        "description": "Event-specific payload",
                        "properties": {
                            "phase": {
                                "type": "string",
                                "description": "Current curriculum phase (e.g., 'exploration', 'exploitation')"
                            },
                            "target_coverage": {
                                "type": "number",
                                "description": "Target coverage ratio for the current step"
                            },
                            "selected_tasks": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of task IDs selected"
                            },
                            "metrics_triggered": {
                                "type": "array",
                                "description": "List of metrics that triggered the selection",
                                "items": {
                                    "type": "object",
                                    "required": ["variable_name", "transition_value"],
                                    "properties": {
                                        "variable_name": {
                                            "type": "string",
                                            "description": "Name of the state variable (e.g., 'dark_mode')"
                                        },
                                        "transition_value": {
                                            "type": ["string", "number", "boolean"],
                                            "description": "The value that triggered the transition"
                                        }
                                    }
                                }
                            },
                            "reason": {
                                "type": "string",
                                "description": "Explanation for the selection or error"
                            },
                            "entropy_score": {
                                "type": "number",
                                "description": "Entropy score of the selected batch"
                            }
                        }
                    }
                }
            }
        }
    },
    "required": ["schema_version", "created_at", "entries"]
}

def get_schema_description() -> str:
    """Returns a human-readable description of the schema."""
    return SCHEMA_DEFINITION["description"]

def validate_trace_entry(entry: Dict[str, Any]) -> bool:
    """
    Validates a single trace entry against the schema requirements.
    
    Args:
        entry: The dictionary entry to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ["timestamp", "event_type", "data"]
    if not all(key in entry for key in required_keys):
        return False
    
    valid_events = [
        "scheduler_start", "scheduler_step", "metrics_triggered",
        "fallback_triggered", "batch_selected", "error"
    ]
    if entry["event_type"] not in valid_events:
        return False
    
    if not isinstance(entry["data"], dict):
        return False
        
    return True

def get_initial_trace_content() -> Dict[str, Any]:
    """
    Generates the initial content for the scheduler_trace.json file.
    
    Returns:
        A dictionary representing the initial JSON structure.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": []
    }

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
