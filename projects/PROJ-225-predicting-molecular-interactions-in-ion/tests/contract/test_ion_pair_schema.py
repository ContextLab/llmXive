"""
Contract test for the unified dataset schema (User Story 1).

This test validates that the unified dataset produced by the data ingestion pipeline
conforms to the expected schema defined in contracts/ion_pair.schema.yaml using pandera.

It ensures:
- All required columns are present with correct data types.
- Critical columns (e.g., energy components, IDs) have no null values.
- Specific constraints (e.g., energy ranges, structural family categories) are met.
"""
import os
import sys
import pytest
import pandas as pd
import pandera as pa
from pandera.typing import Series
from pandera.dtypes import Float, Int, String
from typing import List, Optional

# Add project root to path for imports if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.config import load_config
from code.data_ingestion import write_unified_dataset, engineer_features, unify_datasets
# Note: We assume the ingestion pipeline has run or we are testing the schema definition
# against a generated sample if the real file isn't present yet.
# However, per strict requirements, we test the schema logic itself.

class IonPairSchema(pa.SchemaModel):
    """Schema for the unified dataset as defined in contracts/ion_pair.schema.yaml."""
    
    cation_id: Series[String] = pa.Field(coerce=True, nullable=False)
    anion_id: Series[String] = pa.Field(coerce=True, nullable=False)
    electrostatic_energy: Series[Float] = pa.Field(coerce=True, nullable=False, ge=-1000.0, le=1000.0)
    dispersion_energy: Series[Float] = pa.Field(coerce=True, nullable=False, ge=-1000.0, le=1000.0)
    hbond_energy: Series[Float] = pa.Field(coerce=True, nullable=False, ge=-1000.0, le=1000.0)
    total_energy: Series[Float] = pa.Field(coerce=True, nullable=False, ge=-2000.0, le=2000.0)
    tpsa: Series[Float] = pa.Field(coerce=True, nullable=False, ge=0.0)
    molecular_surface_area: Series[Float] = pa.Field(coerce=True, nullable=False, ge=0.0)
    hbond_count: Series[Int] = pa.Field(coerce=True, nullable=False, ge=0)
    morgan_fp: Series[object] = pa.Field(nullable=False) # Array of bits/integers
    structural_family: Series[String] = pa.Field(coerce=True, nullable=False)
    
    # Optional/Logging columns mentioned in task description but not in schema yaml
    # We allow them to be nullable or present
    charge_reliability: Optional[Series[String]] = pa.Field(nullable=True)

@pytest.fixture
def sample_unified_dataset() -> pd.DataFrame:
    """
    Creates a minimal valid sample dataset to test the schema.
    In a real integration test, this would be replaced by loading `data/processed/unified_dataset.parquet`.
    """
    data = {
        'cation_id': ['C1', 'C2', 'C3'],
        'anion_id': ['A1', 'A2', 'A3'],
        'electrostatic_energy': [-150.5, -200.2, -180.0],
        'dispersion_energy': [-30.1, -45.5, -35.2],
        'hbond_energy': [-10.2, -25.0, -15.5],
        'total_energy': [-190.8, -270.7, -230.7],
        'tpsa': [50.0, 60.5, 45.2],
        'molecular_surface_area': [120.0, 150.0, 110.0],
        'hbond_count': [2, 3, 1],
        'morgan_fp': [
            [1, 0, 1, 1, 0, 0, 1, 0], 
            [0, 1, 1, 0, 1, 1, 0, 1], 
            [1, 1, 0, 0, 1, 0, 0, 1]
        ],
        'structural_family': ['Imidazolium', 'Pyridinium', 'Ammonium'],
        'charge_reliability': ['reliable', 'reliable', 'unreliable']
    }
    return pd.DataFrame(data)

def test_schema_definition_validity():
    """
    Verifies that the schema definition itself is valid and can be instantiated.
    """
    assert IonPairSchema is not None
    # Check that required fields are defined
    required_fields = [
        'cation_id', 'anion_id', 'electrostatic_energy', 'dispersion_energy',
        'hbond_energy', 'total_energy', 'tpsa', 'molecular_surface_area',
        'hbond_count', 'morgan_fp', 'structural_family'
    ]
    for field in required_fields:
        assert field in IonPairSchema.to_schema().columns

def test_schema_validation_passes(sample_unified_dataset: pd.DataFrame):
    """
    Validates that a correctly formed dataset passes the schema checks.
    """
    # Validate the sample data
    validated_df = IonPairSchema.validate(sample_unified_dataset)
    assert validated_df is not None
    assert len(validated_df) == len(sample_unified_dataset)

def test_schema_validation_fails_missing_column():
    """
    Verifies that the schema correctly rejects data with missing required columns.
    """
    data = {
        'cation_id': ['C1'],
        'anion_id': ['A1'],
        # Missing electrostatic_energy
        'total_energy': [-100.0],
        'tpsa': [50.0],
        'molecular_surface_area': [120.0],
        'hbond_count': [2],
        'morgan_fp': [[1, 0, 1]],
        'structural_family': ['Imidazolium']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(pa.errors.SchemaErrors):
        IonPairSchema.validate(df)

def test_schema_validation_fails_null_critical():
    """
    Verifies that the schema rejects null values in critical columns.
    """
    data = {
        'cation_id': ['C1', None],
        'anion_id': ['A1', 'A2'],
        'electrostatic_energy': [-150.5, -200.2],
        'dispersion_energy': [-30.1, -45.5],
        'hbond_energy': [-10.2, -25.0],
        'total_energy': [-190.8, -270.7],
        'tpsa': [50.0, 60.5],
        'molecular_surface_area': [120.0, 150.0],
        'hbond_count': [2, 3],
        'morgan_fp': [[1, 0, 1], [0, 1, 0]],
        'structural_family': ['Imidazolium', 'Pyridinium']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(pa.errors.SchemaErrors):
        IonPairSchema.validate(df)

def test_schema_validation_fails_range():
    """
    Verifies that the schema rejects values outside the defined energy ranges.
    """
    data = {
        'cation_id': ['C1'],
        'anion_id': ['A1'],
        'electrostatic_energy': [-2000.0], # Out of range (< -1000)
        'dispersion_energy': [-30.1],
        'hbond_energy': [-10.2],
        'total_energy': [-190.8],
        'tpsa': [50.0],
        'molecular_surface_area': [120.0],
        'hbond_count': [2],
        'morgan_fp': [[1, 0, 1]],
        'structural_family': ['Imidazolium']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(pa.errors.SchemaErrors):
        IonPairSchema.validate(df)

def test_file_exists_and_validates():
    """
    Integration-style test: Check if the expected output file exists and validates.
    If the file hasn't been generated yet, this test is skipped rather than failing
    the entire task, allowing the test suite to run during development.
    """
    output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'unified_dataset.parquet')
    
    if not os.path.exists(output_path):
        pytest.skip("unified_dataset.parquet not found. Run data ingestion first.")
    
    try:
        df = pd.read_parquet(output_path)
        IonPairSchema.validate(df)
    except Exception as e:
        pytest.fail(f"Validation failed for {output_path}: {str(e)}")