"""
Schema definitions and validation for the global batch manifest.
"""
from typing import Any, Dict

REQUIRED_KEYS = {
    "global_batch_id",
    "generation_algorithm",
    "stratification_summary",
    "graphs"
}

STRATIFICATION_REQUIRED_KEYS = {
    "bins",
    "target_counts",
    "actual_counts",
    "quota_fulfilled"
}

def validate_manifest_schema(data: Dict[str, Any]) -> bool:
    """
    Validate the manifest against the required schema.
    Returns True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False

    # Check required top-level keys
    if not REQUIRED_KEYS.issubset(data.keys()):
        missing = REQUIRED_KEYS - set(data.keys())
        return False

    # Validate stratification_summary structure
    strat = data.get("stratification_summary", {})
    if not isinstance(strat, dict):
        return False

    if not STRATIFICATION_REQUIRED_KEYS.issubset(strat.keys()):
        return False

    # Validate graphs is a list
    if not isinstance(data.get("graphs"), list):
        return False

    return True

def get_schema_definition() -> Dict[str, Any]:
    """
    Return a JSON-schema-like definition for documentation.
    """
    return {
        "$schema": "manifest_global_batch_v1",
        "required": list(REQUIRED_KEYS),
        "properties": {
            "global_batch_id": {"type": "string"},
            "generation_algorithm": {"type": "array", "items": {"type": "string"}},
            "stratification_summary": {
                "type": "object",
                "required": list(STRATIFICATION_REQUIRED_KEYS),
                "properties": {
                    "bins": {"type": "array", "items": {"type": "number"}},
                    "target_counts": {"type": "object"},
                    "actual_counts": {"type": "object"},
                    "quota_fulfilled": {"type": "boolean"}
                }
            },
            "graphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "graph_id": {"type": "string"},
                        "clustering_coefficient": {"type": "number"},
                        "topology_type": {"type": "string"}
                    }
                }
            }
        }
    }
