"""
Inference module for running LLM models on code snippets.
"""
from code.inference.runner import run_inference_pipeline, load_model

__all__ = [
    "run_inference_pipeline",
    "load_model",
]
