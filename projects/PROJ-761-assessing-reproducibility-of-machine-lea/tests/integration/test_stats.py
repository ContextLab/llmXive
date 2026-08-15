"""
Integration test for Bland-Altman plot generation.

This test verifies that the stats module can successfully:
1. Generate Bland-Altman plots for MAE, R2, and Spearman rho metrics.
2. Save the plots to the expected artifacts/plots directory.
3. Handle the input data format expected from repro_results.json.

Note: This test requires T025 (paired t-tests) and T028 (plot generation logic)
to be implemented in code/stats.py.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

# Import the stats module functions
# We assume code/stats.py has been implemented with the required functions
try:
    from code.stats import generate_bland_altman_plots, run_statistical_analysis
except ImportError:
    pytest.skip("code/stats.py not yet implemented", allow_module_level=True)

# Sample data structure mimicking artifacts/reports/repro_results.json
SAMPLE_REPRO_RESULTS = [
    {
        "paper_id": "paper_001",
        "doi": "10.1038/s41586-021-03000-0",
        "reported_metrics": {"mae": 0.15, "r2": 0.85, "spearman_rho": 0.82},
        "reproduced_metrics": {"mae": 0.18, "r2": 0.82, "spearman_rho": 0.80},
        "deviations": {"mae": 0.03, "r2": -0.03, "spearman_rho": -0.02},
        "reproducibility_score": 0.95
    },
    {
        "paper_id": "paper_002",
        "doi": "10.1021/jacs.1c00000",
        "reported_metrics": {"mae": 0.20, "r2": 0.78, "spearman_rho": 0.75},
        "reproduced_metrics": {"mae": 0.22, "r2": 0.76, "spearman_rho": 0.73},
        "deviations": {"mae": 0.02, "r2": -0.02, "spearman_rho": -0.02},
        "reproducibility_score": 0.96
    },
    {
        "paper_id": "paper_003",
        "doi": "10.1016/j.chempr.2021.01.001",
        "reported_metrics": {"mae": 0.12, "r2": 0.90, "spearman_rho": 0.88},
        "reproduced_metrics": {"mae": 0.14, "r2": 0.88, "spearman_rho": 0.86},
        "deviations": {"mae": 0.02, "r2": -0.02, "spearman_rho": -0.02},
        "reproducibility_score": 0.97
    },
    {
        "paper_id": "paper_004",
        "doi": "10.1038/s41929-021-00600-0",
        "reported_metrics": {"mae": 0.25, "r2": 0.70, "spearman_rho": 0.68},
        "reproduced_metrics": {"mae": 0.28, "r2": 0.67, "spearman_rho": 0.65},
        "deviations": {"mae": 0.03, "r2": -0.03, "spearman_rho": -0.03},
        "reproducibility_score": 0.94
    },
    {
        "paper_id": "paper_005",
        "doi": "10.1002/anie.202100000",
        "reported_metrics": {"mae": 0.10, "r2": 0.92, "spearman_rho": 0.90},
        "reproduced_metrics": {"mae": 0.11, "r2": 0.91, "spearman_rho": 0.89},
        "deviations": {"mae": 0.01, "r2": -0.01, "spearman_rho": -0.01},
        "reproducibility_score": 0.99
    }
]

def test_bland_altman_plot_generation():
    """
    Test that Bland-Altman plots are generated and saved correctly.
    
    This test:
    1. Creates a temporary directory structure
    2. Writes sample repro results to a temporary file
    3. Calls generate_bland_altman_plots
    4. Verifies that plot files are created in the expected location
    5. Verifies that the plot files are non-empty and valid images
    """
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up directory structure
        reports_dir = temp_path / "reports"
        plots_dir = temp_path / "plots"
        reports_dir.mkdir(parents=True)
        plots_dir.mkdir(parents=True)
        
        # Write sample data to a temporary JSON file
        repro_results_file = reports_dir / "repro_results.json"
        with open(repro_results_file, 'w') as f:
            json.dump(SAMPLE_REPRO_RESULTS, f, indent=2)
        
        # Call the function to generate Bland-Altman plots
        # This should create plots in the plots_dir
        result = generate_bland_altman_plots(
            repro_results_file=str(repro_results_file),
            output_dir=str(plots_dir)
        )
        
        # Verify the function returned success
        assert result is True, "generate_bland_altman_plots should return True on success"
        
        # Verify that plot files were created
        expected_plots = [
            "mae_bland_altman.png",
            "r2_bland_altman.png",
            "spearman_rho_bland_altman.png"
        ]
        
        for plot_name in expected_plots:
            plot_path = plots_dir / plot_name
            assert plot_path.exists(), f"Expected plot {plot_name} was not created"
            assert plot_path.stat().st_size > 0, f"Plot {plot_name} is empty"
            
            # Verify it's a valid PNG file (check magic bytes)
            with open(plot_path, 'rb') as f:
                magic_bytes = f.read(8)
                assert magic_bytes[:8] == b'\x89PNG\r\n\x1a\n', \
                    f"Plot {plot_name} does not appear to be a valid PNG file"
        
        # Verify the function logs were created (if applicable)
        # This is optional but good to check
        log_files = list(plots_dir.glob("*.log"))
        # We don't require log files, but if they exist, they should be non-empty
        for log_file in log_files:
            assert log_file.stat().st_size > 0, f"Log file {log_file.name} is empty"

def test_bland_altman_with_single_paper():
    """
    Test Bland-Altman plot generation with only one paper (edge case).
    
    Bland-Altman plots typically require multiple data points to be meaningful,
    but the function should handle this gracefully without crashing.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up directory structure
        reports_dir = temp_path / "reports"
        plots_dir = temp_path / "plots"
        reports_dir.mkdir(parents=True)
        plots_dir.mkdir(parents=True)
        
        # Create a single paper result
        single_paper_results = [SAMPLE_REPRO_RESULTS[0]]
        
        # Write sample data to a temporary JSON file
        repro_results_file = reports_dir / "repro_results_single.json"
        with open(repro_results_file, 'w') as f:
            json.dump(single_paper_results, f, indent=2)
        
        # Call the function - should handle gracefully
        result = generate_bland_altman_plots(
            repro_results_file=str(repro_results_file),
            output_dir=str(plots_dir)
        )
        
        # The function should return True even with limited data
        # (though the plots may not be statistically meaningful)
        assert result is True, "generate_bland_altman_plots should handle single paper gracefully"
        
        # Verify that plot files were created (even if with limited data)
        expected_plots = [
            "mae_bland_altman.png",
            "r2_bland_altman.png",
            "spearman_rho_bland_altman.png"
        ]
        
        for plot_name in expected_plots:
            plot_path = plots_dir / plot_name
            assert plot_path.exists(), f"Expected plot {plot_name} was not created for single paper"
            assert plot_path.stat().st_size > 0, f"Plot {plot_name} is empty for single paper"

def test_bland_altman_with_missing_metrics():
    """
    Test Bland-Altman plot generation when some metrics are missing.
    
    The function should handle missing metrics gracefully by skipping
    those metrics or using placeholders.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up directory structure
        reports_dir = temp_path / "reports"
        plots_dir = temp_path / "plots"
        reports_dir.mkdir(parents=True)
        plots_dir.mkdir(parents=True)
        
        # Create results with missing metrics
        incomplete_results = [
            {
                "paper_id": "paper_001",
                "reported_metrics": {"mae": 0.15, "r2": 0.85},  # Missing spearman_rho
                "reproduced_metrics": {"mae": 0.18, "r2": 0.82},
                "deviations": {"mae": 0.03, "r2": -0.03},
                "reproducibility_score": 0.95
            },
            {
                "paper_id": "paper_002",
                "reported_metrics": {"mae": 0.20},  # Only mae
                "reproduced_metrics": {"mae": 0.22},
                "deviations": {"mae": 0.02},
                "reproducibility_score": 0.96
            }
        ]
        
        # Write sample data to a temporary JSON file
        repro_results_file = reports_dir / "repro_results_incomplete.json"
        with open(repro_results_file, 'w') as f:
            json.dump(incomplete_results, f, indent=2)
        
        # Call the function - should handle missing metrics gracefully
        result = generate_bland_altman_plots(
            repro_results_file=str(repro_results_file),
            output_dir=str(plots_dir)
        )
        
        # The function should return True even with missing metrics
        assert result is True, "generate_bland_altman_plots should handle missing metrics gracefully"
        
        # Verify that at least the mae plot was created
        mae_plot = plots_dir / "mae_bland_altman.png"
        assert mae_plot.exists(), "MAE Bland-Altman plot should be created even with incomplete data"
        assert mae_plot.stat().st_size > 0, "MAE Bland-Altman plot is empty"

def test_bland_altman_integration_with_full_pipeline():
    """
    Integration test that runs the full statistical analysis pipeline including
    Bland-Altman plot generation.
    
    This test verifies that:
    1. The full statistical analysis can be run
    2. Bland-Altman plots are generated as part of the pipeline
    3. The stat_summary.json file is created with expected content
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up directory structure
        reports_dir = temp_path / "reports"
        plots_dir = temp_path / "plots"
        reports_dir.mkdir(parents=True)
        plots_dir.mkdir(parents=True)
        
        # Write sample data to a temporary JSON file
        repro_results_file = reports_dir / "repro_results.json"
        with open(repro_results_file, 'w') as f:
            json.dump(SAMPLE_REPRO_RESULTS, f, indent=2)
        
        # Call the full statistical analysis pipeline
        # This should include Bland-Altman plot generation
        result = run_statistical_analysis(
            repro_results_file=str(repro_results_file),
            output_dir=str(reports_dir),
            plots_dir=str(plots_dir)
        )
        
        # Verify the function returned success
        assert result is True, "run_statistical_analysis should return True on success"
        
        # Verify that Bland-Altman plots were created
        expected_plots = [
            "mae_bland_altman.png",
            "r2_bland_altman.png",
            "spearman_rho_bland_altman.png"
        ]
        
        for plot_name in expected_plots:
            plot_path = plots_dir / plot_name
            assert plot_path.exists(), f"Expected plot {plot_name} was not created by full pipeline"
            assert plot_path.stat().st_size > 0, f"Plot {plot_name} is empty in full pipeline"
        
        # Verify that stat_summary.json was created
        stat_summary_file = reports_dir / "stat_summary.json"
        assert stat_summary_file.exists(), "stat_summary.json was not created by full pipeline"
        assert stat_summary_file.stat().st_size > 0, "stat_summary.json is empty"
        
        # Verify the content of stat_summary.json
        with open(stat_summary_file, 'r') as f:
            stat_summary = json.load(f)
        
        # Check for expected keys
        expected_keys = ["paired_t_tests", "bland_altman_plots", "summary_statistics"]
        for key in expected_keys:
            assert key in stat_summary, f"stat_summary.json missing expected key: {key}"
        
        # Check that Bland-Altman plots are listed
        assert "bland_altman_plots" in stat_summary
        assert isinstance(stat_summary["bland_altman_plots"], list)
        assert len(stat_summary["bland_altman_plots"]) > 0