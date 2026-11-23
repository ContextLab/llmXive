"""
Unit tests for code/inference_pipeline.py.
"""
import tempfile
import torch
import pytest
import numpy as np

from code.inference_pipeline import InferencePipeline


class TestInferencePipeline:
    def test_init(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as tmp:
            torch.save({"state_dict": {}}, tmp.name)
            tmp_path = tmp.name

        try:
            pipeline = InferencePipeline(gfm_model_path=tmp_path)
            assert pipeline.gfm.is_loaded is True
            assert pipeline.solver.timeout == 30.0
        finally:
            import os
            os.unlink(tmp_path)

    def test_run_trial_success(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as tmp:
            torch.save({"state_dict": {}}, tmp.name)
            tmp_path = tmp.name

        try:
            pipeline = InferencePipeline(gfm_model_path=tmp_path)
            obs = np.random.randn(10)
            target = np.array([0.0, 0.0, 0.0])

            result = pipeline.run_trial(obs, target)
            assert "success" in result
            assert "latency_ms" in result
            assert result["latency_ms"] >= 0
        finally:
            import os
            os.unlink(tmp_path)