"""JSON Schema contract definitions for pipeline outputs.

This module provides schema validation for all pipeline output files:
- features.csv: Feature engineering outputs
- model_trace.nc: Posterior samples from Bayesian inference
- posterior_summary.csv: Summary statistics of posterior distributions
- cv_metrics.json: Cross-validation performance metrics
- collinearity_report.txt: Multicollinearity diagnostics report

Schemas are defined in contracts/ directory as JSON Schema Draft-07 files.
"""
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

SCHEMAS = {
    "features": CONTRACTS_DIR / "features_schema.json",
    "model_trace": CONTRACTS_DIR / "model_trace_schema.json",
    "posterior_summary": CONTRACTS_DIR / "posterior_summary_schema.json",
    "cv_metrics": CONTRACTS_DIR / "cv_metrics_schema.json",
    "collinearity_report": CONTRACTS_DIR / "collinearity_report_schema.json",
}


def get_schema(name: str):
    """Load a JSON schema by name.

    Args:
        name: Schema name (e.g., 'features', 'posterior_summary')

    Returns:
        dict: Parsed JSON schema

    Raises:
        KeyError: If schema name is not found
    """
    if name not in SCHEMAS:
        raise KeyError(f"Unknown schema: {name}. Available: {list(SCHEMAS.keys())}")
    import json
    with open(SCHEMAS[name]) as f:
        return json.load(f)