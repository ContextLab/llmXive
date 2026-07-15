"""
Student model implementation for CPU-tractable distillation.

Defines a lightweight transformer model based on DistilBERT-base-uncased
architecture, constrained to <100M parameters, suitable for CPU inference
without CUDA dependencies.
"""
import torch
import torch.nn as nn
from torch.nn import CrossEntropyLoss, MSELoss
from transformers import DistilBertConfig, DistilBertModel
from transformers.modeling_outputs import SequenceClassifierOutput

from utils.logger import get_logger
from models.synthetic_problem import SyntheticProblem

logger = get_logger(__name__)

# Configuration for a lightweight DistilBERT-like model
# DistilBERT-base-uncased has ~66M parameters, well under the 100M limit.
# We use a custom configuration to ensure CPU optimization and strict parameter limits.
DEFAULT_CONFIG = {
    "vocab_size": 30522,  # Standard BERT vocab size
    "dim": 768,           # Hidden size
    "n_heads": 12,        # Attention heads
    "n_layers": 6,        # Transformer layers (DistilBERT uses 6 vs BERT's 12)
    "dim_ffn": 3072,      # Feed-forward dimension
    "dropout": 0.1,
    "activation": "gelu",
    "max_position_embeddings": 512,
    "num_labels": 2,      # Binary classification for logical entailment/solvability
}


class DistilBERTStudent(nn.Module):
    """
    A DistilBERT-based student model for logical reasoning tasks.
    
    This model is designed to be CPU-tractable (<100M parameters) and
    does not require CUDA. It wraps the HuggingFace DistilBertModel
    with a classification head suitable for the synthetic problem domain.
    """

    def __init__(self, config_dict: dict = None):
        super().__init__()
        
        # Merge default with provided config
        if config_dict is None:
            config_dict = DEFAULT_CONFIG.copy()
        else:
            base = DEFAULT_CONFIG.copy()
            base.update(config_dict)
            config_dict = base

        # Create HuggingFace config
        self.hf_config = DistilBertConfig(
            vocab_size=config_dict["vocab_size"],
            dim=config_dict["dim"],
            n_heads=config_dict["n_heads"],
            n_layers=config_dict["n_layers"],
            hidden_dim=config_dict["dim_ffn"],
            dropout=config_dict["dropout"],
            activation=config_dict["activation"],
            max_position_embeddings=config_dict["max_position_embeddings"],
            num_labels=config_dict["num_labels"],
            attention_dropout=config_dict["dropout"],
            hidden_dropout=config_dict["dropout"],
        )

        # Initialize the transformer backbone
        self.bert = DistilBertModel(self.hf_config)
        
        # Classification head
        self.pre_classifier = nn.Linear(config_dict["dim"], config_dict["dim"])
        self.classifier = nn.Linear(config_dict["dim"], config_dict["num_labels"])
        self.dropout = nn.Dropout(config_dict["dropout"])

        # Log parameter count
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"Initialized DistilBERTStudent with {total_params:,} parameters")
        if total_params >= 100_000_000:
            logger.warning(f"Parameter count {total_params} exceeds 100M limit!")

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        labels=None,
        position_ids=None,
        head_mask=None,
        inputs_embeds=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        """
        Forward pass for the student model.
        
        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            labels: Optional labels for loss computation
            ... (other standard transformer args)
        
        Returns:
            SequenceClassifierOutput with loss, logits, and hidden states
        """
        return_dict = return_dict if return_dict is not None else self.hf_config.use_return_dict

        # Get transformer outputs
        distilbert_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        # Get the first token embedding (CLS equivalent)
        hidden_state = distilbert_output.last_hidden_state
        pooled_output = hidden_state[:, 0]

        # Apply classification head
        pooled_output = self.pre_classifier(pooled_output)
        pooled_output = nn.ReLU()(pooled_output)
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            # Compute cross-entropy loss for classification
            loss_fct = CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.hf_config.num_labels), labels.view(-1))

        if not return_dict:
            output = (logits,) + distilbert_output[1:]
            return ((loss,) + output) if loss is not None else output

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=distilbert_output.hidden_states,
            attentions=distilbert_output.attentions,
        )

    def count_parameters(self):
        """Returns the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def save_pretrained(self, save_directory):
        """Save the model weights and config to a directory."""
        import os
        from pathlib import Path
        
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save weights
        torch.save(self.state_dict(), save_path / "pytorch_model.bin")
        
        # Save config
        import json
        config_path = save_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(self.hf_config.to_dict(), f, indent=2)
        
        logger.info(f"Model saved to {save_directory}")

    @classmethod
    def from_pretrained(cls, save_directory):
        """Load a model from a saved directory."""
        import os
        from pathlib import Path
        import json
        
        save_path = Path(save_directory)
        
        # Load config
        config_path = save_path / "config.json"
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        
        # Create model
        model = cls(config_dict)
        
        # Load weights
        weights_path = save_path / "pytorch_model.bin"
        state_dict = torch.load(weights_path, map_location="cpu")
        model.load_state_dict(state_dict)
        
        logger.info(f"Model loaded from {save_directory}")
        return model


def create_student_model(config_overrides=None):
    """
    Factory function to create a student model instance.
    
    Args:
        config_overrides: Optional dict to override default configuration.
    
    Returns:
        DistilBERTStudent instance
    """
    return DistilBERTStudent(config_overrides)


def main():
    """
    Standalone script to verify the student model initialization and parameter count.
    """
    logger.info("Initializing Student Model for CPU inference...")
    
    # Create model with default config
    model = create_student_model()
    model.eval()
    
    param_count = model.count_parameters()
    logger.info(f"Total parameters: {param_count:,}")
    
    # Verify CPU compatibility
    if torch.cuda.is_available():
        logger.warning("CUDA detected, but model is designed for CPU. Forcing CPU mode.")
    
    device = torch.device("cpu")
    model.to(device)
    
    # Test forward pass with dummy input
    dummy_input = torch.randint(0, 30522, (2, 10)).to(device)
    dummy_mask = torch.ones_like(dummy_input).to(device)
    
    with torch.no_grad():
        output = model(input_ids=dummy_input, attention_mask=dummy_mask)
    
    logger.info(f"Forward pass successful. Output logits shape: {output.logits.shape}")
    logger.info("Student model ready for distillation.")
    
    return model


if __name__ == "__main__":
    main()