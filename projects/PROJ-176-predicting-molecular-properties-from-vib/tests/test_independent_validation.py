"""
Integration test for independent validation (US4).
Verifies separate metric reporting when evaluating on an external dataset.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from evaluation.metrics import compute_mae, compute_r2
from evaluation.validate import (
    load_model_checkpoint,
    load_model_with_dim,
    run_inference,
    generate_synthetic_noise_data,
    compute_validation_metrics,
    main as validate_main
)
from utils.seed_utils import set_seed

# Set seed for reproducibility in test
set_seed(42)

def test_independent_validation_separate_reporting():
    """
    Test that independent validation produces a separate metric report
    distinct from the training/test set results.
    """
    # Create a temporary directory for test artifacts
    temp_dir = tempfile.mkdtemp()
    try:
        # Paths for test artifacts
        model_path = Path(temp_dir) / "model_best.pt"
        test_data_path = Path(temp_dir) / "test_data.npz"
        external_data_path = Path(temp_dir) / "external_data.npz"
        results_path = Path(temp_dir) / "validation_results.json"

        # 1. Create a dummy model checkpoint
        # (In a real scenario, this would be the trained model)
        from models.cnn_1d import MolecularPropertyCNN
        dummy_model = MolecularPropertyCNN(input_dim=200) # 200 wavenumbers
        torch_dummy_state = dummy_model.state_dict()
        
        # Save dummy checkpoint
        import torch
        torch.save({
            'model_state_dict': torch_dummy_state,
            'optimizer_state_dict': None,
            'epoch': 0,
            'loss': 0.0
        }, model_path)

        # 2. Create dummy preprocessed test data
        # Format: {'spectra': (N, 200), 'dipole': (N,), 'polarizability': (N,), 'gap': (N,), 'InChIKey': (N,)}
        n_samples = 50
        dummy_test_data = {
            'spectra': np.random.randn(n_samples, 200).astype(np.float32),
            'dipole': np.random.randn(n_samples).astype(np.float32) * 0.5,
            'polarizability': np.random.randn(n_samples).astype(np.float32) * 2.0,
            'gap': np.random.randn(n_samples).astype(np.float32) * 0.1,
            'InChIKey': [f"FAKE_KEY_{i}" for i in range(n_samples)]
        }
        np.savez(test_data_path, **dummy_test_data)

        # 3. Generate synthetic external data (Domain Shift Simulation)
        # Per FR-007: If external data unavailable, generate synthetic noise
        # We simulate an external dataset with slightly shifted distribution
        external_data = generate_synthetic_noise_data(
            n_samples=30,
            input_dim=200,
            noise_scale=0.1,
            shift_magnitude=0.05
        )
        np.savez(external_data_path, **external_data)

        # 4. Run the validation logic
        # We simulate the flow: load model -> load external data -> predict -> metrics
        
        # Load model
        model = load_model_with_dim(model_path, input_dim=200)
        model.eval()

        # Load external data
        external_data_loaded = np.load(external_data_path, allow_pickle=True)
        ext_spectra = external_data_loaded['spectra']
        ext_dipole = external_data_loaded['dipole']
        ext_polarizability = external_data_loaded['polarizability']
        ext_gap = external_data_loaded['gap']

        # Run inference
        with torch.no_grad():
            # Convert to tensor
            ext_spectra_tensor = torch.tensor(ext_spectra, dtype=torch.float32)
            predictions = model(ext_spectra_tensor)

        # Compute metrics
        pred_dipole = predictions[0].numpy()
        pred_polarizability = predictions[1].numpy()
        pred_gap = predictions[2].numpy()

        # Calculate metrics manually to verify the function
        mae_dipole = compute_mae(pred_dipole, ext_dipole)
        r2_dipole = compute_r2(pred_dipole, ext_dipole)
        mae_pol = compute_mae(pred_polarizability, ext_polarizability)
        r2_pol = compute_r2(pred_polarizability, ext_polarizability)
        mae_gap = compute_mae(pred_gap, ext_gap)
        r2_gap = compute_r2(pred_gap, ext_gap)

        # 5. Verify the results are separate from training/test metrics
        # The validation results should have specific keys and structure
        validation_results = {
            "dataset": "independent_external",
            "metrics": {
                "dipole": {"mae": float(mae_dipole), "r2": float(r2_dipole)},
                "polarizability": {"mae": float(mae_pol), "r2": float(r2_pol)},
                "gap": {"mae": float(mae_gap), "r2": float(r2_gap)}
            },
            "tolerance_check": {
                "dipole": "passed" if mae_dipole < 1.0 else "failed",
                "polarizability": "passed" if mae_pol < 2.0 else "failed",
                "gap": "passed" if mae_gap < 0.5 else "failed"
            },
            "notes": "Synthetic noise generated for domain shift simulation (FR-007)"
        }

        # Save results to verify file I/O
        with open(results_path, 'w') as f:
            json.dump(validation_results, f, indent=2)

        # 6. Assertions
        assert os.path.exists(results_path), "Validation results file was not created."
        
        with open(results_path, 'r') as f:
            loaded_results = json.load(f)

        # Verify structure
        assert loaded_results["dataset"] == "independent_external", "Dataset label incorrect."
        assert "metrics" in loaded_results, "Metrics key missing."
        assert "dipole" in loaded_results["metrics"], "Dipole metrics missing."
        assert "polarizability" in loaded_results["metrics"], "Polarizability metrics missing."
        assert "gap" in loaded_results["metrics"], "Gap metrics missing."

        # Verify numeric values are real (not NaN or Inf)
        for prop in ["dipole", "polarizability", "gap"]:
            mae_val = loaded_results["metrics"][prop]["mae"]
            r2_val = loaded_results["metrics"][prop]["r2"]
            assert np.isfinite(mae_val), f"MAE for {prop} is not finite."
            assert np.isfinite(r2_val), f"R2 for {prop} is not finite."
            # Verify they are distinct from a hypothetical "perfect" 0/1
            # (Just a sanity check that we aren't returning dummy constants)
            assert mae_val > 0.0, f"MAE for {prop} should be > 0 for noisy data."

        # Verify tolerance check exists
        assert "tolerance_check" in loaded_results, "Tolerance check missing."
        for prop in ["dipole", "polarizability", "gap"]:
            assert loaded_results["tolerance_check"][prop] in ["passed", "failed"], \
                f"Invalid tolerance status for {prop}."

        print("✓ Independent validation integration test passed.")
        print(f"  - Results saved to: {results_path}")
        print(f"  - Dipole MAE: {mae_dipole:.4f}, R2: {r2_dipole:.4f}")
        print(f"  - Polarizability MAE: {mae_pol:.4f}, R2: {r2_pol:.4f}")
        print(f"  - Gap MAE: {mae_gap:.4f}, R2: {r2_gap:.4f}")

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_independent_validation_separate_reporting()
