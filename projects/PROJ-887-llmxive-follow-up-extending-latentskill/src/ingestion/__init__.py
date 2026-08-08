"""
Ingestion package for llmXive.
Handles downloading and processing of LoRA weights.
"""

from src.ingestion.flatten_lora import (
    load_lora_weights_from_path,
    validate_dimensions,
    flatten_and_normalize,
    process_single_adapter,
    run_ingestion_pipeline
)

__all__ = [
    "load_lora_weights_from_path",
    "validate_dimensions",
    "flatten_and_normalize",
    "process_single_adapter",
    "run_ingestion_pipeline"
]