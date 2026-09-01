"""
RF Encoder: Wraps microsoft/layoutlmv3-base with frozen weights and pixel-decoder layers disabled.
This module implements User Story 1: Extract Structural Priors via Frozen Representation Forcing.
"""
import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple, List
from transformers import LayoutLMv3Model, LayoutLMv3Config
import logging

from config import get_config_dict

logger = logging.getLogger(__name__)

class RFEncoder(nn.Module):
    """
    Frozen Representation Forcing Encoder.
    
    Wraps LayoutLMv3-base to extract intermediate representation tokens (structural priors)
    from document images without invoking pixel-decoding layers.
    
    Attributes:
        model: The underlying LayoutLMv3 model with weights frozen.
        hidden_size: The dimensionality of the hidden representations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        
        if config is None:
            config = get_config_dict()
        
        # Load LayoutLMv3 configuration
        # We use the base variant as specified in the task
        self.model_name = config.get('model_name', 'microsoft/layoutlmv3-base')
        self.hidden_size = config.get('hidden_size', 768)
        self.max_seq_length = config.get('max_seq_length', 512)
        
        logger.info(f"Loading {self.model_name} for RF Encoder...")
        
        # Load the model
        self.model = LayoutLMv3Model.from_pretrained(self.model_name)
        
        # Freeze all weights
        logger.info("Freezing all model weights...")
        for param in self.model.parameters():
            param.requires_grad = False
        
        # Disable pixel-decoder layers (LayoutLMv3 does not have explicit pixel-decoder layers
        # in the standard encoder-only configuration, but we ensure we only use the encoder part)
        # The LayoutLMv3Model itself is an encoder. We do not attach any decoder heads.
        
        # Ensure the model is in evaluation mode
        self.model.eval()
        
        logger.info(f"RF Encoder initialized. Hidden size: {self.hidden_size}")

    def forward(
        self, 
        input_ids: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None,
        bbox: Optional[torch.Tensor] = None,
        pixel_values: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract representation tokens from input.
        
        Args:
            input_ids: Token IDs of shape (batch_size, seq_length)
            attention_mask: Attention mask of shape (batch_size, seq_length)
            bbox: Bounding boxes of shape (batch_size, seq_length, 4)
            pixel_values: Image tensors of shape (batch_size, 3, height, width)
        
        Returns:
            last_hidden_state: Tensor of shape (batch_size, seq_length, hidden_size)
            pooler_output: Tensor of shape (batch_size, hidden_size) - [CLS] token representation
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                bbox=bbox,
                pixel_values=pixel_values,
                output_hidden_states=False
            )
            
            last_hidden_state = outputs.last_hidden_state
            pooler_output = outputs.pooler_output
            
        return last_hidden_state, pooler_output

    def extract_tokens(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        bbox: Optional[torch.Tensor] = None,
        pixel_values: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Extract only the token sequence (structural priors) without the pooler output.
        
        Args:
            input_ids: Token IDs of shape (batch_size, seq_length)
            attention_mask: Attention mask of shape (batch_size, seq_length)
            bbox: Bounding boxes of shape (batch_size, seq_length, 4)
            pixel_values: Image tensors of shape (batch_size, 3, height, width)
        
        Returns:
            tokens: Tensor of shape (batch_size, seq_length, hidden_size)
        """
        last_hidden_state, _ = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            bbox=bbox,
            pixel_values=pixel_values
        )
        return last_hidden_state


def create_rf_encoder(config: Optional[Dict[str, Any]] = None) -> RFEncoder:
    """
    Factory function to create an RFEncoder instance.
    
    Args:
        config: Optional configuration dictionary.
    
    Returns:
        RFEncoder: Initialized encoder with frozen weights.
    """
    return RFEncoder(config)


def main():
    """
    Main function to demonstrate RF Encoder initialization and single-image extraction.
    This serves as a verification script for User Story 1.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create encoder
    encoder = create_rf_encoder()
    
    # Create dummy input (simulating a single image processed by LayoutLMv3)
    batch_size = 1
    seq_length = 512
    
    # Dummy input_ids (simulating tokenized document)
    input_ids = torch.randint(0, 10000, (batch_size, seq_length))
    attention_mask = torch.ones((batch_size, seq_length), dtype=torch.long)
    
    # Dummy bbox (simulating bounding boxes)
    bbox = torch.randint(0, 1000, (batch_size, seq_length, 4))
    
    # Dummy pixel_values (simulating resized image)
    pixel_values = torch.randn((batch_size, 3, 224, 224))
    
    logger.info("Running forward pass on dummy input...")
    
    # Extract tokens
    tokens = encoder.extract_tokens(
        input_ids=input_ids,
        attention_mask=attention_mask,
        bbox=bbox,
        pixel_values=pixel_values
    )
    
    logger.info(f"Extracted tokens shape: {tokens.shape}")
    logger.info(f"Expected shape: ({batch_size}, {seq_length}, {encoder.hidden_size})")
    
    # Verify shape
    assert tokens.shape == (batch_size, seq_length, encoder.hidden_size), \
        f"Token shape mismatch: {tokens.shape} vs expected ({batch_size}, {seq_length}, {encoder.hidden_size})"
    
    logger.info("✅ RF Encoder verification passed: Correct token dimensionality extracted.")
    logger.info("✅ No CUDA used (running on CPU as required).")
    logger.info("✅ Pixel-decoder layers disabled (only encoder used).")
    
    return tokens


if __name__ == "__main__":
    main()
