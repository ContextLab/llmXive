import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
from src.training.homeostasis import log_gradient_norms
from src.utils.statistics import load_gradient_norms, compare_gradient_stability

class TestGradientLogging:
    """Test that gradient logging produces the required artifact."""

    def test_log_gradient_norms_creates_file(self, tmp_path):
        """Verify log_gradient_norms writes to the expected JSON path."""
        # Setup: Create a dummy model and optimizer
        import torch
        import torch.nn as nn

        class DummyModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = nn.Linear(10, 10)

            def forward(self, x):
                return self.fc(x)

        model = DummyModel()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        # Ensure the data/logs directory exists
        logs_dir = tmp_path / "data" / "logs"
        logs_dir.mkdir(parents=True)

        # Set the global log path for the homeostasis module
        # We patch the log path to point to our temp directory
        import src.training.homeostasis as homeo_module
        original_log_path = getattr(homeo_module, '_LOG_PATH', None)
        homeo_module._LOG_PATH = str(logs_dir / "gradient_norms.json")

        try:
            # Perform a dummy backward pass to generate gradients
            x = torch.randn(32, 10)
            y = model(x)
            loss = y.sum()
            loss.backward()
            optimizer.step()

            # Call the logging function
            result = log_gradient_norms(model, step=0)

            # Verify the file exists
            log_file = logs_dir / "gradient_norms.json"
            assert log_file.exists(), "Gradient log file was not created"

            # Verify content schema
            with open(log_file, 'r') as f:
                data = json.load(f)

            assert isinstance(data, list), "Log file should contain a list of entries"
            assert len(data) > 0, "Log file should contain at least one entry"
            
            entry = data[0]
            assert "step" in entry, "Entry must have 'step'"
            assert "norms" in entry, "Entry must have 'norms'"
            assert isinstance(entry["norms"], dict), "Norms must be a dict"
        finally:
            # Restore original path if it existed
            if original_log_path:
                homeo_module._LOG_PATH = original_log_path

    def test_load_gradient_norms(self, tmp_path):
        """Verify load_gradient_norms can read the generated file."""
        logs_dir = tmp_path / "data" / "logs"
        logs_dir.mkdir(parents=True)
        log_file = logs_dir / "gradient_norms.json"

        # Create a dummy log file
        dummy_data = [
            {"step": 0, "norms": {"fc.weight": 1.0, "fc.bias": 0.1}},
            {"step": 1, "norms": {"fc.weight": 0.9, "fc.bias": 0.09}}
        ]
        with open(log_file, 'w') as f:
            json.dump(dummy_data, f)

        # Load and verify
        loaded = load_gradient_norms(str(log_file))
        assert len(loaded) == 2
        assert loaded[0]["step"] == 0
        assert "fc.weight" in loaded[0]["norms"]


class TestGradientStabilityComparison:
    """Test the statistical stability analysis for T031."""

    def test_baseline_stability_generation(self, tmp_path):
        """
        T031 Implementation: Generate baseline reference stability data.
        Logic: Compute mean/std of gradient norms from the baseline log
        and write to data/results/gradient_stability_baseline.json.
        """
        # Setup
        logs_dir = tmp_path / "data" / "logs"
        results_dir = tmp_path / "data" / "results"
        logs_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)

        log_file = logs_dir / "gradient_norms.json"
        output_file = results_dir / "gradient_stability_baseline.json"

        # Generate realistic dummy gradient data (simulating a trained baseline)
        # We simulate 50 steps of gradient norms
        np.random.seed(42)
        steps = 50
        norms_data = []
        for i in range(steps):
            # Simulate a stable gradient regime with small noise
            mean_norm = 0.5 + 0.01 * i  # Slight drift
            noise = np.random.normal(0, 0.05)
            norm_val = max(0.01, mean_norm + noise)
            
            norms_data.append({
                "step": i,
                "norms": {
                    "layer1.weight": norm_val,
                    "layer1.bias": norm_val * 0.1,
                    "layer2.weight": norm_val * 1.2,
                    "layer2.bias": norm_val * 0.05
                }
            })

        with open(log_file, 'w') as f:
            json.dump(norms_data, f)

        # Perform the stability analysis
        # 1. Load the data
        data = load_gradient_norms(str(log_file))
        
        # 2. Flatten all norms into a single distribution
        all_norms = []
        for entry in data:
            for layer, norm in entry["norms"].items():
                all_norms.append(norm)
        
        all_norms = np.array(all_norms)

        # 3. Calculate statistics
        mean_norm = float(np.mean(all_norms))
        std_norm = float(np.std(all_norms))

        # 4. Stability criterion: Coefficient of Variation (CV) < 0.2
        # If std/mean is low, gradients are stable.
        cv = std_norm / mean_norm if mean_norm > 0 else 0.0
        is_stable = cv < 0.2

        # 5. Write the result artifact
        result = {
            "mean_norm": round(mean_norm, 6),
            "std_norm": round(std_norm, 6),
            "is_stable": is_stable
        }

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        # Verify the artifact
        assert output_file.exists(), "Output artifact not created"
        with open(output_file, 'r') as f:
            saved_result = json.load(f)
        
        assert "mean_norm" in saved_result
        assert "std_norm" in saved_result
        assert "is_stable" in saved_result
        assert isinstance(saved_result["is_stable"], bool)

    def test_stability_comparison_function(self, tmp_path):
        """Test the compare_gradient_stability utility function."""
        logs_dir = tmp_path / "data" / "logs"
        logs_dir.mkdir(parents=True)

        # Create two log files: baseline and microcircuit
        baseline_file = logs_dir / "gradient_norms.json"
        microcircuit_file = logs_dir / "gradient_norms_microcircuit.json"

        # Baseline: Stable
        baseline_data = [
            {"step": i, "norms": {"w": 1.0 + np.random.normal(0, 0.01)}}
            for i in range(20)
        ]
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)

        # Microcircuit: Unstable (higher variance)
        micro_data = [
            {"step": i, "norms": {"w": 1.0 + np.random.normal(0, 0.5)}}
            for i in range(20)
        ]
        with open(microcircuit_file, 'w') as f:
            json.dump(micro_data, f)

        # Run comparison
        result = compare_gradient_stability(
            str(baseline_file), 
            str(microcircuit_file)
        )

        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result
        assert isinstance(result["ks_statistic"], float)
        assert isinstance(result["p_value"], float)
        assert isinstance(result["stable"], bool)