import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any
import yaml
from pathlib import Path

class TextCrossAttentionAdapter(nn.Module):
    """
    Maps frozen CLIP text embeddings to reference KV slots for the video generation backbone.
    Implements a cross-attention mechanism where text queries attend to image-derived keys/values.
    
    Constraint: Must explicitly initialize on CPU.
    """
    def __init__(
        self,
        text_dim: int = 512,
        hidden_dim: int = 768,
        num_heads: int = 8,
        dropout: float = 0.1,
        device: str = 'cpu'
    ):
        super().__init__()
        self.device = device
        self.text_dim = text_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        
        # Ensure CPU initialization strictly
        if device != 'cpu':
            raise RuntimeError("TextCrossAttentionAdapter must be initialized on CPU. "
                             f"Requested device: {device}")
        
        # Projection layers to map text embeddings to the backbone's hidden dimension
        self.text_projection = nn.Linear(text_dim, hidden_dim, device=device)
        
        # Cross-attention mechanism
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
            device=device
        )
        
        # Feed-forward network for refinement
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4, device=device),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim, device=device),
            nn.Dropout(dropout)
        )
        
        # Layer norms
        self.norm1 = nn.LayerNorm(hidden_dim, device=device)
        self.norm2 = nn.LayerNorm(hidden_dim, device=device)
        
        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights with small random values for stability."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        text_embeddings: torch.Tensor,
        kv_slots: torch.Tensor,
        kv_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass mapping text embeddings to reference KV slots.
        
        Args:
            text_embeddings: [batch_size, seq_len_text, text_dim]
            kv_slots: [batch_size, seq_len_kv, hidden_dim]
            kv_mask: [batch_size, seq_len_kv] (optional, 1 for valid, 0 for padding)
        
        Returns:
            adapted_features: [batch_size, seq_len_kv, hidden_dim]
        """
        # Ensure inputs are on CPU
        if text_embeddings.device.type != 'cpu':
            text_embeddings = text_embeddings.cpu()
        if kv_slots.device.type != 'cpu':
            kv_slots = kv_slots.cpu()
        
        # Project text embeddings to hidden dimension
        text_features = self.text_projection(text_embeddings)  # [B, L_t, H]
        
        # Cross-attention: Query = text, Key/Value = kv_slots
        # text_features acts as the query
        attn_output, attn_weights = self.cross_attention(
            query=text_features,
            key=kv_slots,
            value=kv_slots,
            key_padding_mask=(kv_mask == 0) if kv_mask is not None else None
        )
        
        # Residual connection and normalization
        attn_output = self.norm1(attn_output + text_features)
        
        # Feed-forward refinement
        ffn_output = self.ffn(attn_output)
        output = self.norm2(ffn_output + attn_output)
        
        return output

def load_adapter_from_config(config_path: str) -> TextCrossAttentionAdapter:
    """
    Load the adapter from a YAML configuration file.
    
    Args:
        config_path: Path to the config YAML file
    
    Returns:
        TextCrossAttentionAdapter instance initialized on CPU
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract adapter parameters
    adapter_config = config.get('adapter', {})
    text_dim = adapter_config.get('text_dim', 512)
    hidden_dim = adapter_config.get('hidden_dim', 768)
    num_heads = adapter_config.get('num_heads', 8)
    dropout = adapter_config.get('dropout', 0.1)
    
    # Explicitly enforce CPU
    device = 'cpu'
    
    adapter = TextCrossAttentionAdapter(
        text_dim=text_dim,
        hidden_dim=hidden_dim,
        num_heads=num_heads,
        dropout=dropout,
        device=device
    )
    
    return adapter

def main():
    """
    Main entry point for testing the adapter initialization and basic forward pass.
    This script verifies that the adapter can be instantiated on CPU and performs
    a forward pass with dummy inputs to ensure no CUDA calls are made.
    """
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description="Test TextCrossAttentionAdapter initialization and forward pass")
    parser.add_argument('--config', type=str, default='code/config/settings.yaml',
                      help='Path to configuration file')
    parser.add_argument('--batch-size', type=int, default=2, help='Batch size for dummy input')
    parser.add_argument('--seq-len-text', type=int, default=77, help='Sequence length for text')
    parser.add_argument('--seq-len-kv', type=int, default=50, help='Sequence length for KV slots')
    args = parser.parse_args()

    try:
        # Load adapter from config
        if not os.path.exists(args.config):
            print(f"Warning: Config file {args.config} not found. Using default parameters.")
            adapter = TextCrossAttentionAdapter(device='cpu')
        else:
            adapter = load_adapter_from_config(args.config)
        
        print(f"Adapter loaded successfully on device: {next(adapter.parameters()).device}")
        
        # Create dummy inputs on CPU
        batch_size = args.batch_size
        seq_len_text = args.seq_len_text
        seq_len_kv = args.seq_len_kv
        
        # Simulate CLIP text embeddings (frozen)
        text_embeddings = torch.randn(batch_size, seq_len_text, 512, device='cpu')
        
        # Simulate reference KV slots from image backbone
        kv_slots = torch.randn(batch_size, seq_len_kv, 768, device='cpu')
        
        # Optional mask for KV slots
        kv_mask = torch.ones(batch_size, seq_len_kv, device='cpu', dtype=torch.int)
        
        # Perform forward pass
        print(f"Running forward pass with batch_size={batch_size}, seq_len_text={seq_len_text}, seq_len_kv={seq_len_kv}")
        output = adapter(text_embeddings, kv_slots, kv_mask)
        
        print(f"Forward pass completed successfully.")
        print(f"Input text shape: {text_embeddings.shape}")
        print(f"Input KV shape: {kv_slots.shape}")
        print(f"Output shape: {output.shape}")
        
        # Verify output is on CPU
        assert output.device.type == 'cpu', "Output tensor is not on CPU!"
        print("Verification passed: All tensors are on CPU.")
        
        return 0
        
    except RuntimeError as e:
        if "CUDA" in str(e) or "cuda" in str(e):
            print(f"CRITICAL ERROR: CUDA detected where only CPU is allowed: {e}")
            return 1
        raise
    except Exception as e:
        print(f"Error during adapter test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())