"""
Complex-valued BERT Adapter for Quantum Cognition in LLMs.

This module implements the core adapter logic:
1. Linear projection of real-valued hidden states to complex space (R^d -> C^d).
2. Context-dependent phase shift operations.
3. Superposition (vector addition) and Born rule probability calculation.
4. Softmax normalization for final probabilities.

The implementation strictly follows the quantum-inspired formalism:
- States are represented as complex vectors (amplitudes).
- Probabilities are derived via the Born rule (squared magnitude).
- Interference arises from the cross-term in the squared magnitude of the sum.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any

# Import shared utilities from the project API surface
from utils.complex_ops import to_complex, phase_shift, vector_add, born_rule
from utils.logging import detect_nan_inf, safe_normalize


class ComplexLinearProjection(nn.Module):
    """
    Projects real-valued hidden states to complex-valued space.
    
    Maps input R^d to C^d by learning separate real and imaginary weight matrices.
    Output shape: [batch, seq_len, hidden] with dtype torch.complex64.
    """
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Learnable parameters for real and imaginary components
        self.weight_real = nn.Parameter(torch.empty(hidden_size, hidden_size))
        self.bias_real = nn.Parameter(torch.empty(hidden_size))
        self.weight_imag = nn.Parameter(torch.empty(hidden_size, hidden_size))
        self.bias_imag = nn.Parameter(torch.empty(hidden_size))
        
        self.reset_parameters()

    def reset_parameters(self) -> None:
        """Initialize weights using Xavier uniform."""
        nn.init.xavier_uniform_(self.weight_real)
        nn.init.xavier_uniform_(self.weight_imag)
        nn.init.zeros_(self.bias_real)
        nn.init.zeros_(self.bias_imag)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Real-valued input tensor of shape [batch, seq_len, hidden]
        
        Returns:
            Complex-valued tensor of shape [batch, seq_len, hidden] (dtype: complex64)
        """
        # Ensure input is float32 for complex construction
        if x.dtype != torch.float32:
            x = x.float()
        
        # Compute real and imaginary parts
        real_part = F.linear(x, self.weight_real, self.bias_real)
        imag_part = F.linear(x, self.weight_imag, self.bias_imag)
        
        # Combine into complex tensor
        return torch.complex(real_part, imag_part)


class ContextDependentPhaseShift(nn.Module):
    """
    Implements context-dependent phase shift operator U_c.
    
    Computes a context embedding via attention pooling over sentence tokens,
    projects it to rotation angles theta, and applies a diagonal phase shift exp(i*theta).
    
    The phase shift is applied element-wise to the complex vector.
    """
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Attention pooling layer to compute context vector
        self.context_attention = nn.Linear(hidden_size, 1)
        
        # Projection from context vector to phase angles (one per hidden dimension)
        self.phase_projection = nn.Linear(hidden_size, hidden_size)

    def forward(self, x: torch.Tensor, context_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Complex-valued input tensor of shape [batch, seq_len, hidden]
            context_mask: Optional boolean mask of shape [batch, seq_len] indicating valid tokens
        
        Returns:
            Phase-shifted complex tensor of shape [batch, seq_len, hidden]
        """
        if x.dtype != torch.complex64:
            x = x.to(torch.complex64)
        
        batch_size, seq_len, hidden = x.shape
        
        # Extract real part for context computation (phase depends on magnitude/content)
        real_input = x.real
        
        # Compute attention scores for context pooling
        attn_scores = self.context_attention(real_input)  # [batch, seq_len, 1]
        
        if context_mask is not None:
            # Apply mask to attention scores
            attn_scores = attn_scores.masked_fill(~context_mask.unsqueeze(-1), float('-inf'))
        
        # Softmax to get attention weights
        attn_weights = F.softmax(attn_scores, dim=1)  # [batch, seq_len, 1]
        
        # Compute context vector as weighted sum of token representations
        context_vector = torch.sum(attn_weights * real_input, dim=1)  # [batch, hidden]
        
        # Project context to phase angles
        theta = self.phase_projection(context_vector)  # [batch, hidden]
        
        # Expand theta to match x dimensions [batch, 1, hidden] -> [batch, seq_len, hidden]
        theta_expanded = theta.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Create phase shift factor: exp(i * theta)
        phase_factor = torch.exp(1j * theta_expanded)
        
        # Apply phase shift: element-wise multiplication
        output = x * phase_factor
        
        return output


class BERTComplexAdapter(nn.Module):
    """
    Full Complex-Valued Adapter for BERT.
    
    Implements the complete pipeline:
    1. Projection: R^d -> C^d
    2. Phase Shift: Context-dependent rotation
    3. Superposition: Vector addition of alternative interpretations
    4. Measurement: Born rule + Softmax normalization
    
    This adapter is designed to be inserted into a frozen BERT model's hidden states
    to enable quantum-inspired ambiguity resolution.
    """
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Core components
        self.projection = ComplexLinearProjection(hidden_size)
        self.phase_shift = ContextDependentPhaseShift(hidden_size)
        
    def forward(
        self, 
        hidden_states: torch.Tensor,
        alt_interpretations: Optional[torch.Tensor] = None,
        context_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass of the complex adapter.
        
        Args:
            hidden_states: Real-valued BERT hidden states [batch, seq_len, hidden]
            alt_interpretations: Optional alternative interpretation states [batch, seq_len, hidden]
            context_mask: Optional mask for valid tokens [batch, seq_len]
        
        Returns:
            Dictionary containing:
              - 'complex_state': The processed complex state [batch, seq_len, hidden]
              - 'probabilities': Final probabilities via Born rule + softmax [batch, seq_len, 2]
              - 'cross_term': Interference cross-term values [batch, seq_len]
        """
        # Step 1: Project real hidden states to complex space
        complex_state = self.projection(hidden_states)
        
        # Step 2: Apply context-dependent phase shift
        if context_mask is not None:
            # Ensure mask is boolean
            if context_mask.dtype != torch.bool:
                context_mask = context_mask.bool()
        
        shifted_state = self.phase_shift(complex_state, context_mask)
        
        # Step 3: Handle alternative interpretations for superposition
        if alt_interpretations is not None:
            # Project alternative interpretation to complex space
            alt_complex = self.projection(alt_interpretations)
            alt_shifted = self.phase_shift(alt_complex, context_mask)
            
            # Superposition: vector addition
            superposed_state = vector_add(shifted_state, alt_shifted)
            
            # Calculate interference cross-term
            # Cross-term = 2 * Re(c1 * conj(c2))
            cross_term = 2 * torch.real(shifted_state * torch.conj(alt_shifted))
            cross_term = torch.sum(cross_term, dim=-1)  # Sum over hidden dimension
        else:
            superposed_state = shifted_state
            cross_term = torch.zeros_like(hidden_states[..., 0])
        
        # Step 4: Born rule (squared magnitude)
        # P_raw = ||c||^2
        p_raw = born_rule(superposed_state)
        
        # Step 5: Softmax normalization for final probabilities
        # If we have two interpretations (original + alt), we normalize over them
        if alt_interpretations is not None:
            # Stack probabilities: [batch, seq_len, 2]
            p_original = born_rule(shifted_state)
            p_alt = born_rule(alt_shifted)
            probs = torch.stack([p_original, p_alt], dim=-1)
            probs_normalized = F.softmax(probs, dim=-1)
        else:
            # Single interpretation: probability is 1.0 (or normalized over sequence)
            probs_normalized = torch.ones_like(p_raw).unsqueeze(-1)
        
        # Safety checks
        detect_nan_inf(p_raw, "Born rule output")
        detect_nan_inf(probs_normalized, "Probability output")
        
        return {
            'complex_state': superposed_state,
            'probabilities': probs_normalized,
            'cross_term': cross_term,
            'p_raw': p_raw
        }


def main():
    """
    Simple demonstration of the BERTComplexAdapter.
    
    This function creates a dummy input, runs it through the adapter,
    and prints the resulting shapes and a sample of the probabilities.
    """
    # Configuration
    batch_size = 2
    seq_len = 10
    hidden_size = 768  # BERT base hidden size
    
    # Create dummy real-valued hidden states (simulating BERT output)
    hidden_states = torch.randn(batch_size, seq_len, hidden_size)
    
    # Create dummy alternative interpretations (e.g., different sense embeddings)
    alt_interpretations = torch.randn(batch_size, seq_len, hidden_size)
    
    # Create dummy context mask (all True for simplicity)
    context_mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
    
    # Initialize adapter
    adapter = BERTComplexAdapter(hidden_size)
    
    # Run forward pass
    output = adapter(
        hidden_states=hidden_states,
        alt_interpretations=alt_interpretations,
        context_mask=context_mask
    )
    
    # Print results
    print("=== BERT Complex Adapter Demo ===")
    print(f"Input shape: {hidden_states.shape}")
    print(f"Complex state shape: {output['complex_state'].shape}")
    print(f"Probabilities shape: {output['probabilities'].shape}")
    print(f"Cross-term shape: {output['cross_term'].shape}")
    print(f"\nSample probabilities (batch 0, token 0): {output['probabilities'][0, 0]}")
    print(f"Sample cross-term (batch 0, token 0): {output['cross_term'][0, 0].item():.4f}")
    
    # Verify probability sums to 1
    prob_sum = torch.sum(output['probabilities'], dim=-1)
    print(f"Probability sum (should be ~1.0): {prob_sum[0, 0].item():.4f}")


if __name__ == "__main__":
    main()