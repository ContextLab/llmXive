import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any
import os
import sys

# Import from sibling modules in the same project structure
from ..utils.complex_ops import to_complex, phase_shift, vector_add, born_rule, interference_cross_term
from ..utils.logging import detect_nan_inf, safe_normalize
from .loss_utils import compute_phase_penalty_loss, verify_gradient_direction

class ComplexLinearProjection(nn.Module):
    """
    Projects real-valued hidden states to complex vectors.
    Maps R^d -> C^d by learning separate real and imaginary linear projections.
    """
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.real_proj = nn.Linear(input_dim, output_dim)
        self.imag_proj = nn.Linear(input_dim, output_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Real-valued tensor of shape [batch, seq_len, input_dim]
        Returns:
            Complex tensor of shape [batch, seq_len, output_dim] with dtype torch.complex64
        """
        real_part = self.real_proj(x)
        imag_part = self.imag_proj(x)
        return torch.complex(real_part, imag_part)

class ContextDependentPhaseShift(nn.Module):
    """
    Implements context-dependent phase shift operator U_c.
    Computes a context embedding via attention pooling over sentence tokens,
    projects to rotation angle theta, and applies diagonal phase shift exp(i*theta).
    """
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attention_pool = nn.MultiheadAttention(
            embed_dim=hidden_dim, 
            num_heads=4, 
            batch_first=True
        )
        self.theta_proj = nn.Linear(hidden_dim, hidden_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Real-valued tensor of shape [batch, seq_len, hidden_dim]
        Returns:
            Complex tensor of shape [batch, seq_len, hidden_dim] with phase shifts applied
        """
        batch_size, seq_len, hidden_dim = x.shape
        
        # Create a single context token (learnable or mean-pooled)
        # Here we use a simple mean pooling over sequence dimension for context
        context = x.mean(dim=1, keepdim=True)  # [batch, 1, hidden_dim]
        
        # Project context to rotation angles
        theta = self.theta_proj(context)  # [batch, 1, hidden_dim]
        theta = theta.squeeze(1)  # [batch, hidden_dim]
        
        # Apply phase shift to each token in the sequence
        # Expand theta to match sequence length
        theta_expanded = theta.unsqueeze(1)  # [batch, 1, hidden_dim]
        
        # Create phase shift matrix: exp(i * theta)
        phase_shifts = torch.exp(1j * theta_expanded)  # [batch, 1, hidden_dim] complex
        
        # Broadcast to all sequence positions
        phase_shifts = phase_shifts.expand(-1, seq_len, -1)  # [batch, seq_len, hidden_dim]
        
        # Apply phase shift: multiply each token by the phase factor
        # First convert x to complex
        x_complex = to_complex(x)  # [batch, seq_len, hidden_dim] complex
        
        # Element-wise multiplication for diagonal phase shift
        output = x_complex * phase_shifts
        
        return output

class BERTComplexAdapter(nn.Module):
    """
    Full quantum-inspired adapter for BERT hidden states.
    Implements:
    1. Complex linear projection R^d -> C^d
    2. Context-dependent phase shift U_c
    3. Superposition (vector addition)
    4. Born rule probability calculation
    5. Softmax normalization
    """
    def __init__(self, hidden_dim: int, num_classes: int = 2):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        
        # Complex linear projection
        self.complex_proj = ComplexLinearProjection(hidden_dim, hidden_dim)
        
        # Context-dependent phase shift
        self.phase_shift = ContextDependentPhaseShift(hidden_dim)
        
        # Learnable parameters for ambiguity detection
        self.ambiguity_head = nn.Linear(hidden_dim, 1)
        
    def forward(self, hidden_states: torch.Tensor, 
                context_states: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Args:
            hidden_states: Real-valued tensor [batch, seq_len, hidden_dim]
            context_states: Optional context tensor for phase shift computation
        Returns:
            Tuple of (final_probabilities, intermediate_states_dict)
        """
        # Step 1: Complex linear projection
        complex_states = self.complex_proj(hidden_states)  # [batch, seq_len, hidden_dim] complex
        
        # Step 2: Context-dependent phase shift
        shifted_states = self.phase_shift(hidden_states)  # [batch, seq_len, hidden_dim] complex
        
        # Step 3: Superposition (vector addition of original complex and shifted states)
        superposed_states = vector_add(complex_states, shifted_states)  # [batch, seq_len, hidden_dim] complex
        
        # Step 4: Born rule - compute squared magnitude
        raw_probs = born_rule(superposed_states)  # [batch, seq_len, hidden_dim] real
        
        # Step 5: Softmax normalization across classes (assuming last dim is classes)
        # For binary classification, we take the last two dimensions as class probabilities
        if raw_probs.shape[-1] >= 2:
            # Take the last two dimensions as class scores
            class_scores = raw_probs[..., -2:]  # [batch, seq_len, 2]
            final_probs = F.softmax(class_scores, dim=-1)  # [batch, seq_len, 2]
        else:
            final_probs = F.softmax(raw_probs, dim=-1)
        
        # Collect intermediate states for analysis
        intermediate_states = {
            'complex_states': complex_states,
            'shifted_states': shifted_states,
            'superposed_states': superposed_states,
            'raw_probs': raw_probs,
            'final_probs': final_probs
        }
        
        return final_probs, intermediate_states
    
    def compute_loss(self, hidden_states: torch.Tensor, 
                    labels: torch.Tensor, 
                    lambda_penalty: float = 0.5) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute training loss with phase penalty for ambiguous tokens.
        
        Args:
            hidden_states: Real-valued tensor [batch, seq_len, hidden_dim]
            labels: Ground truth labels [batch, seq_len] or [batch]
            lambda_penalty: Weight for phase penalty term (default 0.5)
        
        Returns:
            Tuple of (total_loss, phase_penalty_loss)
        """
        # Forward pass to get probabilities
        final_probs, intermediate_states = self.forward(hidden_states)
        
        # Standard cross-entropy loss
        # Reshape for loss computation
        batch_size = final_probs.shape[0]
        
        # Assume binary classification: take first class probability
        if final_probs.shape[-1] == 2:
            pred_probs = final_probs[..., 0]  # [batch, seq_len]
        else:
            pred_probs = final_probs[..., 0]
        
        # Compute cross-entropy loss
        ce_loss = F.cross_entropy(
            final_probs.view(-1, final_probs.shape[-1]),
            labels.view(-1),
            reduction='mean'
        )
        
        # Compute phase penalty loss for ambiguous tokens
        phase_penalty_loss = compute_phase_penalty_loss(
            intermediate_states['superposed_states'],
            lambda_penalty=lambda_penalty
        )
        
        # Total loss
        total_loss = ce_loss + lambda_penalty * phase_penalty_loss
        
        return total_loss, phase_penalty_loss

def main():
    """
    Example usage and testing of the BERTComplexAdapter.
    """
    # Initialize model
    model = BERTComplexAdapter(hidden_dim=768, num_classes=2)
    
    # Create dummy input
    batch_size = 4
    seq_len = 10
    hidden_dim = 768
    
    hidden_states = torch.randn(batch_size, seq_len, hidden_dim)
    labels = torch.randint(0, 2, (batch_size, seq_len))
    
    # Forward pass
    final_probs, intermediate_states = model(hidden_states)
    print(f"Output probabilities shape: {final_probs.shape}")
    print(f"Intermediate states keys: {intermediate_states.keys()}")
    
    # Compute loss
    total_loss, phase_penalty_loss = model.compute_loss(hidden_states, labels)
    print(f"Total loss: {total_loss.item():.4f}")
    print(f"Phase penalty loss: {phase_penalty_loss.item():.4f}")
    
    # Test gradient flow
    total_loss.backward()
    print("Gradient computation successful!")
    
    # Verify gradient direction for phase penalty
    test_phases = torch.randn(batch_size, seq_len, hidden_dim)
    gradient_direction = verify_gradient_direction(test_phases)
    print(f"Gradient direction test: {gradient_direction}")

if __name__ == "__main__":
    main()
