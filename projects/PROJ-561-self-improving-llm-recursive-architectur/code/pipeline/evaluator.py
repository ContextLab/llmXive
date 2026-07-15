import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
import math
import os

from pipeline.loader import load_gsm8k, load_arc_challenge, load_wikitext2
from pipeline.model import GPTForCausalLM
from config import get_config_summary

def compute_gsm8k_accuracy(
    model: GPTForCausalLM,
    tokenizer: Any,
    max_new_tokens: int = 128,
    batch_size: int = 1,
    device: str = "cpu"
) -> Dict[str, float]:
    """
    Evaluate GSM8K math reasoning accuracy.
    Uses greedy decoding to extract the final answer and compares it to the ground truth.
    """
    dataset = load_gsm8k(split="test")
    correct = 0
    total = 0

    # GSM8K prompt template (simplified)
    prompt_prefix = "Question: "
    
    for item in dataset:
        question = item["question"]
        ground_truth = item["answer"]
        
        # Extract the final answer from ground truth (format: "... #### 123")
        gt_parts = ground_truth.split("####")
        if len(gt_parts) < 2:
            continue
        gt_answer = gt_parts[-1].strip()
        
        prompt = prompt_prefix + question
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer from generated text (look for "####" or last number)
        if "####" in generated_text:
            gen_answer = generated_text.split("####")[-1].strip()
        else:
            # Fallback: extract last number sequence
            import re
            numbers = re.findall(r'\d+\.?\d*', generated_text)
            gen_answer = numbers[-1] if numbers else ""
        
        # Normalize comparison (remove commas, spaces)
        if gen_answer.replace(",", "").replace(" ", "") == gt_answer.replace(",", "").replace(" ", ""):
            correct += 1
        
        total += 1
        if total % 10 == 0:
            print(f"  GSM8K Progress: {total}/{len(dataset)}")

    accuracy = correct / total if total > 0 else 0.0
    return {
        "dataset": "gsm8k",
        "accuracy": accuracy,
        "total_samples": total,
        "correct": correct
    }

def compute_arc_challenge_accuracy(
    model: GPTForCausalLM,
    tokenizer: Any,
    device: str = "cpu"
) -> Dict[str, float]:
    """
    Evaluate ARC-Challenge multiple choice accuracy.
    Formats prompt as "Question: ... Choices: ..." and selects the option with lowest log prob.
    """
    dataset = load_arc_challenge(split="test")
    correct = 0
    total = 0

    for item in dataset:
        question = item["question"]
        choices = item["choices"]
        label = item["answerKey"]
        
        # Construct prompt with choices
        choice_text = " ".join([f"{c['label']}. {c['text']}" for c in choices])
        prompt = f"Question: {question}\nChoices: {choice_text}\nAnswer:"
        
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        input_len = inputs["input_ids"].shape[1]
        
        # Evaluate log probability for each choice letter
        choice_probs = {}
        for choice in choices:
            label_char = choice["label"]
            # Tokenize just the choice label
            choice_input = tokenizer(label_char, return_tensors="pt").to(device)
            
            with torch.no_grad():
                outputs = model(
                    input_ids=torch.cat([inputs["input_ids"], choice_input["input_ids"]], dim=1),
                    attention_mask=torch.cat([inputs["attention_mask"], choice_input["attention_mask"]], dim=1)
                )
            
            logits = outputs.logits[0, input_len-1 : input_len]
            probs = F.softmax(logits, dim=-1)
            token_ids = choice_input["input_ids"][0]
            
            # Get probability of the first token of the choice label
            if len(token_ids) > 0:
                prob = probs[token_ids[0]].item()
            else:
                prob = 0.0
            
            choice_probs[label_char] = prob

        # Select best choice
        best_choice = max(choice_probs, key=choice_probs.get)
        
        if best_choice == label:
            correct += 1
        
        total += 1
        if total % 10 == 0:
            print(f"  ARC Progress: {total}/{len(dataset)}")

    accuracy = correct / total if total > 0 else 0.0
    return {
        "dataset": "arc_challenge",
        "accuracy": accuracy,
        "total_samples": total,
        "correct": correct
    }

def compute_wikitext2_ece(
    model: GPTForCausalLM,
    tokenizer: Any,
    device: str = "cpu",
    num_bins: int = 15
) -> Dict[str, float]:
    """
    Compute Expected Calibration Error (ECE) on Wikitext-2.
    Measures the difference between predicted confidence and actual accuracy.
    """
    dataset = load_wikitext2(split="test")
    
    # Concatenate all text for continuous evaluation
    text_samples = [item["text"] for item in dataset if item["text"].strip()]
    full_text = " ".join(text_samples)
    
    # Tokenize
    tokens = tokenizer.encode(full_text, add_special_tokens=False)
    
    if len(tokens) < 2:
        return {"dataset": "wikitext2", "ece": 0.0, "perplexity": float('inf')}

    # We will evaluate token-by-token calibration
    # Group predictions into bins based on confidence
    bins = [[] for _ in range(num_bins)]
    
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        # Process in chunks to avoid memory issues
        chunk_size = 512
        for i in range(0, len(tokens) - 1, chunk_size):
            chunk = tokens[i : i + chunk_size]
            if len(chunk) < 2:
                continue
            
            input_ids = torch.tensor([chunk[:-1]]).to(device)
            target_ids = torch.tensor([chunk[1:]]).to(device)
            
            outputs = model(input_ids=input_ids)
            logits = outputs.logits[0] # [seq_len, vocab]
            
            probs = F.softmax(logits, dim=-1)
            confidences, predictions = torch.max(probs, dim=-1)
            
            for j in range(len(confidences)):
                conf = confidences[j].item()
                pred = predictions[j].item()
                actual = target_ids[0, j].item()
                
                is_correct = (pred == actual)
                bin_idx = int(conf * num_bins)
                if bin_idx >= num_bins:
                    bin_idx = num_bins - 1
                
                bins[bin_idx].append((conf, is_correct))
                total_samples += 1
                if is_correct:
                    total_correct += 1

    # Calculate ECE
    ece = 0.0
    for bin_items in bins:
        if not bin_items:
            continue
        
        avg_conf = sum(c for c, _ in bin_items) / len(bin_items)
        avg_acc = sum(1 for _, c in bin_items if c) / len(bin_items)
        
        ece += (len(bin_items) / total_samples) * abs(avg_conf - avg_acc)

    # Also compute Perplexity (standard metric for Wikitext-2)
    # Re-run for perplexity calculation on the full set if needed, 
    # but for this task ECE is the primary focus.
    # A simple perplexity estimate based on average log prob
    avg_log_prob = 0.0
    count = 0
    with torch.no_grad():
       # Re-iterate to get exact log probs for PPL
       chunk_size = 512
       for i in range(0, len(tokens) - 1, chunk_size):
          chunk = tokens[i : i + chunk_size]
          if len(chunk) < 2: continue
          input_ids = torch.tensor([chunk[:-1]]).to(device)
          target_ids = torch.tensor([chunk[1:]]).to(device)
          outputs = model(input_ids=input_ids, labels=target_ids)
          loss = outputs.loss.item()
          avg_log_prob -= loss * chunk[1:].shape[0] # loss is per token
          count += chunk[1:].shape[0]
       
       if count > 0:
           avg_log_prob /= count
           perplexity = math.exp(avg_log_prob)
       else:
           perplexity = float('inf')

    return {
        "dataset": "wikitext2",
        "ece": ece,
        "perplexity": perplexity,
        "total_samples": total_samples
    }

def run_all_benchmarks(
    model: GPTForCausalLM,
    tokenizer: Any,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Orchestrates evaluation across all three benchmarks.
    Returns a consolidated dictionary of metrics.
    """
    print("Starting benchmark evaluation...")
    
    results = {
        "gsm8k": None,
        "arc_challenge": None,
        "wikitext2": None,
        "summary": {}
    }

    try:
        print("Evaluating GSM8K...")
        results["gsm8k"] = compute_gsm8k_accuracy(model, tokenizer, device=device)
        print(f"  GSM8K Accuracy: {results['gsm8k']['accuracy']:.4f}")
    except Exception as e:
        print(f"  GSM8K failed: {e}")
        results["gsm8k"] = {"error": str(e)}

    try:
        print("Evaluating ARC-Challenge...")
        results["arc_challenge"] = compute_arc_challenge_accuracy(model, tokenizer, device=device)
        print(f"  ARC Accuracy: {results['arc_challenge']['accuracy']:.4f}")
    except Exception as e:
        print(f"  ARC failed: {e}")
        results["arc_challenge"] = {"error": str(e)}

    try:
        print("Evaluating Wikitext-2 (ECE)...")
        results["wikitext2"] = compute_wikitext2_ece(model, tokenizer, device=device)
        print(f"  Wikitext-2 ECE: {results['wikitext2']['ece']:.4f}, PPL: {results['wikitext2']['perplexity']:.2f}")
    except Exception as e:
        print(f"  Wikitext-2 failed: {e}")
        results["wikitext2"] = {"error": str(e)}

    # Summary
    gsm_acc = results["gsm8k"].get("accuracy", 0.0) if results["gsm8k"] else 0.0
    arc_acc = results["arc_challenge"].get("accuracy", 0.0) if results["arc_challenge"] else 0.0
    ece = results["wikitext2"].get("ece", 0.0) if results["wikitext2"] else 0.0

    results["summary"] = {
        "gsm8k_accuracy": gsm_acc,
        "arc_accuracy": arc_acc,
        "wikitext2_ece": ece,
        "overall_score": (gsm_acc + arc_acc) / 2.0 if (gsm_acc + arc_acc) > 0 else 0.0
    }

    return results