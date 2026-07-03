"""
GPT-2 Medium Baseline Wrapper.

This module provides a unified interface for the GPT-2 Medium baseline model.
It wraps the Hugging Face Transformers model to ensure consistent behavior
with the spatial memory variant and the fallback DistilGPT2 model.
"""

import torch
import logging
from typing import Optional, Dict, Any, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


class GPT2MediumBaseline:
    """
    Wrapper for the GPT-2 Medium model used as the non-spatial baseline.

    This class implements the standard interface expected by the training loop:
    - forward(input_ids, attention_mask) -> logits
    - generate(input_ids, max_length) -> generated_ids
    - get_num_params() -> int

    It handles quantization configuration via the `quantized` flag during initialization.
    """

    def __init__(self, model_name: str = "gpt2-medium", quantized: bool = True):
        """
        Initialize the GPT-2 Medium baseline.

        Args:
            model_name: Hugging Face model identifier.
            quantized: If True, attempts to load in 4-bit mode (requires bitsandbytes).
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.quantized = quantized
        
        logger.info(f"Loading GPT-2 Medium baseline: {model_name} (quantized={quantized})")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        if self.quantized:
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                logger.info("Loaded GPT-2 Medium in 4-bit quantized mode.")
            except ImportError:
                logger.warning("bitsandbytes not found, falling back to float16 loading.")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                device_map="auto"
            )

        self.model.eval()

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through the model.

        Args:
            input_ids: Tensor of shape (batch_size, seq_len)
            attention_mask: Optional tensor of shape (batch_size, seq_len)

        Returns:
            Logits tensor of shape (batch_size, seq_len, vocab_size)
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True
            )
            return outputs.logits

    def generate(self, input_ids: torch.Tensor, max_length: int = 50, **kwargs) -> torch.Tensor:
        """
        Generate text using the model.

        Args:
            input_ids: Tensor of shape (batch_size, seq_len)
            max_length: Maximum length of generated sequence.

        Returns:
            Generated token IDs tensor of shape (batch_size, new_seq_len)
        """
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_length=max_length,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs
            )
            return outputs

    def get_num_params(self) -> int:
        """Return the number of parameters in the model."""
        return sum(p.numel() for p in self.model.parameters())

    def set_train(self, mode: bool = True):
        """Set training mode."""
        self.model.train(mode)
    
    def get_hidden_states(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Extract hidden states from the model.
        
        Args:
            input_ids: Tensor of shape (batch_size, seq_len)
        
        Returns:
            Hidden states tensor of shape (batch_size, seq_len, hidden_dim)
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                output_hidden_states=True,
                return_dict=True
            )
            # Return the last hidden state
            return outputs.hidden_states[-1]
