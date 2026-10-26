"""
frozen_distilbert_classifier.py
-------------------------------
Implements the CPU‑only frozen DistilBERT intent classifier required for the
Gatekeeper pipeline (Task T011).

The public API matches the expectations of the unit tests in
`tests/unit/test_classifier.py`:

* ``FrozenDistilBERTClassifier`` – loads the model with a single retry,
  enforces CPU execution, and aborts with ``sys.exit(1)`` on a second
  failure (logging “Critical: Model Unavailable”).

* ``run_inference`` – runs a single inference through the classifier,
  profiles latency and peak RAM using the shared ``profile_execution``
  utility, and returns a dictionary containing the inferred intent label,
  its confidence score, and the profiling metrics.

The implementation deliberately avoids any GPU usage and relies only on
the standard ``transformers`` pipeline for text‑classification.
"""

import sys
import logging
from typing import List, Any, Dict

import torch
from transformers import pipeline  # type: ignore

from llmxive_toolkit import get_logger
from utils.profiling import profile_execution

__all__ = ["FrozenDistilBERTClassifier", "run_inference"]

class FrozenDistilBERTClassifier:
    """
    Wrapper around a frozen DistilBERT model fine‑tuned on SST‑2.
    The model is loaded on CPU only; if the first load attempt fails
    (e.g., due to cache corruption), a single retry is performed.
    On a second failure the process exits with status code 1 and logs a
    critical message as required by the specification.
    """

    def __init__(self, model_id: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_id = model_id
        self.log = get_logger(__name__)
        self.pipeline = None  # type: ignore
        self._load_model()

    def _load_model(self) -> None:
        """
        Load the ``transformers`` pipeline with CPU enforcement.
        Retries once on failure; aborts with ``sys.exit(1)`` on the second
        failure while logging a critical error.
        """
        attempts = 0
        while attempts < 2:
            try:
                device = 0 if torch.cuda.is_available() else "cpu"
                # ``pipeline`` returns a callable that performs inference.
                self.pipeline = pipeline(
                    "text-classification",
                    model=self.model_id,
                    tokenizer=self.model_id,
                    device=device,
                )
                # Enforce CPU: the underlying model must not be on CUDA.
                if str(self.pipeline.model.device).startswith("cuda"):
                    raise RuntimeError("Model loaded on CUDA despite CPU‑only enforcement")
                # Successful load – exit the retry loop.
                return
            except Exception as exc:
                attempts += 1
                self.log.warning(f"Model load attempt {attempts} failed: {exc}")
                if attempts >= 2:
                    self.log.critical("Critical: Model Unavailable")
                    sys.exit(1)

    def run_inference(self, text: str, candidate_labels: List[str] = None) -> Dict[str, Any]:
        """
        Perform inference on a single text string, profile the execution,
        and return a dictionary compatible with the unit tests.

        Parameters
        ----------
        text: str
            Input text to classify.
        candidate_labels: List[str] | None
            Not used by the underlying DistilBERT model; present for API
            compatibility with potential future extensions.

        Returns
        -------
        dict
            ``{
                "inference_time_ms": float,
                "peak_ram_mb": float,
                "label": str,
                "score": float
            }``
        """
        # ``profile_execution`` expects a callable and its arguments.
        # It returns a dict containing at least ``latency_ms``, ``peak_ram_mb``,
        # and ``data`` (the raw pipeline output).
        profile = profile_execution(self.pipeline, text)

        # Extract the raw model output from the profiling payload.
        raw_output = profile.get("data")
        # The transformers pipeline may return a list of dicts; normalise.
        if isinstance(raw_output, list) and len(raw_output) > 0:
            raw_output = raw_output[0]

        # Defensive extraction of label and score.
        label = raw_output.get("labels")
        if isinstance(label, list) and len(label) > 0:
            label = label[0]

        score = raw_output.get("scores")
        if isinstance(score, list) and len(score) > 0:
            score = score[0]

        return {
            "inference_time_ms": profile.get("latency_ms"),
            "peak_ram_mb": profile.get("peak_ram_mb"),
            "label": label,
            "score": score,
        }

# ----------------------------------------------------------------------
# Helper function kept for backward compatibility with older imports.
# ----------------------------------------------------------------------
def run_inference(classifier: FrozenDistilBERTClassifier, episode_id: str, text: str) -> Dict[str, Any]:
    """
    Compatibility wrapper used by older code paths. It forwards the call
    to ``FrozenDistilBERTClassifier.run_inference`` ignoring ``episode_id``
    (which is retained for signature compatibility).

    Parameters
    ----------
    classifier: FrozenDistilBERTClassifier
        The instantiated classifier.
    episode_id: str
        Identifier of the episode – not used in the current implementation.
    text: str
        Text to classify.

    Returns
    -------
    dict
        Same structure as ``FrozenDistilBERTClassifier.run_inference``.
    """
    # ``episode_id`` is intentionally ignored; the function is a thin shim.
    return classifier.run_inference(text)