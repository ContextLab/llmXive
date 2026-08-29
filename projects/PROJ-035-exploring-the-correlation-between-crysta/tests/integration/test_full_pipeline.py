"""
Integration test for the full data ingestion pipeline (US1).

This test verifies that the entire data ingestion pipeline (T013, T014, T014b, T015, T016)
executes successfully and produces a valid output file with the required properties:
- At least 50 rows
- No null values in 'thermal_conductivity' or 'structure_id' columns
- Valid provenance (peer-reviewed/NIST sources)
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingest.fetch_structures import fetch_perovskite_structures
from src.ingest.fetch_thermal import fetch_perovskite_thermal_data
from src.cleaning.provenance_validator import validate_provenance, save_validation_report
from src.cleaning.temperature_normalize import apply_temperature_normalization
from src.cleaning.clean_merge import merge_datasets, validate_geometry, enforce_minimum_compositions, add_provenance, main as clean_merge_main
from src.utils.validation import setup_logger, handle_error

# Constants
MIN_ROWS = 50
REQUIRED_COLUMNS = ['structure_id', 'thermal_conductivity', 'formula', 'chemistry_class']
PROVENANCE_REQUIRED_FIELDS = ['source_reference']

def cleaned_data_path():
    """Return the expected path for cleaned data output."""
    return project_root / "data" / "cleaned" / "merged_perovskite.csv"

def pipeline_modules_available():
    """Verify all required modules are importable and have expected public names."""
    try:
        from src.ingest.fetch_structures import fetch_perovskite_structures
        from src.ingest.fetch_thermal import fetch_perovskite_thermal_data
        from src.cleaning.provenance_validator import validate_provenance
        from src.cleaning.temperature_normalize import apply_temperature_normalization
        from src.cleaning.clean_merge import merge_datasets
        return True
    except ImportError as e:
        print(f"Module import error: {e}")
        return False

class TestDataIngestionPipeline:
    """Integration tests for the full data ingestion pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.logger = setup_logger("test_full_pipeline", "INFO")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create necessary directories
        (self.temp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (self.temp_path / "data" / "cleaned").mkdir(parents=True, exist_ok=True)
        
        yield
        
        self.temp_dir.cleanup()

    def test_pipeline_modules_available(self):
        """Test that all pipeline modules are available."""
        assert pipeline_modules_available(), "Pipeline modules not available"

    @patch('src.ingest.fetch_structures.fetch_perovskite_structures')
    @patch('src.ingest.fetch_thermal.fetch_perovskite_thermal_data')
    def test_full_pipeline_execution(self, mock_thermal, mock_structures):
        """
        Test the full data ingestion pipeline execution.
        
        This test mocks the API calls to return realistic data and verifies:
        1. Data ingestion works correctly
        2. Provenance validation passes
        3. Temperature normalization works
        4. Final merge produces valid output
        5. Output meets minimum requirements (>= 50 rows, no nulls)
        """
        # Mock structure data
        mock_structures.return_value = pd.DataFrame({
            'structure_id': ['mp-1234', 'mp-5678', 'mp-9012', 'mp-3456', 'mp-7890'] * 12,  # 60 rows
            'formula': ['ABO3', 'ABO3', 'ABO3', 'ABO3', 'ABO3'] * 12,
            'chemistry_class': ['oxide'] * 60,
            'lattice_volume': [100.0] * 60,
            'tolerance_factor': [0.95] * 60,
            'octahedral_factor': [0.45] * 60
        })

        # Mock thermal data
        mock_thermal.return_value = pd.DataFrame({
            'structure_id': ['mp-1234', 'mp-5678', 'mp-9012', 'mp-3456', 'mp-7890'] * 12,  # 60 rows
            'thermal_conductivity': [2.5, 3.1, 2.8, 3.5, 2.9] * 12,
            'temperature': [300.0] * 60,
            'source_reference': [
                'doi:10.1038/s41563-021-01234-5',
                'doi:10.1103/PhysRevB.102.123456',
                'doi:10.1016/j.actamat.2021.123456',
                'doi:10.1038/s41563-021-01234-6',
                'doi:10.1103/PhysRevB.102.123457'
            ] * 12
        })

        # Step 1: Fetch structures
        self.logger.info("Fetching perovskite structures...")
        structures_df = fetch_perovskite_structures()
        assert structures_df is not None, "Structure fetch failed"
        assert len(structures_df) >= MIN_ROWS, f"Not enough structures: {len(structures_df)} < {MIN_ROWS}"
        assert 'structure_id' in structures_df.columns, "Missing structure_id column"

        # Step 2: Fetch thermal data
        self.logger.info("Fetching thermal conductivity data...")
        thermal_df = fetch_perovskite_thermal_data()
        assert thermal_df is not None, "Thermal data fetch failed"
        assert len(thermal_df) >= MIN_ROWS, f"Not enough thermal records: {len(thermal_df)} < {MIN_ROWS}"
        assert 'structure_id' in thermal_df.columns, "Missing structure_id column in thermal data"
        assert 'thermal_conductivity' in thermal_df.columns, "Missing thermal_conductivity column"

        # Step 3: Validate provenance
        self.logger.info("Validating provenance...")
        valid_df, invalid_df = validate_provenance(thermal_df)
        assert len(valid_df) >= MIN_ROWS, f"Not enough valid provenance records: {len(valid_df)} < {MIN_ROWS}"
        
        # Save provenance report
        report_path = self.temp_path / "data" / "cleaned" / "provenance_report.json"
        save_validation_report(valid_df, invalid_df, str(report_path))
        assert report_path.exists(), "Provenance report not created"

        # Step 4: Temperature normalization
        self.logger.info("Applying temperature normalization...")
        normalized_df = apply_temperature_normalization(valid_df)
        assert len(normalized_df) >= MIN_ROWS, f"Not enough normalized records: {len(normalized_df)} < {MIN_ROWS}"

        # Step 5: Merge datasets
        self.logger.info("Merging datasets...")
        merged_df = merge_datasets(structures_df, normalized_df)
        assert merged_df is not None, "Merge failed"
        assert len(merged_df) >= MIN_ROWS, f"Not enough merged records: {len(merged_df)} < {MIN_ROWS}"

        # Step 6: Validate geometry
        self.logger.info("Validating geometry...")
        geometry_valid = validate_geometry(merged_df)
        assert geometry_valid, "Geometry validation failed"

        # Step 7: Enforce minimum compositions
        self.logger.info("Enforcing minimum compositions...")
        final_df = enforce_minimum_compositions(merged_df, min_count=MIN_ROWS)
        assert len(final_df) >= MIN_ROWS, f"Not enough final records: {len(final_df)} < {MIN_ROWS}"

        # Step 8: Add provenance metadata
        self.logger.info("Adding provenance metadata...")
        final_df = add_provenance(final_df, "US1 Data Ingestion Pipeline")

        # Step 9: Validate final output
        self.logger.info("Validating final output...")
        
        # Check for nulls in required columns
        for col in ['thermal_conductivity', 'structure_id']:
            null_count = final_df[col].isnull().sum()
            assert null_count == 0, f"Found {null_count} null values in {col}"
        
        # Check required columns exist
        for col in REQUIRED_COLUMNS:
            assert col in final_df.columns, f"Missing required column: {col}"

        # Save final output
        output_path = self.temp_path / "data" / "cleaned" / "merged_perovskite.csv"
        final_df.to_csv(output_path, index=False)
        assert output_path.exists(), "Final output file not created"

        # Verify file contents
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) >= MIN_ROWS, f"Loaded file has too few rows: {len(loaded_df)}"
        assert loaded_df['thermal_conductivity'].isnull().sum() == 0, "Loaded file has null thermal_conductivity"
        assert loaded_df['structure_id'].isnull().sum() == 0, "Loaded file has null structure_id"

        self.logger.info("Pipeline execution test passed!")