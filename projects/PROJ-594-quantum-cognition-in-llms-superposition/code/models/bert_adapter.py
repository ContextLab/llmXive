"""
BERT Complex Adapter Implementation.

Implements the core quantum-inspired adapter:
1. ComplexLinearProjection: R^d -> C^d
2. ContextDependentPhaseShift: U_c operator
3. BERTComplexAdapter: Full superposition and Born rule pipeline
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List
import os
import sys

# Ensure project root is in path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.complex_ops import to_complex, phase_shift, vector_add, born_rule
from utils.logging import detect_nan_inf, safe_normalize


class ComplexLinearProjection(nn.Module):
    """
    Linear projection from real-valued hidden states to complex vectors.
    Maps R^d -> C^d by creating real and imaginary components.
    """
    def __init__(self, hidden_dim: int):
        super().__init__()
        # Project to 2*hidden_dim to separate real and imaginary parts
        self.projection = nn.Linear(hidden_dim, 2 * hidden_dim)
        self.hidden_dim = hidden_dim

    def forward(self, h_real: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h_real: [batch, seq_len, hidden_dim] real-valued tensor
        Returns:
            c_complex: [batch, seq_len, hidden_dim] complex tensor
        """
        batch_size, seq_len, _ = h_real.shape
        
        # Project to 2*hidden_dim
        projected = self.projection(h_real)  # [batch, seq_len, 2*hidden_dim]
        
        # Split into real and imaginary parts
        real_part = projected[:, :, :self.hidden_dim]
        imag_part = projected[:, :, self.hidden_dim:]
        
        # Combine into complex tensor
        c_complex = torch.complex(real_part, imag_part)
        
        # Verify dtype
        assert c_complex.dtype == torch.complex64, f"Expected complex64, got {c_complex.dtype}"
        
        return c_complex


class ContextDependentPhaseShift(nn.Module):
    """
    Context-dependent phase shift operator U_c.
    Computes a context embedding via attention pooling, projects to rotation angle theta,
    and applies a diagonal phase shift exp(i*theta).
    """
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Attention pooling for context embedding
        self.attention = nn.Linear(hidden_dim, 1)
        
        # Project context embedding to rotation angle
        self.angle_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, hidden_dim)
        )

    def forward(self, h_real: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h_real: [batch, seq_len, hidden_dim] real-valued tensor
        Returns:
            c_phased: [batch, seq_len, hidden_dim] complex tensor with phase shifts applied
        """
        batch_size, seq_len, _ = h_real.shape
        
        # Compute attention weights for context pooling
        attn_scores = self.attention(h_real)  # [batch, seq_len, 1]
        attn_weights = F.softmax(attn_scores, dim=1)  # [batch, seq_len, 1]
        
        # Context embedding via weighted sum
        context_embedding = torch.sum(attn_weights * h_real, dim=1, keepdim=False)  # [batch, hidden_dim]
        
        # Project to rotation angles
        theta = self.angle_projection(context_embedding)  # [batch, hidden_dim]
        
        # Expand theta to match sequence length for broadcasting
        theta_expanded = theta.unsqueeze(1)  # [batch, 1, hidden_dim]
        
        # Create complex phase shift: exp(i * theta)
        # For each dimension, the phase shift is a complex number with magnitude 1
        phase_shifts = torch.exp(1j * theta_expanded)  # [batch, 1, hidden_dim]
        
        # Apply to input (input must be complex for phase multiplication)
        # Convert real input to complex with zero imaginary part
        h_complex = torch.complex(h_real, torch.zeros_like(h_real))
        
        # Apply phase shift element-wise
        c_phased = h_complex * phase_shifts  # [batch, seq_len, hidden_dim]
        
        return c_phased


class BERTComplexAdapter(nn.Module):
    """
    Full quantum-inspired adapter combining:
    1. ComplexLinearProjection: R^d -> C^d
    2. ContextDependentPhaseShift: U_c operator
    3. Superposition (vector addition)
    4. Born rule (probability from squared magnitude)
    5. Softmax normalization for binary classification
    """
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        self.complex_projection = ComplexLinearProjection(hidden_dim)
        self.phase_shift = ContextDependentPhaseShift(hidden_dim)
        
        # Classifier head for final probability
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, h_real: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Full forward pass:
        1. Project to complex space
        2. Apply context-dependent phase shift
        3. Compute superposition (vector addition of context representations)
        4. Apply Born rule
        5. Softmax normalization for binary classification
        
        Args:
            h_real: [batch, seq_len, hidden_dim] real-valued BERT hidden states
        
        Returns:
            probabilities: [batch, 2] normalized probabilities for binary classification
            metadata: Dictionary with intermediate values for analysis
        """
        # Step 1: Project to complex space
        c_complex = self.complex_projection(h_real)  # [batch, seq_len, hidden_dim]
        
        # Step 2: Apply context-dependent phase shift
        c_phased = self.phase_shift(h_real)  # [batch, seq_len, hidden_dim] complex
        
        # Step 3: Superposition - vector addition of token representations
        # For ambiguity, we sum all token representations in the sequence
        c_sum = torch.sum(c_phased, dim=1)  # [batch, hidden_dim]
        
        # Step 4: Born rule - probability from squared magnitude
        # P_raw = ||c_sum||^2
        p_raw = torch.abs(c_sum) ** 2  # [batch, hidden_dim]
        
        # For binary classification, we need two probability values
        # We use the first half of dimensions for class 0, second half for class 1
        half_dim = self.hidden_dim // 2
        p_class0 = torch.sum(p_raw[:, :half_dim], dim=1, keepdim=True)  # [batch, 1]
        p_class1 = torch.sum(p_raw[:, half_dim:], dim=1, keepdim=True)  # [batch, 1]
        
        # Step 5: Softmax normalization
        # P_final = exp(P_raw) / (exp(P_raw_0) + exp(P_raw_1))
        p_unnorm = torch.cat([p_class0, p_class1], dim=1)  # [batch, 2]
        
        # Apply softmax for proper probability distribution
        probabilities = F.softmax(p_unnorm, dim=1)  # [batch, 2]
        
        # Check for NaN/Inf
        detect_nan_inf(probabilities, "Output probabilities")
        
        metadata = {
            'c_complex': c_complex,
            'c_phased': c_phased,
            'c_sum': c_sum,
            'p_raw': p_raw,
            'p_unnorm': p_unnorm
        }
        
        return probabilities, metadata


def main():
    """
    Test the BERTComplexAdapter with synthetic data to verify:
    1. Complex output dtype
    2. Softmax normalization produces valid probabilities
    3. Sum of probabilities equals 1.0
    """
    print("Testing BERTComplexAdapter...")
    
    # Create model
    hidden_dim = 768
    model = BERTComplexAdapter(hidden_dim)
    model.eval()
    
    # Create dummy input (real BERT hidden states)
    batch_size = 4
    seq_len = 10
    h_real = torch.randn(batch_size, seq_len, hidden_dim)
    
    # Forward pass
    with torch.no_grad():
        probabilities, metadata = model(h_real)
    
    # Verify output
    print(f"Input shape: {h_real.shape}")
    print(f"Output probabilities shape: {probabilities.shape}")
    print(f"Output dtype: {probabilities.dtype}")
    
    # Verify softmax normalization
    prob_sum = torch.sum(probabilities, dim=1)
    print(f"Sum of probabilities (should be 1.0): {prob_sum}")
    
    # Verify all probabilities are in [0, 1]
    assert torch.all(probabilities >= 0), "Probabilities must be non-negative"
    assert torch.all(probabilities <= 1), "Probabilities must be <= 1"
    assert torch.allclose(prob_sum, torch.ones_like(prob_sum), atol=1e-5), "Probabilities must sum to 1"
    
    print("✓ All tests passed!")
    print(f"  - Output shape: {probabilities.shape}")
    print(f"  - Probabilities sum to 1.0: {torch.allclose(prob_sum, torch.ones_like(prob_sum), atol=1e-5)}")
    print(f"  - All values in [0, 1]: {torch.all(probabilities >= 0) and torch.all(probabilities <= 1)}")
    
    return probabilities, metadata


if __name__ == "__main__":
    main()