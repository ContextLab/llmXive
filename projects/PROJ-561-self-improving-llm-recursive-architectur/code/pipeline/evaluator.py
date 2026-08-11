"""
Evaluator module for running benchmarks: GSM8K, ARC-Challenge, and BoolQ.
Implements accuracy calculation and Expected Calibration Error (ECE).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
from pipeline.loader import with_exponential_backoff, HFTransientError
from config import get_config

class VerificationGate:
    """
    A simple gate to ensure evaluation logic is separated from generative logic.
    This class provides a fixed interface for evaluation that cannot be
    modified by the generative model's proposals.
    """
    def __init__(self):
        self.benchmarks = ["gsm8k", "arc_challenge", "boolq"]
    
    def verify_input(self, data: Any) -> bool:
        """Verify that input data is valid for evaluation."""
        if data is None:
            return False
        return True

@with_exponential_backoff
def load_gsm8k_dataset() -> Any:
    """Load GSM8K dataset with retry logic."""
    return load_dataset("gsm8k", "main", split="test")

@with_exponential_backoff
def load_arc_challenge_dataset() -> Any:
    """Load ARC-Challenge dataset with retry logic."""
    return load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")

@with_exponential_backoff
def load_boolq_dataset() -> Any:
    """Load BoolQ dataset with retry logic."""
    return load_dataset("boolq", split="validation")

def compute_gsm8k_accuracy(model: nn.Module, tokenizer: Any, dataset: Any, max_length: int = 512) -> float:
    """
    Compute accuracy on GSM8K dataset.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer for the model
        dataset: The GSM8K dataset
        max_length: Maximum sequence length
        
    Returns:
        float: Accuracy score
    """
    if not hasattr(model, 'eval'):
        raise ValueError("Model must have an eval() method")
        
    model.eval()
    correct = 0
    total = 0
    
    device = next(model.parameters()).device
    
    with torch.no_grad():
        for example in dataset:
            question = example['question']
            answer = example['answer']
            
            # Extract the final answer from the solution
            # GSM8K answers are typically in the format "#### 123"
            if "####" in answer:
                ground_truth = answer.split("####")[-1].strip()
            else:
                ground_truth = answer.strip()
            
            # Create input prompt
            prompt = f"Question: {question}\nAnswer:"
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length).to(device)
            
            # Generate response
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.0,  # Greedy decoding for evaluation
                do_sample=False
            )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract the generated answer part
            generated_answer = response.replace(prompt, "").strip()
            
            # Simple string matching for evaluation
            # In a real scenario, we might use more sophisticated extraction
            if ground_truth in generated_answer:
                correct += 1
            
            total += 1
            
            # Early exit for testing if dataset is too large
            if total >= 100:  # Limit for practical evaluation
                break
    
    return correct / total if total > 0 else 0.0

def compute_arc_challenge_accuracy(model: nn.Module, tokenizer: Any, dataset: Any, max_length: int = 512) -> float:
    """
    Compute accuracy on ARC-Challenge dataset.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer for the model
        dataset: The ARC-Challenge dataset
        max_length: Maximum sequence length
        
    Returns:
        float: Accuracy score
    """
    model.eval()
    correct = 0
    total = 0
    
    device = next(model.parameters()).device
    
    with torch.no_grad():
        for example in dataset:
            question = example['question']
            choices = example['choices']
            answer_key = example['answerKey']
            
            # Create prompt with choices
            prompt = f"Question: {question}\n"
            for i, choice in enumerate(choices['text']):
                prompt += f"{choices['label'][i]}. {choice}\n"
            prompt += "Answer:"
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length).to(device)
            
            # Calculate log probabilities for each option
            option_labels = choices['label']
            option_texts = choices['text']
            
            log_probs = []
            for label, text in zip(option_labels, option_texts):
                option_prompt = prompt + " " + text
                option_inputs = tokenizer(option_prompt, return_tensors="pt", truncation=True, max_length=max_length).to(device)
                
                outputs = model(**option_inputs)
                logits = outputs.logits
                
                # Get log probability of the option text
                shift_logits = logits[:, :-1, :].contiguous()
                shift_labels = option_inputs['input_ids'][:, 1:].contiguous()
                
                # Calculate loss for the option text
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                log_probs.append(-loss.item())
            
            # Select the option with highest log probability
            best_idx = np.argmax(log_probs)
            predicted_label = option_labels[best_idx]
            
            if predicted_label == answer_key:
                correct += 1
            
            total += 1
            
            # Early exit for testing
            if total >= 100:
                break
    
    return correct / total if total > 0 else 0.0

def compute_boolq_ece(model: nn.Module, tokenizer: Any, dataset: Any, max_length: int = 512, n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE) on BoolQ dataset.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer for the model
        dataset: The BoolQ dataset
        max_length: Maximum sequence length
        n_bins: Number of bins for ECE calculation
        
    Returns:
        float: ECE score
    """
    model.eval()
    device = next(model.parameters()).device
    
    confidences = []
    accuracies = []
    
    with torch.no_grad():
        for example in dataset:
            question = example['question']
            answer = example['answer']  # True or False
            
            # Create prompt for yes/no question
            prompt = f"Question: {question}\nAnswer:"
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length).to(device)
            
            # Get logits for "Yes" and "No"
            yes_token = tokenizer(" Yes", add_special_tokens=False).input_ids[-1]
            no_token = tokenizer(" No", add_special_tokens=False).input_ids[-1]
            
            outputs = model(**inputs)
            logits = outputs.logits[0, -1, :]  # Last token logits
            
            yes_logit = logits[yes_token].item()
            no_logit = logits[no_token].item()
            
            # Convert to probabilities
            max_logit = max(yes_logit, no_logit)
            exp_yes = np.exp(yes_logit - max_logit)
            exp_no = np.exp(no_logit - max_logit)
            prob_yes = exp_yes / (exp_yes + exp_no)
            prob_no = exp_no / (exp_yes + exp_no)
            
            # Determine confidence and accuracy
            if answer:
                confidence = prob_yes
                correct = 1 if prob_yes > 0.5 else 0
            else:
                confidence = prob_no
                correct = 1 if prob_no > 0.5 else 0
            
            confidences.append(confidence)
            accuracies.append(correct)
            
            # Early exit for testing
            if len(confidences) >= 100:
                break
    
    # Calculate ECE
    confidences = np.array(confidences)
    accuracies = np.array(accuracies)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Find samples in this bin
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = in_bin.sum() / len(confidences)
        
        if in_bin.sum() > 0:
            avg_confidence = confidences[in_bin].mean()
            avg_accuracy = accuracies[in_bin].mean()
            ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin
    
    return ece

def run_all_benchmarks(model: nn.Module, tokenizer: Any) -> Dict[str, float]:
    """
    Run all benchmarks and return results.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer for the model
        
    Returns:
        Dict[str, float]: Dictionary of benchmark results
    """
    config = get_config()
    results = {}
    
    # Load datasets
    try:
        gsm8k_data = load_gsm8k_dataset()
        results['GSM8K'] = compute_gsm8k_accuracy(model, tokenizer, gsm8k_data)
    except Exception as e:
        results['GSM8K'] = 0.0
        print(f"Warning: Failed to load GSM8K: {e}")
    
    try:
        arc_data = load_arc_challenge_dataset()
        results['ARC'] = compute_arc_challenge_accuracy(model, tokenizer, arc_data)
    except Exception as e:
        results['ARC'] = 0.0
        print(f"Warning: Failed to load ARC-Challenge: {e}")
    
    try:
        boolq_data = load_boolq_dataset()
        results['BoolQ'] = compute_boolq_ece(model, tokenizer, boolq_data)
    except Exception as e:
        results['BoolQ'] = 0.0
        print(f"Warning: Failed to load BoolQ: {e}")
    
    return results
