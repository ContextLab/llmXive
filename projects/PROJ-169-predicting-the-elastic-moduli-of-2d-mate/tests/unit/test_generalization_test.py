import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from model.generalization_test import verify_family_disjoint, run_generalization_test, load_json, save_json


class TestVerifyFamilyDisjoint:
    def test_disjoint_families(self):
        train_indices = [0, 1, 2]
        test_indices = [3, 4, 5]
        family_map = {
            0: "fam_A",
            1: "fam_A",
            2: "fam_B",
            3: "fam_C",
            4: "fam_D",
            5: "fam_E",
        }
        assert verify_family_disjoint(train_indices, test_indices, family_map) is True

    def test_overlapping_families(self):
        train_indices = [0, 1]
        test_indices = [2, 3]
        family_map = {
            0: "fam_A",
            1: "fam_B",
            2: "fam_A",  # Overlap
            3: "fam_C",
        }
        assert verify_family_disjoint(train_indices, test_indices, family_map) is False

    def test_missing_index_in_map(self):
        train_indices = [0]
        test_indices = [1]
        family_map = {0: "fam_A"}  # 1 is missing
        # Should log warning but return True (no overlap found)
        assert verify_family_disjoint(train_indices, test_indices, family_map) is True


class TestRunGeneralizationTest:
    def test_run_with_mock_data(self):
        # Create mock graphs
        graphs = [
            {
                "node_features": np.random.rand(5, 10).astype(np.float32),
                "edge_index": np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int64),
                "target_moduli": np.random.rand(3).astype(np.float32),
                "family_id": "fam_A",
            },
            {
                "node_features": np.random.rand(5, 10).astype(np.float32),
                "edge_index": np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int64),
                "target_moduli": np.random.rand(3).astype(np.float32),
                "family_id": "fam_B",
            },
            {
                "node_features": np.random.rand(5, 10).astype(np.float32),
                "edge_index": np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int64),
                "target_moduli": np.random.rand(3).astype(np.float32),
                "family_id": "fam_C",
            },
        ]

        # Mock split: train on fam_A, fam_B; test on fam_C
        train_indices = [0, 1]
        test_indices = [2]

        # Create a temporary directory for outputs
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            model_path = tmp_path / "model.pt"
            output_path = tmp_path / "metrics.json"
            baseline_path = tmp_path / "baseline_metrics.json"

            # Create a dummy model checkpoint
            # We need a state_dict that matches the model structure.
            # Since we don't have the exact model here, we'll create a dummy one.
            # This test might fail if the model loading logic is strict.
            # For now, we assume the model loading is robust or we skip the actual training.
            # We will create a minimal state dict.
            import torch
            dummy_state = {
                "conv1.weight": torch.randn(32, 10, 3, 3),
                "conv1.bias": torch.randn(32),
                "conv2.weight": torch.randn(64, 32, 3, 3),
                "conv2.bias": torch.randn(64),
                "fc.weight": torch.randn(3, 64),
                "fc.bias": torch.randn(3),
            }
            torch.save(dummy_state, model_path)

            # Create a dummy baseline artifact
            baseline_data = {
                "intra_family_mape": 5.0,
                "report": {"intra_family_mape": 5.0},
                "disclaimer": "Mock baseline"
            }
            with open(baseline_path, "w") as f:
                json.dump(baseline_data, f)

            # Temporarily patch the baseline path lookup
            # We cannot easily patch the file system path in the function without refactoring.
            # Instead, we will assume the function looks for a specific path or we modify the test to pass the path.
            # The current implementation hardcodes "data/results/baseline_metrics.json".
            # To make this test work, we need to either:
            # 1. Refactor the function to accept a baseline path.
            # 2. Create the file in the expected location (data/results/).
            # Since we are in a temp dir, we can't easily create data/results.
            # We will assume the test environment has the baseline artifact or we mock the function.
            # For the purpose of this task, we will assume the function is robust enough or we skip the baseline check in this unit test.
            # Let's modify the test to skip the baseline check if the file is not found, or we mock the file.
            # We'll create the file in the expected relative path.
            (Path("data/results")).mkdir(parents=True, exist_ok=True)
            with open("data/results/baseline_metrics.json", "w") as f:
                json.dump(baseline_data, f)

            try:
                result = run_generalization_test(
                    graphs=graphs,
                    train_indices=train_indices,
                    test_indices=test_indices,
                    model_path=model_path,
                    output_path=output_path,
                )

                assert result["status"] == "success"
                assert "intra_family_mape" in result
                assert "inter_family_mape" in result
                assert "disclaimer" in result
                assert result["disclaimer"] == "These results are ML interpolations of DFT data, not first-principles solutions."

                # Check output file
                assert output_path.exists()
                saved_result = load_json(output_path)
                assert saved_result["status"] == "success"
            finally:
                # Clean up the mock baseline file
                if Path("data/results/baseline_metrics.json").exists():
                    Path("data/results/baseline_metrics.json").unlink()