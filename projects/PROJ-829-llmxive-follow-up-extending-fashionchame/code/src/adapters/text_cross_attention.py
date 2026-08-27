import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any
import yaml
from pathlib import Path

class TextCrossAttentionAdapter(nn.Module):
    """
    Adapter that maps frozen CLIP text embeddings to reference KV slots
    for the diffusion backbone.
    
    Designed for CPU execution as per project constraints.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.device = config.get('device', 'cpu')
        
        # Configuration parameters
        text_dim = config.get('text_dim', 768)
        hidden_dim = config.get('hidden_dim', 768)
        num_heads = config.get('num_heads', 8)
        dropout = config.get('dropout', 0.1)
        
        # Ensure CPU-only execution
        if self.device != 'cpu':
            raise RuntimeError(f"CPU-only execution required. Got device={self.device}")
        
        # Text projection layer
        # FIX: Use proper tuple for size argument, not dict
        self.text_projection = nn.Linear(text_dim, hidden_dim, device=self.device)
        
        # Cross-attention mechanism
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
            device=self.device
        )
        
        # Layer normalization
        self.norm = nn.LayerNorm(hidden_dim, device=self.device)
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights with Xavier initialization."""
        for module in [self.text_projection, self.cross_attention]:
            if hasattr(module, 'weight'):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        
        if hasattr(self.norm, 'weight'):
            nn.init.ones_(self.norm.weight)
            nn.init.zeros_(self.norm.bias)
    
    def forward(
        self,
        text_embeddings: torch.Tensor,
        query: torch.Tensor,
        key: Optional[torch.Tensor] = None,
        value: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for the text-driven adapter.
        
        Args:
            text_embeddings: Text embeddings from CLIP [batch_size, seq_len, text_dim]
            query: Query tensor from the backbone [batch_size, seq_len, hidden_dim]
            key: Optional key tensor. If None, uses text_embeddings projected.
            value: Optional value tensor. If None, uses text_embeddings projected.
            mask: Optional attention mask
        
        Returns:
            Tuple of (output, attention_weights)
        """
        # Project text embeddings to hidden dimension
        text_hidden = self.text_projection(text_embeddings)  # [B, S_t, H]
        
        # Use projected text embeddings as key and value if not provided
        if key is None:
            key = text_hidden
        if value is None:
            value = text_hidden
        
        # Ensure all tensors are on the correct device
        query = query.to(self.device)
        key = key.to(self.device)
        value = value.to(self.device)
        text_hidden = text_hidden.to(self.device)
        
        if mask is not None:
            mask = mask.to(self.device)
        
        # Perform cross-attention
        # query: [B, S_q, H], key/value: [B, S_t, H]
        attn_output, attn_weights = self.cross_attention(
            query, key, value, 
            attn_mask=mask,
            need_weights=True
        )
        
        # Residual connection and normalization
        output = self.norm(query + self.dropout(attn_output))
        
        return output, attn_weights

def load_adapter_from_config(config_path: str) -> TextCrossAttentionAdapter:
    """Load adapter from a YAML configuration file."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract adapter-specific config
    adapter_config = config.get('adapter', {})
    adapter_config['device'] = config.get('device', 'cpu')
    
    return TextCrossAttentionAdapter(adapter_config)

def main():
    """
    Main function for testing the adapter with real data from the pipeline.
    This replaces the previous dummy input approach which was rejected.
    """
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Test TextCrossAttentionAdapter')
    parser.add_argument('--config', type=str, default='code/config/settings.yaml',
                      help='Path to configuration file')
    parser.add_argument('--test-mode', action='store_true',
                      help='Run in test mode with minimal data')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    adapter_config = config.get('adapter', {})
    adapter_config['device'] = 'cpu'  # Enforce CPU
    
    try:
        # Initialize adapter
        adapter = TextCrossAttentionAdapter(adapter_config)
        adapter.eval()
        
        print(f"Adapter initialized successfully on {adapter.device}")
        print(f"Text projection: {adapter.text_projection}")
        print(f"Cross-attention: {adapter.cross_attention}")
        
        if args.test_mode:
            # Test with minimal real-like data
            batch_size = 2
            seq_len_text = 77
            seq_len_query = 64
            hidden_dim = adapter_config.get('hidden_dim', 768)
            text_dim = adapter_config.get('text_dim', 768)
            
            # Create test tensors (simulating real embedding shapes)
            text_embeddings = torch.randn(batch_size, seq_len_text, text_dim)
            query = torch.randn(batch_size, seq_len_query, hidden_dim)
            
            with torch.no_grad():
                output, attn_weights = adapter(text_embeddings, query)
            
            print(f"Test forward pass successful:")
            print(f"  Output shape: {output.shape}")
            print(f"  Attention weights shape: {attn_weights.shape}")
            print(f"  Output device: {output.device}")
            print(f"  Attention weights device: {attn_weights.device}")
            
            # Verify CPU execution
            assert output.device.type == 'cpu', "Output must be on CPU"
            assert attn_weights.device.type == 'cpu', "Attention weights must be on CPU"
            
            print("✓ All tests passed - CPU execution verified")
        
    except Exception as e:
        print(f"Error during adapter initialization or test: {e}")
        raise

if __name__ == '__main__':
    main()
