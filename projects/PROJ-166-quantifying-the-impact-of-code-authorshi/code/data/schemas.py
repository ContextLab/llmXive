"""
Schema definitions and validation utilities.
Implements T005 schema generation logic.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
import json
from pathlib import Path
from config import CONTRACTS_DIR

def get_repo_metrics_schema() -> Dict[str, Any]:
    """Returns the schema for repo_metrics_clean.csv as a dict."""
    return {
        "url": {"type": "string", "required": True},
        "primary_language": {"type": "string", "required": True},
        "unique_authors": {"type": "integer", "required": True},
        "kloc": {"type": "number", "required": True},
        "authorship_diversity": {"type": "number", "required": True},
        "cve_count": {"type": "integer", "required": True},
        "project_age": {"type": "number", "required": True},
        "release_count": {"type": "integer", "required": True},
    }

def get_model_results_schema() -> Dict[str, Any]:
    """Returns the schema for model results JSON."""
    return {
        "author_count_coefficient": {"type": "number", "required": True},
        "std_err": {"type": "number", "required": True},
        "p_value": {"type": "number", "required": True},
        "ci_95_lower": {"type": "number", "required": True},
        "ci_95_upper": {"type": "number", "required": True},
        "vif": {"type": "object", "required": True},
        "convergence_status": {"type": "boolean", "required": True},
        "model_type": {"type": "string", "required": True},
    }

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validates a dataframe against a schema.
    Returns a list of error messages. Empty list if valid.
    """
    errors = []
    for col, specs in schema.items():
        if specs.get("required", False) and col not in df.columns:
            errors.append(f"Missing required column: {col}")
        elif col in df.columns:
            # Basic type checking
            if specs["type"] == "integer":
                if not pd.api.types.is_integer_dtype(df[col]) and not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column {col} should be integer but is {df[col].dtype}")
            elif specs["type"] == "number":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column {col} should be number but is {df[col].dtype}")
    return errors

def generate_yaml_schemas():
    """
    Generates the YAML schema files in the contracts directory.
    This function is called by T005 to create the artifacts.
    """
    import yaml
    
    # Repo Metrics Schema
    repo_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Repository Metrics Schema",
        "description": "Schema for the cleaned, merged dataset used in the primary analysis.",
        "type": "object",
        "properties": {
            "url": {"type": "string", "pattern": "^https://github\\\\.com/[^/]+/[^/]+$"},
            "primary_language": {"type": "string"},
            "unique_authors": {"type": "integer", "minimum": 1},
            "kloc": {"type": "number", "minimum": 0},
            "authorship_diversity": {"type": "number", "minimum": 0},
            "cve_count": {"type": "integer", "minimum": 0},
            "project_age": {"type": "number", "minimum": 0},
            "release_count": {"type": "integer", "minimum": 0},
        },
        "required": ["url", "primary_language", "unique_authors", "kloc", "authorship_diversity", "cve_count", "project_age", "release_count"]
    }

    # Model Results Schema
    model_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Model Results Schema",
        "description": "Schema for the output of the Negative Binomial GLM analysis.",
        "type": "object",
        "properties": {
            "author_count_coefficient": {"type": "number"},
            "std_err": {"type": "number"},
            "p_value": {"type": "number", "minimum": 0, "maximum": 1},
            "ci_95_lower": {"type": "number"},
            "ci_95_upper": {"type": "number"},
            "vif": {"type": "object", "additionalProperties": {"type": "number"}},
            "convergence_status": {"type": "boolean"},
            "model_type": {"type": "string", "enum": ["NegativeBinomial"]},
            "high_collinearity_warning": {"type": "boolean", "default": False},
            "fallback_model_used": {"type": "boolean", "default": False},
        },
        "required": ["author_count_coefficient", "std_err", "p_value", "ci_95_lower", "ci_95_upper", "vif", "convergence_status", "model_type"]
    }

    # Ensure contracts dir exists
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONTRACTS_DIR / "repo_metrics.schema.yaml", "w") as f:
        yaml.dump(repo_schema, f, default_flow_style=False, sort_keys=False)
    
    with open(CONTRACTS_DIR / "model_results.schema.yaml", "w") as f:
        yaml.dump(model_schema, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated schemas in {CONTRACTS_DIR}")

if __name__ == "__main__":
    generate_yaml_schemas()
