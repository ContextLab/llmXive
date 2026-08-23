import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Import from sibling modules
from src.meta_analysis import validate_gene_panel_against_schema
from src.config import get_project_root

@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create necessary directories
        (root / "results" / "meta_analysis").mkdir(parents=True)
        (root / "specs" / "001-chemo-biomarker-discovery" / "contracts").mkdir(parents=True)
        yield root

def test_valid_gene_panel(temp_project_dir):
    """Test that a valid gene panel passes validation."""
    # Create a valid schema file
    schema_content = """
    type: object
    properties:
      genes:
        type: array
        items:
          type: object
          properties:
            gene_symbol:
              type: string
            meta_p_value:
              type: number
            log2FC_mean:
              type: number
            selected:
              type: boolean
          required:
            - gene_symbol
            - meta_p_value
            - log2FC_mean
            - selected
    required:
      - genes
    """
    schema_path = temp_project_dir / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "gene_panel.schema.yaml"
    with open(schema_path, "w") as f:
        f.write(schema_content)

    # Create a valid gene panel
    panel = {
        "genes": [
            {
                "gene_symbol": "BRCA1",
                "meta_p_value": 0.001,
                "log2FC_mean": 2.5,
                "selected": True
            },
            {
                "gene_symbol": "TP53",
                "meta_p_value": 0.005,
                "log2FC_mean": -1.8,
                "selected": True
            }
        ],
        "metadata": {
            "intersection_count": 2,
            "fallback_used": False,
            "final_panel_size": 2
        }
    }
    panel_path = temp_project_dir / "results" / "meta_analysis" / "gene_panel.json"
    with open(panel_path, "w") as f:
        json.dump(panel, f)

    # Validate
    assert validate_gene_panel_against_schema(panel_path, schema_path) is True

def test_invalid_gene_panel_missing_field(temp_project_dir):
    """Test that a gene panel with missing required fields fails validation."""
    # Create a valid schema file
    schema_content = """
    type: object
    properties:
      genes:
        type: array
        items:
          type: object
          properties:
            gene_symbol:
              type: string
            meta_p_value:
              type: number
            log2FC_mean:
              type: number
            selected:
              type: boolean
          required:
            - gene_symbol
            - meta_p_value
            - log2FC_mean
            - selected
    required:
      - genes
    """
    schema_path = temp_project_dir / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "gene_panel.schema.yaml"
    with open(schema_path, "w") as f:
        f.write(schema_content)

    # Create an invalid gene panel (missing 'selected')
    panel = {
        "genes": [
            {
                "gene_symbol": "BRCA1",
                "meta_p_value": 0.001,
                "log2FC_mean": 2.5
            }
        ]
    }
    panel_path = temp_project_dir / "results" / "meta_analysis" / "gene_panel.json"
    with open(panel_path, "w") as f:
        json.dump(panel, f)

    # Validate
    assert validate_gene_panel_against_schema(panel_path, schema_path) is False

def test_invalid_gene_panel_wrong_type(temp_project_dir):
    """Test that a gene panel with wrong types fails validation."""
    # Create a valid schema file
    schema_content = """
    type: object
    properties:
      genes:
        type: array
        items:
          type: object
          properties:
            gene_symbol:
              type: string
            meta_p_value:
              type: number
            log2FC_mean:
              type: number
            selected:
              type: boolean
          required:
            - gene_symbol
            - meta_p_value
            - log2FC_mean
            - selected
    required:
      - genes
    """
    schema_path = temp_project_dir / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "gene_panel.schema.yaml"
    with open(schema_path, "w") as f:
        f.write(schema_content)

    # Create an invalid gene panel (wrong type for 'selected')
    panel = {
        "genes": [
            {
                "gene_symbol": "BRCA1",
                "meta_p_value": 0.001,
                "log2FC_mean": 2.5,
                "selected": "yes"  # Should be boolean
            }
        ]
    }
    panel_path = temp_project_dir / "results" / "meta_analysis" / "gene_panel.json"
    with open(panel_path, "w") as f:
        json.dump(panel, f)

    # Validate
    assert validate_gene_panel_against_schema(panel_path, schema_path) is False

def test_missing_panel_file(temp_project_dir):
    """Test that validation fails if the panel file is missing."""
    schema_path = temp_project_dir / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "gene_panel.schema.yaml"
    panel_path = temp_project_dir / "results" / "meta_analysis" / "gene_panel.json"

    # Create schema but not panel
    schema_content = "type: object"
    with open(schema_path, "w") as f:
        f.write(schema_content)

    assert validate_gene_panel_against_schema(panel_path, schema_path) is False

def test_missing_schema_file(temp_project_dir):
    """Test that validation fails if the schema file is missing."""
    schema_path = temp_project_dir / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "gene_panel.schema.yaml"
    panel_path = temp_project_dir / "results" / "meta_analysis" / "gene_panel.json"

    # Create panel but not schema
    panel = {"genes": []}
    with open(panel_path, "w") as f:
        json.dump(panel, f)

    assert validate_gene_panel_against_schema(panel_path, schema_path) is False