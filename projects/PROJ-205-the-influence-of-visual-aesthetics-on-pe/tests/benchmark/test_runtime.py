"""
Benchmark tests for the analysis pipeline runtime and resource constraints.

This module verifies:
1. The full analysis pipeline completes within 30 minutes on a CPU-only runner.
2. The generated mock data file size is within acceptable limits (< 5MB for N=250).
"""

import os
import sys
import time
import subprocess
import pytest
from pathlib import Path

# Add project root to path to import utils if needed, though we mostly use subprocess
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import get_submissions_csv_path, get_project_root


def test_runtime_pipeline_completion():
    """
    Asserts that the full analysis pipeline completes within 30 minutes (1800 seconds)
    on a CPU-only runner using mock data.

    The pipeline includes:
    1. Preprocessing (01_preprocess.py)
    2. ANOVA (01_anova.py)
    3. Pairwise tests (02_pairwise.py)
    4. Report generation (03_report.py)
    5. Mixed Effects (04_mixed_effects.py)
    6. Robustness Report (05_robustness_report.py)
    7. Power Analysis (06_power_analysis.py)
    8. Duplicate Audit (07_duplicate_audit.py)
    """
    # Ensure mock data exists first
    mock_data_script = PROJECT_ROOT / "code" / "utils" / "generate_mock_data.py"
    submissions_path = get_submissions_csv_path()

    if not submissions_path.exists():
        print(f"Mock data not found at {submissions_path}. Generating...")
        result = subprocess.run(
            [sys.executable, str(mock_data_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Failed to generate mock data: {result.stderr}")

    if not submissions_path.exists():
        pytest.fail(f"Mock data file {submissions_path} still missing after generation attempt.")

    # Define the sequence of analysis commands
    # Note: We use relative paths from the code/analysis directory or absolute paths
    # The scripts expect --input and --output arguments.
    
    # We need to ensure the data directories exist
    data_processed = PROJECT_ROOT / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    commands = [
        # 1. Preprocess
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "01_preprocess.py"),
            "--input", str(submissions_path),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv")
        ],
        # 2. ANOVA
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "01_anova.py"),
            "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "anova_results.json")
        ],
        # 3. Pairwise
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "02_pairwise.py"),
            "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "pairwise_results.json")
        ],
        # 4. Report
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "03_report.py"),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "analysis_results.json")
        ],
        # 5. Mixed Effects
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "04_mixed_effects.py"),
            "--input", str(PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "mixed_effects_results.json")
        ],
        # 6. Robustness Report
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "05_robustness_report.py"),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "robustness_report.json")
        ],
        # 7. Power Analysis
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "06_power_analysis.py"),
            "--input", str(submissions_path),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "power_analysis_results.json")
        ],
        # 8. Duplicate Audit
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "analysis" / "07_duplicate_audit.py"),
            "--input", str(submissions_path),
            "--output", str(PROJECT_ROOT / "data" / "raw" / "duplicate_audit.csv")
        ]
    ]

    start_time = time.time()
    total_timeout = 30 * 60  # 30 minutes in seconds

    print(f"Starting pipeline benchmark. Timeout: {total_timeout} seconds.")

    for i, cmd in enumerate(commands):
        print(f"Running step {i+1}/{len(commands)}: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            pytest.fail(f"Pipeline step {i+1} failed with return code {result.returncode}. Error: {result.stderr}")
        
        elapsed = time.time() - start_time
        if elapsed > total_timeout:
            pytest.fail(f"Pipeline step {i+1} exceeded total timeout of {total_timeout} seconds.")

    total_elapsed = time.time() - start_time
    print(f"Pipeline completed successfully in {total_elapsed:.2f} seconds.")
    
    # Assert total time is within limit (with a small buffer for overhead)
    assert total_elapsed < total_timeout, f"Total pipeline time {total_elapsed:.2f}s exceeded {total_timeout}s limit."


def test_submissions_csv_file_size():
    """
    Asserts that data/raw/submissions.csv size is < 5MB for N=250 participants.
    """
    submissions_path = get_submissions_csv_path()
    project_root = get_project_root()
    
    # If the file doesn't exist, generate it first using the mock data script
    if not submissions_path.exists():
        mock_data_script = project_root / "code" / "utils" / "generate_mock_data.py"
        result = subprocess.run(
            [sys.executable, str(mock_data_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Failed to generate mock data: {result.stderr}")
    
    if not submissions_path.exists():
        pytest.fail(f"Submissions CSV not found at {submissions_path} after generation attempt.")

    file_size_bytes = submissions_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    max_size_bytes = 5 * 1024 * 1024  # 5 MB
    
    print(f"Submissions CSV size: {file_size_mb:.2f} MB ({file_size_bytes} bytes)")
    
    assert file_size_bytes < max_size_bytes, (
        f"Submissions CSV size ({file_size_mb:.2f} MB) exceeds limit (5.0 MB). "
        f"Size: {file_size_bytes} bytes."
    )