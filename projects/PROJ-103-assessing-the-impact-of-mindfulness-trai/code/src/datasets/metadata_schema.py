"""
JSON schema definition and enforcement for dataset metadata.

This module defines the structure of the metadata associated with each 
OpenNeuro dataset used in the mindfulness-DMN analysis, ensuring 
consistency in pre/post scan counts and ROI coordinates.
"""

import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterventionType(str, Enum):
    """Allowed types of interventions."""
    MINDFULNESS = "mindfulness"
    CONTROL = "control"
    OTHER = "other"

class ScanType(str, Enum):
    """Allowed types of fMRI scans."""
    RESTING_STATE = "resting_state"
    TASK = "task"

@dataclass
class DatasetMetadata:
    """
    Internal representation of dataset metadata.
    Matches the requirements for design verification (T018).
    """
    dataset_id: str
    pre_scan_count: int
    post_scan_count: int
    intervention_type: str
    scan_type: str
    version: str
    dmn_coordinates: Optional[Dict[str, Dict[str, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# JSON Schema matching the project's data model for dataset metadata
METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "dataset_id": {"type": "string", "minLength": 1},
        "pre_scan_count": {"type": "integer", "minimum": 0},
        "post_scan_count": {"type": "integer", "minimum": 0},
        "intervention_type": {
            "type": "string", 
            "enum": [e.value for e in InterventionType]
        },
        "scan_type": {
            "type": "string", 
            "enum": [e.value for e in ScanType]
        },
        "version": {"type": "string", "minLength": 1},
        "dmn_coordinates": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "z": {"type": "number"},
                },
                "required": ["x", "y", "z"],
                "additionalProperties": False,
            }
        },
    },
    "required": [
        "dataset_id", 
        "pre_scan_count", 
        "post_scan_count", 
        "intervention_type", 
        "scan_type", 
        "version"
    ],
    "additionalProperties": True,
}

def validate_schema(data: Dict[str, Any]) -> bool:
    """
    Validates a dictionary against the METADATA_SCHEMA.
    
    Returns:
        bool: True if valid, False otherwise.
    Raises:
        ValidationError: If validation fails (handled by return False).
    """
    try:
        validate(instance=data, schema=METADATA_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        return False

def create_sample_metadata() -> Dict[str, Any]:
    """Creates a valid sample metadata dictionary for testing."""
    return {
        "dataset_id": "ds000226",
        "pre_scan_count": 20,
        "post_scan_count": 20,
        "intervention_type": InterventionType.MINDFULNESS.value,
        "scan_type": ScanType.RESTING_STATE.value,
        "version": "1.0.0",
        "dmn_coordinates": {
            "PCC": {"x": 0.0, "y": -52.0, "z": 26.0},
            "mPFC": {"x": 0.0, "y": 52.0, "z": 0.0},
            "IPL": {"x": 46.0, "y": -66.0, "z": 36.0},
            "AngularGyrus": {"x": -46.0, "y": -66.0, "z": 36.0},
        }
    }

def validate_sample_json() -> bool:
    """Validates the sample metadata dictionary against the schema."""
    sample = create_sample_metadata()
    return validate_schema(sample)

def main():
    """Entry point to verify schema validity with a sample."""
    logger.info("Validating metadata schema with sample data...")
    if validate_sample_json():
        logger.info("Schema validation successful.")
        print("SUCCESS")
    else:
        logger.error("Schema validation failed.")
        print("FAILED")
        exit(1)

if __name__ == "__main__":
    main()
