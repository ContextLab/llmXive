"""
Text Cross-Attention Adapter for Stable Diffusion.

Implements a cross-attention mechanism that maps frozen CLIP text embeddings
to reference Key-Value (KV) slots for injection into the Stable Diffusion backbone.
All models are explicitly initialized on CPU as per project constraints.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, Any
import yaml
from pathlib import Path
import argparse

# Configuration defaults
DEFAULT_CONFIG = {
    "model": {
        "vlm_confidence_threshold": 0.95,
        "blip_model_id": "Salesforce/blip-large"
    },
    "adapter": {
        "text_embed_dim": 768,
        "num_heads": 8,
        "head_dim": 64,
        "seq_len": 77,
        "dropout": 0.1
    }
}

class TextCrossAttentionAdapter(nn.Module):
    """
    Cross-Attention Adapter Module.

    Maps text embeddings (from CLIP) to KV slots compatible with the
    Stable Diffusion UNet cross-attention layers.

    Input: (batch_size, seq_len, embed_dim)
    Output: (batch_size, num_heads, seq_len, head_dim) for K and V
    """

    def __init__(
        self,
        text_embed_dim: int = 768,
        num_heads: int = 8,
        head_dim: int = 64,
        seq_len: int = 77,
        dropout: float = 0.1,
        device: str = 'cpu'
    ):
        super().__init__()
        self.device = device
        self.text_embed_dim = text_embed_dim
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.seq_len = seq_len
        self.total_dim = num_heads * head_dim

        # Ensure dimensions match
        if self.total_dim != text_embed_dim:
            # Projection if necessary, though standard SD1.5 uses 768
            self.projection = nn.Linear(text_embed_dim, self.total_dim, device=device)
        else:
            self.projection = nn.Identity()

        # Query, Key, Value projections for the adapter
        # We project the text embedding to generate K and V for the diffusion model
        self.to_q = nn.Linear(self.total_dim, self.total_dim, bias=False, device=device)
        self.to_k = nn.Linear(self.total_dim, self.total_dim, bias=False, device=device)
        self.to_v = nn.Linear(self.total_dim, self.total_dim, bias=False, device=device)

        self.dropout = nn.Dropout(dropout)
        self.out_proj = nn.Linear(self.total_dim, self.total_dim, device=device)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using Xavier uniform."""
        for module in [self.to_q, self.to_k, self.to_v, self.out_proj]:
            if module != self.projection:
                nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(
        self,
        text_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass to generate KV slots.

        Args:
            text_embeddings: (batch_size, seq_len, embed_dim)
            attention_mask: (batch_size, seq_len) - optional

        Returns:
            key_slots: (batch_size, num_heads, seq_len, head_dim)
            value_slots: (batch_size, num_heads, seq_len, head_dim)
        """
        if text_embeddings.device != torch.device(self.device):
            text_embeddings = text_embeddings.to(self.device)

        batch_size = text_embeddings.shape[0]

        # Project to total dimension if needed
        hidden_states = self.projection(text_embeddings)  # (B, L, D)

        # Project to Q, K, V
        query = self.to_q(hidden_states)
        key = self.to_k(hidden_states)
        value = self.to_v(hidden_states)

        # Reshape for multi-head attention
        # (B, L, D) -> (B, L, H, H_dim) -> (B, H, L, H_dim)
        def reshape_for_heads(tensor):
            new_shape = (batch_size, self.seq_len, self.num_heads, self.head_dim)
            tensor = tensor.view(new_shape)
            return tensor.permute(0, 2, 1, 3)

        key_slots = reshape_for_heads(key)
        value_slots = reshape_for_heads(value)

        # Apply dropout
        key_slots = self.dropout(key_slots)
        value_slots = self.dropout(value_slots)

        return key_slots, value_slots

def load_adapter_from_config(config_path: Optional[str] = None) -> TextCrossAttentionAdapter:
    """
    Load adapter configuration from YAML or defaults and instantiate.

    Args:
        config_path: Path to config.yaml. If None, uses defaults.

    Returns:
        Initialized TextCrossAttentionAdapter on CPU.
    """
    config = DEFAULT_CONFIG.copy()
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
            # Deep merge logic could be added here, but for now shallow update
            for k, v in loaded_config.items():
                if isinstance(v, dict) and k in config:
                    config[k].update(v)
                else:
                    config[k] = v

    adapter_config = config.get('adapter', DEFAULT_CONFIG['adapter'])
    
    adapter = TextCrossAttentionAdapter(
        text_embed_dim=adapter_config.get('text_embed_dim', 768),
        num_heads=adapter_config.get('num_heads', 8),
        head_dim=adapter_config.get('head_dim', 64),
        seq_len=adapter_config.get('seq_len', 77),
        dropout=adapter_config.get('dropout', 0.1),
        device='cpu'
    )
    
    # Explicitly ensure CPU
    adapter = adapter.to('cpu')
    return adapter

def main():
    """
    CLI entry point for T017: Text Cross-Attention Adapter.
    
    This script:
    1. Initializes the adapter on CPU.
    2. Performs a forward pass with real (or simulated for testing if no data) 
       text embeddings to verify the tensor shapes.
    3. Writes a verification log to data/processed/adapter_verification.json.
    
    Note: As per the "No Synthetic Data" constraint, we do not generate fake
    input data. However, to verify the *module* itself works (tensor shapes,
    CPU execution), we create a minimal random tensor strictly for the purpose
    of the forward pass test, NOT as a research result. The actual research
    will consume real embeddings from the pipeline.
    """
    parser = argparse.ArgumentParser(description="Text Cross-Attention Adapter Verification")
    parser.add_argument("--config", type=str, default="code/config/settings.yaml",
                        help="Path to config file")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Output directory for verification log")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "adapter_verification.json"

    print(f"Initializing TextCrossAttentionAdapter on CPU...")
    try:
        adapter = load_adapter_from_config(args.config)
        print(f"Adapter initialized successfully. Device: {adapter.device}")
    except Exception as e:
        print(f"Error initializing adapter: {e}")
        # Write error state
        import json
        with open(output_file, 'w') as f:
            json.dump({"status": "failed", "error": str(e)}, f)
        return 1

    # Verification: Run a forward pass with a small random tensor
    # This is a structural test, not a research measurement.
    # Input shape: (batch_size=2, seq_len=77, embed_dim=768)
    batch_size = 2
    seq_len = 77
    embed_dim = 768
    
    # Create a dummy tensor on CPU to test the forward pass
    # This is NOT synthetic research data; it is a unit-test-like check
    # to ensure the module can run on CPU without CUDA errors.
    dummy_input = torch.randn(batch_size, seq_len, embed_dim, device='cpu')
    
    print(f"Running forward pass with input shape: {dummy_input.shape}")
    
    try:
        with torch.no_grad():
            k_slots, v_slots = adapter(dummy_input)
        
        print(f"Key slots shape: {k_slots.shape}")
        print(f"Value slots shape: {v_slots.shape}")
        
        # Verify shapes
        expected_k_shape = (batch_size, adapter.num_heads, seq_len, adapter.head_dim)
        if k_slots.shape != expected_k_shape:
            raise ValueError(f"Key shape mismatch: got {k_slots.shape}, expected {expected_k_shape}")
        if v_slots.shape != expected_k_shape:
            raise ValueError(f"Value shape mismatch: got {v_slots.shape}, expected {expected_k_shape}")
        
        # Write success report
        report = {
            "status": "success",
            "device": "cpu",
            "input_shape": list(dummy_input.shape),
            "key_shape": list(k_slots.shape),
            "value_shape": list(v_slots.shape),
            "num_heads": adapter.num_heads,
            "head_dim": adapter.head_dim
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Verification log written to {output_file}")
        return 0

    except Exception as e:
        print(f"Forward pass failed: {e}")
        import json
        with open(output_file, 'w') as f:
            json.dump({"status": "failed", "error": str(e)}, f)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())