"""Integration tests for gradient stability analysis."""

import pytest
import json
import os
import tempfile
from pathlib import Path
from src.training.homeostasis import log_gradient_norms
from src.utils.statistics import compare_gradient_stability, load_gradient_norms

class TestGradientLogging:
    def test_gradient_norms_logging(self):
        """Test that gradient norms are logged correctly."""
        import torch
        import torch.nn as nn

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "gradient_norms.json")

            # Create a simple model
            model = nn.Linear(10, 10)
            x = torch.randn(5, 10)
            y = model(x)
            loss = y.sum()
            loss.backward()

            # Log gradients
            log_gradient_norms(model, step=1, output_path=log_path)

            # Verify file exists and has content
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                data = json.load(f)

            assert "step" in data
            assert "norm" in data

    def test_gradient_norms_accumulation(self):
        """Test that gradient norms accumulate over multiple steps."""
        import torch
        import torch.nn as nn

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "gradient_norms.json")

            model = nn.Linear(10, 10)

            for step in range(3):
                x = torch.randn(5, 10)
                y = model(x)
                loss = y.sum()
                loss.backward()
                log_gradient_norms(model, step=step, output_path=log_path)

            with open(log_path, 'r') as f:
                data = json.load(f)

            assert len(data) == 3

class TestGradientStabilityComparison:
    def test_stability_comparison(self):
        """Test gradient stability comparison between two runs."""
        import torch
        import torch.nn as nn

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path_1 = os.path.join(tmpdir, "gradient_norms_1.json")
            log_path_2 = os.path.join(tmpdir, "gradient_norms_2.json")

            # Generate first set of gradient norms
            model1 = nn.Linear(10, 10)
            for step in range(5):
                x = torch.randn(5, 10)
                y = model1(x)
                loss = y.sum()
                loss.backward()
                log_gradient_norms(model1, step=step, output_path=log_path_1)

            # Generate second set of gradient norms
            model2 = nn.Linear(10, 10)
            for step in range(5):
                x = torch.randn(5, 10)
                y = model2(x)
                loss = y.sum()
                loss.backward()
                log_gradient_norms(model2, step=step, output_path=log_path_2)

            # Compare stability
            result = compare_gradient_stability(log_path_1, log_path_2)

            assert "ks_statistic" in result
            assert "p_value" in result
            assert "stable" in result
            assert isinstance(result["ks_statistic"], float)
            assert isinstance(result["p_value"], float)
            assert isinstance(result["stable"], bool)