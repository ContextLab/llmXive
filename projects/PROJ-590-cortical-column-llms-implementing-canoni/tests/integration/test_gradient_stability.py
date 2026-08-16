import pytest
import json
import os
import tempfile
from pathlib import Path
import logging
import numpy as np
from typing import Dict, Any, List, Optional

from src.training.homeostasis import log_gradient_norms
from src.utils.statistics import load_gradient_norms

# Configure logging for the test module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestGradientLogging:
    """
    Test that the gradient logging mechanism correctly writes to disk
    and that the data can be reloaded for analysis.
    """

    def test_log_gradient_norms_writes_file(self, tmp_path):
        """Verify that log_gradient_norms creates the expected JSON file."""
        import torch
        import torch.nn as nn

        # Create a simple dummy model
        model = nn.Sequential(
            nn.Linear(10, 20),
            nn.ReLU(),
            nn.Linear(20, 5)
        )

        # Create a dummy optimizer
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        # Perform a dummy forward/backward pass to populate gradients
        x = torch.randn(4, 10)
        y = torch.randn(4, 5)
        output = model(x)
        loss = nn.MSELoss()(output, y)
        loss.backward()

        # Ensure the log directory exists
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gradient_norms.json"

        # Call the logging function
        result = log_gradient_norms(model, step=0, log_file=str(log_file))

        # Verify the file exists
        assert log_file.exists(), "Gradient norm log file was not created"

        # Verify the content is valid JSON and has the expected structure
        with open(log_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), "Log file content must be a list"
        assert len(data) > 0, "Log file should contain at least one entry"

        entry = data[0]
        assert "step" in entry, "Entry must contain 'step'"
        assert "norm" in entry, "Entry must contain 'norm'"
        assert isinstance(entry["norm"], float), "Norm must be a float"

        logger.info(f"Successfully logged gradient norm: {entry['norm']}")

    def test_log_gradient_norms_multiple_steps(self, tmp_path):
        """Verify that logging multiple steps appends correctly."""
        import torch
        import torch.nn as nn

        model = nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 5))
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gradient_norms.json"

        # Simulate 3 steps
        for step in range(3):
            x = torch.randn(4, 10)
            y = torch.randn(4, 5)
            output = model(x)
            loss = nn.MSELoss()(output, y)
            loss.backward()

            # Zero gradients before next step to avoid accumulation
            if step < 2:
                optimizer.zero_grad()

            log_gradient_norms(model, step=step, log_file=str(log_file))

        # Verify we have 3 entries
        with open(log_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 3, f"Expected 3 log entries, got {len(data)}"
        steps = [entry["step"] for entry in data]
        assert steps == [0, 1, 2], "Steps should be sequential"


class TestGradientStabilityComparison:
    """
    Test the statistical analysis of gradient stability.
    This class implements T031: Statistical test for gradient stability.
    """

    def _generate_dummy_gradient_log(self, file_path: Path, n_entries: int = 50, mean_val: float = 0.5, std_val: float = 0.1):
        """Helper to generate a realistic dummy gradient log for testing."""
        np.random.seed(42)
        norms = np.random.normal(loc=mean_val, scale=std_val, size=n_entries).tolist()
        data = [{"step": i, "norm": float(norm)} for i, norm in enumerate(norms)]
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def test_baseline_stability_analysis(self, tmp_path):
        """
        Reproduce the T031 logic:
        1. Ensure input log exists (simulate T011b output).
        2. Calculate mean, std, and stability metric.
        3. Write output JSON to data/results/gradient_stability_baseline.json.
        """
        from src.utils.statistics import load_gradient_norms

        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gradient_norms.json"

        # Generate dummy baseline data (simulating T011b output)
        self._generate_dummy_gradient_log(log_file, n_entries=100, mean_val=0.8, std_val=0.15)

        # Load the data
        norms = load_gradient_norms(str(log_file))
        assert len(norms) > 0, "No gradient norms loaded"

        # Perform stability analysis
        mean_norm = float(np.mean(norms))
        std_norm = float(np.std(norms))

        # Stability criterion: Coefficient of Variation (CV) < 0.5
        # If std is very small relative to mean, it's stable.
        # If mean is 0, we consider it unstable unless std is also 0.
        if mean_norm == 0.0:
            is_stable = std_norm == 0.0
        else:
            cv = std_norm / mean_norm
            is_stable = cv < 0.5

        result = {
            "mean_norm": round(mean_norm, 6),
            "std_norm": round(std_norm, 6),
            "is_stable": is_stable
        }

        # Write output
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        output_file = results_dir / "gradient_stability_baseline.json"

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        # Verify output
        assert output_file.exists(), "Output file not created"
        with open(output_file, 'r') as f:
            loaded_result = json.load(f)

        assert loaded_result["mean_norm"] == result["mean_norm"]
        assert loaded_result["std_norm"] == result["std_norm"]
        assert loaded_result["is_stable"] == result["is_stable"]

        logger.info(f"Stability analysis complete: {result}")

    def test_stability_threshold_boundary(self, tmp_path):
        """Test that the stability metric correctly identifies the boundary."""
        from src.utils.statistics import load_gradient_norms

        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gradient_norms.json"

        # Create data with CV exactly 0.5 (boundary)
        # mean=1.0, std=0.5 -> CV=0.5 -> is_stable=False (strict < 0.5)
        self._generate_dummy_gradient_log(log_file, n_entries=100, mean_val=1.0, std_val=0.5)

        norms = load_gradient_norms(str(log_file))
        mean_norm = float(np.mean(norms))
        std_norm = float(np.std(norms))

        if mean_norm == 0.0:
            is_stable = std_norm == 0.0
        else:
            cv = std_norm / mean_norm
            is_stable = cv < 0.5

        # With CV=0.5, it should be False (not stable)
        assert is_stable is False, "CV=0.5 should be considered unstable (strict threshold)"

        # Now create data with CV < 0.5
        self._generate_dummy_gradient_log(log_file, n_entries=100, mean_val=1.0, std_val=0.4)
        norms = load_gradient_norms(str(log_file))
        mean_norm = float(np.mean(norms))
        std_norm = float(np.std(norms))
        cv = std_norm / mean_norm
        is_stable = cv < 0.5

        assert is_stable is True, "CV=0.4 should be considered stable"