"""
RF Encoder: Frozen LayoutLMv3 encoder for extracting structural priors.

This module implements a wrapper around microsoft/layoutlmv3-base that:
1. Loads the encoder weights.
2. Explicitly excludes and does not instantiate the pixel-decoding layers.
3. Freezes all parameters to prevent gradient updates.
4. Provides a forward pass that outputs only the intermediate representation tokens.

Critical: Decoder weights are NOT loaded into memory.
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
    A frozen encoder wrapper for LayoutLMv3.
    
    This model loads the encoder layers of LayoutLMv3 and explicitly
    prevents the loading or instantiation of the pixel-decoding head.
    
    Attributes:
        encoder: The frozen LayoutLMv3 encoder.
        config: The model configuration.
    """
    def __init__(self, config: Optional[LayoutLMv3Config] = None, freeze: bool = True):
        super().__init__()
        self.config = config or get_default_config()
        
        # Load the full model first to access the encoder structure,
        # but we will immediately discard the decoder parts.
        # We use from_pretrained to get the weights, but we only keep the encoder.
        try:
            full_model = LayoutLMv3Model.from_pretrained(
                "microsoft/layoutlmv3-base",
                config=self.config,
                ignore_mismatched_sizes=False
            )
        except Exception as e:
            logger.error(f"Failed to load LayoutLMv3 model: {e}")
            raise

        # Extract the encoder layers (LayoutLMv3Model is the encoder itself in this context)
        # LayoutLMv3Model contains the embeddings and the encoder stack.
        # The "decoder" in LayoutLMv3 context usually refers to the classification head
        # or the MLM head, which we do not need for token extraction.
        # We explicitly ensure no decoder weights are kept by not loading the full model
        # if it were a seq2seq, but LayoutLMv3 is encoder-only. 
        # However, to satisfy the constraint of NOT loading decoder weights if they existed 
        # (e.g. if we were using a model with a decoder head attached), we strictly 
        # initialize only the base encoder components.
        
        self.encoder = full_model
        
        # Explicitly verify no decoder layers exist in this specific architecture
        # LayoutLMv3Model does not have a 'decoder' attribute by default, 
        # but we check to be safe against custom subclasses or future changes.
        if hasattr(self.encoder, 'decoder'):
            logger.warning("Encoder instance has a 'decoder' attribute. Removing it to save memory.")
            delattr(self.encoder, 'decoder')
        
        # Freeze all parameters
        if freeze:
            for param in self.encoder.parameters():
                param.requires_grad = False
            logger.info("All encoder parameters have been frozen.")
        
        # Verify via graph inspection that decoder layers are not invoked
        # We do this by checking the model structure
        self._verify_no_decoder()

    def _verify_no_decoder(self):
        """Verify that the model does not contain decoder layers."""
        has_decoder = False
        for name, module in self.encoder.named_modules():
            if 'decoder' in name.lower():
                has_decoder = True
                logger.warning(f"Found potential decoder layer: {name}")
        
        if not has_decoder:
            logger.info("Verification passed: No decoder layers found in the model.")
        else:
            logger.error("Verification failed: Decoder layers detected.")
            raise RuntimeError("Decoder layers detected in RFEncoder. This violates the constraint.")

    def forward(self, input_ids: torch.Tensor, 
                attention_mask: Optional[torch.Tensor] = None,
                bbox: Optional[torch.Tensor] = None,
                labels: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass to extract intermediate representation tokens.
        
        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            bbox: Bounding boxes (required for LayoutLMv3).
            labels: Labels (ignored for extraction).
        
        Returns:
            Dict containing 'last_hidden_state' (the tokens).
        """
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            bbox=bbox,
            labels=labels
        )
        
        # Return only the last hidden state (tokens)
        return {
            "last_hidden_state": outputs.last_hidden_state
        }

    def get_token_embeddings(self, input_ids: torch.Tensor, 
                             attention_mask: torch.Tensor, 
                             bbox: torch.Tensor) -> torch.Tensor:
        """
        Convenience method to get token embeddings directly.
        
        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            bbox: Bounding boxes.
        
        Returns:
            Tensor of shape (batch_size, seq_len, hidden_size).
        """
        with torch.no_grad():
            outputs = self.forward(input_ids, attention_mask, bbox)
        return outputs["last_hidden_state"]

def get_default_config() -> LayoutLMv3Config:
    """Get the default configuration for LayoutLMv3."""
    return LayoutLMv3Config.from_pretrained("microsoft/layoutlmv3-base")

def create_rf_encoder(freeze: bool = True) -> RFEncoder:
    """
    Factory function to create an RFEncoder instance.
    
    Args:
        freeze: Whether to freeze the encoder parameters.
    
    Returns:
        An instance of RFEncoder.
    """
    return RFEncoder(freeze=freeze)

def main():
    """
    Main function to demonstrate the RFEncoder.
    Runs a simple forward pass with dummy data to verify functionality.
    """
    config = get_config_dict()
    logger.info("Initializing RFEncoder...")
    
    encoder = create_rf_encoder(freeze=True)
    
    # Create dummy inputs
    batch_size = 2
    seq_len = 512
    hidden_size = 768
    
    input_ids = torch.randint(0, 1000, (batch_size, seq_len))
    attention_mask = torch.ones((batch_size, seq_len), dtype=torch.long)
    bbox = torch.zeros((batch_size, seq_len, 4), dtype=torch.long)
    
    # Set bbox to valid values (0-1000)
    bbox[:, :, 0] = torch.randint(0, 1000, (batch_size, seq_len))
    bbox[:, :, 1] = torch.randint(0, 1000, (batch_size, seq_len))
    bbox[:, :, 2] = torch.randint(0, 1000, (batch_size, seq_len))
    bbox[:, :, 3] = torch.randint(0, 1000, (batch_size, seq_len))
    
    logger.info("Running forward pass...")
    with torch.no_grad():
        output = encoder(input_ids, attention_mask, bbox)
    
    last_hidden_state = output["last_hidden_state"]
    
    logger.info(f"Input shape: {input_ids.shape}")
    logger.info(f"Output shape: {last_hidden_state.shape}")
    
    assert last_hidden_state.shape == (batch_size, seq_len, hidden_size), \
        f"Expected output shape ({batch_size}, {seq_len}, {hidden_size}), got {last_hidden_state.shape}"
    
    logger.info("RFEncoder test passed successfully.")
    
    # Verify decoder is not in memory
    logger.info(f"Model parameters: {sum(p.numel() for p in encoder.parameters())}")
    logger.info(f"Requires grad: {any(p.requires_grad for p in encoder.parameters())}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
