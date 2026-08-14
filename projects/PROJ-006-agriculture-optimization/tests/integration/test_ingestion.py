"""
Integration test skeleton for the ingestion pipeline (T015-T018).

This test validates the end-to-end execution of:
- Survey data collection (T015)
- Remote sensing data collection (T016)
- Spatial joining (T017)
- Feature engineering (T018)

It ensures that the pipeline produces a valid `data/processed/analysis_dataset.csv`
that adheres to the schema defined in `contracts/dataset.schema.yaml`.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cli.run_pipeline import main as run_pipeline_main
from src.config.schemas import validate_dataset_schema, AnalysisDatasetRecord
from src.utils.io_helpers import read_csv_strict, FatalError
from src.data.generators.synthetic_generator import check_real_data_exists


class TestIngestionPipeline:
    """Integration tests for the full data ingestion and processing pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before and after tests."""
        # Ensure data directories exist
        data_dir = PROJECT_ROOT / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        yield
        # Optional: cleanup generated files if needed for strict isolation
        # output_file = data_dir / "analysis_dataset.csv"
        # if output_file.exists():
        #     output_file.unlink()

    def test_pipeline_execution_and_output_existence(self):
        """
        Test that running the pipeline script successfully generates
        data/processed/analysis_dataset.csv.
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv"

        # Check if real data is available. If not, the pipeline should fail loudly
        # unless --synthetic is provided (which is not the default for integration).
        # We expect the pipeline to raise FatalError if real data is missing.
        # However, for the purpose of this skeleton test, we assume the environment
        # is set up correctly or we are testing the error path.
        
        # Attempt to run the pipeline
        try:
            # We run the main function directly. In a real CI environment, 
            # this would be executed via subprocess to capture stdout/stderr.
            run_pipeline_main()
        except FatalError as e:
            # If real data is missing, this is the expected behavior per T010/T010a
            # The test passes if the failure is explicit and loud.
            if "real data" in str(e).lower() or "missing" in str(e).lower():
                pytest.skip("Real data not available; pipeline correctly failed loudly.")
            else:
                raise e
        
        # If we reach here, the pipeline ran. Check for output.
        assert output_path.exists(), (
            f"Pipeline execution did not produce the expected output file: {output_path}"
        )

    def test_output_schema_compliance(self):
        """
        Test that the generated analysis_dataset.csv passes the schema validation
        defined in contracts/dataset.schema.yaml (via src.config.schemas).
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv"

        if not output_path.exists():
            pytest.skip("Output file not generated; skipping schema validation.")

        try:
            df = read_csv_strict(output_path)
        except Exception as e:
            pytest.fail(f"Failed to read output CSV strictly: {e}")

        if df.empty:
            pytest.skip("Output file is empty; skipping schema validation.")

        # Validate each row against the AnalysisDatasetRecord schema
        validation_errors = []
        for idx, row in df.iterrows():
            try:
                # Convert row to dict for validation
                record_dict = row.to_dict()
                # Remove non-serializable types if any (e.g., timestamps in some pandas versions)
                # For now, assuming standard types
                record = AnalysisDatasetRecord(**record_dict)
                validate_dataset_schema(record)
            except Exception as e:
                validation_errors.append(f"Row {idx}: {str(e)}")

        assert len(validation_errors) == 0, (
            f"Schema validation failed for {len(validation_errors)} rows:\n"
            + "\n".join(validation_errors[:5])  # Show first 5 errors
        )

    def test_required_columns_present(self):
        """
        Verify that the output file contains all required columns for analysis.
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv"

        if not output_path.exists():
            pytest.skip("Output file not generated; skipping column check.")

        df = read_csv_strict(output_path)

        required_columns = {
            "household_id",
            "CSA_Index",
            "Stability_Score",
            "HFIAS",
            "latitude",
            "longitude"
        }

        missing_columns = required_columns - set(df.columns)
        assert not missing_columns, (
            f"Missing required columns in analysis dataset: {missing_columns}"
        )

    def test_non_null_critical_fields(self):
        """
        Ensure critical fields (CSA_Index, Stability_Score) are not null.
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv"

        if not output_path.exists():
            pytest.skip("Output file not generated; skipping null check.")

        df = read_csv_strict(output_path)

        critical_fields = ["CSA_Index", "Stability_Score"]
        for field in critical_fields:
            null_count = df[field].isnull().sum()
            assert null_count == 0, (
                f"Field '{field}' contains {null_count} null values."
            )
        
        # Check sample size
        assert len(df) > 0, "Analysis dataset is empty."