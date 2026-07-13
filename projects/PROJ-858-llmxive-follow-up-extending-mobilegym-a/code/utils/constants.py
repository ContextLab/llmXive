import os
import yaml
from typing import Any, Dict, List, Optional

# Path to the schema file relative to project root
SCHEMA_PATH = "contracts/coverage.schema.yaml"


def _load_schema() -> Optional[Dict[str, Any]]:
    """Load the coverage schema from the YAML file."""
    if not os.path.exists(SCHEMA_PATH):
        # Fallback schema if file missing (for robustness during dev)
        return {
            "dimensions": 5,
            "semantic_proxies": [
                "dark_mode",
                "unread_count",
                "location_permission",
                "night_mode",
                "high_battery_usage",
            ],
        }

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def get_coverage_schema() -> Dict[str, Any]:
    """Return the full coverage schema."""
    schema = _load_schema()
    if schema is None:
        # Default fallback
        return {
            "dimensions": 5,
            "semantic_proxies": [
                "dark_mode",
                "unread_count",
                "location_permission",
                "night_mode",
                "high_battery_usage",
            ],
        }
    return schema


def get_semantic_proxies() -> List[str]:
    """Return the list of semantic proxy names from the schema."""
    schema = get_coverage_schema()
    return schema.get("semantic_proxies", [])


def get_coverage_vector_dimensions() -> int:
    """Return the dimension count for the coverage vector."""
    schema = get_coverage_schema()
    # If explicit dimensions not set, derive from proxies list length
    if "dimensions" in schema:
        return schema["dimensions"]
    return len(get_semantic_proxies())


def get_coverage_vector_schema() -> Dict[str, Any]:
    """Return the schema definition for the vector structure."""
    return {
        "type": "array",
        "items": {"type": "integer", "enum": [0, 1]},
        "minItems": get_coverage_vector_dimensions(),
        "maxItems": get_coverage_vector_dimensions(),
    }


def validate_schema_integrity() -> bool:
    """Basic validation that schema and proxies are consistent."""
    schema = get_coverage_schema()
    proxies = get_semantic_proxies()
    dims = get_coverage_vector_dimensions()

    if not proxies:
        return False

    if "dimensions" in schema and schema["dimensions"] != len(proxies):
        return False

    return True
