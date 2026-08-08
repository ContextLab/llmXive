import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
from src.report_final import (
    load_correlation_results,
    load_ingestion_report,
    load_plot_files,
    generate_html_report,
    run_final_report_generation
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_correlation_results():
    return pd.DataFrame({
        'diversity_index': ['Shannon', 'Simpson'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours'],
        'r': [0.45, -0.12],
        'p': [0.001, 0.35],
        'q': [0.005, 0.40],
        'is_moderate': [True, False],
        'is_meaningful': [True, False],
        'status': ['success', 'success']
    })

@pytest.fixture
def sample_ingestion_report():
    return {
        'status': 'success',
        'measurement_status': 'measurable',
        'total_initial_sample_count': 1000,
        'excluded_count': 50,
        'exclusion_proportion': 0.05
    }

def test_load_correlation_results_creates_dataframe(temp_dir, sample_correlation_results):
    file_path = temp_dir / "corr.csv"
    sample_correlation_results.to_csv(file_path, index=False)
    df = load_correlation_results(str(file_path))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'r' in df.columns

def test_load_correlation_results_missing_file(temp_dir):
    df = load_correlation_results(str(temp_dir / "missing.csv"))
    assert df.empty

def test_load_ingestion_report_creates_dict(temp_dir, sample_ingestion_report):
    file_path = temp_dir / "ingestion.json"
    with open(file_path, 'w') as f:
        json.dump(sample_ingestion_report, f)
    data = load_ingestion_report(str(file_path))
    assert isinstance(data, dict)
    assert data['status'] == 'success'

def test_load_plot_files(temp_dir):
    # Create dummy png files
    (temp_dir / "plot1.png").touch()
    (temp_dir / "plot2.png").touch()
    (temp_dir / "readme.txt").touch() # Should be ignored

    files = load_plot_files(str(temp_dir))
    assert len(files) == 2
    assert all(f.endswith('.png') for f in files)

def test_generate_html_report_creates_file(temp_dir, sample_correlation_results, sample_ingestion_report):
    output_path = temp_dir / "report.html"
    plot_dir = temp_dir / "plots"
    plot_dir.mkdir()
    (plot_dir / "test.png").touch()

    generate_html_report(
        sample_correlation_results,
        sample_ingestion_report,
        [str(plot_dir / "test.png")],
        str(output_path)
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "<title>Gut Microbiome" in content
    assert "0.45" in content # Check for data presence
    assert "Shannon" in content

def test_generate_html_report_blocked_status(temp_dir):
    output_path = temp_dir / "blocked_report.html"
    generate_html_report(
        pd.DataFrame(),
        {}, # Empty ingestion report triggers blocked logic
        [],
        str(output_path)
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "Project Blocked" in content
    assert "No verified data source found" in content

def test_run_final_report_generation_integration(temp_dir, sample_correlation_results, sample_ingestion_report):
    # Setup temp paths
    corr_path = temp_dir / "corr.csv"
    ing_path = temp_dir / "ingestion.json"
    plots_dir = temp_dir / "plots"
    output_path = temp_dir / "final_report.html"

    plots_dir.mkdir()
    (plots_dir / "boxplot.png").touch()

    sample_correlation_results.to_csv(corr_path, index=False)
    with open(ing_path, 'w') as f:
        json.dump(sample_ingestion_report, f)

    run_final_report_generation(
        correlation_results_path=str(corr_path),
        ingestion_report_path=str(ing_path),
        plots_directory=str(plots_dir),
        output_path=str(output_path)
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "Correlation Results" in content
    assert "Visualizations" in content