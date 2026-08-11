import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import signal

# Timeout handling
class TimeoutError(Exception):
    pass

def signal_handler(signum, frame):
    raise TimeoutError("Training cycle timed out")

def run_training_cycle_with_timeout(timeout_seconds: int, func, *args, **kwargs):
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(timeout_seconds)
    try:
        return func(*args, **kwargs)
    finally:
        signal.alarm(0)

def run_epoch_with_timeout_logic(model, dataloader, optimizer, criterion, device, timeout_seconds=60):
    model.train()
    total_loss = 0.0
    start_time = time.time()
    
    # Check for timeout before every batch in a real implementation would require
    # more granular signal handling or threading, but for this scope we check periodically
    for batch_idx, batch in enumerate(dataloader):
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError("Epoch timed out")
        
        inputs, labels = batch
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def count_flops(model: nn.Module, input_shape: Tuple[int, ...], device: torch.device = torch.device('cpu')) -> int:
    """
    Counts the theoretical FLOPs (Floating Point Operations) for a forward pass of the model
    given a specific input shape.
    
    This implementation uses a simplified counting strategy based on known layer types
    (Linear, Conv2d, Attention-like structures) to avoid external dependencies like `thop`
    which might not be installed. It calculates MACs (Multiply-Accumulates) * 2.
    
    Args:
        model: The PyTorch model to analyze.
        input_shape: Tuple representing the input tensor shape (e.g., (batch, seq_len, hidden_dim)).
        device: Device to run the dummy forward pass (CPU preferred for counting).
    
    Returns:
        int: Estimated total FLOPs for one forward pass.
    """
    if not isinstance(model, nn.Module):
        raise TypeError("Model must be an instance of nn.Module")
    
    total_flops = 0
    
    # Create a dummy input
    dummy_input = torch.randn(1, *input_shape).to(device)
    
    def count_linear_flops(module, input, output):
        # Linear layer: out_features * in_features * batch_size (MACs) * 2 (FLOPs)
        # input[0] is input tensor, output is output tensor
        if len(input) > 0 and input[0].dim() > 0:
            batch_size = input[0].shape[0]
            in_features = input[0].shape[-1]
            out_features = output.shape[-1]
            # MACs = batch * seq * in * out (if 2D) or batch * out * in
            # Standard Linear: y = xW^T + b
            # FLOPs = 2 * in_features * out_features * batch_size (assuming 2D input)
                    # If input is (B, S, H), output is (B, S, H_out)
                    # FLOPs = 2 * S * H * H_out * B
            if input[0].dim() == 3:
                seq_len = input[0].shape[1]
                total_flops += 2 * batch_size * seq_len * in_features * out_features
            elif input[0].dim() == 2:
                total_flops += 2 * batch_size * in_features * out_features

    def count_conv2d_flops(module, input, output):
        if len(input) > 0:
            batch_size = input[0].shape[0]
            in_channels = input[0].shape[1]
            out_channels = module.out_channels
            kH, kW = module.kernel_size
            H_out, W_out = output.shape[2], output.shape[3]
            # FLOPs = 2 * in_channels * kH * kW * H_out * W_out * batch_size
            total_flops += 2 * in_channels * kH * kW * H_out * W_out * batch_size

    def count_attention_flops(module, input, output):
        # Simplified attention FLOP count:
        # Q, K, V projections: 3 * (2 * H * H) * B * S
        # QK^T: 2 * (B * H * S) * (H * S) -> 2 * B * H * S^2
        # Softmax: ~S * B * H (negligible compared to matmul)
        # Attention * V: 2 * (B * H * S) * (H * S) -> 2 * B * H * S^2
        # Total approx: 2 * B * S^2 * H + 3 * 2 * B * S * H^2
        if hasattr(module, 'num_heads') and hasattr(module, 'head_dim'):
            B, S, H = input[0].shape
            num_heads = module.num_heads
            head_dim = module.head_dim
            # Projections
            total_flops += 3 * (2 * H * H) * B * S
            # QK^T
            total_flops += 2 * B * num_heads * S * S
            # Attention * V
            total_flops += 2 * B * num_heads * S * S

    # Register hooks
    hooks = []
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            hooks.append(module.register_forward_hook(count_linear_flops))
        elif isinstance(module, nn.Conv2d):
            hooks.append(module.register_forward_hook(count_conv2d_flops))
        # We assume standard GPT blocks have specific attention modules or we count Linear inside them
        # If the model has a custom Attention module, we might need to register it specifically
        # For now, we rely on the Linear layers within the attention block to count the bulk of attention FLOPs
        # (Q, K, V, O projections) which are Linear layers.
        # The matmul operations (QK^T, Attn*V) are often explicit in the forward pass.
        # To capture explicit matmuls, we can hook the torch.matmul or count manually if structure is known.
        # However, for a generic count without knowing internal structure:
        # We will rely on the fact that most attention logic is Linear layers + explicit matmul.
        # We will add a hook for explicit matmul if we can, but that's tricky without wrapping torch.
        # A robust way for GPT is to count Linear layers and assume standard attention complexity.
        # Given the constraints, we will count Linear layers which covers 3/4 of attention FLOPs (projections)
        # and the MLP. The QK^T and Attn*V matmuls are significant.
        # Let's try to hook the model's forward pass to catch explicit matmuls if we can't rely on structure.
        # But for a generic "count_flops" function that works on any model, we usually use a library.
        # Since we can't import thop, we will implement a simplified version that counts Linear and Conv2d
        # and adds a heuristic for attention if the module is named 'attention' or similar.
    
    # Heuristic: If the model has 'attention' or 'attn' modules, we estimate their FLOPs
    # This is a simplification. A true count requires tracing the graph.
    # We will perform a dummy forward pass and count operations by wrapping functions? No, too slow.
    # We will stick to counting parameters * input_size for Linear layers as a proxy for FLOPs in dense layers,
    # and add a specific check for the GPT block structure if possible.
    
    # Alternative: Use a simple recursive count based on known layer types.
    # We will re-implement a simple walker.
    
    def walk_and_count(module, input_shape):
        local_flops = 0
        if isinstance(module, nn.Linear):
            # input_shape is (B, S, H) -> output (B, S, H_out)
            # FLOPs = 2 * B * S * H * H_out
            if len(input_shape) == 3:
                B, S, H = input_shape
                H_out = module.out_features
                local_flops += 2 * B * S * H * H_out
            elif len(input_shape) == 2:
                B, H = input_shape
                H_out = module.out_features
                local_flops += 2 * B * H * H_out
        elif isinstance(module, nn.Conv2d):
            B = input_shape[0]
            C_in = input_shape[1]
            H_in, W_in = input_shape[2], input_shape[3]
            kH, kW = module.kernel_size
            H_out = (H_in + 2 * module.padding[0] - kH) // module.stride[0] + 1
            W_out = (W_in + 2 * module.padding[1] - kW) // module.stride[1] + 1
            local_flops += 2 * B * module.out_channels * kH * kW * H_out * W_out
        
        # Recurse
        child_flops = 0
        new_input_shape = input_shape
        if isinstance(module, nn.Linear):
            if len(input_shape) == 3:
                new_input_shape = (input_shape[0], input_shape[1], module.out_features)
            elif len(input_shape) == 2:
                new_input_shape = (input_shape[0], module.out_features)
        elif isinstance(module, nn.Conv2d):
            B, C, H, W = input_shape
            kH, kW = module.kernel_size
            H_out = (H + 2 * module.padding[0] - kH) // module.stride[0] + 1
            W_out = (W + 2 * module.padding[1] - kW) // module.stride[1] + 1
            new_input_shape = (B, module.out_channels, H_out, W_out)
        
        for child in module.children():
            child_flops += walk_and_count(child, new_input_shape)
        
        return local_flops + child_flops

    # Start the walk
    # Input to the model is (B, S, H) usually for GPT
    if len(input_shape) == 1:
        # If input_shape is just (seq_len,), assume batch=1, hidden=1? No, usually (B, S) or (B, S, H)
        # We expect input_shape to match the model's expected input.
        # If the model expects (B, S), we assume hidden dimension is handled internally or is 1?
        # Let's assume the caller passes the correct shape for the first layer.
        pass
    
    # We need to know the hidden size of the first layer to propagate.
    # If the model is a GPT, the first layer is usually an Embedding.
    # We cannot count Embedding FLOPs easily without knowing the embedding size.
    # Let's assume the input_shape includes the hidden dimension if the first layer is Linear.
    # If the first layer is Embedding, we need to know the embedding dimension.
    # This function is a heuristic. For GPT-124M, we can assume standard structure.
    
    # Let's try a different approach: Use the `torch.jit.trace` to get a graph and count?
    # Too complex for this scope.
    # We will implement a basic walker that counts Linear and Conv2d.
    # For GPT, the bulk of FLOPs are in Linear layers (Attention projections and MLP).
    # We will assume the input_shape is (B, S, H) where H is the hidden size.
    
    # If the model starts with an Embedding, we can't count it without knowing embed_dim.
    # We will assume the model passed is already the transformer part or we handle Embedding.
    # Let's add Embedding support.
    
    def walk_and_count_v2(module, input_shape):
        local_flops = 0
        if isinstance(module, nn.Linear):
            if len(input_shape) == 3:
                B, S, H = input_shape
                H_out = module.out_features
                local_flops += 2 * B * S * H * H_out
            elif len(input_shape) == 2:
                B, H = input_shape
                H_out = module.out_features
                local_flops += 2 * B * H * H_out
        elif isinstance(module, nn.Conv2d):
            B, C, H, W = input_shape
            kH, kW = module.kernel_size
            H_out = (H + 2 * module.padding[0] - kH) // module.stride[0] + 1
            W_out = (W + 2 * module.padding[1] - kW) // module.stride[1] + 1
            local_flops += 2 * B * module.out_channels * kH * kW * H_out * W_out
        elif isinstance(module, nn.Embedding):
            # FLOPs for embedding lookup: B * S * log(V) ? No, it's memory access.
            # Often counted as 0 or B * S * H (to copy). We'll count 0 or B*S*H.
            # Let's count it as B * S * H_out where H_out is embedding_dim
            if len(input_shape) == 2:
                B, S = input_shape
                H_out = module.embedding_dim
                local_flops += B * S * H_out # Approximation
            elif len(input_shape) == 3:
                B, S, _ = input_shape
                H_out = module.embedding_dim
                local_flops += B * S * H_out
        
        new_input_shape = input_shape
        if isinstance(module, nn.Linear):
            if len(input_shape) == 3:
                new_input_shape = (input_shape[0], input_shape[1], module.out_features)
            elif len(input_shape) == 2:
                new_input_shape = (input_shape[0], module.out_features)
        elif isinstance(module, nn.Conv2d):
            B, C, H, W = input_shape
            kH, kW = module.kernel_size
            H_out = (H + 2 * module.padding[0] - kH) // module.stride[0] + 1
            W_out = (W + 2 * module.padding[1] - kW) // module.stride[1] + 1
            new_input_shape = (B, module.out_channels, H_out, W_out)
        elif isinstance(module, nn.Embedding):
            if len(input_shape) == 2:
                B, S = input_shape
                new_input_shape = (B, S, module.embedding_dim)
            elif len(input_shape) == 3:
                B, S, _ = input_shape
                new_input_shape = (B, S, module.embedding_dim)
        
        child_flops = 0
        for child in module.children():
            child_flops += walk_and_count_v2(child, new_input_shape)
        
        return local_flops + child_flops

    return walk_and_count_v2(model, input_shape)

def get_model_param_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, 
                criterion: nn.Module, device: torch.device, epoch: int) -> float:
    model.train()
    total_loss = 0.0
    for batch_idx, batch in enumerate(dataloader):
        inputs, labels = batch
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def run_training_cycle(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer,
                       criterion: nn.Module, device: torch.device, epochs: int = 1) -> Dict[str, float]:
    losses = []
    for epoch in range(epochs):
        epoch_loss = train_epoch(model, dataloader, optimizer, criterion, device, epoch)
        losses.append(epoch_loss)
    return {"epoch_losses": losses, "avg_loss": sum(losses)/len(losses)}
