import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math

def count_flops(model: nn.Module, input_ids: torch.Tensor) -> int:
    """
    Count the approximate number of FLOPs for a single forward pass of the model
    on the given input_ids tensor.
    
    This implementation focuses on the GPT-124M architecture components:
    - Embedding layer (lookup is negligible, but we count the projection if applicable)
    - Transformer blocks (Self-Attention + MLP)
    
    Approximation logic for GPT-like models:
    1. Self-Attention per layer:
       - Q, K, V projections: 3 * (hidden_size * hidden_size) * seq_len
       - Attention scores: hidden_size * seq_len * seq_len
       - Softmax + Weighted Sum: 2 * hidden_size * seq_len * seq_len
       - Output projection: hidden_size * hidden_size * seq_len
       Total per layer ~ 8 * hidden_size * seq_len^2 + 4 * hidden_size^2 * seq_len
    
    2. MLP per layer (usually 4x expansion):
       - Up projection: hidden_size * (4 * hidden_size) * seq_len
       - Down projection: (4 * hidden_size) * hidden_size * seq_len
       Total per layer ~ 8 * hidden_size^2 * seq_len
    
    3. Embedding:
       - Usually lookup, but if we consider the full matrix size for potential
         updates or just the parameter count contribution: vocab_size * hidden_size.
         For FLOPs in forward pass (lookup), it's effectively 0 arithmetic ops,
         but we might count the parameter access or ignore it. 
         Standard practice for "compute" FLOPs often ignores embedding lookups 
         as they are memory bound, but for a full "model cost" metric, we can 
         include the parameter count contribution or ignore. 
         We will focus on the arithmetic FLOPs of the transformer blocks.
    
    Note: This is an analytical estimate based on model structure, not a 
    runtime hook measurement (which would require `fvcore` or `thop` and 
    is heavier).
    
    Args:
        model: The GPT model instance.
        input_ids: Input tensor of shape (batch_size, seq_len).
    
    Returns:
        Estimated total FLOPs for the forward pass.
    """
    if not isinstance(model, torch.nn.Module):
        raise TypeError("model must be a torch.nn.Module")
    
    # Ensure input is on CPU for calculation if necessary, though we just need shapes
    batch_size, seq_len = input_ids.shape
    
    total_flops = 0
    
    # Iterate over model modules to find transformer blocks
    # Assuming standard GPT structure with 'transformer.h' or similar
    # We look for modules that look like TransformerBlocks
    
    # Heuristic: Count parameters and infer operations based on standard GPT formulas
    # Standard GPT-124M has:
    # n_layer, n_embd, n_head, vocab_size
    
    n_layer = 0
    n_embd = 0
    
    # Try to extract architecture details
    if hasattr(model, 'config'):
        n_layer = getattr(model.config, 'n_layer', 0)
        n_embd = getattr(model.config, 'n_embd', 0)
    elif hasattr(model, 'transformer'):
        if hasattr(model.transformer, 'h'):
            n_layer = len(model.transformer.h)
            # Get hidden size from first layer
            if len(model.transformer.h) > 0:
                block = model.transformer.h[0]
                if hasattr(block, 'ln_1'):
                    # Infer from linear layers in attention or mlp
                    # Usually ln_1 is LayerNorm, not linear.
                    # Look at the attention module
                    if hasattr(block, 'attn'):
                        if hasattr(block.attn, 'c_attn'):
                            # c_attn is usually 3 * n_embd x n_embd
                            # But we need n_embd.
                            # Let's try to get it from the weight shape of a known linear layer
                            for name, param in block.named_parameters():
                                if 'c_proj' in name or 'c_fc' in name:
                                    # c_proj: n_embd x n_embd
                                    # c_fc: 4*n_embd x n_embd
                                    dim = param.shape[0]
                                    if 'c_fc' in name:
                                        n_embd = dim // 4
                                    else:
                                        n_embd = dim
                                    break
                    if n_embd == 0 and hasattr(block, 'ln_2'):
                        # Fallback: check mlp
                        if hasattr(block, 'mlp'):
                            for name, param in block.mlp.named_parameters():
                                if 'c_fc' in name:
                                    n_embd = param.shape[1]
                                    break
    
    if n_layer == 0 or n_embd == 0:
        # Fallback: try to infer from total params or just use a default if we can't find it
        # This is a robustness measure. If we can't find the config, we can't estimate accurately.
        # However, for GPT-124M, we expect to find these.
        # If not, we return 0 or raise an error? Let's try to infer from the first linear layer found.
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Assume standard GPT structure: first linear in block is c_attn or c_proj
                # We need to guess n_embd. 
                # Let's assume the input dimension is n_embd.
                n_embd = module.in_features
                # We need n_layer. Hard to guess without config.
                # We will count total linear params and divide by approx params per layer?
                # No, that's too noisy.
                # Let's just count FLOPs based on the layers we can see.
                # This is tricky. Let's assume the model is GPT-124M if we can't find config.
                # But the task says "accurate FLOP measurement".
                # Let's assume we can find n_layer and n_embd.
                pass
        if n_layer == 0:
            # If we still don't know, we might have to scan for blocks.
            # Count how many blocks we found.
            # This is getting too complex for a heuristic. 
            # Let's assume the model passed is a standard GPT with config.
            # If not, we return 0 and log a warning?
            # For the sake of this implementation, we assume valid GPT structure.
            pass

    # If we successfully extracted n_layer and n_embd:
    if n_layer > 0 and n_embd > 0:
        # FLOPs per layer (Forward Pass only)
        # Attention:
        # Q, K, V: 3 * (n_embd * n_embd) * seq_len
        # Attention Matrix: n_embd * seq_len * seq_len (matmul Q*Kt)
        # Softmax + Weighted Sum: 2 * n_embd * seq_len * seq_len (approx)
        # Output Proj: n_embd * n_embd * seq_len
        # Total Attention ~ 4 * n_embd * n_embd * seq_len + 3 * n_embd * seq_len^2
        
        # MLP:
        # Up: n_embd * (4*n_embd) * seq_len
        # Down: (4*n_embd) * n_embd * seq_len
        # Total MLP ~ 8 * n_embd * n_embd * seq_len
        
        # Total per layer ~ 12 * n_embd^2 * seq_len + 3 * n_embd * seq_len^2
        
        flops_per_layer = (12 * n_embd * n_embd * seq_len) + (3 * n_embd * seq_len * seq_len)
        total_flops = n_layer * flops_per_layer
        
        # Add Embedding FLOPs? 
        # Embedding is a lookup. In FLOPs counting for compute, it's often 0.
        # But if we consider the parameter access as cost, it's not FLOPs.
        # We'll stick to arithmetic FLOPs.
        
        # Add LM Head FLOPs?
        # LM Head: n_vocab * n_embd * seq_len
        # If model has lm_head
        if hasattr(model, 'lm_head') and isinstance(model.lm_head, nn.Linear):
            n_vocab = model.lm_head.out_features
            total_flops += n_vocab * n_embd * seq_len
        
        # Multiply by batch size?
        # The input_ids is (batch_size, seq_len).
        # The operations above are per token.
        # So we multiply by batch_size.
        total_flops *= batch_size
    else:
        # Fallback: If we can't parse the architecture, we try a parameter-based heuristic.
        # Total Params ~ 124M for GPT-124M.
        # FLOPs per token ~ 2 * Params (for forward pass in dense models).
        # This is a very rough estimate.
        # Let's count total params in the model.
        total_params = sum(p.numel() for p in model.parameters())
        # Approx FLOPs = 2 * Params * batch_size * seq_len
        total_flops = 2 * total_params * batch_size * seq_len
    
    return total_flops

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    max_steps: Optional[int] = None
) -> Dict[str, float]:
    """
    Train the model for one epoch.
    
    Args:
        model: The model to train.
        dataloader: DataLoader for the training dataset.
        optimizer: Optimizer instance.
        epoch: Current epoch number.
        max_steps: Optional limit on the number of update steps.
    
    Returns:
        Dictionary containing training metrics (loss, time, etc.).
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    start_time = time.time()
    
    for step, batch in enumerate(dataloader):
        if max_steps is not None and step >= max_steps:
            break
        
        input_ids = batch['input_ids']
        labels = batch['labels']
        
        # Forward pass
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping (optional but recommended)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    end_time = time.time()
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    elapsed_time = end_time - start_time
    
    return {
        "epoch": epoch,
        "loss": avg_loss,
        "time_seconds": elapsed_time,
        "batches_processed": num_batches
    }

def run_training_cycle(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    cycle_num: int = 0
) -> Dict[str, Any]:
    """
    Execute a full training cycle (one epoch) and return metrics.
    
    Args:
        model: The model to train.
        train_loader: Training data loader.
        optimizer: Optimizer.
        scheduler: Learning rate scheduler (optional).
        cycle_num: Cycle identifier.
    
    Returns:
        Dictionary with cycle results.
    """
    # Train one epoch
    metrics = train_epoch(model, train_loader, optimizer, epoch=cycle_num)
    
    # Update scheduler if present
    if scheduler is not None:
        scheduler.step()
    
    return metrics