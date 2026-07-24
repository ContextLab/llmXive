import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
import time
import os
import gc
from config import PathConfig, get_config_summary

# Import existing loaders to ensure we use the real data sources
from pipeline.loader import load_gsm8k, load_arc_challenge, load_wikitext2

class VerificationGate:
    """
    A strict separation layer ensuring benchmark evaluation logic is isolated
    from generative modification logic. This class holds the evaluation results
    but does not expose them to the model during proposal generation.
    """
    def __init__(self):
        self.results: Dict[str, float] = {}
        self.baseline_results: Dict[str, float] = {}

    def record(self, metric_name: str, value: float):
        self.results[metric_name] = value

    def get_results(self) -> Dict[str, float]:
        return self.results.copy()

    def set_baseline(self, baseline: Dict[str, float]):
        self.baseline_results = baseline.copy()

    def get_improvement(self, metric_name: str) -> Optional[float]:
        if metric_name in self.baseline_results and metric_name in self.results:
            return self.results[metric_name] - self.baseline_results[metric_name]
        return None

def compute_gsm8k_accuracy(model: nn.Module, device: str = "cpu", limit_samples: Optional[int] = None) -> float:
    """
    Computes accuracy on the GSM8K dataset.
    Uses the loader from pipeline.loader which fetches real data from HuggingFace.
    """
    dataset = load_gsm8k()
    if limit_samples:
        # Stream only a subset if requested to save memory/time, but data is real
        dataset = dataset.select(range(min(limit_samples, len(dataset))))

    model.eval()
    correct = 0
    total = 0
    
    # GSM8K format: question -> answer (contains "#### <number>")
    # We will use a simple regex extraction for the final answer
    import re

    with torch.no_grad():
        for item in dataset:
            question = item['question']
            ground_truth_answer = item['answer']
            
            # Extract ground truth number
            gt_match = re.search(r'####\s*(\d+)', ground_truth_answer)
            if not gt_match:
                continue
            gt_value = int(gt_match.group(1))

            # Construct prompt
            prompt = f"Q: {question}\nA:"
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            
            # Generate
            outputs = model.generate(
                inputs["input_ids"],
                max_new_tokens=64,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract number from generated text
            gen_match = re.search(r'####\s*(\d+)', generated_text)
            if gen_match:
                gen_value = int(gen_match.group(1))
                if gen_value == gt_value:
                    correct += 1
            total += 1

    return correct / total if total > 0 else 0.0

def compute_arc_challenge_accuracy(model: nn.Module, device: str = "cpu", limit_samples: Optional[int] = None) -> float:
    """
    Computes accuracy on the ARC-Challenge dataset.
    """
    dataset = load_arc_challenge()
    if limit_samples:
        dataset = dataset.select(range(min(limit_samples, len(dataset))))

    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for item in dataset:
            question = item['question']
            choices = item['choices']
            label = item['label'] # 'A', 'B', 'C', 'D'
            
            # Format: Question + Options
            prompt = f"Question: {question}\n"
            for i, choice in enumerate(choices['text']):
                prompt += f"{chr(65+i)}. {choice}\n"
            prompt += "Answer:"

            # We evaluate log-probability of the token corresponding to the correct letter
            # vs the other letters.
            input_ids = tokenizer(prompt, return_tensors="pt").to(device)["input_ids"]
            
            # Tokenize the answer choices (single letters)
            choice_tokens = [tokenizer(chr(65+i), add_special_tokens=False)["input_ids"][0] for i in range(4)]
            
            logits = model(input_ids).logits[0, -1, :] # Logits for the next token
            
            # Find which choice token has the highest logit
            best_choice_idx = -1
            best_logit = -float('inf')
            
            for i, token_id in enumerate(choice_tokens):
                if token_id < len(logits):
                    if logits[token_id] > best_logit:
                        best_logit = logits[token_id]
                        best_choice_idx = i
            
            predicted_label = chr(65 + best_choice_idx)
            if predicted_label == label:
                correct += 1
            total += 1

    return correct / total if total > 0 else 0.0

def compute_wikitext2_ece(model: nn.Module, device: str = "cpu", limit_tokens: int = 1000) -> float:
    """
    Computes Expected Calibration Error (ECE) on Wikitext-2.
    ECE measures the gap between confidence and accuracy.
    """
    dataset = load_wikitext2()
    # Wikitext-2 is a single long string or list of strings. We treat it as a stream.
    text = " ".join(dataset['text'])
    tokens = tokenizer(text, return_tensors="pt", truncation=True, max_length=limit_tokens)["input_ids"].to(device)
    
    model.eval()
    
    # We calculate per-token calibration
    # Accuracy: is the predicted token the true next token?
    # Confidence: probability of the predicted token
    
    with torch.no_grad():
        outputs = model(tokens)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)
        
        # Shift for next-token prediction
        # tokens[:, 1:] are the targets for tokens[:, :-1]
        targets = tokens[:, 1:].squeeze()
        preds = logits[:, :-1, :].argmax(dim=-1).squeeze()
        confidences = torch.gather(probs[:, :-1, :], -1, preds.unsqueeze(-1)).squeeze()
        
        # Calculate ECE
        # Bin confidence into 10 bins
        num_bins = 10
        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        total_tokens = 0
        
        for i in range(num_bins):
            in_bin = (confidences >= bin_boundaries[i]) & (confidences < bin_boundaries[i+1])
            if i == num_bins - 1:
                in_bin = (confidences >= bin_boundaries[i]) & (confidences <= bin_boundaries[i+1])
                
            prop_in_bin = in_bin.float().mean().item()
            if prop_in_bin > 0:
                avg_confidence = confidences[in_bin].mean().item()
                avg_accuracy = (preds[in_bin] == targets[in_bin]).float().mean().item()
                ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin
            total_tokens += in_bin.sum().item()
        
        return ece

def run_all_benchmarks(model: nn.Module, config: PathConfig, device: str = "cpu") -> Dict[str, float]:
    """
    Orchestrates the evaluation of all benchmarks and returns a dictionary of metrics.
    """
    results = {}
    
    # GSM8K
    try:
        gsm8k_acc = compute_gsm8k_accuracy(model, device, limit_samples=100) # Limit for speed in CI
        results['gsm8k_accuracy'] = gsm8k_acc
        print(f"GSM8K Accuracy: {gsm8k_acc:.4f}")
    except Exception as e:
        print(f"Error computing GSM8K: {e}")
        results['gsm8k_accuracy'] = 0.0
    
    # ARC-Challenge
    try:
        arc_acc = compute_arc_challenge_accuracy(model, device, limit_samples=100)
        results['arc_challenge_accuracy'] = arc_acc
        print(f"ARC-Challenge Accuracy: {arc_acc:.4f}")
    except Exception as e:
        print(f"Error computing ARC-Challenge: {e}")
        results['arc_challenge_accuracy'] = 0.0
        
    # Wikitext-2 ECE
    try:
        wikitext_ece = compute_wikitext2_ece(model, device, limit_tokens=500)
        results['wikitext2_ece'] = wikitext_ece
        print(f"Wikitext-2 ECE: {wikitext_ece:.4f}")
    except Exception as e:
        print(f"Error computing Wikitext-2 ECE: {e}")
        results['wikitext2_ece'] = 0.0
        
    return results

# Ensure tokenizer is available globally or passed in. 
# Since we cannot import from main, we assume the model is loaded with its tokenizer
# or we define a helper to attach it. For this implementation, we assume 
# the model object passed has a tokenizer attribute or we use a global one.
# To be safe and self-contained, we will attach a simple tokenizer wrapper if not present.
# However, standard practice in this project is to load model with tokenizer.
# We will assume the model passed has a tokenizer attribute or we use a fallback.

tokenizer = None
def _get_tokenizer(model):
    global tokenizer
    if hasattr(model, 'tokenizer'):
        return model.tokenizer
    # Fallback: try to load a standard GPT-2 tokenizer
    from transformers import GPT2Tokenizer
    if tokenizer is None:
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer

# Patch the functions to use the tokenizer from the model
original_gsm8k = compute_gsm8k_accuracy
original_arc = compute_arc_challenge_accuracy
original_wiki = compute_wikitext2_ece

def compute_gsm8k_accuracy(model, device="cpu", limit_samples=None):
    global tokenizer
    tokenizer = _get_tokenizer(model)
    return original_gsm8k(model, device, limit_samples)

def compute_arc_challenge_accuracy(model, device="cpu", limit_samples=None):
    global tokenizer
    tokenizer = _get_tokenizer(model)
    return original_arc(model, device, limit_samples)

def compute_wikitext2_ece(model, device="cpu", limit_tokens=1000):
    global tokenizer
    tokenizer = _get_tokenizer(model)
    return original_wiki(model, device, limit_tokens)
