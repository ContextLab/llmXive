"""
Model initialization utilities for the llmXive DanceOPD pipeline.

This module handles the loading and caching of pre-trained models required
for metrics calculation and data processing, specifically the CLIP model.
"""
import torch
from transformers import CLIPModel, CLIPProcessor
from typing import Optional, Tuple
import logging

from utils.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for initialized models to avoid reloading
_clip_model: Optional[CLIPModel] = None
_clip_processor: Optional[CLIPProcessor] = None

def get_clip_model() -> Tuple[CLIPModel, CLIPProcessor]:
    """
    Initialize and return the CLIP model and processor.
    
    This function implements a singleton pattern: the model is loaded only once
    and cached in memory for subsequent calls. It respects the configuration
    settings for device (CPU/GPU) and model weights.
    
    Returns:
        Tuple[CLIPModel, CLIPProcessor]: The initialized CLIP model and its processor.
        
    Raises:
        RuntimeError: If the model fails to load or configuration is invalid.
    """
    global _clip_model, _clip_processor
    
    if _clip_model is not None and _clip_processor is not None:
        logger.debug("Returning cached CLIP model and processor.")
        return _clip_model, _clip_processor
    
    config = get_config()
    
    # Determine device based on configuration and availability
    if torch.cuda.is_available() and config.get('USE_GPU', False):
        device = torch.device('cuda')
        logger.info("Initializing CLIP model on CUDA.")
    else:
        device = torch.device('cpu')
        logger.info("Initializing CLIP model on CPU.")
    
    try:
        # Load the model and processor
        # Using a standard pretrained checkpoint compatible with the pipeline
        model_name = "openai/clip-vit-base-patch32"
        
        logger.info(f"Loading CLIP model: {model_name}...")
        _clip_model = CLIPModel.from_pretrained(model_name)
        _clip_processor = CLIPProcessor.from_pretrained(model_name)
        
        _clip_model.to(device)
        _clip_model.eval()  # Set to evaluation mode
        
        logger.info("CLIP model initialized successfully.")
        
    except Exception as e:
        logger.error(f"Failed to initialize CLIP model: {e}")
        raise RuntimeError(f"Could not initialize CLIP model: {e}")
    
    return _clip_model, _clip_processor

def clear_model_cache():
    """
    Clear the global model cache.
    
    Useful for testing or forcing a reload of models with different configurations.
    """
    global _clip_model, _clip_processor
    _clip_model = None
    _clip_processor = None
    logger.info("Model cache cleared.")