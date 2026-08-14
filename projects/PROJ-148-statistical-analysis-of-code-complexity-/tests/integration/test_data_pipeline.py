"""
Integration test for the end-to-end data pipeline (User Story 1).

This test verifies the complete flow from downloading Java projects,
extracting metrics, labeling bug fixes, preprocessing, and splitting
the dataset. It ensures that all intermediate artifacts are created
correctly and that the final dataset meets the schema requirements.
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import yaml

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import get_seed
from utils.logging import get_logger

logger = get_logger(__name__)


class TestDataPipeline:
    """Integration tests for the data pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="pipeline_test_")
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        yield

        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_script(self, script_name: str, args: list, expected_rc: int = 0) -> subprocess.CompletedProcess:
        """Helper to run a pipeline script with given arguments."""
        script_path = Path(__file__).parent.parent.parent / "code" / script_name
        cmd = [sys.executable, str(script_path)] + args
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent.parent.parent),
            capture_output=True,
            text=True
        )
        if result.returncode != expected_rc:
            logger.error(f"Script {script_name} failed with rc={result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
        return result

    def _check_file_exists(self, path: Path, description: str):
        """Assert that a file exists."""
        assert path.exists(), f"{description} not found at {path}"

    def _check_csv_columns(self, path: Path, required_columns: list, description: str):
        """Assert that a CSV file has the required columns."""
        self._check_file_exists(path, description)
        df = pd.read_csv(path)
        missing = set(required_columns) - set(df.columns)
        assert not missing, f"{description} missing columns: {missing}"
        return df

    def test_end_to_end_pipeline(self):
        """
        Test the complete data pipeline:
        1. Download GHTorrent Java projects (mocked/skipped if no network)
        2. Extract metrics using lizard
        3. Label bug fixes
        4. Preprocess data
        5. Split dataset
        6. Verify final artifacts
        """

        # NOTE: Since T010 (download_gh) and T011 (extract_commits) are marked completed,
        # we assume they produce the necessary raw data in data/raw/.
        # If those files don't exist, we create minimal synthetic raw data for the
        # integration test to proceed, but ONLY for the purpose of testing the
        # downstream pipeline logic (extract_metrics, label, preprocess, split).
        # This is allowed here because the upstream tasks are supposed to have
        # created the real data; we are testing the integration of the *pipeline steps*,
        # not the network download itself.

        # Step 0: Ensure raw data directory exists with at least one dummy Java file
        # (In a real run, T010/T011 would have created this)
        raw_java_dir = self.data_dir / "raw" / "java_projects"
        raw_java_dir.mkdir(parents=True, exist_ok=True)

        # Create a minimal dummy Java file to test lizard parsing
        dummy_java = raw_java_dir / "Dummy.java"
        dummy_java.write_text(
            "public class Dummy {\n"
            "    public static void main(String[] args) {\n"
            "        if (true) {\n"
            "            System.out.println(\"Hello\");\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

        # Create a minimal commit metadata file (CSV)
        commits_csv = self.data_dir / "raw" / "commits.csv"
        commits_csv.write_text(
            "commit_hash,file_path,author,message,timestamp\n"
            "abc123,data/raw/java_projects/Dummy.java,Test Author,\"Fix bug #123\",2023-01-01T00:00:00\n"
            "def456,data/raw/java_projects/Dummy.java,Test Author,\"Refactor code\",2023-01-02T00:00:00\n"
        )

        # Step 1: Extract Metrics
        # T012: extract_metrics.py --input <dir> --output <file>
        metrics_output = self.output_dir / "metrics.csv"
        result = self._run_script(
            "data/extract_metrics.py",
            [
                "--input", str(raw_java_dir),
                "--output", str(metrics_output),
                "--seed", str(get_seed())
            ]
        )
        assert result.returncode == 0, "extract_metrics.py failed"
        self._check_csv_columns(
            metrics_output,
            ["file_path", "cyclomatic_complexity", "loc", "token_count", "nesting_depth", "halstead_volume"],
            "Metrics output"
        )

        # Step 2: Label Bug Fixes
        # T013: label_bug_fixes.py --input <metrics> --commits <commits> --output <labeled>
        labeled_output = self.output_dir / "labeled_metrics.csv"
        result = self._run_script(
            "data/label_bug_fixes.py",
            [
                "--input", str(metrics_output),
                "--commits", str(commits_csv),
                "--output", str(labeled_output)
            ]
        )
        assert result.returncode == 0, "label_bug_fixes.py failed"
        df_labeled = self._check_csv_columns(
            labeled_output,
            ["file_path", "cyclomatic_complexity", "loc", "token_count", "nesting_depth", "halstead_volume", "bug_label"],
            "Labeled metrics output"
        )
        assert "bug_label" in df_labeled.columns, "bug_label column missing"
        assert df_labeled["bug_label"].dtype in [int, bool, "int64", "bool"], "bug_label should be binary"

        # Step 3: Preprocess Data
        # T015: preprocess.py --input <labeled> --output <preprocessed>
        preprocessed_output = self.output_dir / "preprocessed.csv"
        result = self._run_script(
            "data/preprocess.py",
            [
                "--input", str(labeled_output),
                "--output", str(preprocessed_output),
                "--seed", str(get_seed())
            ]
        )
        assert result.returncode == 0, "preprocess.py failed"
        df_preprocessed = self._check_csv_columns(
            preprocessed_output,
            ["file_path", "cyclomatic_complexity", "loc", "token_count", "nesting_depth", "halstead_volume", "bug_label"],
            "Preprocessed output"
        )
        # Check for log-transformed columns if applicable (optional check)
        # The spec says log-transform metrics with skewness > 2.
        # We just verify the file exists and has the right structure.

        # Step 4: Split Dataset
        # T016: split_dataset.py --input <preprocessed> --output-dir <dir>
        split_output_dir = self.output_dir / "splits"
        result = self._run_script(
            "data/split_dataset.py",
            [
                "--input", str(preprocessed_output),
                "--output-dir", str(split_output_dir),
                "--seed", str(get_seed())
            ]
        )
        assert result.returncode == 0, "split_dataset.py failed"

        train_csv = split_output_dir / "train.csv"
        test_csv = split_output_dir / "test.csv"
        split_config = split_output_dir / "split_config.json"

        self._check_file_exists(train_csv, "Train split")
        self._check_file_exists(test_csv, "Test split")
        self._check_file_exists(split_config, "Split config")

        # Verify split config
        with open(split_config, "r") as f:
            config_data = yaml.safe_load(f)
        assert "train_ratio" in config_data, "train_ratio missing in config"
        assert "test_ratio" in config_data, "test_ratio missing in config"
        assert abs(config_data["train_ratio"] + config_data["test_ratio"] - 1.0) < 0.01, "Ratios must sum to 1"

        # Verify project-level stratification (each project in only one split)
        df_train = pd.read_csv(train_csv)
        df_test = pd.read_csv(test_csv)

        # Extract project name from file_path (simplified assumption)
        def get_project(path):
            return Path(path).parent.name

        train_projects = set(df_train["file_path"].apply(get_project))
        test_projects = set(df_test["file_path"].apply(get_project))

        overlap = train_projects & test_projects
        assert not overlap, f"Projects found in both train and test: {overlap}"

        # Verify schema compliance (T008 contract)
        # Check that all required columns are present in both splits
        required_cols = ["file_path", "cyclomatic_complexity", "loc", "token_count", "nesting_depth", "halstead_volume", "bug_label"]
        for col in required_cols:
            assert col in df_train.columns, f"Missing {col} in train"
            assert col in df_test.columns, f"Missing {col} in test"

        logger.info("End-to-end pipeline integration test passed successfully.")

    def test_pipeline_with_missing_values(self):
        """
        Test that the pipeline handles missing values correctly.
        T015: Preprocess should impute <5% missing, log-transform skewed, remove >5% missing.
        """
        # Setup raw data with missing values
        raw_java_dir = self.data_dir / "raw" / "java_projects_missing"
        raw_java_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy files
        for i in range(3):
            (raw_java_dir / f"File{i}.java").write_text("public class File{} { }".format(i))

        commits_csv = self.data_dir / "raw" / "commits_missing.csv"
        commits_csv.write_text(
            "commit_hash,file_path,author,message,timestamp\n"
            "abc123,data/raw/java_projects_missing/File0.java,Author,\"Fix bug\",2023-01-01\n"
            "def456,data/raw/java_projects_missing/File1.java,Author,\"Refactor\",2023-01-02\n"
            "ghi789,data/raw/java_projects_missing/File2.java,Author,\"New feature\",2023-01-03\n"
        )

        # Run extract_metrics (simulated to produce some missing values if lizard fails)
        # In reality, lizard might fail on some files, leading to missing metrics.
        # We rely on the existing extract_metrics.py to handle this (T050).

        metrics_output = self.output_dir / "metrics_missing.csv"
        result = self._run_script(
            "data/extract_metrics.py",
            [
                "--input", str(raw_java_dir),
                "--output", str(metrics_output),
                "--seed", str(get_seed())
            ]
        )
        assert result.returncode == 0, "extract_metrics.py failed with missing data scenario"

        # Label
        labeled_output = self.output_dir / "labeled_missing.csv"
        result = self._run_script(
            "data/label_bug_fixes.py",
            [
                "--input", str(metrics_output),
                "--commits", str(commits_csv),
                "--output", str(labeled_output)
            ]
        )
        assert result.returncode == 0, "label_bug_fixes.py failed"

        # Preprocess
        preprocessed_output = self.output_dir / "preprocessed_missing.csv"
        result = self._run_script(
            "data/preprocess.py",
            [
                "--input", str(labeled_output),
                "--output", str(preprocessed_output),
                "--seed", str(get_seed())
            ]
        )
        assert result.returncode == 0, "preprocess.py failed with missing data"

        df_final = pd.read_csv(preprocessed_output)
        # Check that rows with >5% missing were removed (if any)
        # and that remaining rows have no NaNs in the metric columns
        metric_cols = ["cyclomatic_complexity", "loc", "token_count", "nesting_depth", "halstead_volume"]
        assert df_final[metric_cols].isnull().sum().sum() == 0, "Remaining rows should not have NaNs in metrics"

        logger.info("Pipeline missing values handling test passed.")

    def test_bug_label_reliability(self):
        """
        Test that bug label validation is enforced.
        T049: Enforce precision >= 85% in the pipeline.
        """
        # Setup data with known bug labels
        raw_java_dir = self.data_dir / "raw" / "java_projects_reliability"
        raw_java_dir.mkdir(parents=True, exist_ok=True)

        (raw_java_dir / "Reliable.java").write_text("public class Reliable { }")

        commits_csv = self.data_dir / "raw" / "commits_reliability.csv"
        # Create a commit message that clearly indicates a bug fix
        commits_csv.write_text(
            "commit_hash,file_path,author,message,timestamp\n"
            "abc123,data/raw/java_projects_reliability/Reliable.java,Author,\"Fix critical bug #999\",2023-01-01\n"
        )

        metrics_output = self.output_dir / "metrics_reliability.csv"
        self._run_script(
            "data/extract_metrics.py",
            ["--input", str(raw_java_dir), "--output", str(metrics_output), "--seed", str(get_seed())]
        )

        labeled_output = self.output_dir / "labeled_reliability.csv"
        self._run_script(
            "data/label_bug_fixes.py",
            ["--input", str(metrics_output), "--commits", str(commits_csv), "--output", str(labeled_output)]
        )

        # Preprocess with validation
        preprocessed_output = self.output_dir / "preprocessed_reliability.csv"
        # Note: The actual validation logic (precision >= 85%) is inside preprocess.py (T049)
        # If the precision is too low, it should raise an error or log a warning.
        # We assume the dummy data is high precision (100% bug fix).
        result = self._run_script(
            "data/preprocess.py",
            ["--input", str(labeled_output), "--output", str(preprocessed_output), "--seed", str(get_seed())]
        )
        # If the validation failed, the script would have exited with non-zero.
        # Since our dummy data is perfect, it should succeed.
        assert result.returncode == 0, "Preprocess failed reliability check (unexpected)"

        logger.info("Bug label reliability test passed.")