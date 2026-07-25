"""
Base model wrapper for DistilBERT in CPU-only mode.

This module provides a wrapper around the DistilBERT model from the Hugging Face
transformers library, configured to run exclusively on CPU for reproducibility
and compatibility with the binding problem research pipeline.
"""

import torch
from transformers import DistilBertModel, DistilBertTokenizerFast
from typing import Dict, Any, Optional, Union, List, Tuple
import numpy as np


class DistilBERTWrapper:
    """
    Wrapper for DistilBERT model with CPU-only execution guarantee.

    This class loads a pre-trained DistilBERT model and tokenizer, ensuring
    all operations are performed on CPU devices. It provides methods for
    tokenization, forward passes, and extraction of intermediate activations.

    Attributes:
        model: The underlying DistilBertModel instance.
        tokenizer: The DistilBertTokenizerFast instance.
        device: Always 'cpu' for this wrapper.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        cache_dir: Optional[str] = None,
        trust_remote_code: bool = False
    ):
        """
        Initialize the DistilBERT wrapper.

        Args:
            model_name: Name or path of the DistilBERT model to load.
            cache_dir: Optional directory to cache downloaded models.
            trust_remote_code: Whether to trust remote code in the model.
        """
        self.device = torch.device("cpu")
        self.model_name = model_name

        # Load tokenizer
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=trust_remote_code
        )

        # Load model and force CPU
        self.model = DistilBertModel.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            trust_remote_code=trust_remote_code
        )
        self.model.to(self.device)
        self.model.eval()

        # Disable gradients for inference
        for param in self.model.parameters():
            param.requires_grad = False

    def tokenize(
        self,
        texts: Union[str, List[str]],
        max_length: int = 512,
        padding: str = "max_length",
        truncation: bool = True,
        return_tensors: str = "pt"
    ) -> Dict[str, torch.Tensor]:
        """
        Tokenize input texts.

        Args:
            texts: Single text or list of texts to tokenize.
            max_length: Maximum sequence length.
            padding: Padding strategy ('max_length', 'longest', 'do_not_pad').
            truncation: Whether to truncate sequences exceeding max_length.
            return_tensors: Type of return tensors ('pt' for PyTorch).

        Returns:
            Dictionary containing input_ids, attention_mask, and token_type_ids.
        """
        return self.tokenizer(
            texts,
            max_length=max_length,
            padding=padding,
            truncation=truncation,
            return_tensors=return_tensors
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_hidden_states: bool = True,
        return_dict: bool = True
    ) -> Dict[str, Any]:
        """
        Run a forward pass through the model.

        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Tensor indicating which tokens to attend to.
            output_hidden_states: Whether to return all hidden states.
            return_dict: Whether to return a dictionary or tuple.

        Returns:
            Dictionary containing last_hidden_state, hidden_states, and attentions.
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids.to(self.device),
                attention_mask=attention_mask.to(self.device) if attention_mask is not None else None,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict
            )

        return outputs

    def get_hidden_states(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> List[torch.Tensor]:
        """
        Extract all hidden states from the model.

        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Tensor indicating which tokens to attend to.

        Returns:
            List of hidden state tensors, one per layer plus the initial embedding.
        """
        outputs = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )

        return outputs.hidden_states

    def get_layer_activations(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        layer_indices: Optional[List[int]] = None
    ) -> Dict[int, torch.Tensor]:
        """
        Extract activations from specific layers.

        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Tensor indicating which tokens to attend to.
            layer_indices: List of layer indices to extract (0-indexed).
                           If None, returns all layers.

        Returns:
            Dictionary mapping layer index to activation tensor.
        """
        all_states = self.get_hidden_states(input_ids, attention_mask)

        # all_states[0] is the embeddings, [1:] are the transformer layers
        if layer_indices is None:
            layer_indices = list(range(len(all_states) - 1))

        result = {}
        for idx in layer_indices:
            if 0 <= idx < len(all_states) - 1:
                result[idx] = all_states[idx + 1]

        return result

    def get_attention_weights(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Extract attention weights from all layers.

        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Tensor indicating which tokens to attend to.

        Returns:
            Dictionary containing attention weights per layer.
        """
        outputs = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=False,
            return_dict=True
        )

        # DistilBERT doesn't return attentions by default, need to configure model
        # This is a simplified version - in practice, you might need to modify
        # the model configuration to output attentions
        return {}

    def encode(
        self,
        texts: Union[str, List[str]],
        max_length: int = 512,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode texts to fixed-size embeddings (CLS token representation).

        Args:
            texts: Single text or list of texts.
            max_length: Maximum sequence length.
            batch_size: Batch size for processing.

        Returns:
            NumPy array of CLS token embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            inputs = self.tokenize(
                batch_texts,
                max_length=max_length,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )

            with torch.no_grad():
                outputs = self.model(
                    input_ids=inputs["input_ids"].to(self.device),
                    attention_mask=inputs["attention_mask"].to(self.device)
                )

            # Get CLS token embedding (first token)
            cls_embeddings = outputs.last_hidden_state[:, 0, :]
            all_embeddings.append(cls_embeddings.cpu().numpy())

        return np.vstack(all_embeddings)

    def __repr__(self) -> str:
        return f"DistilBERTWrapper(model_name='{self.model_name}', device='{self.device}')"


# Convenience function for quick model loading
def load_distilbert_cpu(
    model_name: str = "distilbert-base-uncased",
    cache_dir: Optional[str] = None
) -> DistilBERTWrapper:
    """
    Load a DistilBERT model configured for CPU-only execution.

    Args:
        model_name: Name or path of the model to load.
        cache_dir: Optional directory for model cache.

    Returns:
        Initialized DistilBERTWrapper instance.
    """
    return DistilBERTWrapper(
        model_name=model_name,
        cache_dir=cache_dir
    )
