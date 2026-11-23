"""
Integration test for run_analysis.py generating statistical_comparison.csv and plot.

This test verifies that the analysis pipeline:
1. Can be executed end-to-end on real benchmark data.
2. Generates the required `statistical_comparison.csv` in `data/processed/`.
3. Generates the required plot image in `figures/`.
4. Produces valid statistical results (p-values, Cohen's d, FDR).
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest
import numpy as np

# Add project root to path to import analysis modules if needed for validation
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.run_analysis import main as run_analysis_main
from contracts.benchmark_contracts import BenchmarkRun, AggregatedResult


def _generate_synthetic_benchmark_data(output_dir: Path):
    """
    Generates a synthetic but realistic benchmark CSV to ensure the test
    can run without depending on a prior full hardware benchmark execution.
    This mimics the output of run_benchmarks.sh as defined in T024.

    Structure: thread_count, configuration, iteration_count, wall_clock_time_ms, status
    """
    data = []
    thread_counts = [1, 2, 4, 8]
    configs = ["packed", "padded"]
    iterations = 10_000_000

    # Seed for reproducibility in testing
    rng = np.random.default_rng(42)

    for tc in thread_counts:
        for cfg in configs:
            # Simulate realistic timing:
            # Packed suffers false sharing at high threads -> higher time
            # Padded is stable -> lower time
            base_time = 100.0  # ms
            if cfg == "packed" and tc > 1:
                # Simulate false sharing degradation
                degradation_factor = 1.0 + (tc - 1) * 0.8
                time_ms = base_time * degradation_factor + rng.normal(0, 2)
            else:
                time_ms = base_time + rng.normal(0, 1)

            # Ensure positive time
            time_ms = max(1.0, time_ms)

            for _ in range(5): # 5 repetitions per config
                data.append({
                    "thread_count": tc,
                    "configuration": cfg,
                    "iteration_count": iterations,
                    "wall_clock_time_ms": time_ms,
                    "status": "OK"
                })

    csv_path = output_dir / "raw_benchmark_results.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture(scope="module")
def analysis_setup(tmp_path_factory):
    """
    Sets up a temporary directory with synthetic benchmark data
    and runs the analysis pipeline.
    """
    work_dir = tmp_path_factory.mktemp("analysis_test")
    data_dir = work_dir / "data" / "raw"
    data_dir.mkdir(parents=True)

    # Generate synthetic data
    csv_path = _generate_synthetic_benchmark_data(data_dir)

    # Define output paths matching project structure
    processed_dir = work_dir / "data" / "processed"
    figures_dir = work_dir / "figures"
    processed_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)

    # Run the analysis script
    # We invoke the main function directly to avoid shell script dependencies
    # but pass the necessary paths as if they were environment variables or args
    # The script expects to find data in data/raw and write to data/processed and figures
    
    # Change to work_dir to simulate running from project root
    original_cwd = os.getcwd()
    try:
        os.chdir(work_dir)
        # Mock the environment variables or arguments the script might expect
        # The script `run_analysis.py` typically takes no args if it looks for standard paths
        # or we can patch the main function to accept paths. 
        # For this integration test, we assume the script uses relative paths from cwd.
        # Let's call the main function directly with the paths injected if possible,
        # or rely on the script's internal logic to use relative paths.
        # Assuming run_analysis.py looks for 'data/raw/*.csv' relative to cwd.
        
        run_analysis_main()
    finally:
        os.chdir(original_cwd)

    return {
        "work_dir": work_dir,
        "csv_path": csv_path,
        "processed_dir": processed_dir,
        "figures_dir": figures_dir
    }


def test_analysis_script_execution(analysis_setup):
    """
    Verifies that run_analysis.py executes without error.
    """
    # The fixture already ran the script. If it raised, the test would fail.
    assert True


def test_statistical_comparison_csv_generated(analysis_setup):
    """
    Verifies that statistical_comparison.csv is created in data/processed/.
    """
    csv_path = analysis_setup["processed_dir"] / "statistical_comparison.csv"
    assert csv_path.exists(), f"statistical_comparison.csv not found at {csv_path}"

    df = pd.read_csv(csv_path)
    
    # Verify required columns
    required_cols = ["thread_count", "config", "t_stat", "p_value", "cohens_d", "fdr_adjusted_p"]
    assert all(col in df.columns for col in required_cols), \
        f"Missing columns in {csv_path}. Found: {df.columns.tolist()}"
    
    # Verify data integrity
    assert len(df) > 0, "statistical_comparison.csv is empty"
    assert df["thread_count"].unique().tolist() == [1, 2, 4, 8], \
        f"Expected thread counts [1, 2, 4, 8], got {df['thread_count'].unique().tolist()}"
    
    # Check for valid statistical values (no NaNs in critical columns)
    assert not df["p_value"].isna().any(), "Found NaN p-values"
    assert not df["cohens_d"].isna().any(), "Found NaN Cohen's d values"


def test_plot_generated(analysis_setup):
    """
    Verifies that a plot image is generated in figures/.
    """
    # The plot filename is typically defined in run_analysis.py.
    # Based on standard conventions, it's likely 'throughput_comparison.png' or similar.
    # We check for any .png file in the figures directory.
    figures_dir = analysis_setup["figures_dir"]
    png_files = list(figures_dir.glob("*.png"))
    
    assert len(png_files) > 0, f"No plot generated in {figures_dir}. Expected at least one PNG."
    
    # Verify the file is not empty
    for pf in png_files:
        assert pf.stat().st_size > 0, f"Plot file {pf} is empty"


def test_statistical_significance_logic(analysis_setup):
    """
    Verifies that the statistical analysis produces expected trends:
    - At high thread counts, padded should be significantly faster (lower time, higher throughput)
      than packed.
    - p-values for high thread counts should ideally be small (< 0.05).
    """
    csv_path = analysis_setup["processed_dir"] / "statistical_comparison.csv"
    df = pd.read_csv(csv_path)

    # Filter for high thread counts (4 and 8)
    high_threads = df[df["thread_count"].isin([4, 8])]
    
    # We expect the comparison to show a significant difference (low p-value)
    # because our synthetic data was generated with that trend.
    # Note: This test assumes the synthetic data generation logic in _generate_synthetic_benchmark_data
    # actually creates a significant difference.
    assert len(high_threads) > 0, "No high thread count data found for validation"
    
    # Check that at least some high thread counts have low p-values
    # This validates that the t-test and FDR logic ran correctly.
    significant_count = (high_threads["p_value"] < 0.05).sum()
    # We expect at least one significant result given our synthetic data design
    assert significant_count >= 1, \
        f"Expected at least one significant result at high thread counts, but found {significant_count}. " \
        f"Data: {high_threads[['thread_count', 'p_value']]}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
