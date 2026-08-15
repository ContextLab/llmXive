"""
Evaluator module for benchmarking model performance on GSM8K, ARC-Challenge, and BoolQ.

This module implements the benchmark runner and evaluation logic as specified in T010.
It includes functions to load datasets, compute accuracy/ECE metrics, and run all benchmarks.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
import re
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VerificationGate:
    """
    A verification gate that ensures evaluation logic remains immutable.
    This addresses the "Fixed-Point Problem" by preventing modification of benchmark criteria.
    """
    
    def __init__(self):
        self._benchmark_names = frozenset(['GSM8K', 'ARC_Challenge', 'BoolQ'])
        self._is_immutable = True
    
    def get_benchmark_names(self) -> Tuple[str, ...]:
        """Return the immutable list of benchmark names."""
        return tuple(self._benchmark_names)
    
    def validate_benchmark(self, name: str) -> bool:
        """Validate that a benchmark name is in the allowed set."""
        if name not in self._benchmark_names:
            raise ValueError(f"Unknown benchmark: {name}. Allowed: {self._benchmark_names}")
        return True

# Global verification gate instance
_verification_gate = VerificationGate()

def load_gsm8k_dataset(split: str = "test", streaming: bool = False) -> Any:
    """
    Load the GSM8K dataset (grade school math word problems).
    
    Args:
        split: Dataset split to load (default: "test")
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset object from HuggingFace datasets
    """
    try:
        dataset = load_dataset(
            "gsm8k",
            "main",
            split=split,
            streaming=streaming
        )
        logger.info(f"Loaded GSM8K dataset ({split}) with {len(dataset) if not streaming else 'streaming'} examples")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

def load_arc_challenge_dataset(split: str = "test", streaming: bool = False) -> Any:
    """
    Load the ARC-Challenge dataset (science questions).
    
    Args:
        split: Dataset split to load (default: "test")
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset object from HuggingFace datasets
    """
    try:
        dataset = load_dataset(
            "allenai/ai2_arc",
            "ARC-Challenge",
            split=split,
            streaming=streaming
        )
        logger.info(f"Loaded ARC-Challenge dataset ({split}) with {len(dataset) if not streaming else 'streaming'} examples")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load ARC-Challenge dataset: {e}")
        raise

def load_boolq_dataset(split: str = "validation", streaming: bool = False) -> Any:
    """
    Load the BoolQ dataset (Boolean questions).
    
    Args:
        split: Dataset split to load (default: "validation")
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset object from HuggingFace datasets
    """
    try:
        dataset = load_dataset(
            "boolq",
            split=split,
            streaming=streaming
        )
        logger.info(f"Loaded BoolQ dataset ({split}) with {len(dataset) if not streaming else 'streaming'} examples")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load BoolQ dataset: {e}")
        raise

def compute_gsm8k_accuracy(model: nn.Module, tokenizer, dataset: Any, max_examples: Optional[int] = None) -> float:
    """
    Compute accuracy on GSM8K dataset.
    
    The model generates answers to math word problems. Accuracy is computed
    by checking if the generated answer matches the ground truth.
    
    Args:
        model: The model to evaluate
        tokenizer: Tokenizer for the model
        dataset: GSM8K dataset
        max_examples: Maximum number of examples to evaluate (None for all)
    
    Returns:
        Accuracy as a float between 0 and 1
    """
    model.eval()
    correct = 0
    total = 0
    
    device = next(model.parameters()).device
    
    def extract_answer(text: str) -> Optional[str]:
        """Extract the final answer from model output."""
        # Look for the last occurrence of "####" followed by a number
        match = re.search(r'####\s*([0-9,\.]+)', text)
        if match:
            return match.group(1).replace(',', '')
        # Fallback: look for the last number in the text
        numbers = re.findall(r'[-+]?\d*\.?\d+', text)
        if numbers:
            return numbers[-1]
        return None
    
    examples = list(dataset) if not hasattr(dataset, '__iter__') else dataset
    if max_examples:
        examples = examples[:max_examples]
    
    for example in tqdm(examples, desc="Evaluating GSM8K"):
        question = example['question']
        answer = example['answer']
        
        # Extract ground truth answer
        gt_answer = extract_answer(answer)
        if gt_answer is None:
            continue
        
        # Prepare input
        prompt = f"Question: {question}\nAnswer: "
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        pred_answer = extract_answer(generated_text)
        
        if pred_answer is not None and pred_answer == gt_answer:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0.0

def compute_arc_challenge_accuracy(model: nn.Module, tokenizer, dataset: Any, max_examples: Optional[int] = None) -> float:
    """
    Compute accuracy on ARC-Challenge dataset.
    
    The model must select the correct answer from multiple choices.
    Accuracy is computed by comparing the model's choice with the ground truth.
    
    Args:
        model: The model to evaluate
        tokenizer: Tokenizer for the model
        dataset: ARC-Challenge dataset
        max_examples: Maximum number of examples to evaluate (None for all)
    
    Returns:
        Accuracy as a float between 0 and 1
    """
    model.eval()
    correct = 0
    total = 0
    
    device = next(model.parameters()).device
    
    examples = list(dataset) if not hasattr(dataset, '__iter__') else dataset
    if max_examples:
        examples = examples[:max_examples]
    
    for example in tqdm(examples, desc="Evaluating ARC-Challenge"):
        question = example['question']
        choices = example['choices']
        answer_key = example['answerKey']
        
        # Format choices
        choice_text = "\n".join([f"{label}. {text}" for label, text in zip(choices['label'], choices['text'])])
        prompt = f"Question: {question}\nChoices:\n{choice_text}\nAnswer:"
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            last_token_logits = logits[0, -1, :]
        
        # Get the token ID for each choice label
        choice_logits = []
        for label in choices['label']:
            token_ids = tokenizer.encode(label, add_special_tokens=False)
            if len(token_ids) == 1:
                choice_logits.append(last_token_logits[token_ids[0]].item())
            else:
                # If multiple tokens, average the logits
                avg_logit = torch.mean(last_token_logits[token_ids]).item()
                choice_logits.append(avg_logit)
        
        predicted_label = choices['label'][np.argmax(choice_logits)]
        
        if predicted_label == answer_key:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0.0

def compute_boolq_ece(model: nn.Module, tokenizer, dataset: Any, max_examples: Optional[int] = None, n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE) on BoolQ dataset.
    
    ECE measures the calibration of the model's confidence predictions.
    A lower ECE indicates better calibration.
    
    Args:
        model: The model to evaluate
        tokenizer: Tokenizer for the model
        dataset: BoolQ dataset
        max_examples: Maximum number of examples to evaluate (None for all)
        n_bins: Number of bins for ECE calculation
    
    Returns:
        ECE as a float between 0 and 1
    """
    model.eval()
    
    device = next(model.parameters()).device
    
    examples = list(dataset) if not hasattr(dataset, '__iter__') else dataset
    if max_examples:
        examples = examples[:max_examples]
    
    confidences = []
    accuracies = []
    
    for example in tqdm(examples, desc="Evaluating BoolQ ECE"):
        question = example['question']
        answer = example['answer']
        
        prompt = f"Passage: {question}\nQuestion: Is this true? Answer:"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            last_token_logits = logits[0, -1, :]
        
        # Get probabilities for True/False
        true_token_ids = tokenizer.encode("True", add_special_tokens=False)
        false_token_ids = tokenizer.encode("False", add_special_tokens=False)
        
        # Use the first token of each answer
        true_prob = F.softmax(last_token_logits[true_token_ids[0]], dim=0).item()
        false_prob = F.softmax(last_token_logits[false_token_ids[0]], dim=0).item()
        
        # Normalize
        total_prob = true_prob + false_prob
        true_prob /= total_prob
        false_prob /= total_prob
        
        # Model's prediction and confidence
        if true_prob > false_prob:
            pred = True
            confidence = true_prob
        else:
            pred = False
            confidence = false_prob
        
        confidences.append(confidence)
        accuracies.append(1.0 if pred == answer else 0.0)
    
    # Calculate ECE
    confidences = np.array(confidences)
    accuracies = np.array(accuracies)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = in_bin.sum() / len(confidences)
        
        if in_bin.sum() > 0:
            avg_confidence = confidences[in_bin].mean()
            avg_accuracy = accuracies[in_bin].mean()
            ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin
    
    return ece

def run_all_benchmarks(
    model: nn.Module,
    tokenizer,
    gsm8k_max: Optional[int] = None,
    arc_max: Optional[int] = None,
    boolq_max: Optional[int] = None
) -> Dict[str, float]:
    """
    Run all benchmarks (GSM8K, ARC-Challenge, BoolQ) and return metrics.
    
    Args:
        model: The model to evaluate
        tokenizer: Tokenizer for the model
        gsm8k_max: Maximum examples for GSM8K (None for all)
        arc_max: Maximum examples for ARC-Challenge (None for all)
        boolq_max: Maximum examples for BoolQ (None for all)
    
    Returns:
        Dictionary with keys: 'GSM8K_accuracy', 'ARC_Challenge_accuracy', 'BoolQ_ECE'
    """
    logger.info("Starting benchmark evaluation...")
    
    # Load datasets
    logger.info("Loading datasets...")
    gsm8k_dataset = load_gsm8k_dataset()
    arc_dataset = load_arc_challenge_dataset()
    boolq_dataset = load_boolq_dataset()
    
    # Run evaluations
    results = {}
    
    logger.info("Computing GSM8K accuracy...")
    gsm8k_acc = compute_gsm8k_accuracy(model, tokenizer, gsm8k_dataset, max_examples=gsm8k_max)
    results['GSM8K_accuracy'] = gsm8k_acc
    logger.info(f"GSM8K Accuracy: {gsm8k_acc:.4f}")
    
    logger.info("Computing ARC-Challenge accuracy...")
    arc_acc = compute_arc_challenge_accuracy(model, tokenizer, arc_dataset, max_examples=arc_max)
    results['ARC_Challenge_accuracy'] = arc_acc
    logger.info(f"ARC-Challenge Accuracy: {arc_acc:.4f}")
    
    logger.info("Computing BoolQ ECE...")
    boolq_ece = compute_boolq_ece(model, tokenizer, boolq_dataset, max_examples=boolq_max)
    results['BoolQ_ECE'] = boolq_ece
    logger.info(f"BoolQ ECE: {boolq_ece:.4f}")
    
    logger.info("Benchmark evaluation complete.")
    return results
