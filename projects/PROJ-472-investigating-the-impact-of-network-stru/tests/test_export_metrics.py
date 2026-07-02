"""
Tests for the export_metrics module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.export_metrics import (
    load_metrics_from_store,
    load_avalanche_fitting_results,
    load_qc_status,
    collect_subject_metrics,
    run_export_pipeline
)
from utils.logger import ResearchError

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking the project data layout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create directory structure
        (root / "processed" / "metrics").mkdir(parents=True)
        (root / "processed" / "avalanches").mkdir(parents=True)
        (root / "processed" / "qc").mkdir(parents=True)
        (root / "results").mkdir(parents=True)
        yield root

def test_load_metrics_from_store_missing_file(temp_data_dir):
    """Test loading metrics when file does not exist."""
    result = load_metrics_from_store("sub-001", temp_data_dir)
    assert result is None

def test_load_metrics_from_store_valid(temp_data_dir):
    """Test loading valid metrics file."""
    metrics_path = temp_data_dir / "processed" / "metrics" / "sub-001_metrics.json"
    data = {
        "mean_degree_centrality": 0.5,
        "std_degree_centrality": 0.1,
        "mean_clustering_coefficient": 0.3,
        "std_clustering_coefficient": 0.05,
        "rich_club_coefficient": 0.8
    }
    with open(metrics_path, 'w') as f:
        json.dump(data, f)
    
    result = load_metrics_from_store("sub-001", temp_data_dir)
    assert result is not None
    assert result["mean_degree_centrality"] == 0.5

def test_load_avalanche_fitting_results_missing_file(temp_data_dir):
    """Test loading fitting results when file does not exist."""
    result = load_avalanche_fitting_results("sub-001", temp_data_dir)
    assert result is None

def test_load_avalanche_fitting_results_valid(temp_data_dir):
    """Test loading valid fitting results file."""
    fitting_path = temp_data_dir / "processed" / "avalanches" / "sub-001_fitting.json"
    data = {
        "exponent": 1.5,
        "duration_exponent": 2.0,
        "p_value": 0.03,
        "log_likelihood": -100.5,
        "best_model": "power-law",
        "n_avalanches": 1500
    }
    with open(fitting_path, 'w') as f:
        json.dump(data, f)
    
    result = load_avalanche_fitting_results("sub-001", temp_data_dir)
    assert result is not None
    assert result["exponent"] == 1.5

def test_load_qc_status_missing_file(temp_data_dir):
    """Test loading QC status when file does not exist."""
    result = load_qc_status("sub-001", temp_data_dir)
    assert result["passed"] is False
    assert result["reason"] == "No QC data found"

def test_load_qc_status_valid(temp_data_dir):
    """Test loading valid QC status file."""
    qc_path = temp_data_dir / "processed" / "qc" / "sub-001_qc.json"
    data = {
        "passed": True,
        "mean_snr": 12.5,
        "is_connected": True,
        "reason": "All checks passed"
    }
    with open(qc_path, 'w') as f:
        json.dump(data, f)
    
    result = load_qc_status("sub-001", temp_data_dir)
    assert result["passed"] is True
    assert result["mean_snr"] == 12.5

def test_collect_subject_metrics_complete(temp_data_dir):
    """Test collecting metrics for a subject with all data present."""
    # Setup metrics
    metrics_path = temp_data_dir / "processed" / "metrics" / "sub-001_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump({"mean_degree_centrality": 0.5, "rich_club_coefficient": 0.8}, f)
    
    # Setup fitting
    fitting_path = temp_data_dir / "processed" / "avalanches" / "sub-001_fitting.json"
    with open(fitting_path, 'w') as f:
        json.dump({"exponent": 1.5, "n_avalanches": 1000}, f)
    
    # Setup QC
    qc_path = temp_data_dir / "processed" / "qc" / "sub-001_qc.json"
    with open(qc_path, 'w') as f:
        json.dump({"passed": True, "mean_snr": 10.0, "is_connected": True}, f)
    
    row = collect_subject_metrics("sub-001", temp_data_dir)
    
    assert row["subject_id"] == "sub-001"
    assert row["qc_passed"] is True
    assert row["mean_snr"] == 10.0
    assert row["degree_centrality_mean"] == 0.5
    assert row["rich_club_coeff"] == 0.8
    assert row["avalanche_size_exponent"] == 1.5
    assert row["n_avalanches"] == 1000

def test_run_export_pipeline_creates_csv(temp_data_dir):
    """Test that the export pipeline creates a valid CSV file."""
    # Create mock data for two subjects
    subjects = ["sub-001", "sub-002"]
    
    for sub in subjects:
        # Metrics
        metrics_path = temp_data_dir / "processed" / "metrics" / f"{sub}_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump({"mean_degree_centrality": 0.5, "rich_club_coefficient": 0.8}, f)
        
        # Fitting
        fitting_path = temp_data_dir / "processed" / "avalanches" / f"{sub}_fitting.json"
        with open(fitting_path, 'w') as f:
            json.dump({"exponent": 1.5, "n_avalanches": 1000}, f)
        
        # QC
        qc_path = temp_data_dir / "processed" / "qc" / f"{sub}_qc.json"
        with open(qc_path, 'w') as f:
            json.dump({"passed": True, "mean_snr": 10.0, "is_connected": True}, f)
    
    output_path = temp_data_dir / "results" / "test_export.csv"
    
    result_path = run_export_pipeline(subject_ids=subjects, output_path=output_path)
    
    assert result_path.exists()
    
    df = pd.read_csv(result_path)
    assert len(df) == 2
    assert "subject_id" in df.columns
    assert "avalanche_size_exponent" in df.columns
    assert "degree_centrality_mean" in df.columns
    assert df["subject_id"].iloc[0] == "sub-001"
    assert df["subject_id"].iloc[1] == "sub-002"

def test_run_export_pipeline_handles_missing_data(temp_data_dir):
    """Test that export handles subjects with missing data gracefully."""
    # Only create QC for sub-001, no metrics or fitting
    qc_path = temp_data_dir / "processed" / "qc" / "sub-001_qc.json"
    with open(qc_path, 'w') as f:
        json.dump({"passed": False, "reason": "No data"}, f)
    
    output_path = temp_data_dir / "results" / "test_missing.csv"
    
    result_path = run_export_pipeline(subject_ids=["sub-001"], output_path=output_path)
    
    assert result_path.exists()
    df = pd.read_csv(result_path)
    assert len(df) == 1
    assert df["subject_id"].iloc[0] == "sub-001"
    assert pd.isna(df["avalanche_size_exponent"].iloc[0])
    assert df["qc_reason"].iloc[0] == "No data"
