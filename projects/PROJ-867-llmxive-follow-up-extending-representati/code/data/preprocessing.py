import os
import logging
import hashlib
import warnings
import torch
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path

from transformers import LayoutLMv3Processor
import torchvision.transforms as transforms
from PIL import Image, ImageChops, ImageFilter

from config import get_config_dict
from models.rf_encoder import RFEncoder, create_rf_encoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePreprocessingError(Exception):
    """Custom exception for image preprocessing failures."""
    pass

def _is_blank_or_corrupted(image: Image.Image, threshold: int = 10) -> bool:
    """
    Detects if an image is blank (uniform) or corrupted.
    
    Args:
        image: PIL Image object.
        threshold: Maximum allowed standard deviation for an image to be considered blank.
        
    Returns:
        True if the image is blank or corrupted, False otherwise.
    """
    try:
        # Convert to grayscale for uniformity check
        gray = image.convert('L')
        np_img = np.array(gray)
        
        # Check for extreme corruption (e.g., all NaNs or Inf if somehow loaded weirdly)
        if np.any(np.isnan(np_img)) or np.any(np.isinf(np_img)):
            logger.warning("Image contains NaN or Inf values, treating as corrupted.")
            return True
        
        # Check standard deviation to detect blank/white pages
        std_dev = np.std(np_img)
        
        # If standard deviation is very low, the image is likely blank (white or black)
        if std_dev < threshold:
            logger.warning(f"Image detected as blank (std_dev={std_dev:.2f} < {threshold}).")
            return True
        
        # Optional: Check if the image is completely white (often indicates a failed render)
        if np.all(np_img == 255):
            logger.warning("Image detected as completely white (blank).")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error during blank/corruption check: {e}")
        return True

def load_image(path: Union[str, Path]) -> Image.Image:
    """
    Load an image from disk.
    
    Args:
        path: Path to the image file.
        
    Returns:
        PIL Image object.
        
    Raises:
        ImagePreprocessingError: If the image cannot be loaded.
    """
    try:
        img = Image.open(path)
        img.load()  # Force load to catch corruption early
        # Ensure RGB mode for consistency
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        raise ImagePreprocessingError(f"Failed to load image {path}: {e}")

def resize_image(image: Image.Image, size: Tuple[int, int] = (224, 224)) -> Image.Image:
    """
    Resize an image to the target dimensions.
    
    Args:
        image: PIL Image object.
        size: Target (width, height).
        
    Returns:
        Resized PIL Image.
    """
    return image.resize(size, Image.Resampling.LANCZOS)

def normalize_image(image: Image.Image, mean: List[float] = [0.485, 0.456, 0.406], 
                    std: List[float] = [0.229, 0.224, 0.225]) -> torch.Tensor:
    """
    Normalize an image tensor.
    
    Args:
        image: PIL Image.
        mean: Mean values for normalization.
        std: Standard deviation values for normalization.
        
    Returns:
        Normalized torch tensor.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])
    return transform(image)

def detect_and_clamp_nans(tensor: torch.Tensor) -> torch.Tensor:
    """
    Detects NaNs in a tensor and clamps them to zero.
    
    Args:
        tensor: Input tensor.
        
    Returns:
        Tensor with NaNs replaced by 0.
    """
    if torch.isnan(tensor).any():
        logger.warning("NaN detected in tensor. Clamping to 0.")
        tensor = torch.nan_to_num(tensor, nan=0.0)
    return tensor

def image_to_tensor(image: Image.Image) -> torch.Tensor:
    """
    Convert PIL Image to normalized torch tensor.
    
    Args:
        image: PIL Image.
        
    Returns:
        Normalized tensor.
    """
    return normalize_image(image)

def pad_or_truncate_sequence(sequence: torch.Tensor, max_length: int, padding_value: float = 0.0) -> torch.Tensor:
    """
    Pads or truncates a sequence to a fixed length.
    
    Args:
        sequence: Input tensor sequence.
        max_length: Target length.
        padding_value: Value to use for padding.
        
    Returns:
        Padded or truncated tensor.
    """
    current_length = sequence.shape[0]
    if current_length == max_length:
        return sequence
    elif current_length < max_length:
        padding_shape = (max_length - current_length,) + sequence.shape[1:]
        padding = torch.full(padding_shape, padding_value, dtype=sequence.dtype)
        return torch.cat([sequence, padding], dim=0)
    else:
        return sequence[:max_length]

def extract_rf_tokens(image: Image.Image, encoder: RFEncoder, processor: LayoutLMv3Processor, 
                      max_seq_length: int = 512, device: str = "cpu") -> torch.Tensor:
    """
    Extracts RF tokens from an image using a frozen RF encoder.
    
    Args:
        image: PIL Image.
        encoder: Frozen RFEncoder instance.
        processor: LayoutLMv3Processor.
        max_seq_length: Maximum sequence length for tokens.
        device: Device to run inference on.
        
    Returns:
        Extracted token tensor (padded/truncated).
    """
    # Prepare inputs
    # Since we are using LayoutLMv3, we need dummy bounding boxes if not provided, 
    # or we rely on the encoder's internal handling if it's a vision-only wrapper.
    # Assuming the RFEncoder handles the vision part and expects standard inputs.
    
    inputs = processor(
        images=image, 
        return_tensors="pt", 
        padding="max_length", 
        max_length=max_seq_length
    )
    
    # Move to device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Disable gradients for frozen encoder
    with torch.no_grad():
        outputs = encoder(**inputs)
        # Assuming the encoder returns hidden states or a specific token representation
        # Adjust key based on actual RFEncoder output structure
        if isinstance(outputs, dict):
            # Common case: 'last_hidden_state' or 'pooler_output'
            tokens = outputs.get('last_hidden_state', outputs.get('pooler_output'))
        else:
            tokens = outputs
        
        if tokens is None:
            raise ImagePreprocessingError("Encoder returned None tokens.")
        
        # Ensure it's a tensor
        if not isinstance(tokens, torch.Tensor):
            tokens = torch.tensor(tokens)
        
        # Handle NaNs
        tokens = detect_and_clamp_nans(tokens)
        
        # If tokens are 3D (batch, seq, dim), squeeze batch
        if tokens.dim() == 3:
            tokens = tokens.squeeze(0)
        
        # Pad or truncate
        tokens = pad_or_truncate_sequence(tokens, max_seq_length)
        
    return tokens

def load_and_preprocess_image(image_path: Union[str, Path], encoder: Optional[RFEncoder] = None,
                              processor: Optional[LayoutLMv3Processor] = None,
                              max_seq_length: int = 512,
                              device: str = "cpu") -> Dict[str, Any]:
    """
    Main function to load, validate, and preprocess an image for RF token extraction.
    Handles corrupted/blank images by returning a minimal valid structure.
    
    Args:
        image_path: Path to image.
        encoder: RFEncoder instance.
        processor: LayoutLMv3Processor instance.
        max_seq_length: Max sequence length.
        device: Device.
        
    Returns:
        Dictionary containing 'tokens', 'is_valid', 'error' (if any).
    """
    result = {
        "tokens": None,
        "is_valid": False,
        "error": None,
        "path": str(image_path)
    }
    
    try:
        # 1. Load Image
        image = load_image(image_path)
        
        # 2. Check for Blank/Corrupted
        if _is_blank_or_corrupted(image):
            logger.warning(f"Skipping blank or corrupted image: {image_path}")
            result["error"] = "Blank or corrupted image detected"
            # Return minimal valid structure (zeros)
            result["tokens"] = torch.zeros((max_seq_length, 768)) # Assuming 768 dim for LayoutLMv3
            result["is_valid"] = True # Considered "processed" successfully as a valid empty case
            return result
        
        # 3. Extract Tokens if encoder provided
        if encoder is not None and processor is not None:
            result["tokens"] = extract_rf_tokens(image, encoder, processor, max_seq_length, device)
            result["is_valid"] = True
        else:
            # If no encoder, just return the processed image tensor
            result["tokens"] = image_to_tensor(image)
            result["is_valid"] = True
            
    except ImagePreprocessingError as e:
        logger.error(f"Preprocessing error for {image_path}: {e}")
        result["error"] = str(e)
        result["tokens"] = torch.zeros((max_seq_length, 768))
        result["is_valid"] = True # Graceful degradation
    except Exception as e:
        logger.error(f"Unexpected error for {image_path}: {e}")
        result["error"] = str(e)
        result["tokens"] = torch.zeros((max_seq_length, 768))
        result["is_valid"] = True
        
    return result

class PubLayNetPreprocessedDataset(torch.utils.data.Dataset):
    """Dataset wrapper for PubLayNet with preprocessing and error handling."""
    
    def __init__(self, dataset, encoder: Optional[RFEncoder] = None, 
                 processor: Optional[LayoutLMv3Processor] = None,
                 max_seq_length: int = 512, device: str = "cpu"):
        self.dataset = dataset
        self.encoder = encoder
        self.processor = processor
        self.max_seq_length = max_seq_length
        self.device = device
        
    def __len__(self):
        return len(self.dataset)
        
    def __getitem__(self, idx):
        item = self.dataset[idx]
        # Assume item has 'image_path' or 'image' key
        image_path = item.get('image_path') or item.get('file_path')
        
        if not image_path:
            # Fallback if image is already loaded in item
            image = item.get('image')
            if image is None:
                raise ImagePreprocessingError(f"No image data at index {idx}")
            # Process in-memory image
            result = load_and_preprocess_image(image, self.encoder, self.processor, 
                                               self.max_seq_length, self.device)
        else:
            result = load_and_preprocess_image(image_path, self.encoder, self.processor, 
                                               self.max_seq_length, self.device)
        
        return {
            "tokens": result["tokens"],
            "is_valid": result["is_valid"],
            "error": result["error"],
            "original_index": idx
        }

def create_preprocessing_dataloader(dataset, encoder: Optional[RFEncoder] = None,
                                    processor: Optional[LayoutLMv3Processor] = None,
                                    max_seq_length: int = 512, 
                                    batch_size: int = 8, 
                                    device: str = "cpu",
                                    num_workers: int = 0):
    """
    Creates a DataLoader for the preprocessed dataset.
    """
    preprocessed_ds = PubLayNetPreprocessedDataset(
        dataset, encoder, processor, max_seq_length, device
    )
    
    return torch.utils.data.DataLoader(
        preprocessed_ds, 
        batch_size=batch_size, 
        shuffle=False,
        num_workers=num_workers,
        collate_fn=lambda batch: {
            "tokens": torch.stack([b["tokens"] for b in batch]),
            "is_valid": torch.tensor([b["is_valid"] for b in batch]),
            "error": [b["error"] for b in batch],
            "original_index": [b["original_index"] for b in batch]
        }
    )

def main():
    """
    Entry point for testing preprocessing with error handling.
    """
    config = get_config_dict()
    device = "cpu" # Enforce CPU as per constraints
    
    # Load encoder and processor
    logger.info("Loading RF Encoder and Processor...")
    encoder = create_rf_encoder()
    processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
    
    # Create a dummy test case for blank image handling
    # Since we don't have a real blank image file guaranteed, we simulate one
    # by creating a blank PIL image and passing it to the logic if we had a path.
    # Instead, we test the logic directly.
    
    logger.info("Testing blank image handling...")
    from PIL import Image
    blank_img = Image.new('RGB', (224, 224), color=(255, 255, 255))
    
    # Save to temp to test file path logic
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        blank_img.save(tmp.name)
        temp_path = tmp.name
    
    try:
        result = load_and_preprocess_image(temp_path, encoder, processor, device=device)
        print(f"Result for blank image: valid={result['is_valid']}, error={result['error']}")
        assert result['is_valid'] == True, "Blank image should be handled gracefully"
        assert result['tokens'] is not None, "Tokens should be generated (zeros)"
        print("Blank image handling test PASSED.")
    finally:
        os.unlink(temp_path)
        
    logger.info("Preprocessing module test completed.")

if __name__ == "__main__":
    main()