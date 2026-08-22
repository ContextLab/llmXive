"""
Integration test skeleton for the ingestion pipeline (T014).

This test validates the implementation of T015-T022 by executing the full
ingestion pipeline and verifying the output artifact against the dataset schema.

Note: This test is expected to fail until T015-T022 are implemented.
It serves as a TDD contract test for the ingestion pipeline.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil
import json

# Ensure the project root is in the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.run_pipeline import main as run_pipeline_main
from src.config.schemas import validate_dataset_schema, AnalysisDatasetRecord
from src.utils.io_helpers import read_csv_strict, FatalError


class TestIngestionPipeline:
    """
    Integration tests for the end-to-end ingestion pipeline.
    
    These tests verify that:
    1. The pipeline runs without crashing (T015-T022 implementation).
    2. The output artifact `data/processed/analysis_dataset.csv` is generated.
    3. The output artifact passes the schema contract (T007).
    4. The output contains non-null values for critical fields (CSA_Index, Stability_Score).
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """
        Setup a temporary environment for the test run.
        We use a temporary directory to avoid polluting the actual data/ directory
        during test runs, but we mock the paths or run in a controlled env.
        
        For this skeleton, we assume the pipeline can be pointed to a temp dir
        or we verify the existence of the file in the expected location if
        the pipeline is designed to run in-place.
        
        Given the task is a skeleton and T015-T022 are not implemented,
        we primarily test the *structure* of the test and the expectation of failure.
        """
        self.original_cwd = os.getcwd()
        self.temp_dir = tmp_path
        
        # Create the necessary directory structure in the temp dir to mimic the project
        # This allows the pipeline to run without immediate FileNotFoundError on dirs
        (self.temp_dir / "data").mkdir(parents=True)
        (self.temp_dir / "data" / "raw").mkdir()
        (self.temp_dir / "data" / "processed").mkdir()
        (self.temp_dir / "data" / "logs").mkdir()
        (self.temp_dir / "state").mkdir()
        (self.temp_dir / "state" / "projects").mkdir()
        (self.temp_dir / "contracts").mkdir()
        
        # Copy necessary config files if they exist in the real project to temp
        # (In a real CI, these would be present)
        src_dir = project_root
        if (src_dir / "contracts" / "dataset.schema.yaml").exists():
            shutil.copy(src_dir / "contracts" / "dataset.schema.yaml", self.temp_dir / "contracts")
        
        if (src_dir / "src" / "config" / "constants.py").exists():
            # We might need to copy config if it has relative paths, but for now
            # we rely on the pipeline logic.
            pass

        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)

    def test_pipeline_execution_exists(self):
        """
        Verify that the pipeline entry point exists and can be invoked.
        This test will fail if T019 (run_pipeline.py) is missing.
        """
        # The import at the top of this file already checks if the module exists.
        # We assert that the function is callable.
        assert callable(run_pipeline_main)

    def test_output_artifact_generation(self):
        """
        Verify that the pipeline generates the expected output artifact.
        
        Expected artifact: data/processed/analysis_dataset.csv
        This test expects the pipeline to run and create this file.
        
        Current Status: EXPECTED TO FAIL (T015-T022 not implemented).
        """
        # We run the pipeline with a flag to avoid hanging on real data fetch
        # if the synthetic generator is not yet wired correctly for this specific
        # integration context, or we rely on the synthetic generator (T010/T010a).
        # 
        # Since T010a wires the synthetic generator for CI, we simulate CI=true.
        os.environ["CI"] = "true"
        
        # Construct args for the main function
        # We assume the pipeline accepts --dry-run or similar, but the spec says
        # it should run. If it fails due to missing real data and no synthetic fallback,
        # that is a failure of T010a, not this test logic.
        #
        # We capture the exit code or exception.
        try:
            # Note: run_pipeline_main usually takes sys.argv. We simulate it.
            # If the implementation is strictly CLI based, we might need subprocess.
            # However, the provided API surface shows `main` in run_pipeline.
            # We assume it handles args or we pass a mock sys.argv.
            
            # For a robust test, we use subprocess to capture stdout/stderr
            # and ensure the process exits cleanly.
            import subprocess
            
            cmd = [
                sys.executable, "-m", "src.cli.run_pipeline",
                # "--dry-run", # If supported, use this to speed up
            ]
            
            # We run it. If T015-T022 are missing, this will likely crash or fail loudly.
            # The test passes if the crash is expected (i.e., the test is a skeleton).
            # But the requirement is "Write integration test skeleton".
            # The skeleton should assert the *expectation* of success once implemented.
            
            # For now, we assert that the file exists after a successful run.
            # Since it won't run successfully yet, we expect an exception or file missing.
            # We structure the test to fail gracefully with a clear message.
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # If the pipeline ran successfully, the file should exist.
            output_path = Path("data/processed/analysis_dataset.csv")
            
            if result.returncode != 0:
                # The pipeline failed. This is expected for T014 (skeleton)
                # until T015-T022 are done.
                # We record the error for debugging but the test itself
                # documents the requirement.
                pytest.fail(
                    f"Pipeline execution failed (expected until T015-T022 implemented). "
                    f"Return code: {result.returncode}\n"
                    f"Stderr: {result.stderr}\n"
                    f"Stdout: {result.stdout}"
                )
            
            # If we get here, the pipeline ran. Check for the file.
            assert output_path.exists(), f"Expected output file {output_path} was not generated."
            
        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution timed out.")

    def test_output_schema_validation(self):
        """
        Verify that the generated output artifact validates against the dataset schema.
        
        This test depends on T007 (schema creation) and T022 (output generation).
        """
        output_path = Path("data/processed/analysis_dataset.csv")
        
        if not output_path.exists():
            # If the file doesn't exist, we can't validate it.
            # This is a secondary failure to the execution failure.
            pytest.skip("Output file not generated. Skipping schema validation.")
        
        # Load the data
        try:
            df = read_csv_strict(output_path)
        except FatalError as e:
            pytest.fail(f"Failed to read output CSV: {e}")
        
        # Validate against schema
        # The schema path is expected to be in contracts/dataset.schema.yaml
        schema_path = Path("contracts/dataset.schema.yaml")
        
        if not schema_path.exists():
            pytest.fail("Dataset schema contract not found. Ensure T007 is implemented.")
        
        try:
            # We assume the validate_dataset_schema function from src.config.schemas
            # can take a dataframe or path. The API surface says:
            # validate_dataset_schema (from src.config.schemas)
            # We check the signature. If it expects a file path:
            valid = validate_dataset_schema(str(output_path))
            assert valid, "Dataset failed schema validation."
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")

    def test_critical_fields_non_null(self):
        """
        Verify that critical fields (CSA_Index, Stability_Score) are not null.
        
        This ensures the feature engineering (T018b) actually computed values.
        """
        output_path = Path("data/processed/analysis_dataset.csv")
        
        if not output_path.exists():
            pytest.skip("Output file not generated.")
        
        df = read_csv_strict(output_path)
        
        required_fields = ["CSA_Index", "Stability_Score"]
        
        for field in required_fields:
            assert field in df.columns, f"Required field '{field}' missing from output."
            null_count = df[field].isnull().sum()
            assert null_count == 0, f"Field '{field}' contains {null_count} null values."

    def test_sample_size_adequacy(self):
        """
        Verify that the dataset meets the minimum sample size requirement (N > 300).
        
        Per T017c and T021, if N < 300, aggregation should have occurred.
        This test checks the final row count.
        """
        output_path = Path("data/processed/analysis_dataset.csv")
        
        if not output_path.exists():
            pytest.skip("Output file not generated.")
        
        df = read_csv_strict(output_path)
        
        # Check if the file is the aggregated one or the household one
        # The task description says output is `analysis_dataset.csv`
        # If T021 triggered, it might be `analysis_dataset_village_aggregated.csv`
        # but T022 says "Generate `data/processed/analysis_dataset.csv` (or ...)"
        # We check the existence of the main one first.
        
        assert len(df) >= 300, f"Sample size {len(df)} is below the required threshold of 300."

    def test_linkage_validation_log_exists(self):
        """
        Verify that T017c produced the linkage validation log.
        
        Expected file: data/logs/linkage_validation.json
        """
        log_path = Path("data/logs/linkage_validation.json")
        
        # If the pipeline ran successfully, this log should exist.
        if not log_path.exists():
            # It might not exist if the pipeline failed early or T017c is missing.
            # We assert it exists if the pipeline is considered "complete".
            # For the skeleton, we assert existence as a requirement.
            pytest.fail("Linkage validation log not found. Ensure T017c is implemented.")
        
        # Validate the JSON structure
        try:
            with open(log_path, "r") as f:
                data = json.load(f)
            
            assert "linkage_percentage" in data, "Linkage percentage missing from log."
            assert "total_valid_households" in data, "Total valid households missing from log."
        except json.JSONDecodeError:
            pytest.fail("Linkage validation log is not valid JSON.")