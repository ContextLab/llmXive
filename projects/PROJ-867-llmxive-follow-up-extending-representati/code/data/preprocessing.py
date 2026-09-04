import os
import logging
import hashlib
import warnings
import torch
import numpy as np
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Iterator, Union
from torch.utils.data import Dataset, DataLoader
import pyarrow.parquet as pq

from config import get_config_dict, ensure_dirs
from models.rf_encoder import RFEncoder, create_rf_encoder
from data.loaders import load_publaynet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def load_image(image_path: str) -> np.ndarray:
    """
    Load an image from disk using PIL and convert to numpy array.
    """
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        return np.array(img)
    except Exception as e:
        raise ImagePreprocessingError(f"Failed to load image {image_path}: {e}")

def resize_image(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Resize image to target dimensions.
    """
    try:
        from PIL import Image
        img_pil = Image.fromarray(image)
        resized = img_pil.resize(target_size, Image.Resampling.LANCZOS)
        return np.array(resized)
    except Exception as e:
        raise ImagePreprocessingError(f"Failed to resize image: {e}")

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image pixel values to [0, 1] range if in 0-255 range.
    """
    if image.max() > 1.0:
        return image.astype(np.float32) / 255.0
    return image.astype(np.float32)

def image_to_tensor(image: np.ndarray) -> torch.Tensor:
    """
    Convert numpy image array to PyTorch tensor (C, H, W).
    """
    if image.ndim == 3:
        # H, W, C -> C, H, W
        tensor = torch.from_numpy(image).permute(2, 0, 1)
    else:
        tensor = torch.from_numpy(image)
    return tensor.float()

def detect_and_clamp_nans(tensor: torch.Tensor) -> torch.Tensor:
    """
    Detect NaNs and Inf in tensor and clamp them to zero.
    """
    if torch.isnan(tensor).any() or torch.isinf(tensor).any():
        logger.warning("Detected NaN or Inf values in tensor. Clamping to 0.")
        tensor = torch.where(torch.isnan(tensor), torch.tensor(0.0), tensor)
        tensor = torch.where(torch.isinf(tensor), torch.tensor(0.0), tensor)
    return tensor

def pad_or_truncate_sequence(sequence: List[float], target_len: int, pad_value: float = 0.0) -> List[float]:
    """
    Pad or truncate a sequence to target length.
    """
    if len(sequence) >= target_len:
        return sequence[:target_len]
    return sequence + [pad_value] * (target_len - len(sequence))

def handle_corruption(image_shape: Tuple[int, int]) -> List[float]:
    """
    Return a minimal valid structure for blank/corrupted images.
    Returns a sequence of zeros representing a minimal token sequence.
    """
    # Assuming a minimal token sequence length of 10 for corruption handling
    return [0.0] * 10

def extract_tokens(model: RFEncoder, image_tensor: torch.Tensor) -> List[float]:
    """
    Extract intermediate representation tokens from the frozen RF encoder.
    Expects image_tensor in shape (C, H, W).
    Returns a list of token embeddings (flattened).
    """
    model.eval()
    with torch.no_grad():
        # Ensure input is batched: (B, C, H, W)
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        try:
            # Forward pass through encoder only
            # The RFEncoder wrapper should handle the LayoutLMv3 extraction
            # and return the hidden states (tokens)
            output = model(image_tensor)
            
            # output is expected to be a dict or tensor containing hidden states
            if isinstance(output, dict):
                # Assuming 'last_hidden_state' or similar key
                tokens = output.get('last_hidden_state', output.get('hidden_states', None))
                if tokens is None:
                    raise ImagePreprocessingError("Model output does not contain expected token keys.")
            else:
                tokens = output
            
            # Flatten tokens to a 1D list of floats
            # Shape: (B, Seq_Len, Hidden_Dim) -> (Seq_Len * Hidden_Dim)
            tokens_np = tokens.cpu().numpy().flatten()
            return tokens_np.tolist()
            
        except Exception as e:
            raise ImagePreprocessingError(f"Failed to extract tokens: {e}")

def pad_sequences(tokens_list: List[List[float]], max_len: int) -> List[List[float]]:
    """
    Pad a list of token sequences to a fixed context window (max_len).
    """
    return [pad_or_truncate_sequence(seq, max_len) for seq in tokens_list]

def load_and_preprocess_image(model: RFEncoder, image_path: str, max_tokens: int = 512) -> List[float]:
    """
    Full pipeline: load, resize, normalize, extract tokens, clamp nans.
    """
    try:
        img = load_image(image_path)
        img = resize_image(img)
        img = normalize_image(img)
        tensor = image_to_tensor(img)
        tensor = detect_and_clamp_nans(tensor)
        
        tokens = extract_tokens(model, tensor)
        return tokens
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        # Return minimal valid structure on error
        return handle_corruption((224, 224))

class PubLayNetPreprocessedDataset(Dataset):
    """
    Dataset class for RF token pairs.
    Loads from the parquet file produced by T016.
    """
    def __init__(self, parquet_path: str, config: Dict[str, Any]):
        super().__init__()
        self.parquet_path = parquet_path
        self.config = config
        self.max_len = config.get('max_context_window', 512)
        
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Token artifact not found: {parquet_path}")
        
        # Load parquet into pandas
        self.df = pd.read_parquet(parquet_path)
        
        # Ensure necessary columns exist
        if 'tokens' not in self.df.columns:
            raise ValueError("Parquet file must contain 'tokens' column.")
        
        logger.info(f"Loaded {len(self.df)} samples from {parquet_path}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        tokens = row['tokens']
        
        # If tokens is stored as a string (e.g. JSON), parse it
        if isinstance(tokens, str):
            tokens = json.loads(tokens)
        
        # Pad or truncate to fixed context window
        tokens = pad_or_truncate_sequence(tokens, self.max_len)
        
        # Convert to tensor
        x = torch.tensor(tokens, dtype=torch.float32)
        
        # Create a dummy target for now (US2 will define real targets)
        # For T023, we just need the DataLoader structure for RF tokens
        # Target could be the original text/structure if available, or dummy
        y = torch.zeros(1, dtype=torch.long) # Placeholder target
        
        return x, y

def create_preprocessing_dataloader(parquet_path: str, config: Dict[str, Any], batch_size: int = 4) -> DataLoader:
    """
    Create a PyTorch DataLoader for the RF token pairs.
    """
    dataset = PubLayNetPreprocessedDataset(parquet_path, config)
    dataloader = DataLoader(
        dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=0, # Keep 0 for CPU-only compatibility as per constraints
        drop_last=False
    )
    return dataloader

def main():
    """
    Main entry point to test the DataLoader creation.
    """
    config = get_config_dict()
    ensure_dirs(config)
    
    # Path to the tokens.parquet produced by T016
    # Assuming standard output path from T016
    tokens_path = Path(config.get('data_dir', 'data')) / 'processed' / 'tokens.parquet'
    
    if not tokens_path.exists():
        logger.error(f"Required artifact {tokens_path} not found. Run T016 first.")
        # In a real pipeline, this would be a hard failure
        return
    
    logger.info(f"Creating DataLoader for {tokens_path}")
    dataloader = create_preprocessing_dataloader(str(tokens_path), config, batch_size=4)
    
    # Iterate over a few batches to verify
    for i, (x, y) in enumerate(dataloader):
        logger.info(f"Batch {i}: x shape {x.shape}, y shape {y.shape}")
        if i >= 2:
            break
    
    logger.info("DataLoader verification successful.")

if __name__ == "__main__":
    main()