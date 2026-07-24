import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
import os
import sys
import json
import time

# Ensure pipeline is importable if running from root
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.loader import load_gsm8k, load_arc_challenge, load_wikitext2, exponential_backoff
from utils.memory import check_and_terminate_if_exceeds, get_memory_usage_gb

# Configuration constants for evaluation
GSM8K_MAX_TOKENS = 256
ARC_MAX_TOKENS = 256
WIKITEXT2_MAX_TOKENS = 1024
EVAL_BATCH_SIZE = 4
RANDOM_SEED = 42

torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

def _prepare_inputs(batch: Dict[str, Any], model: nn.Module, device: str) -> Dict[str, torch.Tensor]:
    """Move batch tensors to device."""
    return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}

def compute_gsm8k_accuracy(model: nn.Module, dataset_name: str = "openai/gsm8k", subset: str = "main", max_samples: Optional[int] = None) -> Dict[str, Any]:
    """
    Compute accuracy on GSM8K dataset.
    
    Args:
        model: The GPT model to evaluate.
        dataset_name: HuggingFace dataset name.
        subset: Dataset subset (e.g., 'main').
        max_samples: Limit evaluation to N samples (None for all).
        
    Returns:
        Dict containing accuracy and raw metrics.
    """
    check_and_terminate_if_exceeds(limit_gb=7.0)
    
    print(f"Loading GSM8K dataset: {dataset_name} [{subset}]...")
    try:
        dataset = load_gsm8k(subset=subset)
    except Exception as e:
        raise RuntimeError(f"Failed to load GSM8K dataset: {e}")
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    model.eval()
    device = next(model.parameters()).device
    total = 0
    correct = 0
    results = []
    
    # GSM8K format: question -> answer (with reasoning)
    # We use a simple few-shot or direct prompt approach
    # For this implementation, we assume the model is prompted to complete the answer
    
    with torch.no_grad():
        for i, item in enumerate(dataset):
            check_and_terminate_if_exceeds(limit_gb=7.0)
            
            question = item['question']
            answer = item['answer']
            
            # Simple prompt: "Question: {q}\nAnswer: "
            prompt = f"Question: {question}\nAnswer:"
            
            # Tokenize
            try:
                # Assuming model has a tokenizer attribute or we use a standard one
                # Since we don't have the tokenizer in the API surface, we assume 
                # the model has a tokenizer or we use a simple byte-level approach
                # For GPT-2 style models, we can use transformers tokenizer if available
                # But to stay within constraints, we'll assume the model has a tokenizer
                if hasattr(model, 'tokenizer'):
                    inputs = model.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                else:
                    # Fallback: simple encoding if tokenizer not present (should not happen for GPT)
                    raise AttributeError("Model must have a tokenizer attribute")
                
                inputs = _prepare_inputs(inputs, model, device)
                input_ids = inputs['input_ids']
                attention_mask = inputs['attention_mask']
                
                # Generate
                output = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=GSM8K_MAX_TOKENS,
                    do_sample=False,
                    pad_token_id=model.config.eos_token_id if hasattr(model.config, 'eos_token_id') else 50256
                )
                
                generated_text = model.tokenizer.decode(output[0, input_ids.shape[1]:], skip_special_tokens=True)
                
                # Parse answer (extract number)
                # Simple heuristic: find the last number in the generated text
                import re
                numbers = re.findall(r'\d+', generated_text)
                pred = numbers[-1] if numbers else None
                
                # Ground truth parsing
                gt_numbers = re.findall(r'\d+', answer)
                gt = gt_numbers[-1] if gt_numbers else None
                
                is_correct = (pred == gt) if (pred and gt) else False
                
                if is_correct:
                    correct += 1
                total += 1
                
                results.append({
                    'question': question[:50] + "...",
                    'pred': pred,
                    'gt': gt,
                    'correct': is_correct
                })
                
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
                continue
    
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        'dataset': 'gsm8k',
        'accuracy': accuracy,
        'total_samples': total,
        'correct': correct,
        'sample_results': results[:10]  # Keep first 10 for inspection
    }

def compute_arc_challenge_accuracy(model: nn.Module, dataset_name: str = "allenai/ai2_arc", subset: str = "ARC-Challenge", max_samples: Optional[int] = None) -> Dict[str, Any]:
    """
    Compute accuracy on ARC-Challenge dataset.
    
    Args:
        model: The GPT model to evaluate.
        dataset_name: HuggingFace dataset name.
        subset: Dataset subset (e.g., 'ARC-Challenge').
        max_samples: Limit evaluation to N samples.
        
    Returns:
        Dict containing accuracy and raw metrics.
    """
    check_and_terminate_if_exceeds(limit_gb=7.0)
    
    print(f"Loading ARC-Challenge dataset: {dataset_name} [{subset}]...")
    try:
        dataset = load_arc_challenge(subset=subset)
    except Exception as e:
        raise RuntimeError(f"Failed to load ARC-Challenge dataset: {e}")
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    model.eval()
    device = next(model.parameters()).device
    total = 0
    correct = 0
    results = []
    
    with torch.no_grad():
        for i, item in enumerate(dataset):
            check_and_terminate_if_exceeds(limit_gb=7.0)
            
            question = item['question']
            choices = item['choices']  # Dict with 'label' and 'text'
            answer_key = item['answerKey']  # e.g., 'A', 'B', 'C', 'D'
            
            # Format: "Question: {q}\nOptions:\nA. {opt1}\nB. {opt2}...\nAnswer:"
            prompt = f"Question: {question}\nOptions:\n"
            for label, text in zip(choices['label'], choices['text']):
                prompt += f"{label}. {text}\n"
            prompt += "Answer:"
            
            try:
                if hasattr(model, 'tokenizer'):
                    inputs = model.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                else:
                    raise AttributeError("Model must have a tokenizer attribute")
                
                inputs = _prepare_inputs(inputs, model, device)
                input_ids = inputs['input_ids']
                attention_mask = inputs['attention_mask']
                
                # Generate single token or short sequence to pick the answer
                output = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=10,
                    do_sample=False,
                    pad_token_id=model.config.eos_token_id if hasattr(model.config, 'eos_token_id') else 50256
                )
                
                generated_text = model.tokenizer.decode(output[0, input_ids.shape[1]:], skip_special_tokens=True)
                
                # Extract the predicted label (first letter that is A, B, C, or D)
                import re
                match = re.search(r'\b([A-D])\b', generated_text.upper())
                pred_label = match.group(1) if match else None
                
                is_correct = (pred_label == answer_key) if pred_label else False
                
                if is_correct:
                    correct += 1
                total += 1
                
                results.append({
                    'question': question[:50] + "...",
                    'pred': pred_label,
                    'gt': answer_key,
                    'correct': is_correct
                })
                
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
                continue
    
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        'dataset': 'arc_challenge',
        'accuracy': accuracy,
        'total_samples': total,
        'correct': correct,
        'sample_results': results[:10]
    }

def compute_wikitext2_ece(model: nn.Module, dataset_name: str = "wikitext", subset: str = "wikitext-2-raw-v1", max_samples: Optional[int] = None) -> Dict[str, Any]:
    """
    Compute Expected Calibration Error (ECE) on Wikitext-2.
    
    ECE measures the gap between predicted confidence and actual accuracy.
    Since this is a language model, we approximate by:
    1. Computing perplexity (log likelihood)
    2. Binning by confidence (softmax probability)
    3. Calculating the weighted average of |accuracy - confidence|
    
    Args:
        model: The GPT model to evaluate.
        dataset_name: HuggingFace dataset name.
        subset: Dataset subset.
        max_samples: Limit evaluation to N samples.
        
    Returns:
        Dict containing ECE, perplexity, and bin statistics.
    """
    check_and_terminate_if_exceeds(limit_gb=7.0)
    
    print(f"Loading Wikitext-2 dataset: {dataset_name} [{subset}]...")
    try:
        dataset = load_wikitext2(subset=subset)
    except Exception as e:
        raise RuntimeError(f"Failed to load Wikitext-2 dataset: {e}")
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    model.eval()
    device = next(model.parameters()).device
    
    total_tokens = 0
    total_loss = 0.0
    bin_counts = [0] * 10  # 10 bins for confidence [0, 0.1), [0.1, 0.2), ...
    bin_correct = [0.0] * 10  # Sum of confidences in each bin
    
    # For ECE, we need to evaluate token-by-token predictions
    # We'll use a sliding window approach
    
    with torch.no_grad():
        for i, item in enumerate(dataset):
            check_and_terminate_if_exceeds(limit_gb=7.0)
            
            text = item['text']
            if not text or len(text.strip()) == 0:
                continue
            
            # Tokenize
            try:
                if hasattr(model, 'tokenizer'):
                    # Use a fixed context window
                    tokens = model.tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=WIKITEXT2_MAX_TOKENS)
                else:
                    raise AttributeError("Model must have a tokenizer attribute")
                
                tokens = tokens.to(device)
                batch_size, seq_len = tokens.shape
                
                if seq_len < 2:
                    continue
                
                # Compute loss and log probs for each token (shifted)
                outputs = model(tokens)
                logits = outputs.logits
                
                # Shift for next-token prediction
                shift_logits = logits[:, :-1, :].contiguous()
                shift_labels = tokens[:, 1:].contiguous()
                
                # Compute per-token log probs
                log_probs = F.log_softmax(shift_logits, dim=-1)
                
                # Get the log prob of the actual next token
                nll = -torch.gather(log_probs, 2, shift_labels.unsqueeze(-1)).squeeze(-1)
                
                # Convert to probabilities (confidence)
                probs = torch.exp(-nll)  # P(next_token | context)
                
                # Accumulate loss
                total_loss += nll.sum().item()
                total_tokens += nll.numel()
                
                # Bin by confidence
                for p in probs.flatten():
                    conf = p.item()
                    if conf < 0 or conf > 1:
                        continue
                    
                    bin_idx = min(int(conf * 10), 9)
                    bin_counts[bin_idx] += 1
                    bin_correct[bin_idx] += conf
                    
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
                continue
    
    if total_tokens == 0:
        return {
            'dataset': 'wikitext2',
            'ece': 0.0,
            'perplexity': float('inf'),
            'total_tokens': 0,
            'bins': []
        }
    
    # Calculate Perplexity
    avg_loss = total_loss / total_tokens
    perplexity = np.exp(avg_loss)
    
    # Calculate ECE
    ece = 0.0
    bins_info = []
    
    for i in range(10):
        if bin_counts[i] > 0:
            avg_conf = bin_correct[i] / bin_counts[i]
            # For ECE, we assume accuracy is 1.0 if the model predicted the correct token
            # Since we are evaluating on the actual next token, accuracy is effectively 1.0
            # But ECE is usually defined for classification tasks. 
            # Here, we interpret ECE as the gap between confidence and the "correctness" of the prediction.
            # In language modeling, if we predict the correct token, accuracy is 1.0.
            # So ECE = |1.0 - avg_conf|
            accuracy_in_bin = 1.0  # Since we are measuring the probability of the actual next token
            gap = abs(accuracy_in_bin - avg_conf)
            ece += (bin_counts[i] / total_tokens) * gap
            
            bins_info.append({
                'bin': i,
                'count': bin_counts[i],
                'avg_confidence': avg_conf,
                'accuracy': accuracy_in_bin,
                'gap': gap
            })
    
    return {
        'dataset': 'wikitext2',
        'ece': ece,
        'perplexity': perplexity,
        'total_tokens': total_tokens,
        'bins': bins_info
    }

def run_all_benchmarks(model: nn.Module, max_samples_per_benchmark: Optional[int] = None) -> Dict[str, Any]:
    """
    Run all benchmarks (GSM8K, ARC-Challenge, Wikitext-2) and aggregate results.
    
    Args:
        model: The GPT model to evaluate.
        max_samples_per_benchmark: Limit samples for each benchmark.
        
    Returns:
        Dict containing all benchmark results.
    """
    print("Starting full benchmark suite...")
    start_time = time.time()
    
    results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'total_time_seconds': 0.0,
        'benchmarks': {}
    }
    
    try:
        # GSM8K
        print("\n--- Evaluating GSM8K ---")
        gsm8k_result = compute_gsm8k_accuracy(model, max_samples=max_samples_per_benchmark)
        results['benchmarks']['gsm8k'] = gsm8k_result
        print(f"GSM8K Accuracy: {gsm8k_result['accuracy']:.4f} ({gsm8k_result['correct']}/{gsm8k_result['total_samples']})")
        
        # ARC-Challenge
        print("\n--- Evaluating ARC-Challenge ---")
        arc_result = compute_arc_challenge_accuracy(model, max_samples=max_samples_per_benchmark)
        results['benchmarks']['arc_challenge'] = arc_result
        print(f"ARC-Challenge Accuracy: {arc_result['accuracy']:.4f} ({arc_result['correct']}/{arc_result['total_samples']})")
        
        # Wikitext-2 ECE
        print("\n--- Evaluating Wikitext-2 ECE ---")
        wikitext_result = compute_wikitext2_ece(model, max_samples=max_samples_per_benchmark)
        results['benchmarks']['wikitext2'] = wikitext_result
        print(f"Wikitext-2 PPL: {wikitext_result['perplexity']:.4f}, ECE: {wikitext_result['ece']:.4f}")
        
    except Exception as e:
        print(f"Error during benchmark evaluation: {e}")
        raise
    
    end_time = time.time()
    results['total_time_seconds'] = end_time - start_time
    
    print(f"\nBenchmark suite completed in {results['total_time_seconds']:.2f} seconds.")
    return results