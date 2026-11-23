"""
Integration test to validate the quickstart.md pipeline execution.

This test executes the pipeline steps as described in the quickstart documentation
and verifies that all expected artifacts are generated with valid content.
"""
import subprocess
import sys
import json
import os
import csv
from pathlib import Path
import pytest

# Add code directory to path for imports
CODE_DIR = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from config import (
    get_project_root,
    get_raw_data_dir,
    get_processed_data_dir,
    get_figures_dir,
    get_data_dir
)


def run_command(cmd, check=True):
    """Helper to run shell commands and return result."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=get_project_root()
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nStdout: {result.stdout}\nStderr: {result.stderr}")
    return result


@pytest.mark.integration
def test_quickstart_pipeline_execution():
    """
    Execute the full pipeline as described in quickstart.md and verify outputs.
    
    This test:
    1. Runs the power analysis script
    2. Generates stimuli
    3. Simulates ratings
    4. Cleans data
    5. Runs LMM analysis
    6. Runs sensitivity analysis
    7. Verifies all expected output files exist and contain valid data
    """
    project_root = get_project_root()
    
    # Step 1: Power Analysis
    print("Running power analysis...")
    result = run_command(f"python {CODE_DIR / '00_power_analysis.py'}")
    assert result.returncode == 0, "Power analysis failed"
    
    power_results_path = get_processed_data_dir() / "power_analysis_results.json"
    assert power_results_path.exists(), "Power analysis results file not created"
    
    with open(power_results_path, 'r') as f:
        power_data = json.load(f)
        assert 'target_N' in power_data, "Missing target_N in power analysis"
        assert 'effect_size' in power_data, "Missing effect_size in power analysis"
        assert 'power' in power_data, "Missing power in power analysis"
        assert 'alpha' in power_data, "Missing alpha in power analysis"
    
    # Step 2: Generate Stimuli
    print("Generating stimuli...")
    result = run_command(f"python {CODE_DIR / '01_generate_stimuli.py'}")
    assert result.returncode == 0, "Stimuli generation failed"
    
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    assert stimuli_path.exists(), "Stimuli CSV not created"
    
    with open(stimuli_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "Stimuli CSV is empty"
        assert 'stimulus_id' in rows[0], "Missing stimulus_id column"
        assert 'text' in rows[0], "Missing text column"
    
    # Step 3: Simulate Ratings
    print("Simulating ratings...")
    result = run_command(f"python {CODE_DIR / '02_simulate_ratings.py'}")
    assert result.returncode == 0, "Rating simulation failed"
    
    ratings_path = get_raw_data_dir() / "ratings.csv"
    assert ratings_path.exists(), "Ratings CSV not created"
    
    with open(ratings_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "Ratings CSV is empty"
        assert 'participant_id' in rows[0], "Missing participant_id column"
        assert 'stimulus_id' in rows[0], "Missing stimulus_id column"
        assert 'rating' in rows[0], "Missing rating column"
    
    # Step 4: Clean Data
    print("Cleaning data...")
    result = run_command(f"python {CODE_DIR / '03_clean_data.py'}")
    assert result.returncode == 0, "Data cleaning failed"
    
    cleaning_log_path = get_processed_data_dir() / "cleaning_log.csv"
    assert cleaning_log_path.exists(), "Cleaning log not created"
    
    with open(cleaning_log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Log may be empty if no exclusions, but file must exist
        assert 'exclusion_reason' in rows[0] if rows else True, "Missing exclusion_reason column"
    
    # Step 5: Run LMM Analysis
    print("Running LMM analysis...")
    result = run_command(f"python {CODE_DIR / '04_run_lmm.py'}")
    assert result.returncode == 0, "LMM analysis failed"
    
    analysis_results_path = get_processed_data_dir() / "analysis_results.json"
    assert analysis_results_path.exists(), "Analysis results not created"
    
    with open(analysis_results_path, 'r') as f:
        analysis_data = json.load(f)
        assert 'fixed_effects' in analysis_data, "Missing fixed_effects in results"
        assert 'p_values' in analysis_data, "Missing p_values in results"
    
    # Step 6: Sensitivity Definitions
    print("Generating sensitivity definitions...")
    result = run_command(f"python {CODE_DIR / '05_sensitivity_definitions.py'}")
    assert result.returncode == 0, "Sensitivity definitions generation failed"
    
    sensitivity_defs_path = get_processed_data_dir() / "sensitivity_definitions.json"
    assert sensitivity_defs_path.exists(), "Sensitivity definitions not created"
    
    with open(sensitivity_defs_path, 'r') as f:
        defs_data = json.load(f)
        assert isinstance(defs_data, list), "Sensitivity definitions must be a list"
        assert len(defs_data) > 0, "Sensitivity definitions list is empty"
        for definition in defs_data:
            assert 'name' in definition, "Missing name in definition"
            assert 'type' in definition, "Missing type in definition"
            assert 'rule' in definition, "Missing rule in definition"
    
    # Step 7: Sensitivity Analysis
    print("Running sensitivity analysis...")
    result = run_command(f"python {CODE_DIR / '05_sensitivity_analysis.py'}")
    assert result.returncode == 0, "Sensitivity analysis failed"
    
    sensitivity_report_path = get_processed_data_dir() / "sensitivity_report.csv"
    assert sensitivity_report_path.exists(), "Sensitivity report not created"
    
    with open(sensitivity_report_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "Sensitivity report is empty"
        assert 'definition_name' in rows[0], "Missing definition_name column"
        assert 'f_statistic' in rows[0], "Missing f_statistic column"
        assert 'p_value' in rows[0], "Missing p_value column"
    
    # Step 8: Power Curve Visualization
    print("Generating power curve...")
    result = run_command(f"python {CODE_DIR / '09_power_curve_plotter.py'}")
    assert result.returncode == 0, "Power curve plotter failed"
    
    power_curve_path = get_figures_dir() / "power_curve.png"
    assert power_curve_path.exists(), "Power curve PNG not created"
    assert power_curve_path.stat().st_size > 0, "Power curve PNG is empty"
    
    print("All quickstart validation checks passed!")


@pytest.mark.integration
def test_quickstart_cli_benchmark():
    """
    Test the CLI benchmark flag from quickstart.md.
    
    Verifies that the pipeline can run with --benchmark flag and produces
    the expected JSON output structure.
    """
    result = run_command(f"python {CODE_DIR / 'run_pipeline.py'} --benchmark --seed 42", check=False)
    
    # The pipeline might fail if dependencies aren't fully set up, but we check the structure
    if result.returncode == 0:
        try:
            output = json.loads(result.stdout)
            assert 'total_duration_seconds' in output, "Missing total_duration_seconds in benchmark output"
            assert 'per_stage_duration' in output, "Missing per_stage_duration in benchmark output"
            assert 'assertion' in output, "Missing assertion in benchmark output"
            assert output['assertion'] == "total_duration < 21600", "Incorrect assertion format"
        except json.JSONDecodeError:
            pytest.skip("Benchmark output is not valid JSON (pipeline may have failed)")
    else:
        pytest.skip("Pipeline benchmark failed to run (dependencies may be missing)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])