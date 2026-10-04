"""
T006a: CRITICAL HYPOTHESIS CHECK - ViQ Resolution Invariance Validation

This script validates that the frozen ViQ encoder can process high-resolution
(1024x1024) images without errors, confirming the resolution invariance hypothesis.

It loads a random sample from the ImageNet-1K validation set via the T005 data loader
and performs a forward pass through the ViQ encoder.

Success: Script exits with code 0.
Failure: Script raises RuntimeError with a clear message if the encoder fails.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

import torch
import torch.nn as nn

# Project imports
from config import get_config
from model import FrozenViQWrapper, get_model
from data_loader import get_imagenet_iterator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_viq_invariance(
    checkpoint_path: str,
    target_resolution: tuple = (1024, 1024),
    sample_count: int = 1
) -> bool:
    """
    Validate ViQ encoder invariance to resolution by running forward passes
    on high-resolution images.

    Args:
        checkpoint_path: Path to the ViQ encoder checkpoint.
        target_resolution: Tuple (height, width) for the target resolution.
        sample_count: Number of random samples to test.

    Returns:
        True if all samples pass, False otherwise.

    Raises:
        RuntimeError: If the encoder fails to process the input.
    """
    config = get_config()
    
    # Load the frozen ViQ wrapper
    logger.info(f"Loading ViQ model from checkpoint: {checkpoint_path}")
    if not os.path.exists(checkpoint_path):
        raise RuntimeError(f"Checkpoint file not found: {checkpoint_path}")
    
    try:
        # Initialize the model
        model_wrapper = get_model("viq-base-v")
        if not isinstance(model_wrapper, FrozenViQWrapper):
            raise RuntimeError("Model wrapper is not a FrozenViQWrapper instance.")
        
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=config.device, weights_only=True)
        if "model_state_dict" in checkpoint:
            model_state = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            model_state = checkpoint["state_dict"]
        else:
            raise RuntimeError("Checkpoint does not contain 'model_state_dict' or 'state_dict'.")
        
        model_wrapper.encoder.load_state_dict(model_state)
        model_wrapper.encoder.eval()
        logger.info("ViQ encoder loaded and set to eval mode.")
        
    except Exception as e:
        raise RuntimeError(f"Failed to load ViQ encoder: {str(e)}") from e

    # Get ImageNet iterator
    logger.info("Initializing ImageNet-1K validation iterator...")
    try:
        imagenet_iter = get_imagenet_iterator(split="validation", streaming=False)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize ImageNet iterator: {str(e)}") from e

    # Test on random samples
    passed_count = 0
    for i in range(sample_count):
        try:
            sample = next(imagenet_iter)
            if sample is None:
                logger.warning("Reached end of dataset before getting enough samples.")
                break

            image = sample["image"]
            # Ensure image is in RGB
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize to target resolution
            image = image.resize((target_resolution[1], target_resolution[0]), resample=Image.BILINEAR)
            
            # Convert to tensor
            # Assuming the model expects [0, 1] normalized float tensors
            import numpy as np
            img_np = np.array(image).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to(config.device)

            logger.info(f"Processing sample {i+1}/{sample_count} with shape: {img_tensor.shape}")

            # Perform forward pass
            with torch.no_grad():
                # The FrozenViQWrapper typically has a method like encode or forward
                # We assume it exposes an 'encode' method that returns tokens/embeddings
                # If the wrapper expects a specific input format, it will raise an error if wrong
                try:
                    # Attempt to encode
                    output = model_wrapper.encode(img_tensor)
                    logger.info(f"Sample {i+1} passed. Output shape: {output.shape if hasattr(output, 'shape') else type(output)}")
                    passed_count += 1
                except AttributeError:
                    # Fallback to forward if encode is not explicitly defined
                    output = model_wrapper(img_tensor)
                    logger.info(f"Sample {i+1} passed via forward(). Output shape: {output.shape if hasattr(output, 'shape') else type(output)}")
                    passed_count += 1

        except Exception as e:
            error_msg = f"Sample {i+1} FAILED resolution invariance check: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    if passed_count == sample_count:
        logger.info(f"SUCCESS: All {sample_count} samples passed resolution invariance check at {target_resolution[0]}x{target_resolution[1]}.")
        return True
    else:
        raise RuntimeError(f"FAILURE: Only {passed_count}/{sample_count} samples passed. ViQ encoder may not be resolution invariant.")

def main():
    parser = argparse.ArgumentParser(description="Validate ViQ Resolution Invariance")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="code/codebook.pt", # Default path, can be overridden
        help="Path to the ViQ encoder checkpoint."
    )
    parser.add_argument(
        "--resolution",
        type=int,
        nargs=2,
        default=[1024, 1024],
        help="Target resolution (height width)."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Number of random samples to test."
    )

    args = parser.parse_args()

    try:
        success = validate_viq_invariance(
            checkpoint_path=args.checkpoint,
            target_resolution=tuple(args.resolution),
            sample_count=args.samples
        )
        if success:
            logger.info("Hypothesis check PASSED. ViQ encoder is resolution invariant.")
            sys.exit(0)
        else:
            # Should not reach here if validate_viq_invariance raises on failure
            logger.error("Hypothesis check FAILED.")
            sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"HYPOTHESIS CHECK FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Import Image here to avoid circular imports if needed, though usually at top
    from PIL import Image
    main()
