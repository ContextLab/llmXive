"""
Base model wrapper for DistilBERT in CPU-only mode.

This module provides a wrapper around Hugging Face's DistilBERT model,
optimized for CPU execution. It includes utilities for loading the model
and tokenizer, and provides a clean interface for forward passes.
"""
import torch
from transformers import DistilBertModel, DistilBertTokenizerFast
from typing import Dict, Any, Optional, Union, List, Tuple
import numpy as np


class DistilBERTWrapper:
    """
    A wrapper class for DistilBERT model that ensures CPU-only operation.
    
    This class handles model loading, tokenization, and forward pass execution
    while enforcing CPU usage for reproducibility and resource constraints.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "cpu"):
        """
        Initialize the DistilBERT wrapper.
        
        Args:
            model_name: Hugging Face model identifier.
            device: Device to run the model on (forced to 'cpu' for this implementation).
        """
        if device != "cpu":
            raise ValueError("DistilBERTWrapper is designed for CPU-only mode. Please use device='cpu'.")
        
        self.device = device
        self.model_name = model_name
        
        # Load tokenizer and model
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
        self.model = DistilBertModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Cache for hidden states if needed
        self._last_hidden_states = None
    
    def tokenize(self, texts: Union[str, List[str]], 
                padding: str = "max_length", 
                truncation: bool = True,
                max_length: int = 512) -> Dict[str, torch.Tensor]:
        """
        Tokenize input texts.
        
        Args:
            texts: Single text or list of texts to tokenize.
            padding: Padding strategy ('max_length', 'longest', 'do_not_pad').
            truncation: Whether to truncate sequences to max_length.
            max_length: Maximum sequence length.
            
        Returns:
            Dictionary containing input_ids, attention_mask, and token_type_ids.
        """
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=padding,
            truncation=truncation,
            max_length=max_length
        )
        
        # Move tensors to the correct device
        return {k: v.to(self.device) for k, v in inputs.items()}
    
    def forward(self, input_ids: torch.Tensor, 
               attention_mask: Optional[torch.Tensor] = None,
               output_hidden_states: bool = True) -> Dict[str, Any]:
        """
        Run a forward pass through the model.
        
        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Optional attention mask.
            output_hidden_states: Whether to return all hidden states.
            
        Returns:
            Dictionary containing model outputs including last_hidden_state
            and hidden_states if requested.
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=output_hidden_states
            )
        
        result = {
            "last_hidden_state": outputs.last_hidden_state,
            "pooler_output": outputs.pooler_output,
            "hidden_states": outputs.hidden_states if output_hidden_states else None
        }
        
        self._last_hidden_states = result
        return result
    
    def extract_activations(self, texts: Union[str, List[str]], 
                           layer_indices: Optional[List[int]] = None,
                           head_indices: Optional[List[Tuple[int, int]]] = None,
                           max_length: int = 512) -> Dict[str, np.ndarray]:
        """
        Extract specific activations from the model.
        
        Args:
            texts: Input texts to process.
            layer_indices: Specific layers to extract (None for all).
            head_indices: Specific attention heads to extract (None for all).
            max_length: Maximum sequence length.
            
        Returns:
            Dictionary containing extracted activations as numpy arrays.
        """
        # Tokenize
        inputs = self.tokenize(texts, max_length=max_length)
        
        # Forward pass
        outputs = self.forward(inputs["input_ids"], inputs["attention_mask"])
        
        hidden_states = outputs["hidden_states"]
        if hidden_states is None:
            raise ValueError("Hidden states not available. Ensure output_hidden_states=True in forward().")
        
        # Convert to numpy
        activations = {}
        
        for i, layer_hidden in enumerate(hidden_states):
            layer_tensor = layer_hidden.cpu().numpy()
            
            if layer_indices is not None and i not in layer_indices:
                continue
            
            layer_key = f"layer_{i}"
            
            if head_indices is not None:
                # Extract specific heads (simplified: assuming multi-head attention structure)
                # DistilBERT uses multi-head attention but the hidden state is already projected
                # This is a simplified extraction for demonstration
                activations[layer_key] = layer_tensor
            else:
                activations[layer_key] = layer_tensor
        
        return activations
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model configuration and statistics.
        """
        config = self.model.config
        return {
            "model_name": self.model_name,
            "device": self.device,
            "num_layers": config.num_hidden_layers,
            "hidden_size": config.hidden_size,
            "num_attention_heads": config.num_attention_heads,
            "vocab_size": config.vocab_size,
            "max_position_embeddings": config.max_position_embeddings
        }


def load_distilbert_cpu(model_name: str = "distilbert-base-uncased") -> DistilBERTWrapper:
    """
    Convenience function to load a DistilBERT model in CPU-only mode.
    
    Args:
        model_name: Hugging Face model identifier.
        
    Returns:
        Initialized DistilBERTWrapper instance.
    """
    return DistilBERTWrapper(model_name=model_name, device="cpu")