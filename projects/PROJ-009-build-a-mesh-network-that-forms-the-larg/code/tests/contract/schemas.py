"""
YAML Schema definitions for ExecutionRun and RegressionModel validation.
These schemas define the expected structure for data contracts.
"""
from typing import Dict, Any

# Schema for ExecutionRun entity
# Matches the fields expected in orchestrator.models.ExecutionRun
EXECUTION_RUN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": [
        "run_id",
        "timestamp",
        "node_count",
        "granularity",
        "total_tasks",
        "completed_tasks",
        "failed_tasks",
        "start_time",
        "end_time",
        "status",
        "metrics"
    ],
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Unique identifier for the execution run"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of run creation"
        },
        "node_count": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of nodes involved in the run"
        },
        "granularity": {
            "type": "string",
            "enum": ["fine", "medium", "coarse"],
            "description": "Task chunk granularity setting"
        },
        "total_tasks": {
            "type": "integer",
            "minimum": 0,
            "description": "Total number of task chunks dispatched"
        },
        "completed_tasks": {
            "type": "integer",
            "minimum": 0,
            "description": "Number of successfully completed tasks"
        },
        "failed_tasks": {
            "type": "integer",
            "minimum": 0,
            "description": "Number of tasks that failed"
        },
        "start_time": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 start time of the run"
        },
        "end_time": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 end time of the run"
        },
        "status": {
            "type": "string",
            "enum": ["running", "completed", "failed", "timeout", "cancelled"],
            "description": "Current status of the execution run"
        },
        "network_conditions": {
            "type": "object",
            "required": ["latency_ms", "packet_loss_pct"],
            "properties": {
                "latency_ms": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Injected network latency in milliseconds"
                },
                "packet_loss_pct": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Packet loss percentage"
                }
            },
            "description": "Network conditions during the run"
        },
        "metrics": {
            "type": "object",
            "description": "Aggregated metrics for the run",
            "properties": {
                "throughput_tasks_per_sec": {
                    "type": "number",
                    "minimum": 0
                },
                "avg_cpu_utilization_pct": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100
                },
                "coordination_overhead_ratio": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Ratio of handshake time to compute time"
                },
                "heterogeneity_penalty": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Penalty score for node heterogeneity"
                }
            }
        }
    },
    "additionalProperties": False
}

# Schema for RegressionModel entity
# Matches the expected JSON output from analysis/regression.py
REGRESSION_MODEL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": [
        "model_type",
        "r_squared",
        "coefficients",
        "p_values",
        "feature_names",
        "n_observations",
        "theoretical_bound",
        "bound_violation_flag"
    ],
    "properties": {
        "model_type": {
            "type": "string",
            "enum": ["MLR", "GAM"],
            "description": "Type of regression model (Multiple Linear Regression or Generalized Additive Model)"
        },
        "r_squared": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Coefficient of determination"
        },
        "coefficients": {
            "type": "object",
            "description": "Mapping of feature names to coefficients",
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
        "feature_names": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of features used in the model"
        },
        "n_observations": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of observations used in fitting"
        },
        "theoretical_bound": {
            "type": "number",
            "minimum": 0,
            "description": "Ong & Motani theoretical capacity bound"
        },
        "bound_violation_flag": {
            "type": "boolean",
            "description": "True if empirical performance exceeds theoretical limit"
        },
        "interaction_terms": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of interaction terms included in the model"
        }
    },
    "additionalProperties": False
}
