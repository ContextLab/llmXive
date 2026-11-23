"""
Configuration Schema definitions for the Eco-Director.

Defines the expected structure and types for simulation parameters.
This file supports T004a (schema definition) and T004c (validation).
"""

PARAM_SCHEMA = {
    "locality": {
        "type": "dict",
        "keys": {
            "radius": {"type": "int", "min": 0}
        }
    },
    "memory": {
        "type": "dict",
        "keys": {
            "depth": {"type": "int", "min": 0}
        }
    },
    "non_linearity": {
        "type": "dict",
        "keys": {
            "type": {"type": "str", "options": ["linear", "sigmoid", "square"]}
        }
    },
    "grid_size": {"type": "int", "min": 1},
    "steps": {"type": "int", "min": 1}
}
