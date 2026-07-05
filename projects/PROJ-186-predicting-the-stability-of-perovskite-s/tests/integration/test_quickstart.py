"""
Integration test for T046: Quickstart validation
Verifies that the pipeline produces expected artifacts and valid results.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.mark.integration
def test_quickstart_artifacts_exist():
    """Test that all required artifacts exist after pipeline run."""
    required_files = [
        "data/processed/features.csv",
        "results/model.pkl",
        "results/metrics.json",
        "results/screening_full.csv",
        "results/screening_candidates.md",
        "logs/pipeline.log",
        "results/manifest.json"
    ]

    for rel_path in required_files:
        full_path = project_root / rel_path
        assert full_path.exists(), f"Missing artifact: {rel_path}"
        assert full_path.stat().st_size > 0, f"Empty artifact: {rel_path}"

@pytest.mark.integration
def test_quickstart_metrics_valid():
    """Test that metrics file contains expected fields and valid values."""
    metrics_path = project_root / "results/metrics.json"
    
    assert metrics_path.exists(), "Metrics file missing"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Check required fields
    assert 'test_rmse' in metrics, "Missing test_rmse in metrics"
    assert 'best_params' in metrics, "Missing best_params in metrics"
    assert 'cv_score' in metrics, "Missing cv_score in metrics"
    
    # Check value validity
    assert isinstance(metrics['test_rmse'], (int, float)), "test_rmse must be numeric"
    assert metrics['test_rmse'] >= 0, "test_rmse must be non-negative"
    
    assert isinstance(metrics['best_params'], dict), "best_params must be a dict"
    assert 'max_depth' in metrics['best_params'], "Missing max_depth in best_params"
    assert 'min_samples_leaf' in metrics['best_params'], "Missing min_samples_leaf in best_params"

@pytest.mark.integration
def test_quickstart_screening_results():
    """Test that screening results contain expected structure."""
    screening_path = project_root / "results/screening_full.csv"
    
    assert screening_path.exists(), "Screening results missing"
    
    import pandas as pd
    df = pd.read_csv(screening_path)
    
    # Check required columns
    required_cols = ['formula', 'predicted_decomposition_energy', 'is_feasible']
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check data validity
    assert len(df) > 0, "Screening results empty"
    assert df['predicted_decomposition_energy'].notna().all(), "Missing predicted energy values"
    
    # Check that we have feasible candidates
    feasible_count = df['is_feasible'].sum() if 'is_feasible' in df.columns else 0
    assert feasible_count >= 200, f"Expected >= 200 feasible candidates, got {feasible_count}"

@pytest.mark.integration
def test_quickstart_candidate_report():
    """Test that candidate report is generated and contains top candidates."""
    report_path = project_root / "results/screening_candidates.md"
    
    assert report_path.exists(), "Candidate report missing"
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    assert len(content) > 100, "Candidate report too short"
    assert "Top Candidates" in content or "Top" in content, "Report should mention top candidates"
    assert "eV/atom" in content, "Report should contain energy units"

@pytest.mark.integration
def test_quickstart_log_contains_events():
    """Test that pipeline log contains expected events."""
    log_path = project_root / "logs/pipeline.log"
    
    assert log_path.exists(), "Pipeline log missing"
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    assert len(log_content) > 0, "Pipeline log empty"
    assert "T046" in log_content or "Quickstart" in log_content, "Log should reference validation"
    assert "SUCCESS" in log_content or "completed" in log_content.lower(), "Log should indicate success"

@pytest.mark.integration
def test_quickstart_hash_manifest():
    """Test that hash manifest exists and contains valid entries."""
    manifest_path = project_root / "results/manifest.json"
    
    assert manifest_path.exists(), "Hash manifest missing"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert isinstance(manifest, dict), "Manifest should be a dict"
    assert "artifacts" in manifest, "Manifest should contain artifacts key"
    assert len(manifest["artifacts"]) > 0, "Manifest should have artifact entries"
    
    # Check that hashes are valid SHA256 format
    for artifact in manifest["artifacts"].values():
        if "hash" in artifact:
            assert len(artifact["hash"]) == 64, "SHA256 hash should be 64 characters"
            assert all(c in '0123456789abcdef' for c in artifact["hash"]), "Hash should be hex"

@pytest.mark.integration
def test_quickstart_model_metadata():
    """Test that model metadata is valid."""
    import pickle
    model_path = project_root / "results/model.pkl"
    
    assert model_path.exists(), "Model file missing"
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Check that model has expected attributes
    assert hasattr(model, 'best_estimator_') or hasattr(model, 'estimators_'), \
        "Model should have estimator attributes"
    
    # Check for metadata in model attributes
    if hasattr(model, 'metadata_'):
        metadata = model.metadata_
        assert 'dft_functional' in metadata, "Metadata should contain DFT functional"
        assert metadata['dft_functional'] == 'PBE', "DFT functional should be PBE"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
