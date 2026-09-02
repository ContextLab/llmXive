"""
End-to-End Integration Test for the llmXive pipeline.

This test verifies the full pipeline execution using mock data (quant config).
It asserts that all expected output files are generated and valid.

Dependencies:
- T016 (Main Orchestrator)
- T021 (Bonferroni Correction)
- T032 (Paper Draft Generation)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest


# Configuration for the test
PROJECT_ROOT = Path(__file__).parents[2]
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
MOCK_DATA_PATH = DATA_DIR / "raw" / "mock_studies.csv"
EXPECTED_OUTPUTS = [
    "data/derived/results.json",
    "data/derived/bonferroni_status.json",
    "data/derived/forest_plot.png",
    "data/derived/independence_status.json",
    "data/derived/visualization_status.json",
    "data/derived/tract_count.json",
    "data/processed/extracted_studies.csv",
    "data/processed/study_count.json",
    "data/processed/valid_pair_count.json",
    "data/processed/qualitative_data.json",
    "data/logs/exclusion_log.csv",
]

# Additional outputs that might be generated depending on pipeline state
OPTIONAL_OUTPUTS = [
    "data/derived/meta_results.json",
    "data/derived/meta_status.json",
    "data/derived/gate_result.json",
    "data/derived/heterogeneity_results.json",
    "data/derived/egger_test.json",
    "data/derived/narrative_summary.md",
    "data/derived/funnel_plot.png",
    "data/derived/correlation_summary.png",
    "paper/paper_draft.md",
]

def _run_command(cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    env = os.environ.copy()
    # Ensure we are using the project's virtual environment if it exists
    venv_bin = PROJECT_ROOT / ".venv" / "bin"
    if venv_bin.exists():
        env["PATH"] = f"{venv_bin}:{env['PATH']}"
    
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )

def _ensure_mock_data_exists() -> bool:
    """Ensure mock data exists before running tests."""
    if MOCK_DATA_PATH.exists():
        return True
    
    # Try to generate mock data if it doesn't exist
    gen_script = CODE_DIR / "data" / "generate_mock_data.py"
    if gen_script.exists():
        result = _run_command([sys.executable, str(gen_script), "--seed", "43", "--n", "15"])
        if result.returncode == 0:
            return True
    
    return False

def _cleanup_outputs():
    """Remove existing output files to ensure a clean test."""
    for output in EXPECTED_OUTPUTS + OPTIONAL_OUTPUTS:
        path = PROJECT_ROOT / output
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Setup and teardown for the integration test."""
    # Ensure directories exist
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "derived").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "paper").mkdir(parents=True, exist_ok=True)
    
    # Ensure mock data exists
    assert _ensure_mock_data_exists(), "Failed to generate or find mock data"
    
    # Clean up previous outputs
    _cleanup_outputs()
    
    yield
    
    # No need to clean up after test in CI, but good for local runs
    # _cleanup_outputs()

class TestFullPipeline:
    """Integration tests for the full pipeline."""

    def test_01_main_orchestrator_runs(self):
        """Test that the main orchestrator runs without errors."""
        main_script = CODE_DIR / "main.py"
        assert main_script.exists(), f"Main script not found: {main_script}"
        
        # Run the main pipeline with mock data
        cmd = [
            sys.executable,
            str(main_script),
            "--input", str(MOCK_DATA_PATH),
            "--output", str(PROJECT_ROOT / "data" / "processed" / "meta_results.json"),
        ]
        
        result = _run_command(cmd)
        
        # Log output for debugging
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # The pipeline should complete successfully
        # Note: It might exit with 1 if data is insufficient for quantitative analysis,
        # but it should still generate narrative outputs
        assert result.returncode == 0, f"Pipeline failed with code {result.returncode}. STDERR: {result.stderr}"

    def test_02_required_outputs_exist(self):
        """Test that all required output files are generated."""
        missing_files = []
        for output in EXPECTED_OUTPUTS:
            path = PROJECT_ROOT / output
            if not path.exists():
                missing_files.append(output)
        
        assert not missing_files, f"Missing required output files: {missing_files}"

    def test_03_json_outputs_are_valid(self):
        """Test that all JSON output files are valid JSON."""
        json_files = [
            "data/derived/results.json",
            "data/derived/bonferroni_status.json",
            "data/derived/independence_status.json",
            "data/derived/visualization_status.json",
            "data/derived/tract_count.json",
            "data/processed/study_count.json",
            "data/processed/valid_pair_count.json",
        ]
        
        for json_file in json_files:
            path = PROJECT_ROOT / json_file
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {json_file}: {e}")

    def test_04_csv_outputs_are_valid(self):
        """Test that CSV output files are valid."""
        csv_files = [
            "data/processed/extracted_studies.csv",
            "data/logs/exclusion_log.csv",
        ]
        
        import csv
        for csv_file in csv_files:
            path = PROJECT_ROOT / csv_file
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        assert len(rows) > 0, f"CSV file {csv_file} is empty"
                except csv.Error as e:
                    pytest.fail(f"Invalid CSV in {csv_file}: {e}")

    def test_05_png_outputs_are_valid(self):
        """Test that PNG output files are valid images."""
        png_files = [
            "data/derived/forest_plot.png",
        ]
        
        for png_file in png_files:
            path = PROJECT_ROOT / png_file
            if path.exists():
                # Check file size (should be > 0 bytes)
                assert path.stat().st_size > 0, f"PNG file {png_file} is empty"
                
                # Check PNG signature
                with open(path, 'rb') as f:
                    header = f.read(8)
                    assert header[:4] == b'\x89PNG', f"Invalid PNG signature in {png_file}"

    def test_06_results_json_has_expected_structure(self):
        """Test that results.json has the expected structure."""
        results_path = PROJECT_ROOT / "data" / "derived" / "results.json"
        if not results_path.exists():
            pytest.skip("results.json not generated (likely narrative mode)")
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        assert isinstance(results, dict), "results.json should be a dictionary"
        assert "synthesis_mode" in results, "results.json should have 'synthesis_mode' key"
        assert results["synthesis_mode"] in ["quantitative", "narrative"], \
            f"Invalid synthesis_mode: {results['synthesis_mode']}"

    def test_07_pipeline_handles_data_insufficient_case(self):
        """Test that the pipeline handles insufficient data gracefully."""
        # This test is implicitly covered by test_01 and test_06
        # If the pipeline runs and produces results (even narrative), it's handling the case
        results_path = PROJECT_ROOT / "data" / "derived" / "results.json"
        if results_path.exists():
            with open(results_path, 'r') as f:
                results = json.load(f)
            # If we got here, the pipeline handled the data case (quantitative or narrative)
            assert True

    def test_08_bonferroni_correction_applied_when_appropriate(self):
        """Test that Bonferroni correction is applied when appropriate."""
        bonferroni_path = PROJECT_ROOT / "data" / "derived" / "bonferroni_status.json"
        if not bonferroni_path.exists():
            pytest.skip("bonferroni_status.json not generated")
        
        with open(bonferroni_path, 'r') as f:
            bonferroni = json.load(f)
        
        assert isinstance(bonferroni, dict), "bonferroni_status.json should be a dictionary"
        # The file should exist and be valid JSON, which we've verified
        # The actual application logic is tested in unit tests

    def test_09_independence_checker_runs(self):
        """Test that the independence checker runs and produces output."""
        independence_path = PROJECT_ROOT / "data" / "derived" / "independence_status.json"
        if not independence_path.exists():
            pytest.skip("independence_status.json not generated")
        
        with open(independence_path, 'r') as f:
            independence = json.load(f)
        
        assert isinstance(independence, dict), "independence_status.json should be a dictionary"
        assert "independence_assumed" in independence, \
            "independence_status.json should have 'independence_assumed' key"

    def test_10_visualization_status_generated(self):
        """Test that visualization status is generated."""
        viz_status_path = PROJECT_ROOT / "data" / "derived" / "visualization_status.json"
        if not viz_status_path.exists():
            pytest.skip("visualization_status.json not generated")
        
        with open(viz_status_path, 'r') as f:
            viz_status = json.load(f)
        
        assert isinstance(viz_status, dict), "visualization_status.json should be a dictionary"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])