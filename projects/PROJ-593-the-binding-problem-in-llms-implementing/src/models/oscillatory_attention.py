import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, Union

class OscillatoryAttentionModule(nn.Module):
    """
    Injects a sinusoidal gating mask into attention scores at a specified
    relative frequency (cycles per sequence).
    
    This module implements the core mechanism for the binding problem hypothesis:
    synchronized oscillatory dynamics in attention mechanisms. The mask modulates
    attention weights based on the relative position of tokens, creating phase-locked
    patterns that could theoretically bind features across the sequence.
    
    Args:
        hidden_size: Dimension of the hidden state (used for compatibility checks).
        num_heads: Number of attention heads.
        max_seq_len: Maximum expected sequence length for mask pre-computation.
        frequency: Relative frequency in cycles per sequence (e.g., 40 for 40Hz-equivalent).
        phase_offset: Optional phase offset in radians (default 0).
        amplitude: Amplitude of the oscillation (default 1.0).
    """
    def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        max_seq_len: int,
        frequency: float = 40.0,
        phase_offset: float = 0.0,
        amplitude: float = 1.0
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.max_seq_len = max_seq_len
        self.frequency = frequency
        self.phase_offset = phase_offset
        self.amplitude = amplitude
        
        # Pre-compute the oscillatory mask for the maximum sequence length
        # The mask is a sinusoidal wave: amplitude * sin(2 * pi * frequency * t + phase)
        # where t ranges from 0 to 1 (normalized sequence position)
        positions = torch.arange(max_seq_len).float() / max_seq_len
        self.register_buffer(
            "oscillatory_mask",
            amplitude * torch.sin(2 * math.pi * frequency * positions + phase_offset)
        )
        
        # Learnable parameter to scale the oscillation effect per head
        self.head_scale = nn.Parameter(torch.ones(num_heads))

    def forward(
        self,
        attention_scores: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Applies the oscillatory mask to attention scores.
        
        Args:
            attention_scores: Tensor of shape (batch_size, num_heads, seq_len, seq_len)
            attention_mask: Optional standard attention mask (e.g., for padding)
        
        Returns:
            Modified attention scores with oscillatory gating applied.
        """
        batch_size, num_heads, seq_len, _ = attention_scores.shape
        
        # Ensure sequence length matches or is within bounds
        if seq_len > self.max_seq_len:
            raise ValueError(
                f"Sequence length {seq_len} exceeds max_seq_len {self.max_seq_len}. "
                "Increase max_seq_len during initialization."
            )
        
        # Expand the pre-computed mask to match attention score dimensions
        # Shape: (1, 1, max_seq_len, 1) -> broadcast to (batch, heads, seq, seq)
        oscillatory_signal = self.oscillatory_mask[:seq_len].unsqueeze(0).unsqueeze(0)
        
        # Create a relative position mask for attention
        # We want the oscillation to modulate attention based on the relative distance
        # between query and key positions. 
        # Create a grid of relative positions: (1, 1, seq_len, seq_len)
        query_positions = torch.arange(seq_len).unsqueeze(1).float()  # (seq_len, 1)
        key_positions = torch.arange(seq_len).unsqueeze(0).float()    # (1, seq_len)
        relative_positions = (query_positions - key_positions) / seq_len  # Normalize to [-1, 1]
        
        # Apply sinusoidal modulation based on relative positions
        # This creates a phase-locking effect where attention is modulated by distance
        relative_oscillation = self.amplitude * torch.sin(
            2 * math.pi * self.frequency * relative_positions + self.phase_offset
        )
        
        # Expand to (1, 1, seq_len, seq_len) and then to batch/head dimensions
        relative_oscillation = relative_oscillation.unsqueeze(0).unsqueeze(0)
        
        # Apply head-specific scaling
        head_scale = self.head_scale.view(1, num_heads, 1, 1)
        oscillatory_gate = relative_oscillation * head_scale
        
        # Apply the oscillatory gate to attention scores
        # We add the gate to the scores (not multiply) to modulate the logit values
        # This is equivalent to multiplying attention probabilities by exp(gate)
        modified_scores = attention_scores + oscillatory_gate
        
        # Apply standard attention mask if provided (e.g., for padding tokens)
        if attention_mask is not None:
            # attention_mask is typically (batch_size, 1, 1, seq_len) or similar
            # We need to broadcast it correctly
            if attention_mask.dim() == 4:
                modified_scores = modified_scores.masked_fill(
                    attention_mask == 0, -1e9
                )
            else:
                # Handle different mask shapes
                modified_scores = modified_scores.masked_fill(
                    attention_mask.unsqueeze(1).unsqueeze(2) == 0, -1e9
                )
        
        return modified_scores


class OscillatoryDistilBERTWrapper:
    """
    Wrapper for DistilBERT that injects the OscillatoryAttentionModule
    into the attention mechanism.
    
    This class provides an interface to replace the standard attention
    with oscillatory attention in a pre-trained DistilBERT model.
    """
    def __init__(
        self,
        base_model,
        frequency: float = 40.0,
        phase_offset: float = 0.0,
        amplitude: float = 1.0
    ):
        """
        Args:
            base_model: A pre-trained DistilBERT model instance.
            frequency: Relative frequency in cycles per sequence.
            phase_offset: Phase offset in radians.
            amplitude: Amplitude of the oscillation.
        """
        self.base_model = base_model
        self.frequency = frequency
        self.phase_offset = phase_offset
        self.amplitude = amplitude
        self.injected = False
        
        # Store original attention modules for potential restoration
        self.original_attention_modules = []

    def inject_oscillatory_attention(self, max_seq_len: int = 512):
        """
        Replaces standard attention modules with oscillatory versions.
        
        Args:
            max_seq_len: Maximum sequence length for mask pre-computation.
        """
        if self.injected:
            return
        
        # Access DistilBERT's internal structure
        # DistilBERT has a transformer module with layers, each containing attention
        transformer = self.base_model.distilbert.transformer
        
        for layer_idx, layer in enumerate(transformer.layer):
            # Store original attention for potential restoration
            original_attention = layer.attention
            self.original_attention_modules.append((layer_idx, original_attention))
            
            # Create oscillatory attention module
            # DistilBERT hidden size is typically 768, num_heads is 12
            hidden_size = original_attention.hidden_size
            num_heads = original_attention.num_heads
            
            oscillatory_module = OscillatoryAttentionModule(
                hidden_size=hidden_size,
                num_heads=num_heads,
                max_seq_len=max_seq_len,
                frequency=self.frequency,
                phase_offset=self.phase_offset,
                amplitude=self.amplitude
            )
            
            # Replace the attention module
            layer.attention = oscillatory_module
        
        self.injected = True

    def restore_original_attention(self):
        """Restores the original attention modules."""
        if not self.injected:
            return
        
        transformer = self.base_model.distilbert.transformer
        for layer_idx, original_attention in self.original_attention_modules:
            transformer.layer[layer_idx].attention = original_attention
        
        self.injected = False
        self.original_attention_modules = []

    def forward(self, *args, **kwargs):
        """Forward pass through the model."""
        return self.base_model(*args, **kwargs)

    def __getattr__(self, name):
        """Delegate attribute access to the base model."""
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.base_model, name)


def create_oscillatory_attention(
    base_model,
    frequency: float = 40.0,
    phase_offset: float = 0.0,
    amplitude: float = 1.0,
    max_seq_len: int = 512
):
    """
    Factory function to create an oscillatory wrapper around a base model.
    
    Args:
        base_model: The base model to wrap.
        frequency: Relative frequency in cycles per sequence.
        phase_offset: Phase offset in radians.
        amplitude: Amplitude of the oscillation.
        max_seq_len: Maximum sequence length for mask pre-computation.
        
    Returns:
        An OscillatoryDistilBERTWrapper instance with oscillatory attention injected.
    """
    wrapper = OscillatoryDistilBERTWrapper(
        base_model=base_model,
        frequency=frequency,
        phase_offset=phase_offset,
        amplitude=amplitude
    )
    wrapper.inject_oscillatory_attention(max_seq_len=max_seq_len)
    return wrapper