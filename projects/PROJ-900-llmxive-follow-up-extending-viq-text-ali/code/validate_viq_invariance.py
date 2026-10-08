"""
T006a: CRITICAL HYPOTHESIS CHECK
Validates that the frozen ViQ encoder can process 1024x1024 images without error.

This script loads the ViQ encoder from code/model.py, fetches a random sample
from the ImageNet-1K validation set (using streaming), and performs a forward pass.

Success: Script exits with code 0.
Failure: Script raises RuntimeError with a clear message if the forward pass fails.

Note: ChestX-ray14 is explicitly excluded per FR-003 and Decision Record 001.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import torch
from typing import Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from model import FrozenViQWrapper, get_model
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TARGET_RESOLUTION = 1024
IMAGENET_VAL_SPLIT = "validation"
VIQ_MODEL_ID = "viq-base-v"  # Placeholder ID as per spec

def load_viq_encoder() -> FrozenViQWrapper:
    """
    Loads the frozen ViQ encoder.
    
    Returns:
        FrozenViQWrapper: The loaded model.
        
    Raises:
        RuntimeError: If the model cannot be loaded or initialized.
    """
    logger.info(f"Initializing ViQ Encoder with ID: {VIQ_MODEL_ID}")
    try:
        # The get_model function from model.py handles the instantiation
        # We rely on the FrozenViQWrapper to handle the "frozen" state
        model = get_model(model_type="viq_encoder", model_id=VIQ_MODEL_ID)
        
        if not isinstance(model, FrozenViQWrapper):
            # Attempt to wrap if it returns a base model
            logger.warning("Returned model is not a FrozenViQWrapper, wrapping it.")
            model = FrozenViQWrapper(model)
        
        model.eval()
        logger.info("ViQ Encoder loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load ViQ Encoder: {e}")
        raise RuntimeError(f"CRITICAL: Could not load ViQ Encoder. The hypothesis of resolution invariance cannot be tested if the model is unavailable. Error: {e}")

def fetch_imagenet_sample() -> Tuple[torch.Tensor, str]:
    """
    Fetches a single 1024x1024 sample from the ImageNet-1K validation set.
    
    Uses the 'datasets' library as implemented in T005 (data_loader.py).
    Since data_loader.py is not fully importable for the dataset class directly
    without the full environment setup, we implement the fetch logic here
    using the standard 'datasets' library interface directly to ensure
    T006a can run independently as a hypothesis check.
    
    Returns:
        Tuple[torch.Tensor, str]: A tensor of shape (1, 3, 1024, 1024) and the image ID.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched or processed.
    """
    logger.info("Fetching sample from ImageNet-1K validation set (streaming)...")
    try:
        from datasets import load_dataset
        
        # Load ImageNet validation set in streaming mode
        # Note: 'imagenet' is the standard HuggingFace dataset name for ImageNet-1k
        ds = load_dataset("imagenet-1k", split="validation", streaming=True)
        
        # Get a random sample (or the first one if randomization is not needed for the check)
        # We iterate once to get a sample
        sample = next(iter(ds))
        
        if "image" not in sample:
            raise ValueError("Dataset sample does not contain 'image' key.")
        
        img = sample["image"]
        
        # Ensure image is in RGB mode
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize to target resolution (1024x1024)
        # We use PIL's resize for high quality, then convert to tensor
        img_resized = img.resize((TARGET_RESOLUTION, TARGET_RESOLUTION), resample=3) # BICUBIC
        
        # Convert to tensor: (H, W, C) -> (C, H, W)
        import torchvision.transforms as transforms
        transform = transforms.ToTensor()
        tensor_img = transform(img_resized)
        
        # Add batch dimension: (1, C, H, W)
        tensor_img = tensor_img.unsqueeze(0)
        
        logger.info(f"Successfully fetched ImageNet sample. Shape: {tensor_img.shape}")
        return tensor_img, str(sample.get("id", "unknown"))
        
    except Exception as e:
        logger.error(f"Failed to fetch ImageNet sample: {e}")
        raise RuntimeError(f"CRITICAL: Could not fetch real data from ImageNet-1K. "
                           f"The hypothesis check requires real data. "
                           f"Error: {e}")

def validate_viq_invariance(model: FrozenViQWrapper, image_tensor: torch.Tensor) -> bool:
    """
    Performs a forward pass of the ViQ encoder on the 1024x1024 image.
    
    Args:
        model: The FrozenViQWrapper model.
        image_tensor: The input image tensor (1, 3, 1024, 1024).
        
    Returns:
        bool: True if the forward pass completes without error.
        
    Raises:
        RuntimeError: If the forward pass fails (indicating lack of resolution invariance).
    """
    logger.info(f"Performing forward pass on {TARGET_RESOLUTION}x{TARGET_RESOLUTION} image...")
    try:
        with torch.no_grad():
            # The model expects a batch of images
            output = model(image_tensor)
        
        # If we get here, the model handled the resolution
        logger.info(f"Forward pass successful. Output shape: {output.shape if hasattr(output, 'shape') else type(output)}")
        return True
        
    except Exception as e:
        logger.error(f"Forward pass FAILED: {e}")
        raise RuntimeError(
            f"HYPOTHESIS FAILURE: The ViQ encoder FAILED to process a {TARGET_RESOLUTION}x{TARGET_RESOLUTION} image. "
            f"This indicates a lack of resolution invariance in the quantized representation. "
            f"Error details: {e}"
        )

def main():
    parser = argparse.ArgumentParser(description="Validate ViQ Resolution Invariance (T006a)")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to specific checkpoint (optional)")
    args = parser.parse_args()

    logger.info("Starting T006a: Critical Hypothesis Check")
    logger.info(f"Target Resolution: {TARGET_RESOLUTION}x{TARGET_RESOLUTION}")
    logger.info("Data Source: ImageNet-1K Validation (Streaming)")
    logger.info("Excluded: ChestX-ray14 (per FR-003)")

    try:
        # 1. Load Model
        model = load_viq_encoder()
        
        # 2. Fetch Real Data
        image_tensor, image_id = fetch_imagenet_sample()
        
        # 3. Validate Invariance
        success = validate_viq_invariance(model, image_tensor)
        
        if success:
            logger.info("T006a PASSED: ViQ Encoder successfully processed 1024x1024 input.")
            logger.info("Hypothesis of resolution invariance is supported for this sample.")
            sys.exit(0)
        else:
            # This should not be reached if validate_viq_invariance raises on failure
            logger.critical("T006a FAILED: Unexpected return value.")
            sys.exit(1)
            
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()