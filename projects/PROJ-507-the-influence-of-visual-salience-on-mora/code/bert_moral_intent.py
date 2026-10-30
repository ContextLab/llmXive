"""
T015 – Wrapper for the moral-intent model.
Provides a preservation score based on image captions and BERT embeddings.
"""
import hashlib
import logging
from pathlib import Path
from typing import Tuple

import torch
import numpy as np
from scipy.stats import pearsonr
from transformers import (
    AutoModelForSequenceClassification, 
    AutoTokenizer, 
    pipeline, 
    AutoConfig
)
from huggingface_hub import hf_hub_download

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Constants
BERT_MODEL_ID = "bert-base-uncased"
CAPTION_MODEL_ID = "nlpconnect/vit-gpt2-image-captioning"
# Example hash for bert-base-uncased pytorch_model.bin (simplified for implementation)
# In a real scenario, this would be the exact SHA-256 of the fine-tuned weights.
EXPECTED_HASH = "8f69a7c6785e9d3e7b4f9a8c7d6e5f4a3b2c1d0e" 

def compute_model_checksum() -> str:
    """
    Compute the SHA-256 checksum of the BERT model file.
    """
    try:
        # Download the model weights file to compute its hash
        model_path = hf_hub_download(repo_id=BERT_MODEL_ID, filename="pytorch_model.bin")
        sha256_hash = hashlib.sha256()
        with open(model_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log.error(f"Checksum computation failed: {e}")
        return ""

def _load_bert() -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
    """Load the BERT model and tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(BERT_MODEL_ID)
    model.eval()
    return model, tokenizer

def _get_caption_pipe():
    """Create the image-to-text pipeline."""
    return pipeline("image-to-text", model=CAPTION_MODEL_ID)

def _generate_caption(image_path: Path | str) -> str:
    """Generate a short English caption for image_path."""
    try:
        pipe = _get_caption_pipe()
        result = pipe(str(image_path))
        return result[0]['generated_text']
    except Exception as e:
        log.error(f"Caption generation failed for {image_path}: {e}")
        raise RuntimeError(f"Captioning error: {e}")

def _encode_caption(caption: str) -> torch.Tensor:
    """Encode caption with BERT and return the CLS hidden state."""
    model, tokenizer = _load_bert()
    inputs = tokenizer(caption, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model.bert(**inputs)
        # CLS token is the first token
        cls_embedding = outputs.last_hidden_state[:, 0, :]
    return cls_embedding.squeeze().cpu()

def compute_preservation_score(original_image_path: Path | str, manipulated_image_path: Path | str) -> float:
    """
    Compute a moral-intent preservation score between two images.
    Returns the Pearson correlation between the CLS vectors of their captions.
    """
    try:
        cap_orig = _generate_caption(original_image_path)
        cap_man = _generate_caption(manipulated_image_path)

        vec_orig = _encode_caption(cap_orig).numpy()
        vec_man = _encode_caption(cap_man).numpy()

        # If vectors are identical, correlation is 1.0
        if np.array_equal(vec_orig, vec_man):
            return 1.0
        
        corr, _ = pearsonr(vec_orig, vec_man)
        return float(corr)
    except Exception as e:
        log.error(f"Preservation score failed: {e}")
        raise RuntimeError(f"Preservation score error: {e}")
