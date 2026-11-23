"""
Schema definitions for ExecutionRun and RegressionModel validation.
These schemas are used by the validator to ensure data integrity.
"""
from typing import Dict, Any, List, Optional

# Schema for ExecutionRun entity
# Fields: node_count (int), granularity (str enum), throughput (float), overhead_ratio (float)
EXECUTION_RUN_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ExecutionRun",
    "type": "object",
    "properties": {
        "node_count": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of physical nodes involved in the run"
        },
        "granularity": {
            "type": "string",
            "enum": ["fine", "medium", "coarse"],
            "description": "Task chunk size granularity setting"
        },
        "throughput": {
            "type": "number",
            "exclusiveMinimum": 0,
            "description": "Measured throughput in operations per second"
        },
        "overhead_ratio": {
            "type": "number",
            "minimum": 0,
            "description": "Ratio of coordination overhead to compute time"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the run"
        },
        "network_latency_ms": {
            "type": "number",
            "minimum": 0,
            "description": "Injected network latency in milliseconds",
            "optional": True
        }
    },
    "required": ["node_count", "granularity", "throughput", "overhead_ratio", "timestamp"],
    "additionalProperties": False
}

# Schema for RegressionModel entity
# Fields: coefficients (object), p_values (object), r_squared (float), residuals (array), theoretical_bound_deviation (float)
REGRESSION_MODEL_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "RegressionModel",
    "type": "object",
    "properties": {
        "model_type": {
            "type": "string",
            "enum": ["MLR", "GAM"],
            "description": "Type of regression model used"
        },
        "coefficients": {
            "type": "object",
            "description": "Mapping of feature names to coefficient values",
            "additionalProperties": {
                "type": "number"
            }
        },
        "p_values": {
            "type": "object",
            "description": "Mapping of feature names to p-values",
            "additionalProperties": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        },
        "r_squared": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Coefficient of determination"
        },
        "residuals": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "description": "List of residual values for each observation"
        },
        "theoretical_bound_deviation": {
            "type": "number",
            "description": "Deviation from the theoretical capacity bound (Ong & Motani)"
        },
        "interaction_terms": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of interaction terms included in the model"
        }
    },
    "required": [
        "model_type",
        "coefficients",
        "p_values",
        "r_squared",
        "residuals",
        "theoretical_bound_deviation"
    ],
    "additionalProperties": False
}
