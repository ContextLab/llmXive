"""
Contracts module containing JSON schemas for data validation and documentation.

These schemas define the expected structure for:
- SimulationConfig: Input parameters for simulation runs
- ErrorMetric: Output metrics from simulation iterations
- PValueDistribution: Aggregated p-value results
"""

import json
import os
from pathlib import Path

def load_schema(schema_name: str) -> dict:
    """Load a JSON schema by name from the contracts directory."""
    schema_path = Path(__file__).parent / f"{schema_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Pre-load schemas for convenience
SIMULATION_CONFIG_SCHEMA = load_schema("simulation_config")
ERROR_METRIC_SCHEMA = load_schema("error_metric")
P_VALUE_DISTRIBUTION_SCHEMA = load_schema("p_value_distribution")

__all__ = [
    "load_schema",
    "SIMULATION_CONFIG_SCHEMA",
    "ERROR_METRIC_SCHEMA",
    "P_VALUE_DISTRIBUTION_SCHEMA"
]