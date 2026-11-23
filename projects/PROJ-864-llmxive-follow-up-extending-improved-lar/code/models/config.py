"""
Model configuration management for llmXive.

Calculates and exposes feasible model parameters for CPU execution.
Uses binary search to find maximum model dimensions within RAM constraints.
"""
from typing import Dict, Any, Optional
import math
import torch
import psutil
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, load_config


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


# Default configuration values
_DEFAULT_CONFIG = {
    'vocab_size': 50257,  # GPT-2 vocab size
    'embed_dim': 256,     # Feasible embed dim for CPU (T008 calculation)
    'num_heads': 4,       # Feasible heads
    'num_layers': 4,      # Feasible layers
    'max_seq_length': 512,
    'learning_rate': 3e-4,
    'batch_size': 8,
    'num_epochs': 100,
    'dropout': 0.1,
    'weight_decay': 0.01,
    'warmup_steps': 100,
}

# Runtime configuration store
_config_store: Dict[str, Any] = _DEFAULT_CONFIG.copy()

# Feasibility results store
_feasibility_results: Dict[str, int] = {
    'max_embed_dim': 256,
    'max_num_layers': 4,
    'max_params': 0
}


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config_store
    _config_store = _DEFAULT_CONFIG.copy()


def set_config(key: str, value: Any) -> None:
    """Set a configuration value."""
    _config_store[key] = value


def get_model_config() -> Dict[str, Any]:
    """Return the full model configuration dictionary."""
    return _config_store.copy()


def get_embed_dim() -> int:
    """Get embedding dimension."""
    return _config_store.get('embed_dim', 256)


def get_num_heads() -> int:
    """Get number of attention heads."""
    return _config_store.get('num_heads', 4)


def get_num_layers() -> int:
    """Get number of transformer layers."""
    return _config_store.get('num_layers', 4)


def get_vocab_size() -> int:
    """Get vocabulary size."""
    return _config_store.get('vocab_size', 50257)


def get_max_seq_length() -> int:
    """Get maximum sequence length."""
    return _config_store.get('max_seq_length', 512)


def get_learning_rate() -> float:
    """Get learning rate."""
    return _config_store.get('learning_rate', 3e-4)


def get_batch_size() -> int:
    """Get batch size."""
    return _config_store.get('batch_size', 8)


def get_num_epochs() -> int:
    """Get number of epochs."""
    return _config_store.get('num_epochs', 100)


def get_dropout() -> float:
    """Get dropout rate."""
    return _config_store.get('dropout', 0.1)


def get_weight_decay() -> float:
    """Get weight decay."""
    return _config_store.get('weight_decay', 0.01)


def get_warmup_steps() -> int:
    """Get warmup steps."""
    return _config_store.get('warmup_steps', 100)


def _estimate_model_params(embed_dim: int, num_heads: int, num_layers: int, vocab_size: int, max_seq_length: int) -> int:
    """
    Estimate the number of parameters in a transformer model.
    
    Simplified estimation based on standard transformer architecture:
    - Embedding: vocab_size * embed_dim
    - Per layer: 
      - Attention: 4 * embed_dim^2 (Q, K, V, O projections)
      - MLP: 4 * embed_dim * embed_dim (usually 4x expansion)
      - Layer norms and biases are negligible for large models
    - Final layer: embed_dim * vocab_size
    """
    # Token and position embeddings
    embed_params = vocab_size * embed_dim + max_seq_length * embed_dim
    
    # Per transformer layer parameters
    # Attention mechanism: Q, K, V, O projections (4 * embed_dim^2)
    # Plus bias terms (4 * embed_dim)
    attention_params = 4 * (embed_dim * embed_dim) + 4 * embed_dim
    
    # MLP block: typically 4x expansion (embed_dim * 4 * embed_dim * 2 for two linear layers)
    mlp_params = 2 * (embed_dim * 4 * embed_dim) + 2 * (embed_dim * 4)
    
    # Layer norms (2 per layer, embed_dim params each)
    layer_norm_params = 2 * embed_dim * 2  # 2 layers per transformer block
    
    per_layer_params = attention_params + mlp_params + layer_norm_params
    
    # Total for all layers
    layer_params = num_layers * per_layer_params
    
    # Final projection to vocabulary
    final_params = embed_dim * vocab_size + vocab_size
    
    total_params = embed_params + layer_params + final_params
    
    return total_params


def _measure_ram_for_config(embed_dim: int, num_heads: int, num_layers: int) -> float:
    """
    Measure RAM usage for a dummy tensor allocation representing model parameters.
    
    Returns RAM usage in GB.
    """
    vocab_size = get_vocab_size()
    max_seq_length = get_max_seq_length()
    
    # Estimate parameters
    num_params = _estimate_model_params(embed_dim, num_heads, num_layers, vocab_size, max_seq_length)
    
    # Estimate memory: 4 bytes per parameter (float32) + overhead
    # Add 20% overhead for activations and temporary buffers
    estimated_bytes = num_params * 4 * 1.2
    estimated_gb = estimated_bytes / (1024 ** 3)
    
    # Actual measurement via dummy tensor allocation
    try:
        # Create a dummy tensor to simulate memory usage
        # Use float32 (4 bytes per element)
        dummy_size = int(num_params * 1.2)  # 20% overhead
        
        # Allocate in chunks to avoid OOM
        chunk_size = 100_000_000  # 100M elements at a time
        total_allocated = 0
        
        while total_allocated < dummy_size:
            current_chunk = min(chunk_size, dummy_size - total_allocated)
            dummy_tensor = torch.zeros(current_chunk, dtype=torch.float32)
            total_allocated += current_chunk
            
            # Force garbage collection
            del dummy_tensor
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
        # Measure actual RAM usage
        process = psutil.Process(os.getpid())
        ram_gb = process.memory_info().rss / (1024 ** 3)
        
        return ram_gb
        
    except (MemoryError, RuntimeError) as e:
        # If allocation fails, return a high value to indicate OOM
        return 999.0


def _binary_search_feasible_config(target_ram_gb: float = 6.0) -> Dict[str, int]:
    """
    Binary search to find maximum embed_dim and num_layers within RAM constraint.
    
    Args:
        target_ram_gb: Maximum allowed RAM usage in GB (default 6.0)
        
    Returns:
        Dictionary with max_embed_dim, max_num_layers, and max_params
    """
    # Search ranges
    embed_dim_options = [128, 256, 384, 512, 768, 1024]
    num_layers_options = [2, 4, 6, 8, 12, 16]
    
    best_embed_dim = 128
    best_num_layers = 2
    best_params = _estimate_model_params(best_embed_dim, 4, best_num_layers, 
                                       get_vocab_size(), get_max_seq_length())
    
    print("Starting feasibility calculation...")
    print(f"Target RAM limit: {target_ram_gb} GB")
    print(f"Vocab size: {get_vocab_size()}")
    print(f"Max seq length: {get_max_seq_length()}")
    print("-" * 50)
    
    # Test all combinations
    for embed_dim in embed_dim_options:
        for num_layers in num_layers_options:
            try:
                ram_usage = _measure_ram_for_config(embed_dim, 4, num_layers)
                num_params = _estimate_model_params(embed_dim, 4, num_layers, 
                                                  get_vocab_size(), get_max_seq_length())
                
                print(f"embed_dim={embed_dim}, layers={num_layers}: "
                      f"RAM={ram_usage:.2f} GB, Params={num_params:,}")
                
                if ram_usage <= target_ram_gb and num_params > best_params:
                    best_embed_dim = embed_dim
                    best_num_layers = num_layers
                    best_params = num_params
                    
            except Exception as e:
                print(f"embed_dim={embed_dim}, layers={num_layers}: Failed - {e}")
    
    print("-" * 50)
    print(f"Feasible configuration: embed_dim={best_embed_dim}, "
          f"num_layers={best_num_layers}, params={best_params:,}")
    
    return {
        'max_embed_dim': best_embed_dim,
        'max_num_layers': best_num_layers,
        'max_params': best_params
    }


def calculate_feasibility(target_ram_gb: float = 6.0) -> Dict[str, int]:
    """
    Public API to calculate feasible model configuration.
    
    Args:
        target_ram_gb: Maximum allowed RAM usage in GB
        
    Returns:
        Dictionary with max_embed_dim, max_num_layers, and max_params
    """
    global _feasibility_results
    _feasibility_results = _binary_search_feasible_config(target_ram_gb)
    
    # Update the config store with feasible values
    set_config('embed_dim', _feasibility_results['max_embed_dim'])
    set_config('num_layers', _feasibility_results['max_num_layers'])
    
    return _feasibility_results.copy()


def get_feasibility_results() -> Dict[str, int]:
    """Get the results of the feasibility calculation."""
    return _feasibility_results.copy()


def main():
    """Main entry point for feasibility calculation."""
    # Load project root and setup
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # Try to load existing config if available
    try:
        config_path = project_root / 'code' / 'config.yaml'
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if 'model_params' in config:
                    print(f"Using model params from config: {config['model_params']}")
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
    
    # Calculate feasibility
    results = calculate_feasibility(target_ram_gb=6.0)
    
    print("\nFinal Feasibility Results:")
    print(f"  Max Embed Dim: {results['max_embed_dim']}")
    print(f"  Max Num Layers: {results['max_num_layers']}")
    print(f"  Max Params: {results['max_params']:,}")
    
    return results


if __name__ == "__main__":
    main()