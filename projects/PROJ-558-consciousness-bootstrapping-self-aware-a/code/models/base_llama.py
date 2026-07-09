"""
Base LLaMA wrapper for small transformer models (<300M params).

This module provides a lightweight wrapper around HuggingFace's LLaMA architecture,
configured for CPU-only execution with strict parameter limits. It serves as the
foundation for recursive self-modeling experiments.
"""

import os
from typing import Optional, Dict, Any, Tuple

import torch
from transformers import LlamaConfig, LlamaForCausalLM
from transformers.modeling_outputs import CausalLMOutputWithPast

from config import validate_config


class BaseLlamaWrapper:
    """
    A wrapper for small LLaMA models designed for recursive introspection experiments.

    This class enforces CPU-only execution and parameter limits (<300M) as required
    by the project constraints. It provides a standardized interface for model
    initialization, forward passes, and inference.

    Attributes:
        model (LlamaForCausalLM): The underlying LLaMA model.
        config (LlamaConfig): The model configuration.
        device (torch.device): The compute device (CPU only).
    """

    MAX_PARAMS = 300_000_000  # 300M parameter limit

    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0", device: Optional[str] = None):
        """
        Initialize the BaseLlamaWrapper.

        Args:
            model_name: HuggingFace model identifier. Note: While TinyLlama is ~1.1B,
                        we load it with specific configurations to keep active parameters
                        low or use smaller variants if available. For this implementation,
                        we assume the user provides a valid small model or we adjust
                        config to reduce hidden size if possible (though loading a
                        pre-trained 1.1B model might exceed strict 300M if not careful).
                        To strictly adhere to <300M, we will default to a custom config
                        if the model name suggests a large model, or load a known small
                        variant. For robustness, we load the model and check params.
            device: Override device. Defaults to 'cpu'.
        """
        # Enforce CPU-only constraint from config
        if device is None:
            device = "cpu"
        self.device = torch.device(device)

        # Load configuration and model
        # For strict <300M, we might need to instantiate a custom config if the
        # default model is too large. Here we attempt to load, then verify.
        try:
            self.config = LlamaConfig.from_pretrained(model_name)
            
            # Check parameter count immediately
            # If the pre-trained model is too large, we might need to re-init
            # with a smaller config. For this task, we assume a valid small model
            # is passed or we adjust.
            # Let's check the config dimensions.
            total_params = self._count_parameters()
            if total_params > self.MAX_PARAMS:
                # Attempt to create a smaller configuration if possible
                # This is a fallback for strict constraints
                self.config.hidden_size = 256
                self.config.num_attention_heads = 4
                self.config.num_hidden_layers = 4
                self.config.intermediate_size = 512
                total_params = self._count_parameters()
                if total_params > self.MAX_PARAMS:
                    raise ValueError(
                        f"Model configuration results in {total_params} parameters, "
                        f"exceeding the {self.MAX_PARAMS} limit. "
                        "Please specify a smaller model or adjust config dimensions."
                    )

            self.model = LlamaForCausalLM(self.config)
            self.model.to(self.device)
            self.model.eval()

        except OSError as e:
            # Handle missing model files or invalid paths
            raise RuntimeError(f"Failed to load model '{model_name}': {e}")

        validate_config() # Ensure global config constraints are met

    def _count_parameters(self) -> int:
        """Count total trainable parameters in the current config/model."""
        return sum(p.numel() for p in self.model.parameters())

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> CausalLMOutputWithPast:
        """
        Perform a forward pass through the model.

        Args:
            input_ids: Input token IDs of shape (batch_size, seq_len).
            attention_mask: Attention mask of shape (batch_size, seq_len).
            labels: Optional labels for loss computation.

        Returns:
            CausalLMOutputWithPast containing logits, hidden states, etc.
        """
        input_ids = input_ids.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
        if labels is not None:
            labels = labels.to(self.device)

        with torch.no_grad() if labels is None else torch.enable_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
                **kwargs
            )
        return outputs

    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 50,
        temperature: float = 1.0,
        do_sample: bool = False,
        **kwargs
    ) -> torch.Tensor:
        """
        Generate text from the model.

        Args:
            input_ids: Input token IDs.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            do_sample: Whether to use sampling.

        Returns:
            Generated token IDs.
        """
        input_ids = input_ids.to(self.device)
        
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "pad_token_id": self.config.pad_token_id,
            **kwargs
        }

        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                **generation_kwargs
            )
        return output_ids

    def get_hidden_states(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, ...]:
        """
        Extract hidden states from all layers.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.

        Returns:
            Tuple of hidden states for each layer.
        """
        input_ids = input_ids.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )
        return outputs.hidden_states

    def save_checkpoint(self, path: str) -> None:
        """
        Save the model and config to disk.

        Args:
            path: Directory path to save the checkpoint.
        """
        save_path = os.path.join(path, "model")
        self.model.save_pretrained(save_path)
        self.config.save_pretrained(save_path)

    @classmethod
    def load_checkpoint(cls, path: str, device: Optional[str] = None) -> "BaseLlamaWrapper":
        """
        Load a model from a saved checkpoint.

        Args:
            path: Directory path containing the saved model.
            device: Override device.

        Returns:
            Loaded BaseLlamaWrapper instance.
        """
        if device is None:
            device = "cpu"
        
        # Load config first to ensure dimensions match
        config = LlamaConfig.from_pretrained(path)
        
        # Create wrapper with config
        wrapper = cls.__new__(cls)
        wrapper.config = config
        wrapper.device = torch.device(device)
        
        # Load model
        wrapper.model = LlamaForCausalLM.from_pretrained(path, config=config)
        wrapper.model.to(wrapper.device)
        wrapper.model.eval()
        
        return wrapper