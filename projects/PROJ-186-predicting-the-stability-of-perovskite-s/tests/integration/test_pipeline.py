import os
import json
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys
import pandas as pd
import numpy as np

def test_full_training_pipeline_with_sample_data(tmp_path: Path):
    """
    Integration test for the full training pipeline.
    Generates a sample dataset, runs the training script, and verifies outputs.
    
    NOTE: This task specifically requires generating the sample dataset at the
    persistent path `data/processed/sample_features.csv` relative to the project root,
    not just in tmp_path, to satisfy the verification requirements for T020a.
    """
    # 1. Setup paths
    # We need to write to the project's data/processed directory to satisfy T020a
    # We determine the project root based on the test file location
    project_root = Path(__file__).parent.parent.parent
    data_processed_dir = project_root / "data" / "processed"
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = data_processed_dir / "sample_features.csv"
    output_dir = tmp_path / "results"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate sample dataset (100 rows)
    # Columns: tolerance_factor, octahedral_factor, ionic_radius_mismatch, 
    #          electronegativity_diff, decomposition_energy
    # Using numpy for reproducibility and proper float handling
    np.random.seed(42)
    n_rows = 100
    
    data = {
        "tolerance_factor": 0.9 + np.random.uniform(0, 0.1, n_rows),
        "octahedral_factor": 0.8 + np.random.uniform(0, 0.1, n_rows),
        "ionic_radius_mismatch": np.random.uniform(0.0, 0.1, n_rows),
        "electronegativity_diff": np.random.uniform(0.5, 2.0, n_rows),
        "decomposition_energy": np.random.uniform(-0.5, 0.0, n_rows) # eV/atom, negative is stable
    }
    
    df = pd.DataFrame(data)
    
    # Write CSV to the REQUIRED persistent location
    df.to_csv(input_file, index=False)

    assert input_file.exists(), f"Sample features CSV was not created at {input_file}."
    
    # 3. Run training script
    script_path = project_root / "code" / "models" / "train.py"
    
    if not script_path.exists():
        pytest.fail(f"Training script not found at {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        "--input", str(input_file),
        "--output", str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
    
    # 4. Verify execution success
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        pytest.fail(f"Training script failed with return code {result.returncode}")

    # 5. Verify artifacts
    model_path = output_dir / "model.pkl"
    metrics_path = output_dir / "metrics.json"
    importance_path = output_dir / "permutation_importance.json"
    plot_path = output_dir / "feature-importance.png"

    assert model_path.exists(), "Model file (model.pkl) not created."
    assert metrics_path.exists(), "Metrics file (metrics.json) not created."
    assert importance_path.exists(), "Permutation importance file not created."
    assert plot_path.exists(), "Feature importance plot not created."

    # 6. Verify metrics content
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert 'test_rmse' in metrics, "test_rmse key missing in metrics.json"
    assert isinstance(metrics['test_rmse'], (int, float)), "test_rmse is not numeric"
    assert 'best_params' in metrics, "best_params key missing"
    assert 'dft_functional' in metrics, "dft_functional key missing"
    assert metrics['dft_functional'] == "PBE", "dft_functional should be PBE"

    # 7. Verify model can be loaded (basic check)
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    assert model is not None, "Model could not be loaded."
    
    # 8. Verify permutation importance content
    with open(importance_path, 'r') as f:
        importance = json.load(f)
    
    expected_features = ['tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch', 'electronegativity_diff']
    for feat in expected_features:
        assert feat in importance, f"Feature {feat} missing in permutation importance"
        assert isinstance(importance[feat], (int, float)), f"Importance for {feat} is not numeric"

    print("Integration test passed: All artifacts created and validated.")
    print(f"Sample data successfully saved to: {input_file}")