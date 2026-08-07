"""
Schema definitions for ExecutionRun and RegressionModel validation.
These schemas are used by the contract validator to ensure data integrity.
"""
from typing import Dict, Any, List, Optional

# Schema for ExecutionRun entity
# Fields: node_count, granularity, throughput, overhead_ratio
EXECUTION_RUN_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Unique identifier for the execution run"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the run"
        },
        "node_count": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of physical nodes involved in the run"
        },
        "granularity": {
            "type": "string",
            "enum": ["fine", "medium", "coarse"],
            "description": "Task chunk granularity level"
        },
        "throughput": {
            "type": "number",
            "minimum": 0,
            "description": "Operations per second achieved"
        },
        "overhead_ratio": {
            "type": "number",
            "minimum": 0,
            "description": "Ratio of coordination overhead to compute time"
        },
        "latency_injected_ms": {
            "type": "number",
            "minimum": 0,
            "description": "Injected network latency in milliseconds"
        },
        "packet_loss_rate": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Observed packet loss rate (0.0 to 1.0)"
        }
    },
    "required": ["node_count", "granularity", "throughput", "overhead_ratio"]
}

# Schema for RegressionModel entity
# Fields: coefficients, p_values, r_squared
REGRESSION_MODEL_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "model_id": {
            "type": "string",
            "description": "Unique identifier for the model"
        },
        "model_type": {
            "type": "string",
            "enum": ["MLR", "GAM"],
            "description": "Type of regression model (Multiple Linear Regression or Generalized Additive Model)"
        },
        "formula": {
            "type": "string",
            "description": "Statistical formula used for the model"
        },
        "coefficients": {
            "type": "object",
            "additionalProperties": {
                "type": "number"
            },
            "description": "Mapping of feature names to coefficient values"
        },
        "p_values": {
            "type": "object",
            "additionalProperties": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            },
            "description": "Mapping of feature names to p-values"
        },
        "r_squared": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Coefficient of determination"
        },
        "aic": {
            "type": "number",
            "description": "Akaike Information Criterion"
        },
        "bic": {
            "type": "number",
            "description": "Bayesian Information Criterion"
        },
        "interaction_terms": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of interaction term names included in the model"
        }
    },
    "required": ["coefficients", "p_values", "r_squared"]
}
