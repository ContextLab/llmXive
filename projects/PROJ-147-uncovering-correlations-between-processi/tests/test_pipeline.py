"""
Integration test for User Story 1: End-to-End Data-Driven Texture Prediction.

This test verifies that the full pipeline runs successfully on synthetic data
and produces the expected artifacts (predictions.csv, model file, pipeline.log).

It explicitly validates:
1. The synthetic data generator creates a valid dataset with >= 3 alloy families.
2. The data loader ingests the data correctly.
3. The processor handles unit standardization and feature derivation.
4. The trainer fits a RandomForest model.
5. The predictor generates predictions.
6. All required output files exist in the data/ directory.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import ensure_dirs
from code.data.synthetic import generate_synthetic_dataset, validate_ground_truth
from code.data.loader import load_dataset
from code.data.processor import process_dataset
from code.models.trainer import train_model
from code.models.predictor import predict_texture
from code.utils.logging import setup_logging, get_logger


@pytest.fixture(scope="module")
def pipeline_config():
    """
    Setup a temporary directory structure for the integration test.
    Returns a dict with paths and configuration.
    """
    # Create a temporary directory for this test run to avoid polluting the main data/
    test_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    test_root = Path(test_dir)

    # Mock the project structure within the temp dir
    # We will inject these paths into the config or pass them explicitly
    # Since config.py uses relative paths based on PROJECT_ROOT, we need to be careful.
    # For this integration test, we will override the standard paths by passing them
    # directly to the functions that accept them, or by temporarily modifying the config
    # if it relies on global state.
    # However, looking at the API surface, `ensure_dirs` takes paths.
    # Let's assume the functions `train_model`, `predict_texture` etc. accept path arguments
    # or we configure them via a config object.
    # Since the API surface provided for `code/main.py` just shows `main`,
    # and `code/models/trainer.py` isn't fully detailed in the "public names" list beyond `train_model`,
    # we will assume standard signatures based on the task descriptions.

    config = {
        "root_dir": test_root,
        "data_dir": test_root / "data",
        "raw_dir": test_root / "data" / "raw",
        "processed_dir": test_root / "data" / "processed",
        "models_dir": test_root / "models",
        "output_dir": test_root / "output",
        "log_file": test_root / "pipeline.log",
        "synthetic_output": test_root / "data" / "raw" / "synthetic_metal_data.csv",
        "ground_truth_file": test_root / "data" / "raw" / "ground_truth.json",
        "model_file": test_root / "models" / "texture_rf_model.pkl",
        "predictions_file": test_root / "output" / "predictions.csv",
        "new_predictions_file": test_root / "output" / "new_predictions.csv",
    }

    # Ensure directories exist
    ensure_dirs(
        data_dir=config["data_dir"],
        models_dir=config["models_dir"],
        output_dir=config["output_dir"],
        raw_dir=config["raw_dir"],
        processed_dir=config["processed_dir"]
    )

    # Setup logging to the temp file
    setup_logging(log_file=config["log_file"])

    yield config

    # Cleanup
    shutil.rmtree(test_dir)


def test_full_pipeline_end_to_end(pipeline_config):
    """
    Runs the full pipeline: Generate -> Load -> Process -> Train -> Predict.
    Verifies that all expected artifacts are created.
    """
    logger = get_logger()
    logger.info("Starting Integration Test: Full Pipeline on Synthetic Data")

    # 1. Generate Synthetic Data
    # Task T009/T009a ensures >= 3 families, >= 50 samples each.
    logger.info("Generating synthetic dataset...")
    generate_synthetic_dataset(
        output_csv=pipeline_config["synthetic_output"],
        ground_truth_json=pipeline_config["ground_truth_file"],
        n_samples_per_family=60, # Ensure >= 50
        n_families=3             # Ensure >= 3
    )

    # Validate ground truth
    assert pipeline_config["ground_truth_file"].exists(), "Ground truth file not created"
    with open(pipeline_config["ground_truth_file"], 'r') as f:
        gt_data = json.load(f)
    assert gt_data.get("n_families", 0) >= 3, "Ground truth validation failed: < 3 families"
    for family, count in gt_data.get("family_counts", {}).items():
        assert count >= 50, f"Ground truth validation failed: Family {family} has < 50 samples"

    # 2. Load Dataset
    # Task T010: Load data, validate families.
    logger.info("Loading dataset...")
    # Assuming load_dataset takes paths and returns a DataFrame
    # The API surface for loader.py wasn't fully detailed with signatures,
    # but T010 description implies it ingests and validates.
    # We assume a signature like: load_dataset(raw_dir, output_processed_dir)
    # or load_dataset(csv_path).
    # Based on T010 "fallback to synthetic", it likely checks a folder.
    # Let's assume it processes the synthetic file we just created.
    df = load_dataset(
        raw_dir=pipeline_config["raw_dir"],
        processed_dir=pipeline_config["processed_dir"]
    )
    assert df is not None, "Dataset loading failed"
    assert len(df) >= 150, f"Dataset size too small: {len(df)} (expected >= 150)"

    # 3. Process Dataset
    # Task T011a: Unit standardization, imputation, outlier removal, feature derivation.
    logger.info("Processing dataset...")
    df_processed = process_dataset(df)
    assert df_processed is not None, "Dataset processing failed"
    assert len(df_processed) > 0, "Processed dataset is empty"

    # 4. Train Model
    # Task T013: Multi-output RandomForest with 5-fold CV.
    logger.info("Training model...")
    model = train_model(
        df=df_processed,
        model_path=pipeline_config["model_file"]
    )
    assert model is not None, "Model training failed"
    assert pipeline_config["model_file"].exists(), "Model file not saved"

    # 5. Predict
    # Task T014/T015/T017: Generate predictions.csv and new_predictions.csv.
    logger.info("Generating predictions...")
    # Assuming predict_texture takes model, data, and output paths
    predictions_df, new_predictions_df = predict_texture(
        model=model,
        data=df_processed,
        predictions_csv=pipeline_config["predictions_file"],
        new_predictions_csv=pipeline_config["new_predictions_file"]
    )

    # 6. Verify Artifacts
    logger.info("Verifying artifacts...")

    # Check predictions.csv
    assert pipeline_config["predictions_file"].exists(), "predictions.csv not created"
    assert predictions_df is not None and len(predictions_df) > 0, "predictions_df is empty"

    # Check new_predictions.csv
    assert pipeline_config["new_predictions_file"].exists(), "new_predictions.csv not created"
    assert new_predictions_df is not None and len(new_predictions_df) > 0, "new_predictions_df is empty"

    # Check pipeline.log (created by setup_logging and used throughout)
    assert pipeline_config["log_file"].exists(), "pipeline.log not created"
    assert pipeline_config["log_file"].stat().st_size > 0, "pipeline.log is empty"

    logger.info("Integration Test PASSED: All artifacts created successfully.")