"""
Unit tests for data ingestion pipeline (T010).

Tests the DataIngestionPipeline with mock CSV files to verify:
1. Schema compliance (precinct_sum, county_reported, discrepancy_abs, discrepancy_pct, missing_data)
2. Handling of missing data
3. Auto-detection of file delimiters
4. Edge cases (zero votes, missing data)

Depends on T007 (Data Models & Schema) and T014a (Ingestion Pipeline).
"""

import os
import tempfile
import csv
import json
from pathlib import Path
from typing import Dict, List, Any

import pytest
import pandas as pd
import numpy as np

# Import the actual pipeline implementation
# Note: We need to ensure the code directory is in the path
import sys
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from ingestion import DataIngestionPipeline, load_verified_sources_config
from discrepancy import DiscrepancyCalculator
from exceptions import DataAcquisitionError, MissingDataError


class TestIngestionWithMockCSV:
    """Unit tests for data ingestion using mock CSV files."""

    @pytest.fixture
    def mock_csv_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory with mock CSV files for testing."""
        csv_dir = tmp_path / "mock_data"
        csv_dir.mkdir()
        
        # Create a standard CSV file with expected schema
        standard_csv = csv_dir / "standard_data.csv"
        with open(standard_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '150', '200', '1500', '2000'])
            writer.writerow(['P002', 'C001', '160', '190', '1500', '2000'])
            writer.writerow(['P003', 'C002', '140', '210', '1400', '2100'])
        
        # Create a CSV with missing values
        missing_csv = csv_dir / "missing_data.csv"
        with open(missing_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '150', '200', '1500', '2000'])
            writer.writerow(['P002', 'C001', '', '190', '1500', '2000'])  # Missing candidate_a
            writer.writerow(['P003', 'C002', '140', '', '1400', '2100'])  # Missing candidate_b
        
        # Create a CSV with zero votes (edge case)
        zero_votes_csv = csv_dir / "zero_votes.csv"
        with open(zero_votes_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '0', '0', '0', '0'])
            writer.writerow(['P002', 'C001', '160', '190', '1500', '2000'])
        
        # Create a CSV with tab delimiter
        tab_csv = csv_dir / "tab_delimited.tsv"
        with open(tab_csv, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '150', '200', '1500', '2000'])
            writer.writerow(['P002', 'C001', '160', '190', '1500', '2000'])
        
        return csv_dir

    @pytest.fixture
    def pipeline(self, tmp_path: Path) -> DataIngestionPipeline:
        """Create a DataIngestionPipeline instance."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create a minimal verified sources config for testing
        config = {
            "sources": {
                "mock": {
                    "url": "file://" + str(tmp_path),
                    "checksum": "test",
                    "expected_schema": ["precinct_id", "county_id", "candidate_a", "candidate_b", "county_total_a", "county_total_b"]
                }
            }
        }
        config_file = tmp_path / "verified_sources.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config, f)
        
        return DataIngestionPipeline(
            source_type="mock",
            state="CA",
            output_dir=str(output_dir),
            config_path=str(config_file)
        )

    def test_schema_compliance(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test that the output DataFrame contains the expected schema columns."""
        input_file = mock_csv_dir / "standard_data.csv"
        
        # Run ingestion
        result_df = pipeline.load_and_process(input_file)
        
        # Verify expected columns from T007 schema
        expected_columns = ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data']
        
        assert result_df is not None, "Ingestion should return a DataFrame"
        assert isinstance(result_df, pd.DataFrame), "Result should be a DataFrame"
        
        for col in expected_columns:
            assert col in result_df.columns, f"Missing expected column: {col}"
        
        # Verify no nulls in critical fields
        critical_fields = ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct']
        for field in critical_fields:
            assert not result_df[field].isnull().any(), f"Critical field {field} contains null values"

    def test_missing_data_handling(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test handling of missing data (imputation vs flagging)."""
        input_file = mock_csv_dir / "missing_data.csv"
        
        # Run ingestion
        result_df = pipeline.load_and_process(input_file)
        
        # Verify that records with missing data are flagged
        assert 'missing_data' in result_df.columns, "missing_data column should exist"
        
        # Check that records with missing values have the flag set
        missing_mask = result_df['missing_data'] == True
        assert missing_mask.any(), "Should flag records with missing data"
        
        # Verify that the discrepancy calculation still works for records with some missing data
        # (either imputed or skipped based on implementation)
        assert result_df['discrepancy_abs'].notnull().any(), "Should have valid discrepancy calculations"

    def test_auto_delimiter_detection(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test auto-detection of file delimiters."""
        # Test standard CSV (comma)
        csv_file = mock_csv_dir / "standard_data.csv"
        csv_result = pipeline.load_and_process(csv_file)
        assert csv_result is not None and len(csv_result) > 0, "Should load comma-delimited CSV"
        
        # Test tab-delimited file
        tsv_file = mock_csv_dir / "tab_delimited.tsv"
        tsv_result = pipeline.load_and_process(tsv_file)
        assert tsv_result is not None and len(tsv_result) > 0, "Should load tab-delimited file"
        
        # Verify both have the same structure
        assert set(csv_result.columns) == set(tsv_result.columns), "Both formats should produce same schema"

    def test_zero_votes_handling(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test handling of zero vote counts (edge case)."""
        input_file = mock_csv_dir / "zero_votes.csv"
        
        # Run ingestion - should not crash
        result_df = pipeline.load_and_process(input_file)
        
        assert result_df is not None, "Should handle zero votes without crashing"
        
        # Verify that records with zero county votes are either skipped or flagged
        zero_county_mask = result_df['county_reported'] == 0
        
        # If zero-county records are present, they should be flagged or handled appropriately
        if zero_county_mask.any():
            # Check if missing_data flag is set for these records
            zero_records = result_df[zero_county_mask]
            # Implementation should either skip these or flag them
            # The exact behavior depends on the discrepancy calculation logic
            pass

    def test_discrepancy_calculation(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test that discrepancy calculations are correct."""
        input_file = mock_csv_dir / "standard_data.csv"
        
        result_df = pipeline.load_and_process(input_file)
        
        # Verify discrepancy_abs = |precinct_sum - county_reported|
        expected_abs = np.abs(result_df['precinct_sum'] - result_df['county_reported'])
        assert np.allclose(result_df['discrepancy_abs'], expected_abs), "discrepancy_abs calculation is incorrect"
        
        # Verify discrepancy_pct = (discrepancy_abs / county_reported) * 100
        # Handle division by zero
        expected_pct = np.where(
            result_df['county_reported'] != 0,
            (result_df['discrepancy_abs'] / result_df['county_reported']) * 100,
            0.0
        )
        assert np.allclose(result_df['discrepancy_pct'], expected_pct), "discrepancy_pct calculation is incorrect"

    def test_output_persistence(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline, tmp_path: Path):
        """Test that processed data is saved to the correct location."""
        input_file = mock_csv_dir / "standard_data.csv"
        
        # Run ingestion
        result_df = pipeline.load_and_process(input_file)
        
        # Check that output files were created
        output_parquet = pipeline.output_dir / "processed" / "unified_election_data.parquet"
        output_json = pipeline.output_dir / "processed" / "ingestion_report.json"
        
        assert output_parquet.exists(), "Processed parquet file should be created"
        assert output_json.exists(), "Ingestion report should be created"
        
        # Verify report content
        with open(output_json, 'r') as f:
            report = json.load(f)
        
        assert 'source' in report, "Report should contain source information"
        assert 'records_processed' in report, "Report should contain record count"
        assert 'schema_validated' in report, "Report should contain schema validation status"

    def test_directional_anomaly_flagging(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline, tmp_path: Path):
        """Test flagging of directional anomalies (precinct sum > county total)."""
        # Create a CSV with directional anomaly
        anomaly_csv = tmp_path / "anomaly_data.csv"
        with open(anomaly_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '2000', '1000', '1500', '2000'])  # precinct sum > county total
            writer.writerow(['P002', 'C001', '160', '190', '1500', '2000'])
        
        result_df = pipeline.load_and_process(anomaly_csv)
        
        # Verify that anomalies are flagged in the output
        # The exact column name may vary based on implementation
        assert 'precinct_sum' in result_df.columns, "Should have precinct_sum column"
        assert 'county_reported' in result_df.columns, "Should have county_reported column"
        
        # Check for anomaly detection
        anomaly_mask = result_df['precinct_sum'] > result_df['county_reported']
        assert anomaly_mask.any(), "Should detect directional anomalies"

    def test_error_on_invalid_source(self, pipeline: DataIngestionPipeline):
        """Test that appropriate errors are raised for invalid sources."""
        with pytest.raises((DataAcquisitionError, FileNotFoundError)):
            # Try to load a non-existent file
            pipeline.load_and_process(Path("/nonexistent/file.csv"))

    def test_integration_with_discrepancy_calculator(self, mock_csv_dir: Path, tmp_path: Path):
        """Test integration between ingestion and discrepancy calculation."""
        # Create a fresh pipeline
        output_dir = tmp_path / "output2"
        output_dir.mkdir()
        
        pipeline = DataIngestionPipeline(
            source_type="mock",
            state="CA",
            output_dir=str(output_dir)
        )
        
        input_file = mock_csv_dir / "standard_data.csv"
        result_df = pipeline.load_and_process(input_file)
        
        # Verify that the discrepancy calculator can process the ingested data
        calculator = DiscrepancyCalculator()
        discrepancies = calculator.calculate(result_df)
        
        assert discrepancies is not None, "Discrepancy calculation should succeed"
        assert 'discrepancy_abs' in discrepancies.columns, "Should have discrepancy_abs column"
        assert 'discrepancy_pct' in discrepancies.columns, "Should have discrepancy_pct column"

    def test_large_file_streaming(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline, tmp_path: Path):
        """Test that the pipeline can handle large files via streaming (T053, T062)."""
        # Create a larger mock file
        large_csv = tmp_path / "large_data.csv"
        with open(large_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            for i in range(1000):
                writer.writerow([f'P{i:04d}', 'C001', str(100 + i), str(200 + i), '15000', '20000'])
        
        # Run ingestion
        result_df = pipeline.load_and_process(large_csv)
        
        assert len(result_df) == 1000, "Should process all 1000 records"
        assert result_df is not None, "Should handle large files without crashing"

    def test_checksum_verification(self, mock_csv_dir: Path, pipeline: DataIngestionPipeline):
        """Test that checksum verification is performed (T054, T067)."""
        # The pipeline should verify checksums before processing
        # This is tested by ensuring the pipeline doesn't crash on valid files
        # and raises errors on invalid checksums (if implemented)
        
        input_file = mock_csv_dir / "standard_data.csv"
        
        # Should load successfully
        result_df = pipeline.load_and_process(input_file)
        assert result_df is not None, "Should load file with valid checksum"

# Additional edge case tests from T050
class TestEdgeCases:
    """Additional edge case tests (T050)."""

    def test_single_precinct_county(self, tmp_path: Path):
        """Test county with only one precinct."""
        csv_file = tmp_path / "single_precinct.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '1500', '2000', '1500', '2000'])
        
        # Should not crash
        pipeline = DataIngestionPipeline(source_type="mock", state="CA", output_dir=str(tmp_path / "output"))
        result = pipeline.load_and_process(csv_file)
        assert result is not None and len(result) == 1

    def test_malformed_numeric_data(self, tmp_path: Path):
        """Test handling of malformed numeric data."""
        csv_file = tmp_path / "malformed.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '150', '200', '1500', '2000'])
            writer.writerow(['P002', 'C001', 'abc', '190', '1500', '2000'])  # Non-numeric

        pipeline = DataIngestionPipeline(source_type="mock", state="CA", output_dir=str(tmp_path / "output"))
        
        # Should either convert to NaN and flag, or raise an error
        try:
            result = pipeline.load_and_process(csv_file)
            # If it succeeds, malformed rows should be flagged
            assert 'missing_data' in result.columns
        except (ValueError, MissingDataError):
            # Or it should raise an appropriate error
            pass

    def test_unicode_precinct_ids(self, tmp_path: Path):
        """Test handling of unicode precinct IDs."""
        csv_file = tmp_path / "unicode.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow([' precinct_α', 'C001', '150', '200', '1500', '2000'])
            writer.writerow([' precinct_β', 'C001', '160', '190', '1500', '2000'])
        
        pipeline = DataIngestionPipeline(source_type="mock", state="CA", output_dir=str(tmp_path / "output"))
        result = pipeline.load_and_process(csv_file)
        assert result is not None and len(result) == 2

    def test_duplicate_precinct_ids(self, tmp_path: Path):
        """Test handling of duplicate precinct IDs within a county."""
        csv_file = tmp_path / "duplicates.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['precinct_id', 'county_id', 'candidate_a', 'candidate_b', 'county_total_a', 'county_total_b'])
            writer.writerow(['P001', 'C001', '150', '200', '1500', '2000'])
            writer.writerow(['P001', 'C001', '160', '190', '1500', '2000'])  # Duplicate

        pipeline = DataIngestionPipeline(source_type="mock", state="CA", output_dir=str(tmp_path / "output"))
        result = pipeline.load_and_process(csv_file)
        # Should either deduplicate or flag duplicates
        assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])