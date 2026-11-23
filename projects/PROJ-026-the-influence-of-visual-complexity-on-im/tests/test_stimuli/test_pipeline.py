"""
Integration tests for the full stimulus complexity quantification pipeline (US1).

This test suite verifies the end-to-end flow:
1. Validation of images (simulated via pre-existing logs or mock).
2. Computation of metrics (Edge Density, Entropy, Fractal Dimension).
3. Categorization via Median Split.
4. Final CSV output schema and content verification.
"""
import os
import tempfile
import shutil
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Import pipeline components
from stimuli.validate import validate_batch, get_valid_images
from stimuli.metrics import process_image_vectorized
from stimuli.serialize import load_raw_complexity_scores, apply_categorization, save_final_csv
from config import get_data_path

# Configure logging for tests to avoid missing handler errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_test_image(tmp_dir: Path, filename: str, mode: str = "solid") -> Path:
    """
    Helper to create deterministic test images for integration testing.
    mode: 'solid' (low complexity), 'noise' (high complexity), 'gradient' (mid)
    """
    import cv2
    img_path = tmp_dir / filename
    if mode == "solid":
        # Solid gray image (low edge density, low entropy)
        img = np.zeros((100, 100), dtype=np.uint8) + 128
    elif mode == "noise":
        # High frequency noise (high edge density, high entropy)
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    elif mode == "gradient":
        # Linear gradient (mid complexity)
        img = np.tile(np.arange(100, dtype=np.uint8), (100, 1)).T
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    cv2.imwrite(str(img_path), img)
    return img_path


def test_complexity_pipeline(tmp_path: Path):
    """
    Integration test: test_complexity_pipeline
    
    Verifies that the full pipeline:
    1. Validates images (creates valid list).
    2. Computes metrics for valid images.
    3. Applies median split categorization.
    4. Outputs a CSV with correct columns and logical categories.
    
    Assertion: Output CSV has correct columns and categories.
    Specifically:
    - Columns: filename, edge_density, entropy, fractal_dim, complexity_category
    - Categories are 'Low' or 'High'.
    - Noise images should generally be 'High' and solid 'Low' (statistically likely).
    """
    # Setup temporary directories mimicking project structure
    data_root = tmp_path / "data"
    raw_stimuli = data_root / "raw" / "stimuli"
    processed = data_root / "processed"
    logs = tmp_path / "logs"
    
    raw_stimuli.mkdir(parents=True)
    processed.mkdir(parents=True)
    logs.mkdir(parents=True)
    
    # Patch config to use temp paths for this test
    # Note: In a real run, config.py would point to the project root.
    # Here we rely on relative paths or explicit passing if the functions support it.
    # Since process.py/serialize.py use get_data_path, we need to ensure the environment
    # or config is set up correctly. For this integration test, we will use explicit
    # paths where possible or mock the config if necessary.
    # However, to keep it simple and robust, we will pass explicit paths to the functions
    # if they support it, or assume the test runs from the project root context.
    # Given the API surface, let's assume we run this from the project root or
    # we manually set the paths in the functions if they don't take args.
    # Looking at the API:
    # validate_batch: no args -> uses config
    # process_image_vectorized: takes image_path
    # apply_categorization: takes df
    # save_final_csv: takes df, output_path
    
    # To make this test portable, we will temporarily override get_data_path behavior
    # or simply set environment variables if the config relies on them.
    # Alternatively, we can create the files in the expected relative location if
    # we assume the test runner sets the cwd.
    # Let's assume the test is run from the project root, so we create the structure
    # in the temp dir and then change cwd or patch the config.
    # Since we cannot easily patch the module-level constants in config.py without
    # reloading, let's create a mini-project structure in the temp dir and change cwd.
    
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # 1. Create Test Data
        # Create a mix of images to ensure median split works
        # 2 Solid (Low), 2 Noise (High) -> Median split should separate them perfectly
        _create_test_image(raw_stimuli, "solid1.png", "solid")
        _create_test_image(raw_stimuli, "solid2.png", "solid")
        _create_test_image(raw_stimuli, "noise1.png", "noise")
        _create_test_image(raw_stimuli, "noise2.png", "noise")
        
        # 2. Run Validation (T016 simulation)
        # The validate.py script expects to run from the project root and write to logs/validation.log
        # We call the main logic directly or run the script.
        # Let's call the function directly to avoid subprocess complexity in tests.
        valid_images, invalid_images = get_valid_images(raw_stimuli)
        
        # Write the valid list to the expected location
        valid_list_path = processed / "valid_images_list.txt"
        with open(valid_list_path, "w") as f:
            for img in valid_images:
                f.write(img.name + "\n")
        
        assert valid_list_path.exists(), "Valid images list not created"
        assert len(valid_images) == 4, f"Expected 4 valid images, got {len(valid_images)}"
        
        # 3. Compute Metrics (T017a-2 simulation)
        # Read valid list
        with open(valid_list_path, "r") as f:
            valid_files = [line.strip() for line in f if line.strip()]
        
        metrics_rows = []
        for filename in valid_files:
            img_path = raw_stimuli / filename
            try:
                edge_density, entropy, fractal_dim = process_image_vectorized(img_path)
                metrics_rows.append({
                    "filename": filename,
                    "edge_density": edge_density,
                    "entropy": entropy,
                    "fractal_dim": fractal_dim
                })
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                # In a real pipeline, this might be logged and skipped, but for integration
                # we expect success on valid test images.
                raise
        
        raw_metrics_df = pd.DataFrame(metrics_rows)
        raw_metrics_path = processed / "complexity_metrics_raw.csv"
        raw_metrics_df.to_csv(raw_metrics_path, index=False)
        
        assert raw_metrics_path.exists(), "Raw metrics CSV not created"
        assert "edge_density" in raw_metrics_df.columns
        assert "entropy" in raw_metrics_df.columns
        assert "fractal_dim" in raw_metrics_df.columns
        
        # 4. Categorize and Save Final (T017a-3 simulation)
        # Load raw
        df = load_raw_complexity_scores(raw_metrics_path)
        
        # Apply median split
        df_categorized = apply_categorization(df, metric="edge_density")
        
        # Save final
        final_path = processed / "complexity_scores.csv"
        save_final_csv(df_categorized, final_path)
        
        assert final_path.exists(), "Final complexity scores CSV not created"
        
        # 5. Verify Output
        final_df = pd.read_csv(final_path)
        
        # Check columns
        expected_cols = ["filename", "edge_density", "entropy", "fractal_dim", "complexity_category"]
        assert list(final_df.columns) == expected_cols, f"Columns mismatch: {list(final_df.columns)}"
        
        # Check categories
        assert all(cat in ["Low", "High"] for cat in final_df["complexity_category"]), "Invalid categories found"
        
        # Check logic: Noise images should have higher edge density than solid images
        # and thus likely be categorized as 'High'
        noise_rows = final_df[final_df["filename"].str.contains("noise")]
        solid_rows = final_df[final_df["filename"].str.contains("solid")]
        
        if len(noise_rows) > 0 and len(solid_rows) > 0:
            # With 2 solid and 2 noise, median split should put solid in Low and noise in High
            # unless edge density calculation is weirdly non-monotonic (unlikely for solid vs noise)
            assert all(solid_rows["complexity_category"] == "Low"), "Solid images should be Low complexity"
            assert all(noise_rows["complexity_category"] == "High"), "Noise images should be High complexity"
        
        logger.info("Integration test passed: Pipeline produced correct CSV with valid categories.")

    finally:
        os.chdir(original_cwd)