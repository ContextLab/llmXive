"""
DistilGPT2 Fallback Wrapper.

This module provides a fallback model implementation using DistilGPT2.
It is used when memory constraints prevent loading the full GPT-2 Medium model.
"""

import torch
import logging
from typing import Optional, Dict, Any

from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


class DistilGPT2Fallback:
    """
    Wrapper for the DistilGPT2 model used as a memory-efficient fallback.

    This class implements the same interface as GPT2MediumBaseline to ensure
    seamless switching in the training loop.
    """

    def __init__(self, model_name: str = "distilgpt2"):
        """
        Initialize the DistilGPT2 fallback model.

        Args:
            model_name: Hugging Face model identifier.
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Loading DistilGPT2 fallback: {model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model (DistilGPT2 is smaller, usually fits in memory without quantization)
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
            # DistilGPT2 returns all hidden states; return the last one
            return outputs.hidden_states[-1]
