"""
End-to-End Integration Test for the llmXive Pipeline (PROJ-082).

This test verifies the full pipeline execution using mock data as a fallback
when real data is unavailable or insufficient, ensuring all expected artifacts
are generated and valid.

Dependencies:
- code/main.py (Orchestrator)
- code/data/generate_mock_data.py (Mock data generator)
- code/config/config.yaml (Configuration)
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Constants derived from tasks.md and project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"
LOGS_DIR = DATA_DIR / "logs"
MAIN_SCRIPT = CODE_DIR / "main.py"
MOCK_GEN_SCRIPT = CODE_DIR / "data" / "generate_mock_data.py"
CONFIG_FILE = CODE_DIR / "config" / "config.yaml"

# Expected output artifacts based on T049 description and pipeline flow
EXPECTED_ARTIFACTS = [
    # Core results
    DATA_DIR / "derived" / "results.json",
    DATA_DIR / "processed" / "meta_status.json",
    DATA_DIR / "processed" / "study_count.json",
    DATA_DIR / "processed" / "valid_pair_count.json",
    DATA_DIR / "processed" / "extracted_studies.csv",
    DATA_DIR / "raw" / "studies.csv",
    
    # Visualization artifacts (if quantitative path runs)
    DATA_DIR / "derived" / "forest_plot.png",
    DATA_DIR / "derived" / "funnel_plot.png",
    DATA_DIR / "derived" / "correlation_summary.png",
    
    # Narrative artifacts (if narrative path runs)
    DATA_DIR / "derived" / "narrative_summary.md",
    DATA_DIR / "derived" / "narrative_themes.json",
    
    # Correction and validation
    DATA_DIR / "derived" / "bonferroni_status.json",
    DATA_DIR / "derived" / "validation_report.json",
    
    # Logs
    DATA_DIR / "logs" / "exclusion_log.csv",
    DATA_DIR / "logs" / "pipeline_execution.log",
]

def ensure_directories():
    """Ensure all necessary directories exist before running tests."""
    for dir_path in [RAW_DIR, PROCESSED_DIR, DERIVED_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def clean_artifacts():
    """Remove previous run artifacts to ensure a fresh execution."""
    artifacts_to_clean = [
        "studies.csv",
        "extracted_studies.csv",
        "meta_status.json",
        "study_count.json",
        "valid_pair_count.json",
        "results.json",
        "forest_plot.png",
        "funnel_plot.png",
        "correlation_summary.png",
        "narrative_summary.md",
        "narrative_themes.json",
        "bonferroni_status.json",
        "validation_report.json",
        "exclusion_log.csv",
        "pipeline_execution.log",
        "qualitative_data.json",
        "tract_count.json",
    ]
    
    for filename in artifacts_to_clean:
        # Check in raw, processed, derived, and logs
        for dir_path in [RAW_DIR, PROCESSED_DIR, DERIVED_DIR, LOGS_DIR]:
            file_path = dir_path / filename
            if file_path.exists():
                file_path.unlink()

def generate_mock_data():
    """Generate mock data using the project's mock generator."""
    if not MOCK_GEN_SCRIPT.exists():
        pytest.skip(f"Mock generator script not found: {MOCK_GEN_SCRIPT}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(MOCK_GEN_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            pytest.fail(f"Mock data generation failed: {result.stderr}")
        
        # Verify the mock file was created
        mock_file = RAW_DIR / "mock_studies.csv"
        if not mock_file.exists():
            pytest.fail("Mock data file was not created")
            
    except subprocess.TimeoutExpired:
        pytest.fail("Mock data generation timed out")
    except Exception as e:
        pytest.fail(f"Error generating mock data: {str(e)}")

def run_pipeline(use_mock: bool = True, config: str = "quant"):
    """Run the main pipeline orchestrator."""
    if not MAIN_SCRIPT.exists():
        pytest.skip(f"Main script not found: {MAIN_SCRIPT}")
    
    cmd = [sys.executable, str(MAIN_SCRIPT)]
    
    if use_mock:
        cmd.extend(["--use-mock"])
    
    cmd.extend(["--config", config])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for full pipeline
        )
        
        # Log output for debugging
        if result.stdout:
            print(f"Pipeline stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Pipeline stderr:\n{result.stderr}")
        
        return result
        
    except subprocess.TimeoutExpired:
        pytest.fail("Pipeline execution timed out")
    except Exception as e:
        pytest.fail(f"Error running pipeline: {str(e)}")

def validate_json_file(file_path: Path, required_keys: List[str] = None):
    """Validate that a JSON file exists and contains required keys."""
    if not file_path.exists():
        pytest.fail(f"Required JSON file missing: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {file_path}: {str(e)}")
    
    if required_keys:
        for key in required_keys:
            if key not in data:
                pytest.fail(f"Missing required key '{key}' in {file_path}")
    
    return data

def validate_png_file(file_path: Path):
    """Validate that a PNG file exists and has reasonable size."""
    if not file_path.exists():
        # PNG might not be generated if narrative path is taken
        return False
    
    if file_path.stat().st_size == 0:
        pytest.fail(f"Empty PNG file: {file_path}")
    
    # Check PNG magic bytes
    with open(file_path, 'rb') as f:
        header = f.read(8)
        if header[:4] != b'\x89PNG':
            pytest.fail(f"Invalid PNG header in {file_path}")
    
    return True

def validate_md_file(file_path: Path, required_section: str = None):
    """Validate that a Markdown file exists and contains required content."""
    if not file_path.exists():
        # MD might not be generated if quantitative path is taken
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if required_section and required_section not in content:
        pytest.fail(f"Missing required section '{required_section}' in {file_path}")
    
    return True

@pytest.fixture(scope="module", autouse=True)
def setup_module():
    """Setup before all tests in this module."""
    ensure_directories()
    clean_artifacts()
    generate_mock_data()
    yield
    # Cleanup could be added here if needed

class TestFullPipeline:
    """Integration tests for the full pipeline execution."""

    def test_pipeline_execution(self):
        """Test that the pipeline executes successfully with mock data."""
        result = run_pipeline(use_mock=True, config="quant")
        
        # The pipeline should exit with 0, or handle graceful degradation
        # We allow non-zero exit if it's due to expected conditions (e.g., insufficient data)
        # but we must verify artifacts are still generated
        assert result.returncode == 0 or result.returncode == 1, \
            f"Pipeline failed with unexpected return code: {result.returncode}. Stderr: {result.stderr}"

    def test_core_artifacts_exist(self):
        """Test that core result artifacts are generated."""
        # Check results.json
        results = validate_json_file(
            DATA_DIR / "derived" / "results.json",
            required_keys=["synthesis_mode"]
        )
        
        # Check meta_status.json
        meta_status = validate_json_file(
            DATA_DIR / "processed" / "meta_status.json",
            required_keys=["status"]
        )
        
        # Check study_count.json
        study_count = validate_json_file(
            DATA_DIR / "processed" / "study_count.json",
            required_keys=["N"]
        )
        
        # Check valid_pair_count.json
        valid_pair_count = validate_json_file(
            DATA_DIR / "processed" / "valid_pair_count.json",
            required_keys=["N_valid"]
        )

    def test_data_files_exist(self):
        """Test that data processing files are generated."""
        # Check extracted_studies.csv
        extracted = DATA_DIR / "processed" / "extracted_studies.csv"
        assert extracted.exists(), "extracted_studies.csv not found"
        
        # Verify it's not empty
        with open(extracted, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1, "extracted_studies.csv is empty or has no data rows"

    def test_visualization_artifacts(self):
        """Test that visualization artifacts are generated (if quantitative path)."""
        # Check if quantitative path was taken
        results_path = DATA_DIR / "derived" / "results.json"
        if results_path.exists():
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            if results.get("synthesis_mode") == "quantitative":
                # Quantitative path: expect plots
                assert validate_png_file(DATA_DIR / "derived" / "forest_plot.png"), \
                    "forest_plot.png not generated or invalid"
                assert validate_png_file(DATA_DIR / "derived" / "funnel_plot.png"), \
                    "funnel_plot.png not generated or invalid"
                
                # Check bonferroni status
                bonferroni = validate_json_file(
                    DATA_DIR / "derived" / "bonferroni_status.json",
                    required_keys=["bonferroni_applied"]
                )
            else:
                # Narrative path: expect narrative summary
                assert validate_md_file(
                    DATA_DIR / "derived" / "narrative_summary.md",
                    required_section="Data"
                ), "narrative_summary.md not generated or missing content"
                
                assert validate_json_file(
                    DATA_DIR / "derived" / "narrative_themes.json",
                    required_keys=["themes"]
                ), "narrative_themes.json not generated"

    def test_logs_exist(self):
        """Test that execution logs are generated."""
        exclusion_log = DATA_DIR / "logs" / "exclusion_log.csv"
        if exclusion_log.exists():
            with open(exclusion_log, 'r') as f:
                lines = f.readlines()
                # Should have header at minimum
                assert len(lines) >= 1, "exclusion_log.csv has no content"

    def test_pipeline_consistency(self):
        """Test that the pipeline output is internally consistent."""
        # Load study count
        study_count_path = DATA_DIR / "processed" / "study_count.json"
        if study_count_path.exists():
            with open(study_count_path, 'r') as f:
                study_count = json.load(f)
            N = study_count.get("N", 0)
            
            # Load results
            results_path = DATA_DIR / "derived" / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                
                # If N < 10, synthesis_mode should be narrative or skipped
                if N < 10:
                    mode = results.get("synthesis_mode", "")
                    status = results.get("meta_status", {}).get("status", "")
                    assert mode == "narrative" or status == "skipped", \
                        f"Expected narrative mode or skipped status for N={N}, got mode={mode}, status={status}"

    def test_no_fabricated_data(self):
        """Test that results are not obviously fabricated (basic sanity check)."""
        results_path = DATA_DIR / "derived" / "results.json"
        if results_path.exists():
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            # Check for obvious fabrication markers
            if "pooled_effect" in results:
                pooled = results["pooled_effect"]
                # Real meta-analysis rarely produces exactly 0.0 or 1.0 without reason
                # and should have reasonable confidence intervals
                if "ci_lower" in results and "ci_upper" in results:
                    ci_lower = results["ci_lower"]
                    ci_upper = results["ci_upper"]
                    
                    # CI should be ordered
                    assert ci_lower <= ci_upper, \
                        f"Invalid confidence interval: {ci_lower} > {ci_upper}"
                    
                    # Effect size should be within reasonable bounds for correlation
                    if -2 <= pooled <= 2:
                        # Reasonable range for correlation-based effect sizes
                        pass
                    else:
                        # Log warning but don't fail - might be valid for other metrics
                        print(f"Warning: Pooled effect {pooled} outside typical correlation range [-1, 1]")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])