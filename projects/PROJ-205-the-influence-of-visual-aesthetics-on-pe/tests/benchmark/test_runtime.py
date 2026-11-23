"""
Benchmark and validation tests for the research pipeline.
These tests ensure performance constraints and data integrity.
"""

import os
import sys
import time
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Constants
MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_RUNTIME_SECONDS = 1800  # 30 minutes
MOCK_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "submissions.csv"
ANALYSIS_SCRIPTS = [
    PROJECT_ROOT / "code" / "analysis" / "00_preprocess.py",
    PROJECT_ROOT / "code" / "analysis" / "01_anova.py",
    PROJECT_ROOT / "code" / "analysis" / "02_pairwise.py",
    PROJECT_ROOT / "code" / "analysis" / "03_mixed_effects.py",
    PROJECT_ROOT / "code" / "analysis" / "06_power_analysis.py",
]


class TestFileSize:
    """Tests for file size constraints."""

    def test_submissions_csv_size_under_5mb(self):
        """
        T043c: Verify that data/raw/submissions.csv size < 5MB for N=250.
        
        This test asserts that the raw submissions file does not exceed
        the 5MB limit, ensuring the dataset remains lightweight for
        benchmarking and distribution.
        """
        assert MOCK_DATA_PATH.exists(), (
            f"Mock data file not found: {MOCK_DATA_PATH}. "
            "Please run code/utils/generate_mock_data.py first."
        )

        file_size_bytes = MOCK_DATA_PATH.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        assert file_size_bytes < MAX_CSV_SIZE_BYTES, (
            f"Submissions file size ({file_size_mb:.2f} MB) exceeds limit "
            f"of {MAX_CSV_SIZE_BYTES / (1024 * 1024):.2f} MB."
        )


class TestRuntime:
    """Tests for pipeline execution time."""

    @pytest.mark.skipif(
        not MOCK_DATA_PATH.exists(),
        reason="Mock data not generated. Run code/utils/generate_mock_data.py first."
    )
    def test_full_pipeline_runtime(self):
        """
        Verify that the full analysis pipeline completes within 30 minutes.
        
        This test times the execution of the core analysis scripts to ensure
        they are efficient enough for the target hardware constraints.
        """
        start_time = time.time()

        # Run Preprocess
        print("Running 00_preprocess.py...")
        # Note: We use subprocess to capture exit codes properly if needed,
        # but for timing we can import and run main if signatures allow.
        # Given the script structure, we invoke via system call for robustness.
        import subprocess
        
        scripts_to_run = [
            ["python", str(PROJECT_ROOT / "code" / "analysis" / "00_preprocess.py")],
            ["python", str(PROJECT_ROOT / "code" / "analysis" / "01_anova.py"), "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"), "--output", str(PROJECT_ROOT / "data" / "processed" / "anova_results.json")],
            ["python", str(PROJECT_ROOT / "code" / "analysis" / "02_pairwise.py"), "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"), "--output", str(PROJECT_ROOT / "data" / "processed" / "pairwise_results.json")],
            ["python", str(PROJECT_ROOT / "code" / "analysis" / "03_mixed_effects.py"), "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"), "--output", str(PROJECT_ROOT / "data" / "processed" / "mixed_effects_results.json")],
        ]

        for script_cmd in scripts_to_run:
            try:
                result = subprocess.run(
                    script_cmd,
                    cwd=str(PROJECT_ROOT),
                    timeout=MAX_RUNTIME_SECONDS,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    pytest.fail(f"Script failed: {' '.join(script_cmd)}\n{result.stderr}")
            except subprocess.TimeoutExpired:
                pytest.fail(f"Script timed out: {' '.join(script_cmd)}")

        elapsed = time.time() - start_time
        assert elapsed < MAX_RUNTIME_SECONDS, (
            f"Full pipeline took {elapsed:.2f}s, exceeding limit of {MAX_RUNTIME_SECONDS}s."
        )
        print(f"Pipeline completed in {elapsed:.2f}s.")


class TestDataIntegrity:
    """Tests for data schema and content validity."""

    @pytest.mark.skipif(
        not MOCK_DATA_PATH.exists(),
        reason="Mock data not generated."
    )
    def test_csv_schema_compliance(self):
        """Verify that the generated CSV matches the expected schema."""
        df = pd.read_csv(MOCK_DATA_PATH)
        
        expected_columns = {
            'participant_id', 'stimulus_id', 'credibility', 'professionalism',
            'timestamp', 'hashed_ip', 'age', 'education',
            'duplicate_flag', 'session_status', 'submission_status'
        }
        
        actual_columns = set(df.columns)
        
        missing = expected_columns - actual_columns
        assert not missing, f"Missing columns in CSV: {missing}"
        
        # Verify data types and ranges
        assert df['credibility'].between(1, 7).all(), "Credibility out of range [1, 7]"
        assert df['professionalism'].between(1, 7).all(), "Professionalism out of range [1, 7]"
        assert df['age'].between(18, 100).all(), "Age out of expected range"
        assert df['education'].isin(['High School', 'Bachelor', 'Master', 'PhD']).all(), "Invalid education level"

    @pytest.mark.skipif(
        not MOCK_DATA_PATH.exists(),
        reason="Mock data not generated."
    )
    def test_sample_size(self):
        """Verify that the mock data contains the expected number of participants."""
        df = pd.read_csv(MOCK_DATA_PATH)
        # Each participant should have 4 rows (one per stimulus)
        # Total rows = N * 4. If N=250, rows=1000.
        expected_rows = 250 * 4
        assert len(df) == expected_rows, (
            f"Expected {expected_rows} rows for N=250, got {len(df)}."
        )