import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Schema definition for scheduler trace entries
# Extends existing schema to support metrics_triggered events with state transitions
SCHEMA_DEFINITION = {
    "type": "object",
    "required": ["timestamp", "event", "data"],
    "properties": {
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp with timezone"
        },
        "event": {
            "type": "string",
            "enum": [
                "phase1_selection",
                "phase2_selection",
                "fallback_entropy",
                "fallback_random",
                "metrics_triggered",
                "deadlock_prevention"
            ],
            "description": "Type of scheduler event"
        },
        "data": {
            "type": "object",
            "description": "Event-specific data payload"
        }
    }
}

# Specific schema for metrics_triggered event
METRICS_TRIGGERED_SCHEMA = {
    "type": "object",
    "required": ["triggered_metrics", "state_transitions"],
    "properties": {
        "triggered_metrics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of metric names that triggered the selection"
        },
        "state_transitions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["state_variable", "old_value", "new_value"],
                "properties": {
                    "state_variable": {"type": "string"},
                    "old_value": {"type": ["boolean", "integer", "string", "number"]},
                    "new_value": {"type": ["boolean", "integer", "string", "number"]}
                }
            },
            "description": "Specific state variable transitions that were detected"
        },
        "target_success_rate": {
            "type": "number",
            "description": "Target success rate for the selected tasks"
        },
        "selected_task_count": {
            "type": "integer",
            "description": "Number of tasks selected based on this trigger"
        }
    }
}

def validate_trace_entry(entry: Dict[str, Any]) -> bool:
    """
    Validate a trace entry against the schema.
    
    Args:
        entry: Dictionary containing the trace entry
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(entry, dict):
            return False
        
        required_fields = ["timestamp", "event", "data"]
        for field in required_fields:
            if field not in entry:
                return False
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return False
        
        # Validate event type
        if entry["event"] not in SCHEMA_DEFINITION["properties"]["event"]["enum"]:
            return False
        
        # Special validation for metrics_triggered
        if entry["event"] == "metrics_triggered":
            data = entry["data"]
            if not isinstance(data, dict):
                return False
            
            if "triggered_metrics" not in data or "state_transitions" not in data:
                return False
            
            if not isinstance(data["triggered_metrics"], list):
                return False
            
            if not isinstance(data["state_transitions"], list):
                return False
            
            for transition in data["state_transitions"]:
                if not isinstance(transition, dict):
                    return False
                if "state_variable" not in transition or "old_value" not in transition or "new_value" not in transition:
                    return False
        
        return True
    except Exception:
        return False

def get_schema_description(event_type: Optional[str] = None) -> str:
    """
    Get a human-readable description of the schema.
    
    Args:
        event_type: Optional specific event type to describe
        
    Returns:
        String description of the schema
    """
    desc = "Scheduler Trace Schema\n"
    desc += "=" * 50 + "\n\n"
    
    if event_type:
        if event_type == "metrics_triggered":
            desc += "Event: metrics_triggered\n"
            desc += "Purpose: Log when specific state metrics trigger task selection\n"
            desc += "Required fields in data:\n"
            desc += "  - triggered_metrics: List of metric names\n"
            desc += "  - state_transitions: List of {state_variable, old_value, new_value}\n"
            desc += "  - target_success_rate: (optional) Target success rate\n"
            desc += "  - selected_task_count: (optional) Number of tasks selected\n"
        else:
            desc += f"Event: {event_type}\n"
            desc += "See SCHEMA_DEFINITION for details\n"
    else:
        desc += "Base Schema:\n"
        desc += "  - timestamp: ISO 8601 datetime\n"
        desc += "  - event: One of the defined event types\n"
        desc += "  - data: Event-specific payload\n\n"
        desc += "Event Types:\n"
        for event in SCHEMA_DEFINITION["properties"]["event"]["enum"]:
            desc += f"  - {event}\n"
    
    return desc
