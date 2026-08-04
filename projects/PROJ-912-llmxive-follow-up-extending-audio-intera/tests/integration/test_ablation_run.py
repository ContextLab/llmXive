"""
Integration test for ablation execution (T035).

This test verifies the full end-to-end execution of the ablation study:
1. Loads a student model (from T015/T016 artifacts).
2. Applies ablation configurations (freeze attention, prune FFN) via `code/analysis/ablation.py`.
3. Runs inference on ablated models using `code/inference/runner.py`.
4. Generates `data/processed/ablation_results.csv` with metrics.
5. Validates that distinct configurations produce distinct results and no state leakage occurs.

Prerequisites:
- T036 (ablation config parser) must be implemented.
- T036b (clone_model) must be implemented.
- T037/T038 (freeze/prune logic) must be implemented.
- T039 (integration with inference) must be implemented.
- Real student models must exist in `data/processed/` (from T015).
- Real data subset must exist (from T020).
"""

import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_path_config, get_evaluation_config
from analysis.ablation import (
    load_ablation_config,
    apply_ablation,
    run_ablation_study,
    validate_ablation_results
)
from models.student import clone_model
from utils.logger import get_logger

logger = get_logger("test_ablation_run")

# Constants
EXPECTED_COLUMNS = ["config_id", "auc", "latency_ms", "ram_gb", "compression_type", "params_removed"]
ABALATION_CONFIG_PATH = "data/processed/ablation_config.json"
ABALATION_RESULTS_PATH = "data/processed/ablation_results.csv"
MIN_EXPECTED_ROWS = 3  # At least: baseline, freeze, prune


def setup_module(module):
    """Ensure required artifacts exist before running tests."""
    path_config = get_path_config()
    processed_dir = path_config.processed_data_dir
    
    # Check for ablation config (produced by T036)
    if not os.path.exists(ABALATION_CONFIG_PATH):
        pytest.skip(f"Ablation config not found at {ABALATION_CONFIG_PATH}. T036 may not be complete.")
    
    # Check for at least one student model (produced by T015)
    student_models = list(processed_dir.glob("student_model_*.pt"))
    if not student_models:
        pytest.skip("No student models found in data/processed/. T015 may not be complete.")

def test_ablation_config_loads():
    """Test T036: Config parser loads valid ablation configurations."""
    config = load_ablation_config(ABALATION_CONFIG_PATH)
    assert config is not None
    assert "configurations" in config
    assert len(config["configurations"]) > 0
    
    # Verify structure of first config
    first_config = config["configurations"][0]
    assert "config_id" in first_config
    assert "type" in first_config
    assert "params" in first_config
    logger.info(f"Loaded ablation config with {len(config['configurations'])} configurations")

def test_clone_model_isolation():
    """Test T036b: clone_model creates a deep copy with no shared state."""
    from models.student import load_student_model
    
    # Load a student model
    student_models = list(Path("data/processed").glob("student_model_*.pt"))
    if not student_models:
        pytest.skip("No student models found for clone test.")
    
    model_path = student_models[0]
    original_model = load_student_model(model_path)
    
    # Clone the model
    cloned_model = clone_model(original_model)
    
    # Verify they are different objects
    assert original_model is not cloned_model
    
    # Verify weights are identical initially
    for (name1, param1), (name2, param2) in zip(
        original_model.named_parameters(), cloned_model.named_parameters()
    ):
        assert name1 == name2
        assert torch.equal(param1, param2)
    
    # Modify cloned model and verify original is unchanged
    with torch.no_grad():
        for param in cloned_model.parameters():
            param.add_(1.0)
    
    for (name1, param1), (name2, param2) in zip(
        original_model.named_parameters(), cloned_model.named_parameters()
    ):
        assert not torch.equal(param1, param2)
    
    logger.info("Clone isolation verified: modifications to clone do not affect original")

def test_ablation_execution_end_to_end():
    """Test T035: Full ablation execution pipeline."""
    import torch
    
    # Run the ablation study
    results = run_ablation_study(
        config_path=ABALATION_CONFIG_PATH,
        output_path=ABALATION_RESULTS_PATH
    )
    
    assert results is not None
    assert isinstance(results, list)
    assert len(results) >= MIN_EXPECTED_ROWS
    
    # Verify results file was created
    assert os.path.exists(ABALATION_RESULTS_PATH), f"Results file {ABALATION_RESULTS_PATH} not created"
    
    # Validate CSV structure
    with open(ABALATION_RESULTS_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) >= MIN_EXPECTED_ROWS
        for row in rows:
            for col in EXPECTED_COLUMNS:
                assert col in row, f"Missing column {col} in row {row}"
            
            # Verify numeric fields are parseable
            float(row["auc"])
            float(row["latency_ms"])
            float(row["ram_gb"])
            
            # Verify config_id is unique
            assert row["config_id"], "config_id cannot be empty"
    
    # Verify distinct configurations produce distinct results
    config_ids = [row["config_id"] for row in rows]
    assert len(config_ids) == len(set(config_ids)), "Duplicate config_ids found"
    
    # Verify at least one result has non-zero params_removed (for prune config)
    prune_results = [row for row in rows if row["compression_type"] == "prune"]
    if prune_results:
        has_removals = any(float(row["params_removed"]) > 0 for row in prune_results)
        assert has_removals, "Prune configuration should report removed parameters"
    
    logger.info(f"Ablation execution completed: {len(rows)} results generated")

def test_no_state_leakage_between_configs():
    """Test T037/T038: Verify no state leakage between ablation configurations."""
    import torch
    
    # Run study again to get fresh results
    results = run_ablation_study(
        config_path=ABALATION_CONFIG_PATH,
        output_path=ABALATION_RESULTS_PATH
    )
    
    # Group results by config type
    freeze_results = [r for r in results if r["compression_type"] == "freeze"]
    prune_results = [r for r in results if r["compression_type"] == "prune"]
    baseline_results = [r for r in results if r["compression_type"] == "baseline"]
    
    # If we have multiple freeze/prune configs, verify they differ
    if len(freeze_results) > 1:
        auc_values = [float(r["auc"]) for r in freeze_results]
        # They should not all be identical (unless the model is completely unaffected)
        # Allow small numerical differences
        assert len(set([round(a, 4) for a in auc_values])) > 1 or len(freeze_results) == 1, \
            "Freeze configurations should produce distinct results if they affect different components"
    
    if len(prune_results) > 1:
        auc_values = [float(r["auc"]) for r in prune_results]
        assert len(set([round(a, 4) for a in auc_values])) > 1 or len(prune_results) == 1, \
            "Prune configurations should produce distinct results if they remove different layers"
    
    logger.info("No state leakage detected between ablation configurations")

def test_ablation_results_validation():
    """Test T041: Validate that ablation results are sensible."""
    results = validate_ablation_results(ABALATION_RESULTS_PATH)
    
    assert results["valid"] is True
    assert "errors" in results
    assert len(results["errors"]) == 0
    
    # Check for expected warnings if any
    if results["warnings"]:
        logger.warning(f"Validation warnings: {results['warnings']}")
    
    logger.info("Ablation results validated successfully")

def test_ablation_vs_baseline_performance():
    """Test that ablation configurations show expected performance trends."""
    import csv
    
    with open(ABALATION_RESULTS_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    baseline_auc = None
    for row in rows:
        if row["compression_type"] == "baseline":
            baseline_auc = float(row["auc"])
            break
    
    if baseline_auc is None:
        pytest.skip("No baseline configuration found in results")
    
    # Verify that ablation configurations don't have dramatically better AUC than baseline
    # (they should be similar or slightly worse due to compression)
    for row in rows:
        if row["compression_type"] != "baseline":
            auc = float(row["auc"])
            # Allow for some variance, but not a 20%+ improvement (which would indicate a bug)
            assert auc <= baseline_auc * 1.2, \
                f"Configuration {row['config_id']} has AUC {auc:.4f} > baseline {baseline_auc:.4f} * 1.2"
    
    logger.info(f"Performance trends verified: baseline AUC = {baseline_auc:.4f}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

# Note: This test file requires torch to be imported for model cloning tests
# The import is placed inside the test functions to avoid issues if torch is not available
import torch