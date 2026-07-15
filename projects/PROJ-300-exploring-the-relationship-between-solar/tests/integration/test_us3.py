"""
Integration tests for User Story 3: Visualization and Sensitivity.
Verifies that PNG files are generated and sensitivity table is populated.
File: projects/PROJ-300-exploring-the-relationship-between-solar/tests/integration/test_us3.py
"""
import os
import sys
import json
import pytest
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from run_us3_sample import main as run_us3_main
from viz.plots import plot_scatter, plot_timeseries
from analysis.sensitivity import run_sensitivity_sweep

@pytest.mark.integration
def test_us3_generates_png_files():
    """
    Verify that running the US3 sample script generates the required PNG files.
    """
    # We run the sample script which uses real data.
    # If real data fetch fails, this test will fail, which is correct behavior
    # (we must not fake data).
    try:
        run_us3_main()
    except RuntimeError as e:
        if "Failed to fetch real data" in str(e):
            pytest.skip("Real data source unreachable; skipping integration test.")
        raise

    results_dir = os.path.join(project_root, 'data', 'processed', 'us3_results')
    scatter_path = os.path.join(results_dir, 'plot_scatter.png')
    timeseries_path = os.path.join(results_dir, 'plot_timeseries.png')

    assert os.path.exists(scatter_path), f"Scatter plot not generated at {scatter_path}"
    assert os.path.exists(timeseries_path), f"Time-series plot not generated at {timeseries_path}"
    
    # Verify files are not empty
    assert os.path.getsize(scatter_path) > 0, "Scatter plot is empty"
    assert os.path.getsize(timeseries_path) > 0, "Time-series plot is empty"

@pytest.mark.integration
def test_us3_generates_sensitivity_table():
    """
    Verify that the US3 report contains a valid sensitivity table.
    """
    try:
        run_us3_main()
    except RuntimeError as e:
        if "Failed to fetch real data" in str(e):
            pytest.skip("Real data source unreachable; skipping integration test.")
        raise

    results_dir = os.path.join(project_root, 'data', 'processed', 'us3_results')
    report_path = os.path.join(results_dir, 'us3_report.json')

    assert os.path.exists(report_path), "US3 report JSON not found"

    with open(report_path, 'r') as f:
        report = json.load(f)

    assert 'sensitivity_table' in report, "Sensitivity table missing from report"
    
    table = report['sensitivity_table']
    assert isinstance(table, list), "Sensitivity table must be a list"
    assert len(table) > 0, "Sensitivity table is empty"

    # Check expected thresholds
    expected_thresholds = [400, 500, 600]
    found_thresholds = [item['threshold_kmps'] for item in table]
    
    for t in expected_thresholds:
        assert t in found_thresholds, f"Threshold {t} missing from sensitivity table"

    # Check that correlation values are numeric
    for item in table:
        assert 'correlation' in item
        assert isinstance(item['correlation'], (int, float))
        assert not (item['correlation'] != item['correlation']), "Correlation is NaN" # Check for NaN

@pytest.mark.unit
def test_plot_functions_generate_valid_pngs():
    """
    Unit test to ensure plot functions can generate valid PNG files from sample data.
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import tempfile
    
    # Create sample data
    x = np.linspace(0, 10, 100)
    y = 2 * x + np.random.normal(size=100)
    df = pd.DataFrame({'Vsw': x, 'Ey': y})

    with tempfile.TemporaryDirectory() as tmpdir:
        scatter_path = os.path.join(tmpdir, 'test_scatter.png')
        ts_path = os.path.join(tmpdir, 'test_ts.png')

        plot_scatter(df['Vsw'], df['Ey'], optimal_lag=45, output_path=scatter_path)
        plot_timeseries(df['Vsw'], df['Ey'], df.index, optimal_lag=45, output_path=ts_path)

        assert os.path.exists(scatter_path)
        assert os.path.exists(ts_path)
        assert os.path.getsize(scatter_path) > 0
        assert os.path.getsize(ts_path) > 0

        # Verify they are valid images (simple check: file size > 0 and extension)
        # A more robust check could use PIL, but size > 0 is a good proxy for "generated"
        # in this context without adding heavy dependencies.
        plt.close('all')
