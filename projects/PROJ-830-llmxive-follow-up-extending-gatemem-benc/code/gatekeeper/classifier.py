"""
Gatekeeper classifier module.

This module provides a frozen DistilBERT sentiment classifier that is used
to map SST‑2 sentiment labels to intent categories (e.g. ``positive`` →
``query`` and ``negative`` → ``deletion``).  In addition to the existing
public API (``ClassificationResult``, ``FrozenDistilBERTClassifier`` and
``run_intent_classification``), this file now implements a utility function
``evaluate_sentiment_accuracy`` which is used by the T010a unit test to
validate that the sentiment‑to‑intent mapping achieves at least 80 %
accuracy on a real‑world subset of the SST‑2 dataset.

The function streams the GLUE SST‑2 validation split, runs the classifier
on the first ``sample_size`` examples, and returns the classification
accuracy as a float.  If the accuracy falls below the ``threshold`` (default
0.80) a warning is emitted via the standard ``logging`` facility – the
pipeline does **not** abort, matching the task specification which asks for
a warning rather than a hard failure.
"""

import logging
from typing import List

import torch
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from gatekeeper.classifier import (
    ClassificationResult,
    FrozenDistilBERTClassifier,
    run_intent_classification,
)

__all__ = [
    "evaluate_sentiment_accuracy",
]


def evaluate_sentiment_accuracy(
    sample_size: int = 200,
    threshold: float = 0.80,
    device: str = "cpu",
) -> float:
    """
    Evaluate the sentiment‑to‑intent mapping accuracy on a real subset of the
    SST‑2 dataset.

    The function performs the following steps:

    1. Load the GLUE SST‑2 validation split (real data, no synthetic
       generation).  The dataset is small enough to fit in memory, and only
       the first ``sample_size`` examples are used.
    2. Initialise a ``FrozenDistilBERTClassifier`` (CPU‑only) which wraps the
       ``distilbert-base-uncased-finetuned-sst-2-english`` model.
    3. Run the classifier on the selected sentences via
       ``run_intent_classification``.
    4. Convert the classifier's ``ClassificationResult`` objects to binary
       sentiment labels (``positive`` → ``1``, ``negative`` → ``0``) and
       compare them against the ground‑truth ``label`` field from SST‑2
       (where ``1`` denotes positive sentiment).
    5. Compute the accuracy as ``correct / total`` and emit a warning if the
       accuracy is below ``threshold`` (the task requires a warning, not a
       hard abort).

    Parameters
    ----------
    sample_size : int, optional
        Number of examples to evaluate (default is 200).
    threshold : float, optional
        Minimum acceptable accuracy; a warning is logged if the result is
        lower (default is 0.80).
    device : str, optional
        Device to run the model on – forced to ``cpu`` for reproducibility
        (default is ``cpu``).

    Returns
    -------
    float
        The sentiment classification accuracy (range ``[0.0, 1.0]``).

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched (e.g., network issues).  The
        exception is propagated so that the test suite can surface the
        failure.
    """
    # Load the SST‑2 validation split from the GLUE benchmark.
    try:
        dataset = load_dataset("glue", "sst2", split="validation")
    except Exception as exc:
        raise RuntimeError(f"Failed to load SST‑2 dataset: {exc}") from exc

    # Ensure we have enough examples; if the dataset is smaller, use all.
    effective_size = min(sample_size, len(dataset))
    sentences: List[str] = [dataset[i]["sentence"] for i in range(effective_size)]
    true_labels: List[int] = [dataset[i]["label"] for i in range(effective_size)]

    # Initialise the frozen classifier.
    classifier = FrozenDistilBERTClassifier(device=device)

    # Run classification on the selected sentences.
    classification_results: List[ClassificationResult] = run_intent_classification(
        sentences, classifier
    )

    # Map ClassificationResult.label to the binary sentiment used by SST‑2.
    # The DistilBERT SST‑2 model returns ``positive`` or ``negative``.
    pred_labels: List[int] = [
        1 if result.label.lower() == "positive" else 0 for result in classification_results
    ]

    # Compute accuracy.
    correct = sum(p == t for p, t in zip(pred_labels, true_labels))
    accuracy = correct / effective_size if effective_size > 0 else 0.0

    if accuracy < threshold:
        logging.warning(
            "Sentiment‑to‑intent mapping accuracy below threshold: %.2f%% (threshold %.2f%%)",
            accuracy * 100,
            threshold * 100,
        )
    else:
        logging.info(
            "Sentiment‑to‑intent mapping accuracy: %.2f%% (meets threshold)",
            accuracy * 100,
        )

    return accuracy
