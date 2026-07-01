"""
Contract Tests for JSON Schemas.

These tests verify that the JSON Schema files in contracts/ are valid
and that the Pydantic models in code/data_models.py are consistent with them.
"""
import json
import os
import sys
from pathlib import Path

import jsonschema
import pytest
from pydantic import TypeAdapter

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_models import IonSolventPair, BornPrediction, ResidualAnalysis

CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

@pytest.fixture
def ion_solvent_schema():
    with open(CONTRACTS_DIR / "IonSolventPair.json", "r") as f:
        return json.load(f)

@pytest.fixture
def born_prediction_schema():
    with open(CONTRACTS_DIR / "BornPrediction.json", "r") as f:
        return json.load(f)

@pytest.fixture
def residual_analysis_schema():
    with open(CONTRACTS_DIR / "ResidualAnalysis.json", "r") as f:
        return json.load(f)

def test_ion_solvent_pair_schema_valid(ion_solvent_schema):
    """Verify IonSolventPair schema is valid JSON Schema."""
    jsonschema.Draft7Validator.check_schema(ion_solvent_schema)

def test_ion_solvent_pair_model_matches_schema(ion_solvent_schema):
    """Verify a valid IonSolventPair instance passes schema validation."""
    # Create a minimal valid instance
    instance = IonSolventPair(
        ion_identifier="Na+",
        solvent_identifier="water",
        experimental_deltaG=-95.0,
        uncertainty=0.5,
        temperature=298.15,
        charge=1,
        radius=1.02,
        radius_type="crystal",
        instrument_metadata={"source": "NIST"}
    )
    data = instance.model_dump()
    jsonschema.validate(data, ion_solvent_schema)

def test_born_prediction_schema_valid(born_prediction_schema):
    """Verify BornPrediction schema is valid JSON Schema."""
    jsonschema.Draft7Validator.check_schema(born_prediction_schema)

def test_born_prediction_model_matches_schema(born_prediction_schema):
    """Verify a valid BornPrediction instance passes schema validation."""
    from datetime import datetime
    instance = BornPrediction(
        ion_identifier="Na+",
        solvent_identifier="water",
        predicted_deltaG=-90.5,
        ionic_radius=1.02,
        dielectric_constant=78.5,
        calculation_timestamp=datetime.now().isoformat()
    )
    data = instance.model_dump()
    jsonschema.validate(data, born_prediction_schema)

def test_residual_analysis_schema_valid(residual_analysis_schema):
    """Verify ResidualAnalysis schema is valid JSON Schema."""
    jsonschema.Draft7Validator.check_schema(residual_analysis_schema)

def test_residual_analysis_model_matches_schema(residual_analysis_schema):
    """Verify a valid ResidualAnalysis instance passes schema validation."""
    instance = ResidualAnalysis(
        residual=4.5,
        ion_size_class="small",
        solvent_class="water",
        statistical_significance=True,
        p_value=0.02,
        confidence_interval=[2.0, 7.0]
    )
    data = instance.model_dump()
    jsonschema.validate(data, residual_analysis_schema)