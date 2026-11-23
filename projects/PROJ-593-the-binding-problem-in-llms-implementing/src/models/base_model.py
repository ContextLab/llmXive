import torch
from transformers import DistilBertModel, DistilBertTokenizerFast
from typing import Dict, Any, Optional, Union, List, Tuple
import numpy as np


class DistilBERTWrapper:
    """
    Base model wrapper for DistilBERT running in CPU-only mode.
    Handles model loading, tokenization, and forward pass execution.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        device: Optional[str] = None,
        max_length: int = 512
    ):
        """
        Initialize the DistilBERT wrapper.

        Args:
            model_name: HuggingFace model identifier.
            device: Device to run on. Defaults to 'cpu' if not specified.
            max_length: Maximum sequence length for tokenization.
        """
        self.model_name = model_name
        self.max_length = max_length

        # Force CPU-only mode as per task requirement
        if device is None:
            self.device = torch.device("cpu")
        else:
            # Explicitly enforce CPU even if user passes 'cuda'
            self.device = torch.device("cpu")

        # Load model and tokenizer
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
        self.model = DistilBertModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode

    def tokenize(self, texts: Union[str, List[str]]) -> Dict[str, torch.Tensor]:
        """
        Tokenize input texts.

        Args:
            texts: Single string or list of strings to tokenize.

        Returns:
            Dictionary containing 'input_ids', 'attention_mask', and 'token_type_ids' (if applicable).
        """
        if isinstance(texts, str):
            texts = [texts]

        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length
        )

        # Move tensors to the correct device
        return {k: v.to(self.device) for k, v in encoded.items()}

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        output_hidden_states: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        Run a forward pass through the model.

        Args:
            input_ids: Tensor of token IDs.
            attention_mask: Optional attention mask.
            output_hidden_states: Whether to return all hidden states.

        Returns:
            Dictionary containing model outputs including hidden states.
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=output_hidden_states
            )

        return {
            "last_hidden_state": outputs.last_hidden_state,
            "hidden_states": outputs.hidden_states,
            "attention_mask": attention_mask
        }

    def get_activations(
        self,
        texts: Union[str, List[str]],
        layer_indices: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract activations from specific layers for a batch of texts.

        Args:
            texts: Input texts.
            layer_indices: Optional list of layer indices to extract. If None, returns all.

        Returns:
            Dictionary containing extracted activations.
        """
        inputs = self.tokenize(texts)
        outputs = self.forward(
            inputs["input_ids"],
            inputs["attention_mask"],
            output_hidden_states=True
        )

        hidden_states = outputs["hidden_states"]
        # hidden_states[0] is the embedding layer, [1] to [13] are transformer layers for DistilBERT
        # DistilBERT has 6 transformer layers, so indices 1-7 correspond to layers 0-5

        if layer_indices is not None:
            selected_layers = {}
            for idx in layer_indices:
                # Adjust index: hidden_states[0] is embeddings, so layer 0 is at index 1
                actual_idx = idx + 1
                if actual_idx < len(hidden_states):
                    selected_layers[f"layer_{idx}"] = hidden_states[actual_idx].cpu().numpy()
            return selected_layers
        else:
            # Return all transformer layer activations (excluding embeddings)
            return {
                f"layer_{i-1}": state.cpu().numpy()
                for i, state in enumerate(hidden_states[1:], start=1)
            }

    def save_model(self, path: str) -> None:
        """Save the model to a directory."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    @classmethod
    def load(cls, path: str) -> "DistilBERTWrapper":
        """Load a model from a directory."""
        wrapper = cls.__new__(cls)
        wrapper.model_name = path
        wrapper.max_length = 512
        wrapper.device = torch.device("cpu")
        wrapper.tokenizer = DistilBertTokenizerFast.from_pretrained(path)
        wrapper.model = DistilBertModel.from_pretrained(path)
        wrapper.model.to(wrapper.device)
        wrapper.model.eval()
        return wrapper


def load_distilbert_cpu(
    model_name: str = "distilbert-base-uncased",
    max_length: int = 512
) -> DistilBERTWrapper:
    """
    Convenience function to load a DistilBERT model in CPU-only mode.

    Args:
        model_name: HuggingFace model identifier.
        max_length: Maximum sequence length.

    Returns:
        Initialized DistilBERTWrapper instance.
    """
    return DistilBERTWrapper(model_name=model_name, device="cpu", max_length=max_length)
