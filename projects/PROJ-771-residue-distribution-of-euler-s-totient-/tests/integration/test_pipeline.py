"""Integration tests for the full analysis pipeline."""
import os
import json
import pytest
from pathlib import Path

# Import orchestration functions
from run_analysis import load_config, main
from sieve import compute_phi_linear_sieve, compute_residues, save_residue_dataset
from stats import run_full_statistical_analysis, save_statistical_result
from visualize import plot_bar_frequencies, plot_residual_qq, annotate_theoretical_bounds, generate_visualization_report


def test_end_to_end_small_run(tmp_path):
    """Run a small analysis (N=100) and verify outputs are created."""
    # Setup temporary directories
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    results_plots = tmp_path / "results" / "plots"
    results_reports = tmp_path / "results" / "reports"

    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    results_plots.mkdir(parents=True)
    results_reports.mkdir(parents=True)

    # Run sieve for N=100, p=3
    N = 100
    prime = 3
    phi_values = compute_phi_linear_sieve(N)
    residue_counts = compute_residues(phi_values, prime)

    # Save raw data
    output_path = data_raw / f"residues_{prime}_{N}.json"
    save_residue_dataset(residue_counts, str(output_path))

    assert output_path.exists(), "Raw residue data file was not created"

    with open(output_path) as f:
        data = json.load(f)

    assert "prime" in data
    assert data["prime"] == prime
    assert "counts" in data
    assert len(data["counts"]) == prime

    # Run statistical analysis
    statistical_result = run_full_statistical_analysis(str(output_path), prime)
    statistical_result_path = data_processed / f"stats_{prime}_{N}.json"
    save_statistical_result(statistical_result, str(statistical_result_path))
    assert statistical_result_path.exists()

    # Generate visualization
    plot_bar_frequencies(residue_counts, prime, str(results_plots / f"residues_{prime}_{N}.png"))
    plot_residual_qq(residue_counts, str(results_plots / f"qq_{prime}_{N}.png"))
    annotate_theoretical_bounds(str(results_plots / f"residues_{prime}_{N}.png"), prime)
    generate_visualization_report(str(results_reports / f"report_{N}.md"), N, prime)