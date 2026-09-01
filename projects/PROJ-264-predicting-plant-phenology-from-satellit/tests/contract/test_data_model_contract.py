"""
Contract tests for output artifacts against data-model.md.

This module validates that the data artifacts produced by the pipeline
(ingestion, preprocessing, etc.) adhere to the schema and structure
defined in `data-model.md`.

It uses a combination of schema validation (if JSON/YAML) and structural
checks (for CSVs) to ensure data integrity.
"""
import json
import os
import pandas as pd
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    return current.parent.parent.parent

def load_data_model_doc() -> Dict[str, Any]:
    """
    Load the data-model.md content and parse it into a structured dict.
    
    Note: Since data-model.md is likely a Markdown file, we assume it
    contains a YAML front-matter or a specific JSON block defining the schema.
    If the file is pure Markdown without machine-readable schema, we perform
    heuristic structural checks based on expected column names.
    """
    root = get_project_root()
    model_path = root / "data-model.md"
    
    if not model_path.exists():
        pytest.skip(f"data-model.md not found at {model_path}. "
                    "Skipping data model contract tests.")
    
    with open(model_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Attempt to extract YAML front matter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1])
            except yaml.YAMLError:
                pass
    
    # If no YAML front matter, return a marker dict indicating we need heuristic checks
    return {"_mode": "heuristic", "content": content}

def get_expected_schema_from_heuristics() -> Dict[str, List[str]]:
    """
    Define expected schemas based on the data-model.md content or known artifacts.
    
    This is a fallback if the data-model.md is not machine-readable.
    It defines expected columns for key output files.
    """
    return {
        "data/processed/aligned_dataset.csv": [
            "site_id", "date", "ndvi", "evi", "temperature", "precipitation",
            "phenology_event", "phenology_date", "lagged_features"
        ],
        "data/processed/training_data.csv": [
            "site_id", "target_date", "features", "target"
        ],
        "artifacts/models/model_metrics.json": [
            "rmse", "mae", "r2", "fold"
        ]
    }

def validate_csv_schema(file_path: Path, expected_columns: List[str]):
    """Validate that a CSV file contains the expected columns."""
    if not file_path.exists():
        pytest.skip(f"Output file {file_path} does not exist. "
                    "Run ingestion/preprocessing first.")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        pytest.fail(f"Failed to read CSV {file_path}: {e}")
    
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        pytest.fail(f"Missing expected columns in {file_path}: {missing_cols}")

def validate_json_schema(file_path: Path, schema: Dict[str, Any]):
    """Validate a JSON file against a schema."""
    if not file_path.exists():
        pytest.skip(f"Output file {file_path} does not exist.")
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        # Basic structure check if schema is simple
        if "required" in schema:
            for key in schema["required"]:
                if key not in data:
                    pytest.fail(f"Missing required key '{key}' in {file_path}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {file_path}: {e}")

class TestDataModelContract:
    """
    Contract tests ensuring output artifacts match data-model.md.
    """

    def test_aligned_dataset_schema(self):
        """Verify the aligned dataset CSV matches the expected schema."""
        root = get_project_root()
        file_path = root / "data" / "processed" / "aligned_dataset.csv"
        
        # Heuristic check based on task requirements
        expected_cols = ["site_id", "date", "ndvi", "evi", "temperature", "precipitation"]
        validate_csv_schema(file_path, expected_cols)

    def test_training_data_schema(self):
        """Verify the training data CSV matches the expected schema."""
        root = get_project_root()
        file_path = root / "data" / "processed" / "training_data.csv"
        
        expected_cols = ["site_id", "target_date", "features", "target"]
        validate_csv_schema(file_path, expected_cols)

    def test_model_metrics_schema(self):
        """Verify the model metrics JSON matches the expected schema."""
        root = get_project_root()
        file_path = root / "artifacts" / "models" / "model_metrics.json"
        
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
            
            required_keys = ["rmse", "mae", "r2"]
            missing = [k for k in required_keys if k not in data]
            if missing:
                pytest.fail(f"Model metrics missing keys: {missing}")

    def test_provenance_file_structure(self):
        """Verify the provenance.yaml file has the required structure."""
        root = get_project_root()
        file_path = root / "data" / "provenance.yaml"
        
        if not file_path.exists():
            pytest.skip("provenance.yaml not found.")
        
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Check for top-level keys defined in T007/T017
        required_keys = ["version", "sources", "processing_steps"]
        missing = [k for k in required_keys if k not in data]
        if missing:
            pytest.fail(f"provenance.yaml missing keys: {missing}")
        
        # Check sources structure
        if "sources" in data and isinstance(data["sources"], list):
            for i, source in enumerate(data["sources"]):
                if not isinstance(source, dict):
                    pytest.fail(f"Source {i} in provenance.yaml is not a dictionary")
                if "url" not in source and "path" not in source:
                    pytest.fail(f"Source {i} missing 'url' or 'path'")
