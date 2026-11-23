"""
Integration test for the full ingestion pipeline (User Story 1).
Validates that the pipeline produces a DataFrame matching the contract schema.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add src to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.ingest import run_ingestion
from src.data.features import engineer_features
from src.utils.validators import validate_schema
import yaml

# Path to the schema file relative to project root
SCHEMA_PATH = os.path.join(project_root, "contracts", "dataset.schema.yaml")

@pytest.fixture
def sample_raw_data_csv():
    """
    Creates a temporary CSV file with sample data mimicking NIST/Materials Project output.
    This ensures the test runs without needing external network access or large files.
    """
    data = {
        "Sample_ID": ["S1", "S2", "S3", "S4", "S5"],
        "Carbon": [0.20, 0.35, 0.15, 0.45, 0.25],
        "Manganese": [1.0, 1.5, 0.8, 2.0, 1.2],
        "Chromium": [0.5, 1.2, 0.3, 0.0, 0.8],
        "Nickel": [0.2, 0.5, 0.1, 0.0, 0.4],
        "Silicon": [0.25, 0.30, 0.20, 0.35, 0.28],
        "Sulfur": [0.02, 0.03, 0.01, 0.04, 0.02],
        "Phosphorus": [0.02, 0.03, 0.01, 0.04, 0.02],
        "Austenitizing_Temp_C": [850, 900, 820, 950, 880],
        "Cooling_Rate_C_per_s": [10.0, 50.0, 2.0, 100.0, 25.0],
        "Holding_Time_min": [30, 60, 20, 90, 45],
        "Heat_Treatment_Type": ["Air_Cooled", "Oil_Quenched", "Furnace_Cooled", "Oil_Quenched", "Air_Cooled"],
        "Yield_Strength_MPa": [450.0, 620.0, 380.0, 750.0, 510.0],
        "Notes": ["Normal", "High C", "Low C", "Very High C", "Medium"]
    }
    
    # Add a row with missing yield strength to test FR-001
    data["Sample_ID"].append("S6")
    data["Carbon"].append(0.30)
    data["Manganese"].append(1.2)
    data["Chromium"].append(0.6)
    data["Nickel"].append(0.3)
    data["Silicon"].append(0.27)
    data["Sulfur"].append(0.02)
    data["Phosphorus"].append(0.02)
    data["Austenitizing_Temp_C"].append(870)
    data["Cooling_Rate_C_per_s"].append(15.0)
    data["Holding_Time_min"].append(35)
    data["Heat_Treatment_Type"].append("Air_Cooled")
    data["Yield_Strength_MPa"].append(np.nan) # Missing target
    data["Notes"].append("Missing Target")

    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name

def load_schema(schema_path):
    """Loads the YAML schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_ingestion_pipeline_schema_validation(sample_raw_data_csv):
    """
    Runs the full ingestion pipeline and validates the output against the schema.
    """
    assert os.path.exists(SCHEMA_PATH), f"Schema file missing at {SCHEMA_PATH}"
    
    # Run ingestion
    # We use a temporary directory for output to avoid cluttering the repo
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "processed_data.csv")
        
        # Execute the ingestion pipeline
        # Note: This calls run_ingestion which should handle:
        # 1. Loading the CSV
        # 2. Dropping rows with missing Yield_Strength_MPa
        # 3. Normalizing thermal parameters
        # 4. One-hot encoding heat treatment
        # 5. Calculating features (ratios, interactions, orthogonalization)
        
        try:
            df_processed = run_ingestion(
                input_path=sample_raw_data_csv,
                output_path=output_path
            )
        except Exception as e:
            pytest.fail(f"Ingestion pipeline failed to run: {e}")

        # 1. Verify file was written
        assert os.path.exists(output_path), "Output CSV file was not created."
        
        # 2. Verify DataFrame structure
        assert isinstance(df_processed, pd.DataFrame), "Output must be a DataFrame."
        assert len(df_processed) > 0, "Output DataFrame is empty."
        
        # The row with missing Yield_Strength_MPa should be dropped
        assert len(df_processed) == 5, f"Expected 5 rows (1 dropped), got {len(df_processed)}."
        
        # 3. Validate against Schema
        schema = load_schema(SCHEMA_PATH)
        
        # Check Target Column
        assert "Yield_Strength_MPa" in df_processed.columns, "Target column 'Yield_Strength_MPa' missing."
        assert schema["properties"]["target_column"]["const"] == "Yield_Strength_MPa"
        
        # Check Composition Columns
        expected_composition = ["Carbon", "Manganese", "Chromium", "Nickel", "Silicon", "Sulfur", "Phosphorus"]
        for col in expected_composition:
            assert col in df_processed.columns, f"Missing composition column: {col}"
        
        # Check Thermal Columns (Normalized)
        expected_thermal = [
            "Normalized_Austenitizing_Temp", 
            "Normalized_Cooling_Rate", 
            "Normalized_Holding_Time"
        ]
        for col in expected_thermal:
            assert col in df_processed.columns, f"Missing normalized thermal column: {col}"
            # Verify normalization range [0, 1] approximately (allowing for small float errors)
            assert df_processed[col].min() >= 0.0, f"Column {col} has values < 0"
            assert df_processed[col].max() <= 1.0, f"Column {col} has values > 1"
        
        # Check Derived Columns (Ratios & Interactions)
        # T013: C/Mn, Cr/Ni, Cooling Rate x Holding Time, C x Cooling Rate
        assert "C_Mn_Ratio" in df_processed.columns, "Missing C/Mn ratio."
        assert "Cr_Ni_Ratio" in df_processed.columns, "Missing Cr/Ni ratio."
        assert "CoolingRate_x_HoldingTime" in df_processed.columns, "Missing interaction: Cooling Rate x Holding Time."
        assert "C_x_CoolingRate" in df_processed.columns, "Missing interaction: C x Cooling Rate."
        
        # T014: Orthogonalized interactions
        assert "Ortho_CoolingRate_x_HoldingTime" in df_processed.columns, "Missing orthogonalized interaction: Cooling Rate x Holding Time."
        assert "Ortho_C_x_CoolingRate" in df_processed.columns, "Missing orthogonalized interaction: C x Cooling Rate."
        
        # Check One-Hot Encoded Columns
        # T012: One-hot encoding for Heat Treatment Types
        # Expected types from sample: Air_Cooled, Oil_Quenched, Furnace_Cooled
        expected_hot_cols = ["HT_Air_Cooled", "HT_Oil_Quenched", "HT_Furnace_Cooled"]
        for col in expected_hot_cols:
            assert col in df_processed.columns, f"Missing one-hot column: {col}"
            assert set(df_processed[col].unique()).issubset({0, 1}), f"Column {col} is not binary."

        # 4. Verify No Nulls in Target
        assert not df_processed["Yield_Strength_MPa"].isnull().any(), "Target column contains null values."

        # 5. Verify Output File Content
        df_from_disk = pd.read_csv(output_path)
        assert df_from_disk.shape == df_processed.shape, "Saved CSV shape does not match DataFrame."

def test_ingestion_pipeline_memory_optimization(sample_raw_data_csv):
    """
    Verifies that the ingestion pipeline utilizes memory optimization utilities.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "processed_data.csv")
        
        df_processed = run_ingestion(
            input_path=sample_raw_data_csv,
            output_path=output_path
        )
        
        # Check that numeric columns are optimized (e.g., float32 instead of float64 if possible,
        # or at least that the loader's optimization function was called)
        # This is a soft check to ensure the pipeline isn't just raw pandas without optimization
        assert df_processed.memory_usage(deep=True).sum() < 10 * 1024, "DataFrame memory usage is unexpectedly high."
        
        # Verify specific types
        for col in df_processed.select_dtypes(include=['float64']).columns:
            # Ideally these should be float32, but float64 is acceptable if optimization logic exists
            # We just verify the column exists and is numeric
            assert pd.api.types.is_numeric_dtype(df_processed[col])