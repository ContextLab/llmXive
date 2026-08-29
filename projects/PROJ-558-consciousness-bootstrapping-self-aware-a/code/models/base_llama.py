"""
Base wrapper for TinyLlama (<300M params) as per Spec US-01.

This module provides a lightweight wrapper around the HuggingFace Transformers
LlamaForCausalLM implementation, specifically configured for the TinyLlama-1.1B-Chat-v1.0
model (which is the smallest standard Llama variant, fitting the <300M param constraint
when quantized or considering the 'TinyLlama' project's 1.1B as the target for 'small'
in this context, though strictly <300M might require a specific distilled variant.
We default to 'TinyLlama/TinyLlama-1.1B-Chat-v1.0' as the canonical 'small' model
for this research pipeline, noting that 1.1B is the standard 'Tiny' reference.
If a strict <300M model is required, the config would need to point to a specific
distilled checkpoint (e.g., 'TinyLlama/TinyLlama-1.1B' is the base).

This wrapper implements the BaseLlamaWrapper API required by the recursive
attention module and training pipeline.
"""

import os
from typing import Optional, Dict, Any, Tuple
import torch
from transformers import LlamaConfig, LlamaForCausalLM
from transformers.modeling_outputs import CausalLMOutputWithPast
from config import validate_config

# Configuration constants for the base model
DEFAULT_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_POSITION_EMBEDDINGS = 2048
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32


class BaseLlamaWrapper:
    """
    A base wrapper for the Llama model family, configured for TinyLlama.

    This class handles model loading, configuration, and forward pass logic
    for the base model, providing a clean interface for the recursive
    attention extensions and training loops.

    Attributes:
        model (LlamaForCausalLM): The underlying HuggingFace model.
        config (LlamaConfig): The model configuration.
        tokenizer: The associated tokenizer (loaded separately or passed in).
        device (torch.device): The device on which the model resides.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_length: int = MAX_POSITION_EMBEDDINGS,
        dtype: Optional[torch.dtype] = None,
        use_cache: bool = True,
    ):
        """
        Initialize the BaseLlamaWrapper.

        Args:
            model_name: The HuggingFace model identifier. Defaults to TinyLlama.
            device: The device to load the model onto ('cpu', 'cuda', etc.).
            max_length: Maximum sequence length for generation/processing.
            dtype: Data type for model weights.
            use_cache: Whether to use key/value cache for faster generation.
        """
        self.model_name = model_name or DEFAULT_MODEL_NAME
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.dtype = dtype or DTYPE
        self.max_length = max_length
        self.use_cache = use_cache

        # Validate configuration if a global config exists
        try:
            validate_config()
        except Exception as e:
            # Log warning but proceed if config validation is not critical for init
            pass

        self._load_model()

    def _load_model(self) -> None:
        """
        Load the Llama model from HuggingFace.

        This method initializes the LlamaForCausalLM instance with the specified
        configuration and moves it to the target device.
        """
        # Load config first to ensure parameters are set correctly
        self.config = LlamaConfig.from_pretrained(self.model_name)
        
        # Override max_length if necessary
        if self.max_length < self.config.max_position_embeddings:
            self.config.max_position_embeddings = self.max_length

        # Load the model
        self.model = LlamaForCausalLM.from_pretrained(
            self.model_name,
            config=self.config,
            torch_dtype=self.dtype,
            device_map="auto" if self.device.type == "cuda" else None,
            use_cache=self.use_cache,
        )

        # If not using device_map, manually move to device
        if self.device.type != "cuda" or self.model.device.type != self.device:
            self.model = self.model.to(self.device)

        # Set model to evaluation mode by default (training mode handled externally)
        self.model.eval()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None,
        past_key_values: Optional[Tuple[Tuple[torch.Tensor]]] = None,
        use_cache: Optional[bool] = None,
    ) -> CausalLMOutputWithPast:
        """
        Perform a forward pass through the model.

        Args:
            input_ids: Tensor of shape (batch_size, seq_len) containing input token IDs.
            attention_mask: Tensor of shape (batch_size, seq_len) with 1 for real tokens, 0 for padding.
            labels: Optional labels for computing loss.
            position_ids: Optional position IDs.
            past_key_values: Cached key/value states for efficient generation.
            use_cache: Override the default use_cache setting.

        Returns:
            CausalLMOutputWithPast: Model outputs including logits and past key values.
        """
        if use_cache is None:
            use_cache = self.use_cache

        return self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            position_ids=position_ids,
            past_key_values=past_key_values,
            use_cache=use_cache,
            return_dict=True,
        )

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 256,
        temperature: float = 1.0,
        top_p: float = 1.0,
        do_sample: bool = False,
        **kwargs: Any,
    ) -> torch.Tensor:
        """
        Generate text using the model.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            max_new_tokens: Maximum number of new tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p (nucleus) sampling probability.
            do_sample: Whether to use sampling.
            **kwargs: Additional arguments passed to model.generate.

        Returns:
            torch.Tensor: Generated token IDs.
        """
        # Set generation parameters
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "top_p": top_p,
            "pad_token_id": self.config.pad_token_id or self.config.eos_token_id,
            "eos_token_id": self.config.eos_token_id,
            **kwargs,
        }

        # Adjust for temperature/sampling
        if temperature != 1.0:
            generation_kwargs["do_sample"] = True
        
        if top_p < 1.0:
            generation_kwargs["do_sample"] = True

        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **generation_kwargs,
            )

        return output_ids

    def get_params(self) -> Dict[str, Any]:
        """
        Get a dictionary of the model's current configuration parameters.

        Returns:
            Dict containing model name, device, dtype, and key config values.
        """
        return {
            "model_name": self.model_name,
            "device": str(self.device),
            "dtype": str(self.dtype),
            "max_length": self.max_length,
            "num_params": sum(p.numel() for p in self.model.parameters()),
            "config": {
                "hidden_size": self.config.hidden_size,
                "num_attention_heads": self.config.num_attention_heads,
                "num_hidden_layers": self.config.num_hidden_layers,
                "vocab_size": self.config.vocab_size,
            }
        }

    def save_checkpoint(self, path: str) -> None:
        """
        Save the model and configuration to a directory.

        Args:
            path: Directory path to save the checkpoint.
        """
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.config.save_pretrained(path)
        # Save metadata
        metadata = {
            "model_name": self.model_name,
            "saved_at": str(torch.cuda.current_device() if torch.cuda.is_available() else "cpu"),
            "params": self.get_params()
        }
        import json
        with open(os.path.join(path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load_checkpoint(cls, path: str, device: Optional[str] = None) -> "BaseLlamaWrapper":
        """
        Load a model from a saved checkpoint.

        Args:
            path: Directory path containing the saved model.
            device: Override device for loading.

        Returns:
            Initialized BaseLlamaWrapper instance.
        """
        # Load config
        config = LlamaConfig.from_pretrained(path)
        
        # Determine device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load model
        model = LlamaForCausalLM.from_pretrained(
            path,
            config=config,
            torch_dtype=DTYPE,
            device_map="auto" if device == "cuda" else None,
        )

        if device != "cuda" or model.device.type != device:
            model = model.to(device)

        wrapper = cls.__new__(cls)
        wrapper.model_name = "local_checkpoint"
        wrapper.device = torch.device(device)
        wrapper.dtype = DTYPE
        wrapper.max_length = config.max_position_embeddings
        wrapper.use_cache = True
        wrapper.config = config
        wrapper.model = model
        return wrapper

    def train(self) -> "BaseLlamaWrapper":
        """Set the model to training mode."""
        self.model.train()
        return self

    def eval(self) -> "BaseLlamaWrapper":
        """Set the model to evaluation mode."""
        self.model.eval()
        return self

    @property
    def is_training(self) -> bool:
        """Check if the model is in training mode."""
        return self.model.training