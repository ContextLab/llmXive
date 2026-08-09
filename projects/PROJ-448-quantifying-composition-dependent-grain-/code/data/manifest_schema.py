"""
Schema definition and path helpers for data_manifest.json.

This module provides:
- The JSON schema for data_manifest.json (T050)
- Helper functions to get schema and manifest paths
"""

import json
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_FILE = DATA_DIR / "manifest_schema.json"
MANIFEST_FILE = DATA_DIR / "data_manifest.json"


def get_schema_path() -> Path:
    """Return the path to the schema file."""
    return SCHEMA_FILE


def get_manifest_path() -> Path:
    """Return the path to the manifest file."""
    return MANIFEST_FILE


def get_schema() -> dict:
    """
    Return the JSON schema for data_manifest.json.

    This schema enforces FR-007 requirements:
    - All sources must have either doi or url
    - Required fields: source_type, source_id, description
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["version", "project_id", "sources"],
        "properties": {
            "version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+$"
            },
            "generated_at": {
                "type": "string",
                "format": "date-time"
            },
            "project_id": {
                "type": "string"
            },
            "description": {
                "type": "string"
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["source_type", "source_id", "description"],
                    "properties": {
                        "source_type": {
                            "type": "string",
                            "enum": ["thermodynamic_database", "experimental_data", "simulation_data"]
                        },
                        "source_id": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "doi": {
                            "type": ["string", "null"],
                            "pattern": "^10\\.\\d+/.*$"
                        },
                        "url": {
                            "type": ["string", "null"],
                            "format": "uri"
                        },
                        "checksum": {
                            "type": "string"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["verified", "pending", "failed"]
                        },
                        "notes": {
                            "type": "string"
                        }
                    },
                    "oneOf": [
                        {"required": ["doi"]},
                        {"required": ["url"]}
                    ]
                }
            }
        }
    }


def write_schema():
    """Write the schema to manifest_schema.json."""
    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_FILE, 'w', encoding='utf-8') as f:
        json.dump(get_schema(), f, indent=2)


if __name__ == "__main__":
    write_schema()
    print(f"Schema written to {SCHEMA_FILE}")