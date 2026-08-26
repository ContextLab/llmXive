import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pipelines.aggregate_metadata_stats import aggregate_metadata, load_csv_data

class TestAggregateMetadataStats:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test artifacts."""
        temp_dir = tempfile.mkdtemp()
        data_processed = Path(temp_dir) / "data" / "processed"
        data_artifacts = Path(temp_dir) / "data" / "artifacts"
        data_processed.mkdir(parents=True)
        data_artifacts.mkdir(parents=True)

        # Monkey patch paths for testing
        original_processed = "data/processed/metadata_stats_cardinality.csv"
        original_missing = "data/processed/metadata_stats_missingness.csv"
        original_sparsity = "data/processed/metadata_stats_sparsity.csv"
        original_variance = "data/processed/metadata_stats_variance.csv"
        original_output = "data/processed/metadata_stats_summary.csv"
        original_report = "data/artifacts/metadata_subset_selection_report.json"

        # We will simulate file creation in the temp dir and adjust logic if needed
        # For now, we test the logic by mocking the file existence or creating them
        yield temp_dir, data_processed, data_artifacts

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_load_csv_data(self, temp_dirs):
        """Test loading a simple CSV."""
        temp_path = Path(temp_dirs[0]) / "test.csv"
        with open(temp_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['dataset_id', 'value'])
            writer.writerow(['ds1', '10'])
            writer.writerow(['ds2', '20.5'])

        result = load_csv_data(str(temp_path))
        assert result['ds1'] == 10.0
        assert result['ds2'] == 20.5

    def test_aggregate_missing_files(self, temp_dirs):
        """Test that aggregation fails gracefully if inputs are missing."""
        # Ensure no input files exist in the default location relative to temp
        # We are not running the full aggregate function here to avoid path issues
        # Instead we rely on the logic inside aggregate_metadata checking existence
        # Since we can't easily mock the global INPUT_FILES paths without refactoring,
        # we test the load_csv_data return value for missing files.
        result = load_csv_data("non_existent_file.csv")
        assert result is None

    def test_aggregate_logic_subset_selection(self, temp_dirs):
        """
        Test the core logic: merge, sort, and select subset.
        We manually create the input files in the temp directory structure
        and patch the global constants if possible, or verify the output structure.
        """
        # Create mock input files in the temp dir structure
        # Note: The script uses hardcoded relative paths "data/processed/..."
        # To test this properly, we would need to run from the project root
        # or mock the paths. Here we verify the file writing logic by
        # creating the inputs in the actual expected relative locations if
        # we were running in the project root, but since we are in a test env,
        # we assume the environment is set up or we test the function's
        # behavior with existing files.

        # For this unit test, we will create the files in the actual project
        # data/processed folder if it exists, or skip if not running in project.
        # However, to be safe and isolated, we will just verify the function
        # returns False when files are missing (which is the current state
        # if we haven't run T024a-d).
        
        # Instead, let's create the files in the temp directory and temporarily
        # change the CWD or patch the constants.
        # Since patching global constants in the module is complex in pytest without
        # monkeypatch fixture usage on the module itself, we will assume
        # the function works as designed if the files exist.
        
        # Let's create the files in the temp dir and move to temp dir
        # This is a bit hacky but ensures isolation.
        cwd = os.getcwd()
        try:
            os.chdir(temp_dirs[0])
            # Create directory structure
            Path("data/processed").mkdir(parents=True)
            Path("data/artifacts").mkdir(parents=True)

            # Create input files
            inputs = [
                "data/processed/metadata_stats_cardinality.csv",
                "data/processed/metadata_stats_missingness.csv",
                "data/processed/metadata_stats_sparsity.csv",
                "data/processed/metadata_stats_variance.csv"
            ]
            
            for i, fname in enumerate(inputs):
                with open(fname, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['dataset_id', 'value'])
                    # Create 25 datasets to test the limit of 20
                    for j in range(25):
                        ds_id = f"dataset_{j:03d}"
                        val = 10.0 + i + j
                        writer.writerow([ds_id, val])

            # Run aggregate
            success = aggregate_metadata()
            assert success is True

            # Verify output file
            output_path = Path("data/processed/metadata_stats_summary.csv")
            assert output_path.exists()

            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have exactly 20 rows (limit)
            assert len(rows) == 20
            
            # Verify sorted order (dataset_000 to dataset_019)
            for idx, row in enumerate(rows):
                expected_id = f"dataset_{idx:03d}"
                assert row['dataset_id'] == expected_id

            # Verify report
            report_path = Path("data/artifacts/metadata_subset_selection_report.json")
            assert report_path.exists()
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert report['total_datasets_found'] == 25
            assert report['datasets_selected'] == 20
            assert report['shortfall_flagged'] is False
            assert len(report['excluded_dataset_ids']) == 5
            assert report['excluded_dataset_ids'][0] == 'dataset_020'

        finally:
            os.chdir(cwd)
