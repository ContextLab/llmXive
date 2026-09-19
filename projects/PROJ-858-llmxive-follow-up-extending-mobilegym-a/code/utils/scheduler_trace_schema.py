"""
Scheduler Trace Schema Definition and Validation.

This module defines the JSON Schema for the scheduler trace file
and provides utilities to validate trace entries against it.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# The canonical JSON Schema for the scheduler trace
# This defines the structure of the file `data/processed/scheduler_trace.json`
SCHEMA_DEFINITION = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Scheduler Trace Schema",
    "description": "Schema for logging curriculum scheduler decisions and state transitions.",
    "type": "object",
    "required": ["schema_version", "created_at", "entries"],
    "properties": {
        "schema_version": {
            "type": "string",
            "const": "1.0.0",
            "description": "Version of the trace schema."
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of trace creation."
        },
        "entries": {
            "type": "array",
            "description": "List of scheduler decision events.",
            "items": {
                "type": "object",
                "required": [
                    "timestamp",
                    "phase",
                    "selected_tasks",
                    "metrics_triggered"
                ],
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp of the event."
                    },
                    "phase": {
                        "type": "string",
                        "enum": ["low_coverage", "moderate_success", "entropy_fallback", "deadlock_prevention"],
                        "description": "The curriculum phase that triggered this selection."
                    },
                    "target_success_rate": {
                        "type": ["number", "null"],
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Target success rate range or null if not applicable."
                    },
                    "current_coverage_ratio": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Current state coverage ratio."
                    },
                    "selected_tasks": {
                        "type": "array",
                        "description": "List of tasks selected in this batch.",
                        "items": {
                            "type": "object",
                            "required": ["task_id", "difficulty", "reason"],
                            "properties": {
                                "task_id": {"type": "string"},
                                "difficulty": {"type": "number"},
                                "reason": {"type": "string"}
                            }
                        }
                    },
                    "metrics_triggered": {
                        "type": "array",
                        "description": "Specific state variables that triggered the selection logic.",
                        "items": {
                            "type": "object",
                            "required": ["variable_name", "transition_value"],
                            "properties": {
                                "variable_name": {"type": "string"},
                                "transition_value": {"type": ["string", "number", "boolean"]}
                            }
                        }
                    }
                }
            }
        }
    }
}

def get_schema_description() -> str:
    """Return a human-readable description of the schema."""
    return "Schema for recording curriculum scheduler decisions, including phase, selected tasks, and triggering metrics."

def validate_trace_entry(entry: Dict[str, Any]) -> bool:
    """
    Validate a single trace entry against the schema requirements.
    
    Args:
        entry: The dictionary representing a single trace event.
        
    Returns:
        True if valid, False otherwise.
    """
    required_fields = ["timestamp", "phase", "selected_tasks", "metrics_triggered"]
    if not all(field in entry for field in required_fields):
        return False
    
    if entry["phase"] not in SCHEMA_DEFINITION["properties"]["entries"]["items"]["properties"]["phase"]["enum"]:
        return False
        
    return True
