"""
Text Cross-Attention Adapter for FashionChame.

Implements FR-001: Map frozen CLIP text embeddings to reference KV slots
for the image generation backbone.
"""
import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any
import yaml
from pathlib import Path


class TextCrossAttentionAdapter(nn.Module):
    """
    Adapter module that projects frozen CLIP text embeddings into
    the Key/Value slots of the image generation backbone's cross-attention.
    
    This allows the text reference to condition the generation without
    modifying the frozen backbone parameters.
    """
    
    def __init__(
        self,
        text_embedding_dim: int = 512,
        hidden_dim: int = 768,
        num_heads: int = 8,
        dropout: float = 0.1,
        config_path: Optional[str] = None
    ):
        super().__init__()
        
        # Load config if provided
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            # Override defaults with config values if present
            text_embedding_dim = config.get('text_embedding_dim', text_embedding_dim)
            hidden_dim = config.get('hidden_dim', hidden_dim)
            num_heads = config.get('num_heads', num_heads)
            dropout = config.get('adapter_dropout', dropout)
        
        self.text_embedding_dim = text_embedding_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        
        # Project text embeddings to hidden dimension
        self.text_projection = nn.Sequential(
            nn.Linear(text_embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Cross-attention mechanism to integrate text into image generation
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Layer normalization for stability
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize projection and attention weights."""
        for module in self.text_projection:
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        
        # Initialize cross-attention
        for p in self.cross_attention.in_proj_weight:
            nn.init.xavier_uniform_(p)
        nn.init.xavier_uniform_(self.cross_attention.out_proj.weight)
        nn.init.zeros_(self.cross_attention.out_proj.bias)
    
    def forward(
        self,
        image_features: torch.Tensor,
        text_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass: Project text embeddings and cross-attend with image features.
        
        Args:
            image_features: Tensor of shape (batch_size, seq_len, hidden_dim)
                representing image tokens from the backbone.
            text_embeddings: Tensor of shape (batch_size, text_seq_len, text_dim)
                representing frozen CLIP text embeddings.
            attention_mask: Optional mask for text embeddings (batch_size, text_seq_len).
        
        Returns:
            Tensor of shape (batch_size, seq_len, hidden_dim) with text-conditioned
            image features.
        """
        # Project text embeddings to hidden dimension
        projected_text = self.text_projection(text_embeddings)
        
        # Cross-attention: image features query, text keys/values
        # image_features: (B, L_img, D)
        # projected_text: (B, L_txt, D)
        attended_features, _ = self.cross_attention(
            query=image_features,
            key=projected_text,
            value=projected_text,
            key_padding_mask=attention_mask
        )
        
        # Residual connection and normalization
        output = self.norm(image_features + self.dropout(attended_features))
        
        return output
    
    def get_kv_slots(
        self,
        text_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract Key and Value slots from text embeddings for direct injection.
        
        This method projects text embeddings and returns the K and V tensors
        that can be directly used by the backbone's cross-attention layers.
        
        Args:
            text_embeddings: Tensor of shape (batch_size, text_seq_len, text_dim)
            attention_mask: Optional mask for text embeddings
        
        Returns:
            Tuple of (key_slots, value_slots), each of shape 
            (batch_size, text_seq_len, hidden_dim)
        """
        projected_text = self.text_projection(text_embeddings)
        
        # For direct KV injection, we use the projected text as both K and V
        # This assumes the backbone expects K and V to be of the same dimension
        key_slots = projected_text
        value_slots = projected_text
        
        return key_slots, value_slots


def load_adapter_from_config(config_path: str) -> TextCrossAttentionAdapter:
    """
    Load the adapter from a configuration file.
    
    Args:
        config_path: Path to the YAML configuration file.
    
    Returns:
        Initialized TextCrossAttentionAdapter instance.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    adapter = TextCrossAttentionAdapter(
        text_embedding_dim=config.get('text_embedding_dim', 512),
        hidden_dim=config.get('hidden_dim', 768),
        num_heads=config.get('num_heads', 8),
        dropout=config.get('adapter_dropout', 0.1),
        config_path=config_path
    )
    
    return adapter


def main():
    """
    Main function to demonstrate adapter initialization and basic forward pass.
    This script can be run to verify the adapter works correctly.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Test TextCrossAttentionAdapter')
    parser.add_argument('--config', type=str, default='code/config/settings.yaml',
                      help='Path to configuration file')
    parser.add_argument('--batch_size', type=int, default=2, help='Batch size for test')
    parser.add_argument('--image_seq_len', type=int, default=64, help='Image sequence length')
    parser.add_argument('--text_seq_len', type=int, default=77, help='Text sequence length')
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Warning: Config file {config_path} not found. Using defaults.")
        config_path = None
    
    # Initialize adapter
    adapter = TextCrossAttentionAdapter(config_path=str(config_path) if config_path else None)
    adapter.eval()
    
    print(f"Adapter initialized:")
    print(f"  Text embedding dim: {adapter.text_embedding_dim}")
    print(f"  Hidden dim: {adapter.hidden_dim}")
    print(f"  Number of heads: {adapter.num_heads}")
    
    # Create dummy inputs
    batch_size = args.batch_size
    image_seq_len = args.image_seq_len
    text_seq_len = args.text_seq_len
    
    image_features = torch.randn(batch_size, image_seq_len, adapter.hidden_dim)
    text_embeddings = torch.randn(batch_size, text_seq_len, adapter.text_embedding_dim)
    
    # Forward pass
    with torch.no_grad():
        output = adapter(image_features, text_embeddings)
        key_slots, value_slots = adapter.get_kv_slots(text_embeddings)
    
    print(f"\nForward pass results:")
    print(f"  Output shape: {output.shape}")
    print(f"  Key slots shape: {key_slots.shape}")
    print(f"  Value slots shape: {value_slots.shape}")
    
    # Verify shapes
    assert output.shape == (batch_size, image_seq_len, adapter.hidden_dim)
    assert key_slots.shape == (batch_size, text_seq_len, adapter.hidden_dim)
    assert value_slots.shape == (batch_size, text_seq_len, adapter.hidden_dim)
    
    print("\n✓ All shape checks passed. Adapter is working correctly.")


if __name__ == '__main__':
    main()