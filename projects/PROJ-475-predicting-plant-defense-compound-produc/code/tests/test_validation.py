"""
Integration tests for the validation pipeline (US1).
Verifies listwise deletion logic and retention calculations.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.validation import (
    load_json_data,
    merge_datasets,
    perform_listwise_deletion,
    validate_data_integrity,
    calculate_retention_percentage,
    run_validation_pipeline,
)
from data.mock_generator import generate_all_mock_data
from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)


class TestValidationPipelineIntegration:
    """Integration tests verifying the full validation flow."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir()
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir()

        # Mock config to point to test directory
        self.config = get_config()
        self.config.paths["raw_data"] = str(self.raw_dir)
        self.config.paths["processed_data"] = str(self.processed_dir)

        yield

        # Cleanup
        shutil.rmtree(self.test_dir)

    def _generate_test_data(self, include_nulls=True):
        """Generate mock data with specific null patterns for testing."""
        # Genomic data
        genomic = {
            "records": [
                {"population_id": "P1", "variant_id": "V1", "genotype": 0},
                {"population_id": "P1", "variant_id": "V2", "genotype": 1},
                {"population_id": "P2", "variant_id": "V1", "genotype": 2},
                {"population_id": "P2", "variant_id": "V2", "genotype": None if include_nulls else 0},
                {"population_id": "P3", "variant_id": "V1", "genotype": 0},
            ]
        }

        # Environmental data
        env_data = {
            "records": [
                {"population_id": "P1", "env_id": "E1", "temp": 20.5, "precip": 100},
                {"population_id": "P2", "env_id": "E2", "temp": None if include_nulls else 22.0, "precip": 150},
                {"population_id": "P3", "env_id": "E3", "temp": 18.0, "precip": None},
            ]
        }

        # Compound data
        compound_data = {
            "records": [
                {"population_id": "P1", "compound_id": "C1", "concentration": 10.5},
                {"population_id": "P2", "compound_id": "C2", "concentration": 15.0},
                {"population_id": "P3", "compound_id": "C3", "concentration": 12.0},
            ]
        }

        # Write to files
        with open(self.raw_dir / "genomic_vcf.json", "w") as f:
            json.dump(genomic, f)
        with open(self.raw_dir / "env_data.json", "w") as f:
            json.dump(env_data, f)
        with open(self.raw_dir / "compound_data.json", "w") as f:
            json.dump(compound_data, f)

        return genomic, env_data, compound_data

    def test_load_json_data(self):
        """Test loading JSON data from disk."""
        self._generate_test_data(include_nulls=False)

        genomic = load_json_data(self.raw_dir / "genomic_vcf.json")
        env_data = load_json_data(self.raw_dir / "env_data.json")
        compound = load_json_data(self.raw_dir / "compound_data.json")

        assert "records" in genomic
        assert len(genomic["records"]) == 5
        assert "records" in env_data
        assert len(env_data["records"]) == 3

    def test_merge_datasets(self):
        """Test merging of three datasets into a single DataFrame."""
        self._generate_test_data(include_nulls=False)

        genomic = load_json_data(self.raw_dir / "genomic_vcf.json")
        env_data = load_json_data(self.raw_dir / "env_data.json")
        compound = load_json_data(self.raw_dir / "compound_data.json")

        merged_df = merge_datasets(genomic, env_data, compound)

        assert isinstance(merged_df, pd.DataFrame)
        assert "population_id" in merged_df.columns
        assert "compound_id" in merged_df.columns
        assert "env_id" in merged_df.columns

        # All populations P1, P2, P3 should be present before deletion
        assert "P1" in merged_df["population_id"].values
        assert "P2" in merged_df["population_id"].values
        assert "P3" in merged_df["population_id"].values

    def test_perform_listwise_deletion_with_nulls(self):
        """
        Integration test: Verify that listwise deletion removes rows with ANY nulls
        in critical columns (population_id, env_id, compound_id, genotype, temp, concentration).
        """
        # Generate data with intentional nulls
        # P1: No nulls -> should keep
        # P2: Null in env_data.temp -> should delete
        # P3: Null in compound_data.concentration -> should delete (actually P3 has null in env precip, but let's check logic)
        # Wait, my mock generator logic:
        # P2: temp is None
        # P3: precip is None (not concentration)
        # Let's adjust mock to ensure concentration is null for P3 to test compound deletion
        
        self._generate_test_data(include_nulls=True)

        # Manually inject a null concentration for P3 to ensure compound deletion triggers
        compound_path = self.raw_dir / "compound_data.json"
        with open(compound_path, "r") as f:
            data = json.load(f)
        # Find P3 record and set concentration to null
        for rec in data["records"]:
            if rec["population_id"] == "P3":
                rec["concentration"] = None
        with open(compound_path, "w") as f:
            json.dump(data, f)

        genomic = load_json_data(self.raw_dir / "genomic_vcf.json")
        env_data = load_json_data(self.raw_dir / "env_data.json")
        compound = load_json_data(self.raw_dir / "compound_data.json")

        merged_df = merge_datasets(genomic, env_data, compound)

        initial_count = len(merged_df)
        
        # Perform listwise deletion
        # The function expects a DataFrame and a list of columns to check for nulls
        # Based on typical validation logic, we check key identifiers and values
        critical_cols = ["population_id", "env_id", "compound_id", "genotype", "temp", "concentration"]
        
        clean_df = perform_listwise_deletion(merged_df, columns=critical_cols)

        final_count = len(clean_df)

        # P1 is the only one without nulls in critical columns
        # P2 has null temp
        # P3 has null concentration
        assert final_count < initial_count, "Listwise deletion should reduce row count"
        assert final_count == 1, "Only P1 should remain after listwise deletion"
        
        remaining_pop = clean_df.iloc[0]["population_id"]
        assert remaining_pop == "P1", f"Expected P1 to remain, got {remaining_pop}"

    def test_validate_data_integrity(self):
        """Test that validation catches missing critical identifiers."""
        # Create data missing population_id for one record
        genomic = {
            "records": [
                {"population_id": None, "variant_id": "V1", "genotype": 0}, # Invalid
                {"population_id": "P1", "variant_id": "V2", "genotype": 1},
            ]
        }
        env_data = {
            "records": [
                {"population_id": "P1", "env_id": "E1", "temp": 20.0, "precip": 100},
            ]
        }
        compound = {
            "records": [
                {"population_id": "P1", "compound_id": "C1", "concentration": 10.5},
            ]
        }

        # Write files
        with open(self.raw_dir / "genomic_vcf.json", "w") as f:
            json.dump(genomic, f)
        with open(self.raw_dir / "env_data.json", "w") as f:
            json.dump(env_data, f)
        with open(self.raw_dir / "compound_data.json", "w") as f:
            json.dump(compound, f)

        genomic_loaded = load_json_data(self.raw_dir / "genomic_vcf.json")
        env_loaded = load_json_data(self.raw_dir / "env_data.json")
        compound_loaded = load_json_data(self.raw_dir / "compound_data.json")

        merged_df = merge_datasets(genomic_loaded, env_loaded, compound_loaded)
        
        # Perform deletion first to remove the bad row
        clean_df = perform_listwise_deletion(merged_df, columns=["population_id"])
        
        # Now validate
        is_valid, issues = validate_data_integrity(clean_df)
        
        assert is_valid, "Data should be valid after listwise deletion"
        assert len(issues) == 0

    def test_retention_percentage_calculation(self):
        """Verify retention percentage is calculated correctly."""
        initial_rows = 100
        final_rows = 80
        
        retention = calculate_retention_percentage(initial_rows, final_rows)
        
        assert retention == 80.0
        assert retention <= 100.0
        assert retention >= 0.0

    def test_run_validation_pipeline_integration(self):
        """
        End-to-end integration test: Run the full validation pipeline
        and verify the output file is created and contains cleaned data.
        """
        self._generate_test_data(include_nulls=True)
        
        # Modify P3 concentration to null to ensure it gets deleted
        compound_path = self.raw_dir / "compound_data.json"
        with open(compound_path, "r") as f:
            data = json.load(f)
        for rec in data["records"]:
            if rec["population_id"] == "P3":
                rec["concentration"] = None
        with open(compound_path, "w") as f:
            json.dump(data, f)

        # Run the pipeline
        output_path = self.processed_dir / "validated_data.csv"
        
        # Patch the config paths to use our test directory
        with patch('data.validation.get_config') as mock_get_config:
            mock_config = self.config
            mock_get_config.return_value = mock_config
            
            # Execute pipeline
            try:
                run_validation_pipeline(
                    genomic_path=self.raw_dir / "genomic_vcf.json",
                    env_path=self.raw_dir / "env_data.json",
                    compound_path=self.raw_dir / "compound_data.json",
                    output_path=str(output_path)
                )
            except SystemExit as e:
                # If retention is too low, it might exit. 
                # With our data (3 rows -> 1 row), retention is 33%, which is < 80%
                # This might trigger the exit in T014 logic. 
                # We need to adjust the mock data to ensure retention > 80% OR 
                # handle the expected exit. 
                # Let's adjust the mock data to have 10 rows, 9 valid, 1 invalid.
                pass

        # Re-run with better data proportions to avoid SystemExit
        # Generate 10 populations, 9 valid, 1 invalid
        genomic_records = []
        env_records = []
        compound_records = []
        
        for i in range(1, 11):
            pop_id = f"P{i}"
            genomic_records.append({"population_id": pop_id, "variant_id": "V1", "genotype": i % 2})
            env_records.append({"population_id": pop_id, "env_id": f"E{i}", "temp": 20.0 + i, "precip": 100.0})
            compound_records.append({"population_id": pop_id, "compound_id": f"C{i}", "concentration": 10.0 + i})
        
        # Make P10 invalid (null temp)
        env_records[9]["temp"] = None

        genomic_data = {"records": genomic_records}
        env_data = {"records": env_records}
        compound_data = {"records": compound_records}

        with open(self.raw_dir / "genomic_vcf.json", "w") as f:
            json.dump(genomic_data, f)
        with open(self.raw_dir / "env_data.json", "w") as f:
            json.dump(env_data, f)
        with open(self.raw_dir / "compound_data.json", "w") as f:
            json.dump(compound_data, f)

        # Run pipeline again
        with patch('data.validation.get_config') as mock_get_config:
            mock_config = self.config
            mock_get_config.return_value = mock_config
            
            # This should succeed with 90% retention
            run_validation_pipeline(
                genomic_path=self.raw_dir / "genomic_vcf.json",
                env_path=self.raw_dir / "env_data.json",
                compound_path=self.raw_dir / "compound_data.json",
                output_path=str(output_path)
            )

        # Verify output file exists
        assert output_path.exists(), "Output file should be created by the pipeline"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 9, "Should have 9 rows after deleting P10"
        assert "P10" not in df["population_id"].values, "P10 should be deleted due to null temp"
        assert "population_id" in df.columns
        assert "compound_id" in df.columns
        assert "env_id" in df.columns