import torch
import json
import os
from typing import Optional, List, Dict, Any, Callable
from transformers import PreTrainedModel
from src.inference.hooks import KVCacheInterceptor
import numpy as np

class MSELogger:
    """
    Logs per-token Mean Squared Error (MSE) reconstruction errors to JSONL files.
    Implements FR-009 (raw data) and FR-010 (cumulative stats).
    """
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = output_dir
        self.raw_log_path = os.path.join(output_dir, "cumulative_mse_raw.jsonl")
        self.summary_log_path = os.path.join(output_dir, "results.jsonl")
        
        # Ensure directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # In-memory buffers for the current generation
        self.current_generation_mse: List[Dict[str, Any]] = []
        self.current_token_position = 0
        self.quantizer_type = "unknown"

    def set_quantizer_type(self, q_type: str):
        self.quantizer_type = q_type

    def reset_generation(self):
        """Reset buffers for a new generation sequence."""
        self.current_generation_mse = []
        self.current_token_position = 0

    def log_mse(self, mse: float):
        """
        Log a single MSE value for the current token position.
        Format matches contracts/dataset_schema.schema.yaml:
        {"token_position": int, "mse": float, "quantizer_type": str}
        """
        entry = {
            "token_position": self.current_token_position,
            "mse": float(mse),
            "quantizer_type": self.quantizer_type
        }
        self.current_generation_mse.append(entry)
        self.current_token_position += 1

    def finalize_generation(self):
        """
        Write the accumulated MSE data for the current generation to disk.
        Appends to the raw log file immediately to ensure durability.
        """
        if not self.current_generation_mse:
            return

        # Write raw data points
        with open(self.raw_log_path, 'a', encoding='utf-8') as f:
            for entry in self.current_generation_mse:
                f.write(json.dumps(entry) + '\n')
        
        # Clear buffer
        self.current_generation_mse = []

class MSEInterceptor(KVCacheInterceptor):
    """
    Extends KVCacheInterceptor to calculate and log MSE between
    original and quantized KV caches at each step.
    """
    def __init__(self, logger: MSELogger):
        super().__init__()
        self.logger = logger

    def intercept(self, model, layer_idx, original_k: torch.Tensor, 
                original_v: torch.Tensor, quantized_k: torch.Tensor, 
                quantized_v: torch.Tensor):
        """
        Called during the forward pass when KV caches are intercepted.
        Calculates MSE and logs it.
        """
        # Ensure tensors are on CPU and float for MSE calculation
        orig_k = original_k.detach().cpu().float()
        orig_v = original_v.detach().cpu().float()
        q_k = quantized_k.detach().cpu().float()
        q_v = quantized_v.detach().cpu().float()

        # Calculate MSE for K and V separately, then average
        mse_k = torch.mean((orig_k - q_k) ** 2).item()
        mse_v = torch.mean((orig_v - q_v) ** 2).item()
        total_mse = (mse_k + mse_v) / 2.0

        # Log the value
        self.logger.log_mse(total_mse)

def create_mse_interceptor(logger: MSELogger) -> MSEInterceptor:
    """Factory function to create an MSEInterceptor."""
    return MSEInterceptor(logger)

# Re-export for compatibility with existing imports
__all__ = ['MSELogger', 'MSEInterceptor', 'create_mse_interceptor']