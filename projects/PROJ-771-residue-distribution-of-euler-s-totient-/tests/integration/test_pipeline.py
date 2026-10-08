"""Integration test for the full pipeline (T033).

This test suite validates the end-to-end execution of the residue distribution analysis
pipeline, ensuring that:
1. All required directories exist.
2. All core modules can be imported successfully.
3. The full pipeline runs end-to-end on a small dataset (N=100) and produces all expected artifacts.
4. The produced artifacts match the expected schemas and contain valid data.
"""
import os
import json
import pytest
from pathlib import Path
import sys
import tempfile
import shutil
import importlib

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

@pytest.fixture(scope="module")
def temp_run_dir():
    """Create a temporary directory for the pipeline run and clean up afterwards."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    try:
        os.chdir(temp_dir)
        # Create necessary directories manually if they don't exist (simulating setup)
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("results/plots", exist_ok=True)
        os.makedirs("results/reports", exist_ok=True)
        yield temp_dir
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_pipeline_artifacts_exist():
    """Verify all expected directories exist."""
    base = Path(".")
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration"
    ]
    for d in expected_dirs:
        assert (base / d).exists(), f"Directory {d} is missing"

def test_run_analysis_imports():
    """Verify run_analysis can be imported without errors."""
    # Force reload to ensure fresh import if previously imported
    if 'run_analysis' in sys.modules:
        importlib.reload(sys.modules['run_analysis'])
    from run_analysis import main, load_config, pin_orchestration_seed
    assert callable(main)
    assert callable(load_config)
    assert callable(pin_orchestration_seed)

def test_sieve_module_exports():
    """Verify sieve module exports required functions and classes."""
    if 'sieve' in sys.modules:
        importlib.reload(sys.modules['sieve'])
    from sieve import (
        ResidueDataset,
        StatisticalResult,
        pin_random_seed,
        is_seed_pinned,
        get_current_seed,
        log_error,
        compute_phi_linear_sieve,
        compute_residues,
        save_residue_dataset,
        load_residue_dataset,
        save_statistical_result,
        load_statistical_result,
        run_sieve_analysis
    )
    assert callable(compute_phi_linear_sieve)
    assert callable(compute_residues)
    assert callable(run_sieve_analysis)

def test_stats_module_exports():
    """Verify stats module exports required functions."""
    if 'stats' in sys.modules:
        importlib.reload(sys.modules['stats'])
    from stats import (
        StatisticalResult,
        calculate_theoretical_bounds,
        calculate_deviation_D,
        check_bin_counts_and_fallback,
        calculate_chi_squared_statistic,
        exact_test_fallback,
        block_bootstrap_residues,
        run_block_bootstrap_deviation_test,
        calculate_error_term_residual,
        run_full_statistical_analysis,
        determine_primary_pass_fail,
        determine_bonferroni_pass_fail
    )
    assert callable(calculate_chi_squared_statistic)
    assert callable(run_full_statistical_analysis)

def test_visualize_module_exports():
    """Verify visualize module exports required functions."""
    if 'visualize' in sys.modules:
        importlib.reload(sys.modules['visualize'])
    from visualize import (
        plot_bar_frequencies,
        plot_residual_qq,
        annotate_theoretical_bounds,
        generate_visualization_report
    )
    assert callable(plot_bar_frequencies)
    assert callable(generate_visualization_report)

def test_config_module_exports():
    """Verify config module exports required functions."""
    if 'config' in sys.modules:
        importlib.reload(sys.modules['config'])
    from config import load_config, create_argument_parser, parse_cli_args
    assert callable(load_config)
    assert callable(create_argument_parser)

def test_end_to_end_small_run(temp_run_dir):
    """
    Run a minimal end-to-end pipeline on a small N to verify artifact creation.
    This test:
    1. Runs the sieve to generate data/raw/residues_*.json
    2. Runs the stats to generate data/processed/stats_*.json
    3. Runs the visualization to generate results/plots/*.png
    4. Verifies all these files exist and contain valid data.
    """
    import run_analysis
    from run_analysis import main as run_main

    # We will run with a small N to ensure it completes quickly in CI
    # Arguments: --N 100 --primes 3,5
    test_args = [
        "run_analysis.py",
        "--N", "100",
        "--primes", "3,5",
        "--seed", "42"
    ]

    # Save current working directory to restore later
    original_cwd = os.getcwd()
    # temp_run_dir is already set up by the fixture
    
    try:
        os.chdir(temp_run_dir)
        
        # Inject sys.argv for argparse
        old_argv = sys.argv
        sys.argv = test_args
        
        try:
            run_main()
        except SystemExit as e:
            # argparse often calls sys.exit(0) on success
            if e.code != 0:
                raise
        finally:
            sys.argv = old_argv

        # Verify artifacts exist
        # Check for residue files
        raw_dir = Path("data/raw")
        assert raw_dir.exists(), "data/raw directory missing"
        residue_files = list(raw_dir.glob("residues_*.json"))
        assert len(residue_files) > 0, f"No residue files found in {raw_dir}"

        # Check for stats files
        proc_dir = Path("data/processed")
        assert proc_dir.exists(), "data/processed directory missing"
        stats_files = list(proc_dir.glob("stats_*.json"))
        assert len(stats_files) > 0, f"No stats files found in {proc_dir}"

        # Check for plot files
        plots_dir = Path("results/plots")
        assert plots_dir.exists(), "results/plots directory missing"
        plot_files = list(plots_dir.glob("*.png"))
        assert len(plot_files) > 0, f"No plot files found in {plots_dir}"

        # Verify content of a stats file to ensure it's not empty/corrupt
        if stats_files:
            with open(stats_files[0], 'r') as f:
                data = json.load(f)
                # Check for expected keys based on StatisticalResult schema
                expected_keys = ['chi_squared_statistic', 'chi_squared_p_value', 
                                'block_bootstrap_p_value', 'pass_fail_flag', 
                                'bonferroni_pass_fail_flag', 'error_term_residual']
                found_keys = [k for k in expected_keys if k in data]
                assert len(found_keys) > 0, f"Stats file missing expected keys. Found: {list(data.keys())}"

        # Verify content of a residue file
        if residue_files:
            with open(residue_files[0], 'r') as f:
                data = json.load(f)
                assert 'prime_modulus' in data, "Residue file missing prime_modulus"
                assert 'total_count' in data, "Residue file missing total_count"
                assert 'frequency_map' in data, "Residue file missing frequency_map"

        # Verify report generation
        reports_dir = Path("results/reports")
        assert reports_dir.exists(), "results/reports directory missing"
        report_files = list(reports_dir.glob("*.md"))
        assert len(report_files) > 0, f"No report files found in {reports_dir}"

    finally:
        os.chdir(original_cwd)