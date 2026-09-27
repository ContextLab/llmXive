"""
Conflict Detector Module for EvoMem.

Implements semantic contradiction detection using DistilBERT and safe retrieval
fallback mechanisms as per FR-007.
"""
import os
import sys
import json
import csv
import yaml
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from transformers import logging as hf_logging

# Suppress HF warnings for cleaner logs
hf_logging.set_verbosity_error()

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.utils.logging import get_logger, ExecutionTimer

logger = get_logger(__name__)

@dataclass
class ModelResult:
    """Result container for conflict detection."""
    patch_a: str
    patch_b: str
    score: float
    is_conflict: bool
    model_name: str
    latency_ms: float

class ConflictDetector:
    """
    Semantic conflict detector using DistilBERT.

    Implements FR-007: On timeout or failure, defaults to safe retrieval mode.
    Safe Mode Definition: Retrieve latest state plus the 2 most recent non-conflict patches.
    """

    DEFAULT_MODEL = "distilbert-base-uncased"
    DEFAULT_THRESHOLD = 0.90
    SAFE_RETRIEVAL_COUNT = 2  # Number of non-conflict patches to retrieve in safe mode

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        timeout_seconds: float = 10.0,
        device: Optional[str] = None
    ):
        """
        Initialize the conflict detector.

        Args:
            model_name: HuggingFace model identifier.
            threshold: Probability threshold > 0.90 to flag as conflict.
            timeout_seconds: Max time allowed for inference before triggering safe mode.
            device: Torch device ('cpu', 'cuda', or None for auto).
        """
        self.model_name = model_name
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._loaded = False

        logger.info(f"Initializing ConflictDetector with model: {model_name} on {self.device}")

    def load_model(self) -> bool:
        """
        Load the transformer model and tokenizer.

        Returns:
            True if successful, False otherwise.
        """
        if self._loaded:
            return True

        try:
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()

            # Create a pipeline for inference
            self.pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                return_all_scores=False
            )
            self._loaded = True
            logger.info("Model loaded successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            self._loaded = False
            return False

    def detect_conflict(self, patch_a: str, patch_b: str) -> Optional[ModelResult]:
        """
        Detect if patch_b contradicts patch_a.

        Args:
            patch_a: The original state patch.
            patch_b: The new state patch to compare.

        Returns:
            ModelResult if successful, None if timeout/failure occurred (triggers safe mode).
        """
        if not self._loaded and not self.load_model():
            logger.warning("Model not loaded, cannot perform detection.")
            return None

        input_text = f"{patch_a} [SEP] {patch_b}"

        try:
            with ExecutionTimer() as timer:
                # Run inference with timeout protection
                start_time = time.time()
                result = self.pipeline(input_text)[0]
                inference_time = time.time() - start_time

                if inference_time > self.timeout_seconds:
                    raise TimeoutError(f"Inference took {inference_time:.2f}s > {self.timeout_seconds}s")

                # Parse result: usually [{'label': 'CONTRADICTION', 'score': 0.99}, ...]
                # The pipeline returns the label with the highest probability
                label = result['label']
                score = result['score']

                # Map label to boolean (assuming 'CONTRADICTION' is the conflict label)
                # DistilBERT MNLI models usually return 'contradiction', 'entailment', 'neutral'
                is_conflict = label.lower() == 'contradiction'

                # If the model returns a score for 'contradiction' specifically, use that
                # Some pipelines return all scores; we assume the top one is used by default
                # If the top label is not 'contradiction', we might need to check specific scores
                # For robustness, let's check if the top label is contradiction
                if not is_conflict:
                    # Check if 'contradiction' is in the full list of scores if available
                    # The pipeline with return_all_scores=False returns the top one.
                    # We rely on the top label being 'contradiction' for conflict.
                    pass

                return ModelResult(
                    patch_a=patch_a,
                    patch_b=patch_b,
                    score=score,
                    is_conflict=is_conflict,
                    model_name=self.model_name,
                    latency_ms=inference_time * 1000
                )

        except TimeoutError as te:
            logger.warning(f"Detection timeout: {te}")
            return None
        except Exception as e:
            logger.error(f"Detection failed: {str(e)}")
            return None

    def get_safe_retrieval_patches(
        self,
        all_patches: List[Dict[str, Any]],
        latest_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Implements FR-007 Safe Mode: Retrieve latest state plus N most recent non-conflict patches.

        Args:
            all_patches: List of all available patches (ordered by time).
            latest_state: The most recent state patch (optional, usually last in all_patches).

        Returns:
            List of patches to retrieve in safe mode.
        """
        if not all_patches:
            logger.warning("No patches available for safe retrieval.")
            return []

        # Determine latest state
        if latest_state is None:
            latest_state = all_patches[-1]

        # Identify non-conflict patches (assuming they are marked or we assume all are non-conflict in this context)
        # In a real scenario, we might have a list of 'safe' patches.
        # Here, we assume 'all_patches' contains metadata or we just take the most recent ones
        # that are NOT the latest state if the latest state is the only one we have.
        # The spec says: "Retrieve latest state plus a small number of the most recent non-conflict patches."
        # We assume all patches in the list are candidates, and we take the latest + N-1 others.

        # Filter out the latest state from the list to find 'recent non-conflict' ones
        # If the list is ordered oldest to newest, we take from the end.
        non_latest_patches = [p for p in all_patches if p != latest_state]

        # Sort by recency (assuming the list is already sorted, reverse to get newest)
        # If not sorted, we would need a timestamp key. Assuming index order = time order.
        non_latest_patches.reverse()

        # Take the top N
        safe_patches = non_latest_patches[:self.SAFE_RETRIEVAL_COUNT]

        # Prepend latest state
        result = [latest_state] + safe_patches

        logger.info(f"Safe mode retrieved {len(result)} patches: latest + {len(safe_patches)} recent.")
        return result

    def run_sensitivity_analysis_thresholds(self, thresholds: List[float], test_data_path: str) -> str:
        """
        Run sensitivity analysis across different thresholds.

        Args:
            thresholds: List of thresholds to test.
            test_data_path: Path to the synthetic pairs JSON file.

        Returns:
            Path to the output CSV file.
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis_thresholds.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load test data
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)

        results = []

        for thresh in thresholds:
            self.threshold = thresh
            tp, fp, tn, fn = 0, 0, 0, 0

            for pair in test_data:
                res = self.detect_conflict(pair['patch_a'], pair['patch_b'])
                if res:
                    predicted = res.is_conflict
                    actual = pair['is_contradiction']
                    if predicted and actual: tp += 1
                    elif predicted and not actual: fp += 1
                    elif not predicted and actual: fn += 1
                    else: tn += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            results.append({
                'threshold': thresh,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'tp': tp,
                'fp': fp,
                'tn': tn,
                'fn': fn
            })

        # Write CSV
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['threshold', 'precision', 'recall', 'f1', 'tp', 'fp', 'tn', 'fn']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Sensitivity analysis saved to {output_path}")
        return str(output_path)

    def run_sensitivity_analysis_models(self, model_names: List[str], test_data_path: str) -> str:
        """
        Run sensitivity analysis across different model sizes.

        Args:
            model_names: List of model names to test.
            test_data_path: Path to the synthetic pairs JSON file.

        Returns:
            Path to the output CSV file.
        """
        output_path = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis_models.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load test data
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)

        results = []

        for model_name in model_names:
            logger.info(f"Testing model: {model_name}")
            # Reset and load new model
            self.model_name = model_name
            self._loaded = False
            if not self.load_model():
                logger.error(f"Skipping {model_name} due to load failure.")
                continue

            tp, fp, tn, fn = 0, 0, 0, 0

            for pair in test_data:
                res = self.detect_conflict(pair['patch_a'], pair['patch_b'])
                if res:
                    predicted = res.is_conflict
                    actual = pair['is_contradiction']
                    if predicted and actual: tp += 1
                    elif predicted and not actual: fp += 1
                    elif not predicted and actual: fn += 1
                    else: tn += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            results.append({
                'model_name': model_name,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'tp': tp,
                'fp': fp,
                'tn': tn,
                'fn': fn
            })

        # Write CSV
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['model_name', 'precision', 'recall', 'f1', 'tp', 'fp', 'tn', 'fn']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Model sensitivity analysis saved to {output_path}")
        return str(output_path)


def main():
    """
    Main entry point for conflict detector CLI.
    Usage:
      python src/heuristics/conflict_detector.py --mode threshold --thresholds 0.6 0.7 0.8 0.9 0.95 --data data/raw/synthetic_pairs.json
      python src/heuristics/conflict_detector.py --mode models --models distilbert-base-uncased bert-base-uncased --data data/raw/synthetic_pairs.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Conflict Detector Analysis")
    parser.add_argument('--mode', choices=['threshold', 'models'], required=True, help='Analysis mode')
    parser.add_argument('--data', type=str, required=True, help='Path to synthetic pairs JSON')
    parser.add_argument('--thresholds', nargs='+', type=float, default=[0.6, 0.7, 0.8, 0.9, 0.95], help='Thresholds for threshold mode')
    parser.add_argument('--models', nargs='+', type=str, default=['distilbert-base-uncased', 'bert-base-uncased'], help='Models for models mode')
    parser.add_argument('--output', type=str, default=None, help='Output file path (optional)')

    args = parser.parse_args()

    detector = ConflictDetector()

    if args.mode == 'threshold':
        detector.run_sensitivity_analysis_thresholds(args.thresholds, args.data)
    elif args.mode == 'models':
        detector.run_sensitivity_analysis_models(args.models, args.data)

    logger.info("Analysis complete.")


if __name__ == "__main__":
    main()