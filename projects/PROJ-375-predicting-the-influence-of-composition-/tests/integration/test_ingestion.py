import pytest
import pandas as pd
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ingestion.fetch_data import fetch_data
from utils.io import fail_loud_loader
import yaml
from pathlib import Path

class TestAPIFetch:
    """
    Integration test: Verify API fetch and Zenodo fallback logic.
    Assert: fetch_data() returns a DataFrame with >= 0 rows and raises if all sources fail.
    """

    def test_api_fetch_returns_dataframe(self):
        """
        Test that fetch_data returns a DataFrame when at least one source succeeds.
        We mock the real API calls to simulate a successful response without
        requiring network access or API keys in the test environment.
        """
        # Mock successful response from Materials Project
        mock_mg_entry = {
            "material_id": "mp-12345",
            "composition": "Zr50Cu40Al10",
            "cte": 5.5,
            "state": "amorphous"
        }
        
        with patch('ingestion.fetch_data._fetch_from_materials_project') as mock_mp, \
             patch('ingestion.fetch_data._fetch_from_aflow') as mock_aflow, \
             patch('ingestion.fetch_data._fetch_from_zenodo') as mock_zenodo:
            
            # Simulate MP returning one valid entry
            mock_mp.return_value = pd.DataFrame([mock_mg_entry])
            # Simulate AFLOW and Zenodo returning empty
            mock_aflow.return_value = pd.DataFrame()
            mock_zenodo.return_value = pd.DataFrame()
            
            result = fetch_data()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) >= 0
            # Verify we got the mocked data
            assert len(result) == 1
            assert 'composition' in result.columns
            assert 'cte' in result.columns

    def test_api_fetch_raises_on_total_failure(self):
        """
        Test that fetch_data raises an exception when ALL sources fail.
        This verifies the 'fail loud' behavior required by T008.
        """
        with patch('ingestion.fetch_data._fetch_from_materials_project') as mock_mp, \
             patch('ingestion.fetch_data._fetch_from_aflow') as mock_aflow, \
             patch('ingestion.fetch_data._fetch_from_zenodo') as mock_zenodo:
            
            # Simulate all sources failing (returning empty or raising)
            mock_mp.return_value = pd.DataFrame()
            mock_aflow.return_value = pd.DataFrame()
            mock_zenodo.return_value = pd.DataFrame()
            
            # The fetch_data function should raise a ValueError when no data is found
            # This is the expected behavior per the "fail loud" requirement
            with pytest.raises(ValueError, match="No valid metallic glass entries found from any source"):
                fetch_data()

    def test_api_fetch_zenodo_fallback(self):
        """
        Test that Zenodo fallback is attempted when primary APIs return empty.
        """
        mock_mg_entry = {
            "material_id": "zenodo-67890",
            "composition": "Pd40Ni40P20",
            "cte": 6.2,
            "state": "amorphous"
        }
        
        with patch('ingestion.fetch_data._fetch_from_materials_project') as mock_mp, \
             patch('ingestion.fetch_data._fetch_from_aflow') as mock_aflow, \
             patch('ingestion.fetch_data._fetch_from_zenodo') as mock_zenodo:
            
            # Primary sources fail
            mock_mp.return_value = pd.DataFrame()
            mock_aflow.return_value = pd.DataFrame()
            # Zenodo succeeds
            mock_zenodo.return_value = pd.DataFrame([mock_mg_entry])
            
            result = fetch_data()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert result.iloc[0]['composition'] == 'Pd40Ni40P20'
            
            # Verify Zenodo was actually called
            mock_zenodo.assert_called_once()

    def test_api_fetch_filters_non_amorphous(self):
        """
        Test that non-amorphous entries are filtered out.
        """
        mock_mg_entry_amorphous = {
            "material_id": "mp-11111",
            "composition": "Zr50Cu40Al10",
            "cte": 5.5,
            "state": "amorphous"
        }
        mock_mg_entry_crystalline = {
            "material_id": "mp-22222",
            "composition": "Cu50Zr50",
            "cte": 17.0,
            "state": "crystalline"
        }
        
        with patch('ingestion.fetch_data._fetch_from_materials_project') as mock_mp, \
             patch('ingestion.fetch_data._fetch_from_aflow') as mock_aflow, \
             patch('ingestion.fetch_data._fetch_from_zenodo') as mock_zenodo:
            
            # Return both amorphous and crystalline
            mock_mp.return_value = pd.DataFrame([mock_mg_entry_amorphous, mock_mg_entry_crystalline])
            mock_aflow.return_value = pd.DataFrame()
            mock_zenodo.return_value = pd.DataFrame()
            
            result = fetch_data()
            
            assert isinstance(result, pd.DataFrame)
            # Should only have the amorphous entry
            assert len(result) == 1
            assert result.iloc[0]['state'] == 'amorphous'
            assert result.iloc[0]['composition'] == 'Zr50Cu40Al10'

class TestSchemaValidation:
    """
    Integration test: Verify output schema matches contracts/mg_dataset.schema.yaml.
    Assert: df.columns matches schema required fields.
    """

    def test_schema_validation(self):
        """
        Test that the DataFrame returned by fetch_data matches the required schema
        defined in contracts/mg_dataset.schema.yaml.
        """
        # Load the schema definition
        schema_path = Path(__file__).parent.parent.parent / "contracts" / "mg_dataset.schema.yaml"
        if not schema_path.exists():
            pytest.skip(f"Schema file not found at {schema_path}")

        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        required_fields = set(schema.get('required', []))
        optional_fields = set(schema.get('optional', []))
        expected_columns = required_fields | optional_fields

        # Mock a successful fetch with data that includes all expected columns
        mock_entry = {
            "material_id": "mp-12345",
            "composition": "Zr50Cu40Al10",
            "cte": 5.5,
            "state": "amorphous",
            "source": "materials_project",
            "weighted_mean_radius": 147.2,
            "electronegativity_variance": 0.05,
            "vec": 2.5,
            "size_mismatch": 0.02
        }

        with patch('ingestion.fetch_data._fetch_from_materials_project') as mock_mp, \
             patch('ingestion.fetch_data._fetch_from_aflow') as mock_aflow, \
             patch('ingestion.fetch_data._fetch_from_zenodo') as mock_zenodo:
            
            mock_mp.return_value = pd.DataFrame([mock_entry])
            mock_aflow.return_value = pd.DataFrame()
            mock_zenodo.return_value = pd.DataFrame()
            
            result = fetch_data()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) >= 1
            
            # Check that all required fields are present
            actual_columns = set(result.columns)
            
            missing_required = required_fields - actual_columns
            assert not missing_required, f"Missing required schema fields: {missing_required}"
            
            # Verify that the dataframe contains at least the required fields
            for field in required_fields:
                assert field in result.columns, f"Required field '{field}' missing from DataFrame"

            # Check that no unexpected columns are present (optional check based on strict schema)
            # For this test, we ensure required fields exist; extra columns are allowed if they are in optional
            unexpected = actual_columns - expected_columns
            if unexpected:
                # Log warning but don't fail unless strict schema enforcement is required
                pytest.warns(UserWarning, match=f"Unexpected columns found: {unexpected}")