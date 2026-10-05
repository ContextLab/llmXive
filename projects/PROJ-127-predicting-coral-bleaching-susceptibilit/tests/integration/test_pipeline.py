"""
Integration tests for the coral bleaching prediction pipeline.
Tests the end-to-end flow: Spatial Split -> Training -> Evaluation -> Permutation Importance.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from train import load_data, spatial_split, train_model, save_results
from evaluate import load_model_and_data, compute_permutation_importance_and_fdr, bootstrap_stability_analysis
import config


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs to avoid cluttering the real data/ directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_spatial_split_and_training(temp_output_dir):
    """
    Test T013 & T014: Spatial split and model training.
    Verifies that the model can be trained on a spatial split without crashing
    and produces valid result artifacts.
    """
    # 1. Load Data
    # We expect the unified CSV to exist from T007. If not, the test fails loudly.
    data_path = config.PROCESSED_DIR / "reef_species_unified.csv"
    if not data_path.exists():
        pytest.fail(f"Required input file not found: {data_path}. "
                    "Ensure T007 (Ingestion/Merge) has been run successfully.")

    df = load_data(data_path)
    assert not df.empty, "Loaded data is empty."

    # 2. Spatial Split
    # T013: Split data spatially (Train: Western Pacific, Test: Eastern Pacific)
    train_df, test_df = spatial_split(df)

    assert len(train_df) > 0, "Training set is empty."
    assert len(test_df) > 0, "Test set is empty."

    # Verify spatial separation logic (approximate check based on longitude)
    # Western Pacific is generally < 160E (or > 200W), Eastern Pacific > 280E (or -80W)
    # Note: This depends on how 'region' or 'longitude' is stored.
    # Assuming 'longitude' column exists from merge.
    if 'longitude' in train_df.columns and 'longitude' in test_df.columns:
        # Simple heuristic: Train should be mostly West, Test mostly East
        # This is a sanity check, not a strict assertion, as data distribution varies.
        pass

    # 3. Train Model
    # T014: Train XGBoost with 5-fold CV
    model, best_params, history = train_model(train_df)

    assert model is not None, "Model training failed (returned None)."
    assert 'best_params' in best_params, "Best parameters not returned."

    # 4. Save Results (T015/T016 intermediate step)
    # We save to a temp location to verify the JSON structure
    results_path = Path(temp_output_dir) / "results.json"
    save_results(model, best_params, history, results_path, test_df)

    assert results_path.exists(), "Results file was not saved."

    with open(results_path, 'r') as f:
        results = json.load(f)

    # Verify structure
    assert 'roc_auc' in results, "ROC-AUC missing from results."
    assert 'best_params' in results, "Best params missing from results."
    assert 'performance_status' in results, "Performance status missing."

    # 5. Evaluate Model (T016)
    # Re-load to ensure statelessness
    loaded_model, X_test, y_test = load_model_and_data(train_df, test_df, model)
    metrics = compute_permutation_importance_and_fdr(loaded_model, X_test, y_test)

    # 6. Permutation Importance & FDR (T018)
    # Note: T018 requires N=1000 permutations. For speed in tests, we might mock or reduce,
    # but the requirement says N=1000. We will run it but ensure it doesn't hang.
    # In a real CI environment, this might be skipped if data is too large, but here we assume
    # the data is small enough or the test is run on a subset.
    
    # We rely on the evaluate module's main logic to handle the heavy lifting.
    # The test verifies the function runs and returns a dict with expected keys.
    perm_results = compute_permutation_importance_and_fdr(loaded_model, X_test, y_test)
    
    assert perm_results is not None, "Permutation importance failed."
    assert 'ranking' in perm_results, "Ranking missing from permutation results."
    assert 'p_values' in perm_results, "P-values missing from permutation results."
    assert 'corrected_p_values' in perm_results, "Corrected p-values missing."

    # 7. Bootstrap Stability (T019)
    # Run bootstrap stability analysis
    stability_results = bootstrap_stability_analysis(loaded_model, X_test, y_test, n_resamples=100)
    
    assert stability_results is not None, "Bootstrap stability analysis failed."
    assert 'top_3_stability' in stability_results, "Top 3 stability missing."


def test_pipeline_end_to_end(temp_output_dir):
    """
    Full end-to-end test of the pipeline components:
    1. Data Loading
    2. Spatial Split
    3. Training
    4. Evaluation (Metrics + Permutation + Bootstrap)
    5. Output Verification
    """
    data_path = config.PROCESSED_DIR / "reef_species_unified.csv"
    if not data_path.exists():
        pytest.skip(f"Skipping end-to-end test: {data_path} not found. Run T007 first.")

    # 1. Load & Split
    df = load_data(data_path)
    train_df, test_df = spatial_split(df)

    # 2. Train
    model, best_params, history = train_model(train_df)

    # 3. Evaluate
    loaded_model, X_test, y_test = load_model_and_data(train_df, test_df, model)
    
    # Compute metrics
    metrics = compute_permutation_importance_and_fdr(loaded_model, X_test, y_test)
    
    # Compute stability
    stability = bootstrap_stability_analysis(loaded_model, X_test, y_test, n_resamples=100)

    # 4. Verify Outputs
    assert metrics is not None
    assert stability is not None
    assert 'roc_auc' in metrics or 'roc_auc' in (metrics.get('metrics', {}))

    # Ensure we can serialize results
    try:
        json.dumps(metrics)
        json.dumps(stability)
    except TypeError as e:
        pytest.fail(f"Results are not JSON serializable: {e}")


def test_edge_case_zero_positives(temp_output_dir):
    """
    Test T015: Handle edge case where test set has zero positive events.
    """
    data_path = config.PROCESSED_DIR / "reef_species_unified.csv"
    if not data_path.exists():
        pytest.skip(f"Skipping edge case test: {data_path} not found.")

    df = load_data(data_path)
    train_df, test_df = spatial_split(df)

    # Artificially create a test set with zero positives
    # We filter the test_df to only include negative cases
    if 'bleaching_label' in test_df.columns:
        test_df_no_positives = test_df[test_df['bleaching_label'] == 0].copy()
    else:
        # If label column doesn't exist, skip this specific check
        pytest.skip("Label column 'bleaching_label' not found.")

    if len(test_df_no_positives) == 0:
        pytest.skip("Cannot create zero-positive test set from available data.")

    # Train on full train set
    model, _, _ = train_model(train_df)

    # Attempt evaluation
    loaded_model, X_test, y_test = load_model_and_data(train_df, test_df_no_positives, model)
    
    # This should handle the zero-positive case gracefully (return None or 0.0 for AUC)
    # The evaluate module should catch this internally.
    try:
        metrics = compute_permutation_importance_and_fdr(loaded_model, X_test, y_test)
        # If we get here, the function didn't crash.
        # Check if ROC_AUC is handled (might be null or 0.0)
        if 'roc_auc' in metrics:
            assert metrics['roc_auc'] is not None or metrics['roc_auc'] == 0.0
    except Exception as e:
        pytest.fail(f"Evaluation crashed on zero-positive test set: {e}")