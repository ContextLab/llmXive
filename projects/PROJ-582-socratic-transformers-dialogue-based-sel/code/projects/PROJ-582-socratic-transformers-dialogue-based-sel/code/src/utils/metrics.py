"""
Metric utility for standard accuracy and loss calculations.

Implements metrics required for evaluating the Socratic Transformer models,
including accuracy, loss, and specific evaluation proxies for the research
pipeline.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


class MetricCalculator:
    """
    Calculator for various evaluation metrics used in the Socratic Transformer pipeline.
    
    This class provides methods to compute accuracy, loss, and other evaluation
    metrics from model outputs and ground truth labels.
    """

    def __init__(
        self,
        model: Optional[PreTrainedModel] = None,
        tokenizer: Optional[PreTrainedTokenizer] = None,
        ignore_index: int = -100,
    ):
        """
        Initialize the metric calculator.
        
        Args:
            model: The pre-trained model to use for evaluation (optional).
            tokenizer: The tokenizer to use for tokenization (optional).
            ignore_index: The index to ignore in loss calculations (default: -100).
        """
        self.model = model
        self.tokenizer = tokenizer
        self.ignore_index = ignore_index

    def compute_accuracy(
        self,
        predictions: Union[List[int], torch.Tensor],
        labels: Union[List[int], torch.Tensor],
    ) -> float:
        """
        Compute accuracy between predictions and labels.
        
        Args:
            predictions: Predicted token IDs or logits.
            labels: Ground truth token IDs.
            
        Returns:
            Accuracy as a float between 0 and 1.
        """
        if isinstance(predictions, torch.Tensor):
            if predictions.dim() > 1:
                # If logits, take argmax
                predictions = torch.argmax(predictions, dim=-1)
            predictions = predictions.cpu().tolist()
        
        if isinstance(labels, torch.Tensor):
            labels = labels.cpu().tolist()
        
        # Handle list inputs
        if not isinstance(predictions, list):
            predictions = list(predictions)
        if not isinstance(labels, list):
            labels = list(labels)
        
        # Ensure same length
        min_len = min(len(predictions), len(labels))
        predictions = predictions[:min_len]
        labels = labels[:min_len]
        
        # Filter out ignore_index
        correct = 0
        total = 0
        for pred, label in zip(predictions, labels):
            if label == self.ignore_index:
                continue
            if pred == label:
                correct += 1
            total += 1
        
        if total == 0:
            return 0.0
        
        return correct / total

    def compute_loss(
        self,
        model: PreTrainedModel,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> float:
        """
        Compute loss for a given batch of inputs.
        
        Args:
            model: The model to compute loss for.
            input_ids: Input token IDs.
            attention_mask: Attention mask (optional).
            labels: Ground truth labels (optional).
            
        Returns:
            Loss value as a float.
        """
        model.eval()
        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            return loss.item()

    def compute_prediction_error_proxy(
        self,
        generated_text: str,
        target_text: str,
    ) -> float:
        """
        Compute a proxy for prediction error based on text similarity.
        
        This is a simple heuristic that measures the difference between
        generated and target text. In a real implementation, this would
        use more sophisticated metrics like BLEU, ROUGE, or semantic similarity.
        
        Args:
            generated_text: The model's generated text.
            target_text: The ground truth text.
            
        Returns:
            A float representing the error (higher is worse).
        """
        if not generated_text or not target_text:
            return 1.0
        
        # Simple character-level error rate as a proxy
        gen_tokens = generated_text.split()
        target_tokens = target_text.split()
        
        if not gen_tokens or not target_tokens:
            return 1.0
        
        # Calculate token-level error rate
        matches = 0
        min_len = min(len(gen_tokens), len(target_tokens))
        for i in range(min_len):
            if gen_tokens[i] == target_tokens[i]:
                matches += 1
        
        error_rate = 1.0 - (matches / max(len(target_tokens), 1))
        return error_rate

    def compute_calibration_error(
        self,
        predictions: List[dict],
    ) -> float:
        """
        Compute calibration error for probabilistic predictions.
        
        Args:
            predictions: List of dictionaries with 'prediction' and 'confidence' keys.
            
        Returns:
            Expected calibration error (ECE) as a float.
        """
        if not predictions:
            return 0.0
        
        # Group predictions by confidence buckets
        num_buckets = 10
        buckets = [[] for _ in range(num_buckets)]
        
        for pred in predictions:
            confidence = pred.get('confidence', 0.5)
            is_correct = pred.get('is_correct', False)
            
            bucket_idx = min(int(confidence * num_buckets), num_buckets - 1)
            buckets[bucket_idx].append(is_correct)
        
        # Calculate ECE
        ece = 0.0
        total_predictions = len(predictions)
        
        for bucket in buckets:
            if not bucket:
                continue
            
            bucket_size = len(bucket)
            avg_confidence = (bucket_size / num_buckets) / total_predictions * num_buckets
            avg_accuracy = sum(bucket) / bucket_size
            
            ece += (bucket_size / total_predictions) * abs(avg_accuracy - avg_confidence)
        
        return ece

    def compute_ngram_overlap(
        self,
        text1: str,
        text2: str,
        n: int = 2,
    ) -> float:
        """
        Compute n-gram overlap between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            n: Size of n-grams (default: 2 for bigrams).
            
        Returns:
            Overlap score as a float between 0 and 1.
        """
        def get_ngrams(text, n):
            tokens = text.split()
            if len(tokens) < n:
                return set()
            return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))
        
        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        
        return len(intersection) / len(union) if union else 0.0


def compute_prediction_error_proxy(
    generated_text: str,
    target_text: str,
) -> float:
    """
    Standalone function to compute prediction error proxy.
    
    Args:
        generated_text: The model's generated text.
        target_text: The ground truth text.
        
    Returns:
        A float representing the error (higher is worse).
    """
    calculator = MetricCalculator()
    return calculator.compute_prediction_error_proxy(generated_text, target_text)


def compute_calibration_error(
    predictions: List[dict],
) -> float:
    """
    Standalone function to compute calibration error.
    
    Args:
        predictions: List of dictionaries with 'prediction' and 'confidence' keys.
        
    Returns:
        Expected calibration error (ECE) as a float.
    """
    calculator = MetricCalculator()
    return calculator.compute_calibration_error(predictions)


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2,
) -> float:
    """
    Standalone function to compute n-gram overlap.
    
    Args:
        text1: First text.
        text2: Second text.
        n: Size of n-grams (default: 2 for bigrams).
        
    Returns:
        Overlap score as a float between 0 and 1.
    """
    calculator = MetricCalculator()
    return calculator.compute_ngram_overlap(text1, text2, n)
