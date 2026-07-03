"""
GPT-2 Medium Baseline Wrapper.

This module provides a wrapper around the Hugging Face GPT-2 Medium model,
standardizing the interface for both the baseline and the spatial memory variant.
It handles model loading, tokenization, and inference logic.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from typing import Dict, Any, List, Optional, Tuple
import os

class GPT2Baseline:
    """
    Wrapper for GPT-2 Medium (baseline model).
    
    Exposes a unified interface compatible with the spatial memory variant
    for fair comparison in the training loop and evaluation scripts.
    """
    
    def __init__(self, model_name: str = "gpt2-medium", device: str = None):
        """
        Initialize the GPT-2 baseline model.
        
        Args:
            model_name: Hugging Face model identifier.
            device: Target device ('cuda' or 'cpu'). Defaults to auto-detection.
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        
        if self.device == "cpu":
            self.model = self.model.to(self.device)
        
        # Ensure pad token is set (GPT-2 often lacks it)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.config = self.model.config
        self.is_spatial = False  # Flag to distinguish from spatial variant

    def encode(self, text: str, return_tensors: str = "pt") -> Dict[str, torch.Tensor]:
        """
        Tokenize input text.
        
        Args:
            text: Input string.
            return_tensors: Format of returned tensors ('pt', 'tf', etc.).
            
        Returns:
            Dictionary of input tensors (input_ids, attention_mask, etc.).
        """
        return self.tokenizer(
            text,
            return_tensors=return_tensors,
            padding=True,
            truncation=True,
            max_length=self.config.max_position_embeddings
        )

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs.
            skip_special_tokens: Whether to skip special tokens in decoding.
            
        Returns:
            Decoded string.
        """
        return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 50,
        temperature: float = 1.0,
        top_k: int = 50,
        do_sample: bool = False,
        **kwargs
    ) -> torch.Tensor:
        """
        Generate text conditioned on input tokens.
        
        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_k: Top-k sampling parameter.
            do_sample: Whether to use sampling.
            
        Returns:
            Generated token sequence (input + new tokens).
        """
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
        
        # Prepare generation config
        generation_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "max_new_tokens": max_new_tokens,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            **kwargs
        }
        
        if do_sample:
            generation_kwargs.update({
                "temperature": temperature,
                "top_k": top_k,
                "do_sample": True
            })
        
        with torch.no_grad():
            output_ids = self.model.generate(**generation_kwargs)
        
        return output_ids

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass for training or inference.
        
        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            labels: Target labels for loss calculation.
            
        Returns:
            Dictionary containing logits and loss (if labels provided).
        """
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        result = {
            "logits": outputs.logits,
            "loss": outputs.loss if labels is not None else None
        }
        
        return result

    def get_memory_footprint(self) -> Dict[str, Any]:
        """
        Estimate model memory usage.
        
        Returns:
            Dictionary with model size and estimated memory usage.
        """
        param_count = sum(p.numel() for p in self.model.parameters())
        memory_bytes = param_count * 2  # float16 estimation
        
        return {
            "param_count": param_count,
            "estimated_memory_mb": memory_bytes / (1024 * 1024),
            "device": self.device
        }

    def save_pretrained(self, output_dir: str):
        """
        Save model and tokenizer to disk.
        
        Args:
            output_dir: Directory path to save artifacts.
        """
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

    def __repr__(self) -> str:
        return f"GPT2Baseline(model={self.model_name}, device={self.device})"
