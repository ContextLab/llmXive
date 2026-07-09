"""
Recursive LLaMA implementation with temporal recursive self-attention.

This module implements FR-001: A wrapper around a base LLaMA model that
injects a recursive self-attention mechanism. The model maintains an internal
state of previous reasoning traces and attends to them during generation.
"""
import torch
import torch.nn as nn
from transformers import LlamaConfig, LlamaForCausalLM
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

from config import validate_config
from utils.logging import get_logger, RecursionDepthError

logger = get_logger(__name__)


@dataclass
class RecursionState:
    """
    Holds the state required for recursive self-attention.
    """
    hidden_states: torch.Tensor
    attention_mask: Optional[torch.Tensor]
    depth: int
    max_depth: int


class TemporalRecursiveSelfAttention(nn.Module):
    """
    Implements the temporal recursive self-attention mechanism.

    This module takes the current hidden states and allows them to attend
    to a cache of previous hidden states (from previous recursion steps).
    This simulates the model "thinking about its own previous thoughts".
    """
    def __init__(self, config: LlamaConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.hidden_size // self.num_heads

        # Projection for the recursive context
        # We project previous hidden states to match the current query space
        self.recursive_proj = nn.Linear(self.hidden_size, self.hidden_size, bias=False)

        # Learnable gate to control how much of the recursive context is used
        self.gate = nn.Sequential(
            nn.Linear(self.hidden_size, 1),
            nn.Sigmoid()
        )

        # Cache for previous states
        self._cache: List[torch.Tensor] = []

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        recursion_state: Optional[RecursionState] = None,
        is_cache_update: bool = False
    ) -> Tuple[torch.Tensor, Optional[RecursionState]]:
        """
        Forward pass with recursive attention.

        Args:
            hidden_states: Current sequence hidden states [B, S, H]
            attention_mask: Standard attention mask
            recursion_state: State from previous recursion step
            is_cache_update: If True, we are in the 'thinking' phase and updating cache

        Returns:
            Tuple of (new_hidden_states, updated_recursion_state)
        """
        batch_size, seq_len, hidden_size = hidden_states.shape

        if recursion_state is not None:
            prev_hidden = recursion_state.hidden_states
            prev_mask = recursion_state.attention_mask
            current_depth = recursion_state.depth

            if current_depth >= recursion_state.max_depth:
                # Base case: stop recursion, return current states without modification
                logger.debug(f"Max recursion depth {current_depth} reached. Stopping.")
                return hidden_states, None

            # Project previous hidden states
            projected_prev = self.recursive_proj(prev_hidden)

            # Compute gate value (scalar per batch, broadcasted)
            # We use the mean of the current hidden states to determine gate
            gate_input = hidden_states.mean(dim=1, keepdim=True)
            gate_val = self.gate(gate_input)  # [B, 1, 1]

            # Concatenate current and projected previous states
            # We need to handle the mask for the concatenated sequence
            # Current: [B, S, H], Previous: [B, S_prev, H]
            combined_states = torch.cat([hidden_states, projected_prev], dim=1)

            # Create combined attention mask
            # Current mask is [B, S] (or [B, 1, S, S]), previous mask is [B, S_prev]
            # For simplicity in this implementation, we assume standard causal masking
            # and just extend the mask to cover the concatenated sequence.
            # The previous states are treated as "past" and should be attendable.
            if attention_mask is not None:
                # Expand mask for previous tokens (they are all valid for attention from current)
                # Shape: [B, S + S_prev]
                combined_mask = torch.cat(
                    [attention_mask, torch.ones_like(attention_mask[:, :1]).expand(batch_size, prev_hidden.shape[1])],
                    dim=1
                )
            else:
                combined_mask = None

            # Apply standard LLaMA attention on the combined sequence
            # Note: This requires a custom attention implementation or modifying the base model's attention.
            # For this implementation, we will use a simplified self-attention mechanism
            # that mimics the LLaMA behavior but works on the combined sequence.
            # In a full implementation, we would inject this into the LlamaAttention layer.

            # Simplified attention for demonstration of the concept
            # Q, K, V projections
            q = hidden_states  # Current queries
            k = combined_states # Keys from current + previous
            v = combined_states # Values from current + previous

            # Project Q, K, V
            # We need to use the base model's attention weights or re-project
            # For this module, we assume the base model handles the QKV projection
            # and we just modify the K/V to include history.
            # However, to keep it self-contained, we implement a simple attention here.
            # This is a placeholder for the actual integration point.

            # Scale dot product attention
            attn_weights = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)

            if combined_mask is not None:
                # Apply mask (assuming causal + previous tokens are visible)
                # This is a simplified mask application
                mask_value = -1e9
                # Expand mask to [B, 1, S, S+S_prev]
                if combined_mask.dim() == 2:
                    combined_mask = combined_mask.unsqueeze(1).unsqueeze(1)
                attn_weights = attn_weights.masked_fill(combined_mask == 0, mask_value)

            attn_weights = torch.softmax(attn_weights, dim=-1)
            attn_output = torch.matmul(attn_weights, v)

            # Apply gate
            gated_output = hidden_states + gate_val * (attn_output - hidden_states)

            # Update cache for next recursion step
            new_state = RecursionState(
                hidden_states=combined_states, # Store combined for next step? Or just current?
                attention_mask=combined_mask,
                depth=current_depth + 1,
                max_depth=recursion_state.max_depth
            )

            return gated_output, new_state

        return hidden_states, None


class RecursiveLlamaWrapper:
    """
    Wrapper for LlamaForCausalLM that adds recursive self-attention capabilities.

    This class manages the recursion loop, state caching, and integrates
    the TemporalRecursiveSelfAttention module.
    """
    def __init__(self, model: LlamaForCausalLM, max_recursion_depth: int = 2):
        """
        Initialize the wrapper.

        Args:
            model: The base LlamaForCausalLM instance
            max_recursion_depth: Maximum number of recursive steps (default 2 as per config)
        """
        self.model = model
        self.max_recursion_depth = max_recursion_depth
        self.recursive_attention = TemporalRecursiveSelfAttention(model.config)
        self.config = validate_config() # Ensure config is loaded

        logger.info(f"RecursiveLlamaWrapper initialized with max_depth={max_recursion_depth}")

    def _run_recursion(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        initial_hidden_states: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, RecursionState]:
        """
        Execute the recursive self-attention loop.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            initial_hidden_states: Optional initial hidden states (e.g., from a previous pass)

        Returns:
            Tuple of (final_hidden_states, final_recursion_state)
        """
        # Get initial hidden states from the model's embedding layer
        if initial_hidden_states is None:
            initial_hidden_states = self.model.get_input_embeddings()(input_ids)

        batch_size, seq_len, hidden_size = initial_hidden_states.shape

        # Initialize recursion state
        current_state = RecursionState(
            hidden_states=initial_hidden_states,
            attention_mask=attention_mask,
            depth=0,
            max_depth=self.max_recursion_depth
        )

        current_hidden = initial_hidden_states
        current_mask = attention_mask

        # Run recursion loop
        for step in range(self.max_recursion_depth):
            logger.debug(f"Recursion step {step + 1}/{self.max_recursion_depth}")

            # Apply recursive attention
            new_hidden, new_state = self.recursive_attention(
                hidden_states=current_hidden,
                attention_mask=current_mask,
                recursion_state=current_state,
                is_cache_update=True
            )

            if new_state is None:
                # Max depth reached or stopped
                break

            current_hidden = new_hidden
            current_mask = new_state.attention_mask
            current_state = new_state

        return current_hidden, current_state

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        recursion_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Forward pass with optional recursive self-attention.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            labels: Optional labels for loss computation
            recursion_enabled: Whether to enable recursive attention

        Returns:
            Dict containing outputs, logits, and optionally loss
        """
        if not recursion_enabled:
            # Standard forward pass
            return self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

        # Check for OOM or depth constraints before running
        if self.max_recursion_depth > 2:
            raise RecursionDepthError(f"Recursion depth {self.max_recursion_depth} exceeds allowed limit of 2.")

        try:
            # Run recursion to get modified hidden states
            final_hidden_states, _ = self._run_recursion(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

            # Project back to vocabulary size for logits
            # The model's lm_head expects hidden states of shape [B, S, H]
            logits = self.model.lm_head(final_hidden_states)

            loss = None
            if labels is not None:
                # Shift labels for next token prediction
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(shift_logits.view(-1, self.model.config.vocab_size), shift_labels.view(-1))

            return {
                "logits": logits,
                "loss": loss,
                "hidden_states": final_hidden_states,
                "recursion_depth": self.max_recursion_depth
            }

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(f"OOM error during recursion: {e}")
                raise RecursionDepthError(f"OOM during recursive forward pass. Depth: {self.max_recursion_depth}") from e
            raise

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 100,
        **kwargs
    ) -> torch.Tensor:
        """
        Generate text with recursive self-attention.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            max_new_tokens: Maximum number of new tokens to generate
            **kwargs: Additional arguments for generation

        Returns:
            Generated token IDs
        """
        # For generation, we need to handle the recursion step-by-step
        # This is a simplified version; a full implementation would integrate
        # recursion into the generation loop.
        logger.warning("Recursive generation is a simplified implementation.")

        # Use standard generation but with recursive hidden states if possible
        # For now, we just call the base model's generate
        # In a full implementation, we would override the attention layers
        return self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            **kwargs
        )

    def save_pretrained(self, save_directory: str):
        """Save the model and wrapper configuration."""
        self.model.save_pretrained(save_directory)
        # Save wrapper config
        import json
        config_path = os.path.join(save_directory, "recursive_config.json")
        with open(config_path, "w") as f:
            json.dump({"max_recursion_depth": self.max_recursion_depth}, f)

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path: str, max_recursion_depth: int = 2):
        """Load the model and wrapper from a pretrained directory."""
        model = LlamaForCausalLM.from_pretrained(pretrained_model_name_or_path)
        return cls(model, max_recursion_depth=max_recursion_depth)


def create_recursive_model(config: LlamaConfig, max_recursion_depth: int = 2) -> RecursiveLlamaWrapper:
    """
    Factory function to create a RecursiveLlamaWrapper.

    Args:
        config: LlamaConfig instance
        max_recursion_depth: Maximum recursion depth

    Returns:
        RecursiveLlamaWrapper instance
    """
    model = LlamaForCausalLM(config)
    return RecursiveLlamaWrapper(model, max_recursion_depth=max_recursion_depth)

import os # Added for save_pretrained
