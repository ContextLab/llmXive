"""
TinyLSTM baseline architecture with int8 weight quantization.

This module implements a minimal LSTM-based language model designed for CPU
execution. It includes post-training quantization to int8 to reduce memory
footprint and improve inference speed on CPU, serving as a baseline for
comparison against the brain-inspired SparseAutoencoder model.
"""
import torch
import torch.nn as nn
import torch.quantization as quantization
from typing import Tuple, Optional, List, Dict, Any
from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

class TinyLSTM(nn.Module):
    """
    A minimal LSTM network for text generation.
    
    Attributes:
        embedding_dim: Dimension of the token embeddings.
        hidden_dim: Dimension of the LSTM hidden state.
        num_layers: Number of LSTM layers.
        vocab_size: Size of the vocabulary.
        dropout: Dropout probability.
    """
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 1,
        dropout: float = 0.1,
        quantize: bool = True
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.quantize = quantize

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Output projection
        self.fc = nn.Linear(hidden_dim, vocab_size)

        # Dropout for regularization
        self.dropout = nn.Dropout(dropout)

        if quantize:
            self._prepare_quantization()

    def _prepare_quantization(self):
        """
        Prepares the model for int8 quantization on CPU.
        
        Sets the quantization configuration and fuses modules where possible
        (e.g., Conv + BN, or Linear + ReLU) to optimize for quantized inference.
        """
        # Configure quantization for CPU (int8 weights, dynamic activations for LSTM)
        qconfig = quantization.get_default_qconfig('x86')
        self.qconfig = qconfig
        
        # Fuse modules if applicable (LSTM doesn't fuse in the same way as Conv,
        # but we prepare the structure)
        # For LSTM-based models, we typically use dynamic quantization for
        # better CPU performance on the recurrent layers.
        logger.info("Preparing TinyLSTM for int8 quantization...")
        
        # Apply dynamic quantization to the LSTM layer specifically
        # This converts the LSTM weights to int8 while keeping activations dynamic
        # which is the standard approach for RNNs on CPU.
        if self.quantize:
            # We will quantize after initialization or in a separate step
            # to allow for calibration if needed. For now, we mark it ready.
            pass

    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass through the TinyLSTM.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len).
            hidden: Optional initial hidden state (h_0, c_0).
        
        Returns:
            output: LSTM output of shape (batch_size, seq_len, hidden_dim).
            hidden: Final hidden state (h_n, c_n).
        """
        batch_size = x.size(0)
        seq_len = x.size(1)

        # Embedding
        embed_out = self.embedding(x)  # (batch, seq, embed_dim)
        embed_out = self.dropout(embed_out)

        # LSTM
        if hidden is None:
            # Initialize hidden state to zeros
            h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
            c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
            hidden = (h0, c0)

        lstm_out, hidden = self.lstm(embed_out, hidden)
        # lstm_out: (batch, seq, hidden_dim)

        # Project to vocab size
        # We can project the last time step or all time steps.
        # For generation, we usually use the last time step or a sequence-to-sequence approach.
        # Here we return the full sequence output for flexibility.
        output = self.fc(lstm_out)  # (batch, seq, vocab_size)

        return output, hidden

    def quantize_model(self, data_loader: Optional[Any] = None):
        """
        Applies dynamic quantization to the LSTM layers for CPU inference.
        
        Args:
            data_loader: Optional data loader for calibration (not strictly needed
                         for dynamic quantization of LSTM, but kept for API consistency).
        """
        if not self.quantize:
            logger.warning("Quantization is disabled in model config.")
            return

        logger.info("Applying dynamic quantization to LSTM layers...")
        
        # Dynamic quantization is particularly effective for LSTM/GRU on CPU.
        # It quantizes weights to int8 and activations to float16/dynamic.
        self.lstm = quantization.quantize_dynamic(
            self.lstm, {nn.LSTM}, dtype=torch.qint8
        )
        
        # Also quantize the final linear layer if beneficial
        self.fc = quantization.quantize_dynamic(
            self.fc, {nn.Linear}, dtype=torch.qint8
        )
        
        logger.info("Quantization complete. Model is now optimized for CPU.")

    def get_model_info(self) -> Dict[str, Any]:
        """Returns information about the model architecture and quantization status."""
        return {
            "type": "TinyLSTM",
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "is_quantized": self.quantize and isinstance(self.lstm, torch.nn.quantized.dynamic.LSTM),
            "device": "cpu"
        }


def create_baseline_model(
    vocab_size: int,
    use_quantization: bool = True
) -> TinyLSTM:
    """
    Factory function to create a TinyLSTM baseline model.
    
    Args:
        vocab_size: Size of the vocabulary.
        use_quantization: Whether to apply int8 weight quantization.
    
    Returns:
        Initialized TinyLSTM model.
    """
    config = get_config()
    
    # Use config defaults or override
    model = TinyLSTM(
        vocab_size=vocab_size,
        embedding_dim=64,
        hidden_dim=128,
        num_layers=2,
        dropout=0.1,
        quantize=use_quantization
    )
    
    if use_quantization:
        model.quantize_model()
    
    logger.info(f"Created TinyLSTM baseline model: {model.get_model_info()}")
    return model


def generate_text(
    model: TinyLSTM,
    seed_text: str,
    max_length: int = 50,
    temperature: float = 1.0,
    device: str = "cpu"
) -> str:
    """
    Generates text using the TinyLSTM model.
    
    Args:
        model: The TinyLSTM model instance.
        seed_text: Initial text to start generation.
        max_length: Maximum number of tokens to generate.
        temperature: Sampling temperature (lower = more deterministic).
        device: Device to run inference on (default: cpu).
    
    Returns:
        Generated text string.
    """
    model.eval()
    model.to(device)
    
    # Simple tokenization for demo (split by space)
    # In a real scenario, this would use a proper tokenizer aligned with training
    tokens = seed_text.split()
    vocab = sorted(list(set(tokens))) + ["<unk>", "<pad>", "<start>", "<end>"]
    token_to_idx = {t: i for i, t in enumerate(vocab)}
    idx_to_token = {i: t for t, i in token_to_idx.items()}
    vocab_size = len(vocab)
    
    # If model vocab doesn't match, we need to handle it or re-initialize
    # For this baseline, we assume a fixed vocab or dynamic adaptation
    # Here we just use the provided seed to infer a small vocab for demo
    # In production, the model would be loaded with a pre-trained vocab
    
    # Re-initialize model if vocab size mismatch (simplified for demo)
    if model.vocab_size != vocab_size:
        logger.warning(f"Vocab mismatch. Re-initializing model with vocab_size={vocab_size}")
        model = create_baseline_model(vocab_size, use_quantization=True)
        model.to(device)
        model.eval()
    
    input_ids = torch.tensor(
        [token_to_idx.get(t, token_to_idx["<unk>"]) for t in tokens],
        dtype=torch.long
    ).unsqueeze(0).to(device)  # (1, seq_len)
    
    generated_ids = input_ids.clone()
    
    with torch.no_grad():
        for _ in range(max_length):
            output, _ = model(input_ids)
            # Get logits for the last token
            logits = output[0, -1, :] / temperature
            probs = torch.softmax(logits, dim=0)
            next_token_id = torch.multinomial(probs, num_samples=1).item()
            
            generated_ids = torch.cat([generated_ids, torch.tensor([[next_token_id]]).to(device)], dim=1)
            input_ids = torch.tensor([[next_token_id]]).to(device)
            
            # Stop if end token generated (if in vocab)
            if next_token_id == token_to_idx.get("<end>", -1):
                break
    
    # Decode
    generated_tokens = [idx_to_token.get(i.item(), "<unk>") for i in generated_ids.flatten()]
    return " ".join(generated_tokens)


if __name__ == "__main__":
    # Demo: Create model and generate a short sample
    logger.info("Running TinyLSTM baseline demo...")
    
    # Create a small vocab for demo purposes
    demo_vocab_size = 1000
    model = create_baseline_model(demo_vocab_size, use_quantization=True)
    
    # Generate text
    seed = "The quick brown fox"
    output = generate_text(model, seed, max_length=20, temperature=0.8)
    
    info(f"Seed: {seed}")
    info(f"Generated: {output}")
    info("Baseline model ready for comparison.")
