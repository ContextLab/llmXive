import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, Any
import snnTorch as sntorch
from snnTorch import surrogate

# Configuration constants
LIF_TIME_CONSTANT = 0.5  # Tau for Leaky Integrate-and-Fire
SURROGATE_GRADIENT_SIGMOID = 'sigmoid'
NUM_TIME_STEPS = 4  # Unrolling steps for surrogate gradient learning

class SpikingFeedForward(nn.Module):
    """
    Replaces the standard Feed-Forward Network (FFN) in a Transformer layer
    with a Spiking Neural Network (SNN) variant using Leaky Integrate-and-Fire (LIF) neurons.
    
    Implements surrogate-gradient learning as per FR-005.
    """
    def __init__(self, d_model: int, d_ff: int, spike_grad: str = SURROGATE_GRADIENT_SIGMOID):
        super().__init__()
        self.d_model = d_model
        self.d_ff = d_ff
        
        # Linear projections
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        
        # LIF Neurons
        # We use snnTorch's LIF which supports surrogate gradients
        self.lif1 = sntorch.LifCell(
            beta=LIF_TIME_CONSTANT,
            surrogate_grad_fn=spike_grad,
            spike_grad_fn_kwargs={'beta': 1.0}
        )
        self.lif2 = sntorch.LifCell(
            beta=LIF_TIME_CONSTANT,
            surrogate_grad_fn=spike_grad,
            spike_grad_fn_kwargs={'beta': 1.0}
        )
        
        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.zeros_(self.fc1.bias)
        nn.init.xavier_uniform_(self.fc2.weight)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through the spiking feed-forward network.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
        
        Returns:
            output: Final output tensor (batch_size, seq_len, d_model)
            spikes: The spike train from the second LIF layer (for analysis)
        """
        batch_size, seq_len, d_model = x.shape
        
        # Flatten to (batch_size * seq_len, d_model) for cell processing
        x_flat = x.view(-1, d_model)
        
        # Step 1: First Linear -> LIF activation
        # We need to unroll over time steps for surrogate gradient learning
        # snnTorch LIFCell expects input and returns (spike, membrane_potential)
        
        # Initialize membrane potential
        mem1 = torch.zeros_like(x_flat)
        
        # We will accumulate spikes over time steps
        # For simplicity in this implementation, we treat the FFN as a single
        # time-step operation but use the surrogate gradient mechanism.
        # However, to strictly follow SNN dynamics, we unroll.
        
        # Since this is a feed-forward layer within a transformer, we usually
        # want the "steady state" or a specific unrolling. 
        # We'll do a single effective unroll step that mimics the dynamics
        # but allows gradient flow via surrogate.
        
        # Apply Linear 1
        x_pre = self.fc1(x_flat)
        
        # Apply LIF dynamics
        # snnTorch LIFCell: (input, mem) -> (spike, mem)
        # We simulate one step of integration and fire
        spike1, mem1 = self.lif1(x_pre, mem1)
        
        # Apply Linear 2
        x_pre2 = self.fc2(spike1)
        
        # Apply LIF dynamics again
        spike2, mem2 = self.lif2(x_pre2, mem1) # Note: mem2 is updated internally but we return it
        
        # Reshape back to (batch_size, seq_len, d_model)
        output = spike2.view(batch_size, seq_len, d_model)
        
        return output, spike2

class SpikingTransformerEncoderLayer(nn.Module):
    """
    A single encoder layer for the Spiking Transformer.
    Replaces the standard Feed-Forward sub-layer with SpikingFeedForward.
    """
    def __init__(self, d_model: int, nhead: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        
        # Replace standard FFN with Spiking FFN
        self.ffn = SpikingFeedForward(d_model, d_ff)

    def forward(
        self, 
        src: torch.Tensor, 
        src_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            src: Tensor of shape (batch, seq_len, d_model)
            src_mask: Optional mask for attention
            src_key_padding_mask: Optional mask for padding
        
        Returns:
            output: Processed tensor
            spikes: The spike train from the internal FFN (for logging)
        """
        # Self-Attention with residual
        attn_output, _ = self.self_attn(
            src, src, src,
            attn_mask=src_mask,
            key_padding_mask=src_key_padding_mask
        )
        src = src + self.dropout(attn_output)
        src = self.norm1(src)

        # Spiking Feed-Forward with residual
        ffn_output, spikes = self.ffn(src)
        src = src + self.dropout(ffn_output)
        src = self.norm2(src)

        return src, spikes

class SpikingTransformer(nn.Module):
    """
    The full Spiking Transformer model.
    """
    def __init__(
        self, 
        vocab_size: int, 
        d_model: int, 
        nhead: int, 
        num_layers: int, 
        d_ff: int, 
        dropout: float = 0.1,
        max_seq_len: int = 256
    ):
        super().__init__()
        self.d_model = d_model
        
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = nn.Parameter(torch.randn(1, max_seq_len, d_model) * 0.1)
        
        layers = [
            SpikingTransformerEncoderLayer(d_model, nhead, d_ff, dropout)
            for _ in range(num_layers)
        ]
        self.transformer_layers = nn.ModuleList(layers)
        
        self.head = nn.Linear(d_model, vocab_size)
        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.embedding.weight, mean=0, std=self.d_model ** -0.5)
        nn.init.normal_(self.head.weight, mean=0, std=self.d_model ** -0.5)
        nn.init.zeros_(self.head.bias)

    def forward(self, src: torch.Tensor) -> Tuple[torch.Tensor, list]:
        """
        Args:
            src: Tensor of shape (batch, seq_len) containing token indices
        
        Returns:
            output: Logits of shape (batch, seq_len, vocab_size)
            all_spikes: List of spike tensors from each layer for analysis
        """
        src = src * self.d_model ** 0.5
        src = self.embedding(src)
        
        # Add positional encoding (clipped to seq_len)
        seq_len = src.shape[1]
        src = src + self.pos_encoder[:, :seq_len, :]
        
        all_spikes = []
        
        for layer in self.transformer_layers:
            src, layer_spikes = layer(src)
            all_spikes.append(layer_spikes)
        
        logits = self.head(src)
        return logits, all_spikes

def create_spiking_model(
    vocab_size: int = 1000,
    d_model: int = 128,
    nhead: int = 4,
    num_layers: int = 2,
    d_ff: int = 512,
    dropout: float = 0.1,
    max_seq_len: int = 256
) -> SpikingTransformer:
    """
    Factory function to create a SpikingTransformer instance.
    """
    return SpikingTransformer(
        vocab_size=vocab_size,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        d_ff=d_ff,
        dropout=dropout,
        max_seq_len=max_seq_len
    )

def verify_surrogate_gradients(
    model: SpikingTransformer,
    dummy_input: torch.Tensor,
    target: torch.Tensor,
    criterion: nn.Module = None
) -> Dict[str, Any]:
    """
    Constitution Principle VII: Verification function.
    
    Runs a mini-batch forward and backward pass to assert that surrogate-gradient
    learning produces non-NaN gradients. If any parameter has NaN gradients,
    an AssertionError is raised.
    
    Args:
        model: The SpikingTransformer model to verify
        dummy_input: Input tensor (batch, seq_len)
        target: Target tensor (batch, seq_len)
        criterion: Loss function (defaults to CrossEntropyLoss)
    
    Returns:
        Dict containing verification status and gradient statistics.
    """
    if criterion is None:
        criterion = nn.CrossEntropyLoss()
    
    model.train()
    
    # Forward pass
    logits, _ = model(dummy_input)
    
    # Reshape logits for loss calculation: (batch*seq, vocab)
    loss = criterion(logits.view(-1, logits.size(-1)), target.view(-1))
    
    # Backward pass
    model.zero_grad()
    loss.backward()
    
    # Verification logic
    gradient_stats = {
        "has_nan": False,
        "max_grad_norm": 0.0,
        "total_params": 0,
        "checked_params": 0
    }
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            gradient_stats["total_params"] += 1
            
            # Check for NaN
            if torch.isnan(param.grad).any():
                gradient_stats["has_nan"] = True
                raise AssertionError(
                    f"Constitution Principle VII Violation: "
                    f"NaN gradients detected in parameter '{name}'. "
                    f"Surrogate gradient mechanism failed."
                )
            
            # Check for Inf
            if torch.isinf(param.grad).any():
                gradient_stats["has_nan"] = True
                raise AssertionError(
                    f"Constitution Principle VII Violation: "
                    f"Inf gradients detected in parameter '{name}'."
                )
            
            # Record stats
            grad_norm = param.grad.norm().item()
            if grad_norm > gradient_stats["max_grad_norm"]:
                gradient_stats["max_grad_norm"] = grad_norm
            gradient_stats["checked_params"] += 1
    
    gradient_stats["verified"] = True
    gradient_stats["message"] = "Surrogate gradient verification passed. All gradients are finite."
    
    return gradient_stats