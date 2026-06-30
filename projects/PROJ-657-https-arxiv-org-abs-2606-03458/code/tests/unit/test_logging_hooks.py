import pytest
import torch
import json
import os
import tempfile
from src.inference.logging_hooks import MSELogger, MSEInterceptor, create_mse_interceptor

def test_mse_logger_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MSELogger(output_dir=tmpdir, quantizer_type="test")
        
        # Simulate a step
        orig_cache = {
            0: {
                'key': torch.randn(2, 4, 8, 16),
                'value': torch.randn(2, 4, 8, 16)
            }
        }
        quant_cache = {
            0: {
                'key': torch.randn(2, 4, 8, 16),
                'value': torch.randn(2, 4, 8, 16)
            }
        }
        
        logger.log_step(orig_cache, quant_cache)
        logger.finalize()
        
        assert os.path.exists(os.path.join(tmpdir, "results_test.jsonl"))
        assert os.path.exists(os.path.join(tmpdir, "cumulative_mse_raw.jsonl"))

def test_mse_logger_raw_data_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MSELogger(output_dir=tmpdir, quantizer_type="kvarn")
        
        orig_cache = {
            0: {
                'key': torch.tensor([[[[1.0, 2.0]]]]),
                'value': torch.tensor([[[[3.0, 4.0]]]])
            }
        }
        quant_cache = {
            0: {
                'key': torch.tensor([[[[1.1, 2.1]]]]),
                'value': torch.tensor([[[[3.1, 4.1]]]])
            }
        }
        
        logger.log_step(orig_cache, quant_cache)
        logger.finalize()
        
        raw_path = os.path.join(tmpdir, "cumulative_mse_raw.jsonl")
        with open(raw_path, 'r') as f:
            line = f.readline()
            data = json.loads(line)
            
            assert "token_position" in data
            assert "mse" in data
            assert "quantizer_type" in data
            assert data["quantizer_type"] == "kvarn"
            assert isinstance(data["mse"], float)

def test_mse_logger_finalizes_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MSELogger(output_dir=tmpdir, quantizer_type="uniform")
        
        orig_cache = {
            0: {
                'key': torch.ones(1, 1, 1, 1),
                'value': torch.ones(1, 1, 1, 1)
            }
        }
        quant_cache = {
            0: {
                'key': torch.ones(1, 1, 1, 1) * 2,
                'value': torch.ones(1, 1, 1, 1) * 2
            }
        }
        
        logger.log_step(orig_cache, quant_cache)
        logger.log_step(orig_cache, quant_cache) # Second step
        logger.finalize()
        
        res_path = os.path.join(tmpdir, "results_uniform.jsonl")
        with open(res_path, 'r') as f:
            line = f.readline()
            data = json.loads(line)
            
            assert "mean_mse" in data
            assert "total_tokens" in data
            assert data["total_tokens"] == 2