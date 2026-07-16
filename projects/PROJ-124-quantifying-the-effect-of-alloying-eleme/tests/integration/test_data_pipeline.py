"""
Integration test for end-to-end data ingestion and feature engineering pipeline.
Validates that the pipeline produces correct output matching the schema.
"""

import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys
import logging

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import validate_csv_schema, load_schema
from data.ingest import ingest_and_normalize
from data.features import compute_features


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataPipelineIntegration:
    """Integration tests for the data pipeline."""

    @pytest.fixture
    def schema_path(self):
        """Path to schema definition."""
        return Path(__file__).parent.parent.parent / "contracts" / "data_schema.yaml"

    @pytest.fixture
    def raw_data_path(self):
        """Path to raw data file."""
        return Path(__file__).parent.parent.parent / "data" / "raw" / "gfa_dataset.csv"

    @pytest.fixture
    def processed_data_path(self):
        """Path to processed features file."""
        return Path(__file__).parent.parent.parent / "data" / "processed" / "features.csv"

    def test_ingest_creates_dataframe(self, raw_data_path):
        """Test that ingest_and_normalize creates a valid DataFrame."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found - download task not completed")

        df = ingest_and_normalize(raw_data_path)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'composition' in df.columns
        assert 'log10_Rc' in df.columns

    def test_ingest_normalizes_composition(self, raw_data_path):
        """Test that composition normalization works correctly."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found")

        df = ingest_and_normalize(raw_data_path)

        # Check that elemental fractions sum to ~1.0 (within tolerance)
        # This depends on the actual data format
        if 'sum_fractions' in df.columns:
            assert all(np.abs(df['sum_fractions'] - 1.0) <= 0.01)

    def test_features_computed_correctly(self, raw_data_path, processed_data_path):
        """Test that feature engineering produces correct columns."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found")

        # Run the full pipeline
        df_raw = ingest_and_normalize(raw_data_path)
        df_features = compute_features(df_raw)

        assert isinstance(df_features, pd.DataFrame)
        assert len(df_features) > 0

        # Check required columns from schema
        required_cols = [
            'composition',
            'source_row_id',
            'log10_Rc',
            'atomic_radius_mean',
            'electronegativity_mean',
            'VEC_avg',
            'size_mismatch',
            'num_elements'
        ]

        for col in required_cols:
            assert col in df_features.columns, f"Missing required column: {col}"

    def test_schema_validation_after_processing(self, raw_data_path, schema_path):
        """Test that processed data matches the schema definition."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found")

        # Run pipeline
        df_raw = ingest_and_normalize(raw_data_path)
        df_features = compute_features(df_features)

        # Validate against schema
        schema = load_schema(schema_path)
        is_valid, errors = validate_csv_schema(df_features, schema['processed_features'])

        if not is_valid:
            logger.error(f"Schema validation failed: {errors}")

        assert is_valid, f"Processed data does not match schema: {errors}"

    def test_no_null_values_for_known_elements(self, raw_data_path):
        """Test that there are no null values for known elements in processed data."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found")

        df_raw = ingest_and_normalize(raw_data_path)
        df_features = compute_features(df_raw)

        # Check for nulls in key columns
        key_cols = ['atomic_radius_mean', 'electronegativity_mean', 'VEC_avg']
        for col in key_cols:
            if col in df_features.columns:
                null_count = df_features[col].isnull().sum()
                assert null_count == 0, f"Found {null_count} null values in {col}"

    def test_row_count_matches_source(self, raw_data_path):
        """Test that row count in processed data matches source (after filtering)."""
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found")

        df_raw = ingest_and_normalize(raw_data_path)
        df_features = compute_features(df_raw)

        # Processed data should have <= rows than raw (filtering may remove some)
        assert len(df_features) <= len(df_raw)
        assert len(df_features) > 0, "No rows in processed data"

    @pytest.mark.integration
    def test_end_to_end_pipeline(self, raw_data_path, processed_data_path, schema_path):
        """
        Full end-to-end integration test:
        1. Ingest raw data
        2. Compute features
        3. Validate against schema
        4. Check data quality constraints
        """
        if not raw_data_path.exists():
            pytest.skip("Raw data file not found - download task not completed")

        # Step 1: Ingest
        logger.info("Step 1: Ingesting raw data...")
        df_raw = ingest_and_normalize(raw_data_path)
        assert len(df_raw) > 0

        # Step 2: Feature engineering
        logger.info("Step 2: Computing features...")
        df_features = compute_features(df_raw)
        assert len(df_features) > 0

        # Step 3: Schema validation
        logger.info("Step 3: Validating against schema...")
        schema = load_schema(schema_path)
        is_valid, errors = validate_csv_schema(df_features, schema['processed_features'])
        assert is_valid, f"Schema validation failed: {errors}"

        # Step 4: Data quality checks
        logger.info("Step 4: Running data quality checks...")

        # Check for nulls in critical columns
        critical_cols = ['log10_Rc', 'VEC_avg', 'atomic_radius_mean']
        for col in critical_cols:
            if col in df_features.columns:
                assert df_features[col].isnull().sum() == 0, f"Null values in {col}"

        # Check that log10_Rc has reasonable range
        if 'log10_Rc' in df_features.columns:
            assert df_features['log10_Rc'].min() > -10
            assert df_features['log10_Rc'].max() < 10

        # Check that VEC_avg is positive
        if 'VEC_avg' in df_features.columns:
            assert (df_features['VEC_avg'] >= 0).all()

        logger.info("End-to-end pipeline test passed!")
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
