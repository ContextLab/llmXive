import os
import json
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys

def test_full_training_pipeline_with_sample_data(tmp_path: Path):
    """
    Integration test for the full training pipeline.
    Generates a sample dataset, runs the training script, and verifies outputs.
    """
    # 1. Setup paths
    input_file = tmp_path / "sample_features.csv"
    output_dir = tmp_path / "results"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate sample dataset (100 rows)
    # Columns: tolerance_factor, octahedral_factor, ionic_radius_mismatch, 
    #          electronegativity_diff, decomposition_energy
    sample_data = [
        ["tolerance_factor", "octahedral_factor", "ionic_radius_mismatch", "electronegativity_diff", "decomposition_energy"]
    ]
    for i in range(100):
        row = [
            0.9 + (i * 0.001),  # tolerance_factor
            0.8 + (i * 0.001),  # octahedral_factor
            0.05 + (i * 0.0005), # ionic_radius_mismatch
            0.5 + (i * 0.002),   # electronegativity_diff
            -0.1 - (i * 0.001)   # decomposition_energy
        ]
        sample_data.append(row)

    # Write CSV
    with open(input_file, 'w') as f:
        for row in sample_data:
            f.write(','.join(map(str, row)) + '\n')

    assert input_file.exists(), "Sample features CSV was not created."
    
    # 3. Run training script
    # Assuming the script is at code/models/train.py relative to project root
    # We need to run it from the project root context or adjust paths
    project_root = Path(__file__).parent.parent.parent
    script_path = project_root / "code" / "models" / "train.py"
    
    if not script_path.exists():
        pytest.fail(f"Training script not found at {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        "--input", str(input_file),
        "--output", str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    
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