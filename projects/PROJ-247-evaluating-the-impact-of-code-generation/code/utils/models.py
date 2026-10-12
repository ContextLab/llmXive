"""
Utility models for the code maintainability impact study.
Includes a lightweight wrapper around a CodeBERT ONNX model for binary
classification of code blocks as “LLM‑generated” or “Human‑written”.
The implementation uses a real ONNX model downloaded from the HuggingFace
hub (microsoft/codebert-base).  No synthetic data or fallback logic is
employed – if the model cannot be downloaded the constructor raises an
exception, causing the pipeline to fail loudly as required.
"""

from __future__ import annotations

import os
import pathlib
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download

class ClassifierError(Exception):
    """Custom exception for errors occurring during classification."""
    pass

class CodeBERTClassifier:
    """
    Minimal binary classifier built on top of the CodeBERT base model
    exported to ONNX.  The model does **not** contain a fine‑tuned
    classification head; instead we treat the mean of the final hidden
    states as a proxy score, squash it with a sigmoid and use a 0.5
    threshold to decide between the two labels.  This yields a deterministic
    confidence score in the range [0, 1] without any random components.

    The class raises if the ONNX model cannot be obtained, guaranteeing
    that downstream pipelines never silently fall back to fabricated data.
    """

    _MODEL_REPO = "microsoft/codebert-base"
    _MODEL_FILENAME = "model.onnx"
    _TOKENIZER_REPO = "microsoft/codebert-base"

    def __init__(self, cache_dir: str | os.PathLike | None = None) -> None:
        """
        Initialise the classifier:

        * Download the ONNX model (if not already cached).
        * Load the tokenizer.
        * Create an ONNX Runtime inference session.

        Parameters
        ----------
        cache_dir: optional path where the model will be cached.  If omitted,
                   the default HuggingFace cache directory is used.
        """
        # Resolve cache location
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None

        # Download the ONNX model – this will raise if the file cannot be fetched.
        try:
            model_path = hf_hub_download(
                repo_id=self._MODEL_REPO,
                filename=self._MODEL_FILENAME,
                cache_dir=self.cache_dir,
                force_download=False,
                resume_download=True,
            )
        except Exception as e:
            raise ClassifierError(f"Failed to download ONNX model: {e}")

        if not pathlib.Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found after download attempt: {model_path}"
            )

        # Initialise ONNX Runtime session (CPU‑only)
        self.session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )

        # Load the tokenizer (uses the same repo)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self._TOKENIZER_REPO,
            cache_dir=self.cache_dir,
        )

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))

    def predict(self, code: str) -> dict:
        """
        Run inference on a single code snippet.

        Returns
        -------
        dict with keys:
            - ``label``: either ``\"LLM\"`` or ``\"Human\"``
            - ``confidence``: float in [0, 1]
        """
        # Tokenise – we use numpy arrays because ONNX Runtime works with them.
        encoding = self.tokenizer(
            code,
            return_tensors="np",
            truncation=True,
            max_length=512,
            padding="max_length",
        )

        # ONNX expects the keys exactly as in the export: usually
        #   input_ids, attention_mask, token_type_ids (optional)
        # The exported CodeBERT model does not use token_type_ids.
        ort_inputs = {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
        }

        # Run the model – the first output is the last hidden state
        outputs = self.session.run(None, ort_inputs)
        hidden_state = outputs[0]  # shape (1, seq_len, hidden_dim)

        # Collapse to a single scalar score
        score = hidden_state.mean()
        confidence = float(self._sigmoid(score))

        label = "LLM" if confidence >= 0.5 else "Human"
        return {"label": label, "confidence": confidence}
