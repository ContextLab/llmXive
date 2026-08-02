"""
Integration test for model loading (T010).
Verifies that student models saved by T014/T015 load successfully on CPU
without CUDA errors and that their metadata matches expectations.

Prerequisites:
- T011 (Teacher model loader) must be implemented to ensure model infrastructure is ready.
- T014/T015 (Training/Checkpointing) must have run to produce artifacts in data/processed/.

This test:
1. Discovers all student model checkpoints in data/processed/ matching the expected naming pattern.
2. Loads each model's metadata JSON.
3. Validates metadata against the StudentModelMetadata schema.
4. Attempts to load the model state dict into a StudentModel instance on CPU.
5. Verifies that no CUDA tensors are present and that the model is in eval mode.
6. Checks that the model can perform a dummy forward pass (inference) without error.
"""
import os
import json
import glob
import pytest
import torch
from pathlib import Path

# Project imports
from config import PathConfig, get_resource_limits
from models.student import StudentModel, StudentModelMetadata
from utils.logger import get_logger, ModelLoadError

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
CHECKPOINT_PATTERN = "*.pt"
METADATA_PATTERN = "*.json"

# Expected metadata keys based on StudentModelMetadata dataclass
EXPECTED_METADATA_KEYS = {
    "model_id",
    "bit_width",
    "param_count",
    "pruning_ratio",
    "compression_method",
    "training_loss_final",
    "created_at",
    "config_hash"
}


def _discover_checkpoints():
    """
    Discover all student model checkpoints and their corresponding metadata files.
    Returns a list of tuples: (checkpoint_path, metadata_path)
    """
    if not PROCESSED_DATA_DIR.exists():
        logger.warning(f"Processed data directory not found: {PROCESSED_DATA_DIR}")
        return []

    checkpoints = list(PROCESSED_DATA_DIR.glob(CHECKPOINT_PATTERN))
    metadata_files = list(PROCESSED_DATA_DIR.glob(METADATA_PATTERN))

    # Filter metadata files to only those that correspond to a checkpoint
    # We assume metadata files are named <model_id>_metadata.json
    valid_pairs = []
    for ckpt in checkpoints:
        model_id = ckpt.stem  # e.g., "student_int8_0.1"
        # Look for matching metadata
        matching_meta = [
            m for m in metadata_files
            if m.stem.startswith(f"{model_id}_") and m.suffix == ".json"
        ]

        if matching_meta:
            valid_pairs.append((ckpt, matching_meta[0]))
        else:
            logger.warning(f"No metadata found for checkpoint: {ckpt}")

    return valid_pairs


def _load_metadata(metadata_path: Path) -> StudentModelMetadata:
    """
    Load and validate metadata from a JSON file.
    Raises ModelLoadError if validation fails.
    """
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate required keys
        missing_keys = EXPECTED_METADATA_KEYS - set(data.keys())
        if missing_keys:
            raise ModelLoadError(
                f"Metadata file {metadata_path} is missing required keys: {missing_keys}"
            )

        # Create StudentModelMetadata instance
        metadata = StudentModelMetadata(
            model_id=data["model_id"],
            bit_width=data["bit_width"],
            param_count=data["param_count"],
            pruning_ratio=data["pruning_ratio"],
            compression_method=data["compression_method"],
            training_loss_final=data["training_loss_final"],
            created_at=data["created_at"],
            config_hash=data["config_hash"]
        )

        return metadata

    except json.JSONDecodeError as e:
        raise ModelLoadError(f"Failed to parse JSON metadata {metadata_path}: {e}")
    except Exception as e:
        raise ModelLoadError(f"Error loading metadata {metadata_path}: {e}")


def _load_model(checkpoint_path: Path, metadata: StudentModelMetadata) -> StudentModel:
    """
    Load the model state dict and reconstruct the StudentModel.
    Ensures CPU-only loading and eval mode.
    """
    try:
        # Initialize a fresh StudentModel based on metadata
        # Note: The StudentModel class should have a method to reconstruct from metadata
        # or we assume the architecture is fixed and we just load state dict.
        # For this test, we assume StudentModel can be instantiated with default config
        # and then load_state_dict is called.
        
        # Attempt to load on CPU explicitly
        state_dict = torch.load(
            checkpoint_path,
            map_location=torch.device('cpu'),
            weights_only=True
        )

        # Create model instance (assuming default config for now)
        # In a real scenario, we might need to pass specific config based on metadata
        model = StudentModel() 
        
        # Load state
        model.load_state_dict(state_dict)
        
        # Ensure eval mode
        model.eval()
        
        # Verify no CUDA tensors
        for param in model.parameters():
            if param.is_cuda:
                raise ModelLoadError(
                    f"Model loaded with CUDA tensors: {param.device}"
                )

        return model

    except FileNotFoundError:
        raise ModelLoadError(f"Checkpoint file not found: {checkpoint_path}")
    except Exception as e:
        raise ModelLoadError(f"Failed to load model from {checkpoint_path}: {e}")


def _run_dummy_inference(model: StudentModel, metadata: StudentModelMetadata):
    """
    Perform a dummy forward pass to ensure the model is functional.
    Uses a small random input tensor.
    """
    try:
        # Create dummy input: (batch_size, sequence_length) or (batch_size, 1, seq_len)
        # Assuming audio model expects 1D audio signal
        batch_size = 2
        seq_len = 16000  # 1 second at 16kHz
        dummy_input = torch.randn(batch_size, seq_len)

        with torch.no_grad():
            output = model(dummy_input)

        # Verify output shape is reasonable (not empty, not NaN)
        assert output is not None, "Model output is None"
        assert not torch.isnan(output).any(), "Model output contains NaN values"
        assert not torch.isinf(output).any(), "Model output contains Inf values"
        
        logger.info(
            f"Dummy inference successful for {metadata.model_id}. "
            f"Output shape: {output.shape}"
        )

    except Exception as e:
        raise ModelLoadError(f"Dummy inference failed for {metadata.model_id}: {e}")


@pytest.mark.integration
def test_student_model_loading():
    """
    Integration test: Load all student models and verify they work on CPU.
    """
    pairs = _discover_checkpoints()
    
    if not pairs:
        pytest.skip(
            "No student model checkpoints found in data/processed/. "
            "Ensure T014/T015 have been executed to generate artifacts."
        )

    logger.info(f"Found {len(pairs)} student model checkpoints to test.")

    for ckpt_path, meta_path in pairs:
        logger.info(f"Testing model: {ckpt_path.name}")

        # 1. Load metadata
        metadata = _load_metadata(meta_path)
        logger.info(f"  Metadata loaded: {metadata.model_id}, bit_width={metadata.bit_width}")

        # 2. Load model
        model = _load_model(ckpt_path, metadata)
        logger.info(f"  Model loaded successfully on CPU")

        # 3. Run dummy inference
        _run_dummy_inference(model, metadata)
        logger.info(f"  Inference test passed")

        logger.info(f"  ✓ {metadata.model_id} passed all checks")

    logger.info("All student model loading tests passed.")


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])
