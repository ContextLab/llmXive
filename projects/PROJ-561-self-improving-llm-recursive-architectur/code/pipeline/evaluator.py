"""
Evaluator module for benchmarking model performance.
Implements runners for GSM8K, ARC-Challenge, and Wikitext-2 ECE.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
from datasets import load_dataset
import numpy as np
from tqdm import tqdm
import re
import os
from config import get_config

# Import loader utilities to ensure real data fetching logic is consistent
# Note: loader.py handles the actual fetching; we assume datasets are available or fetch on demand
# We will implement the fetch logic here to ensure independence and fail-fast if data missing

class VerificationGate:
    """
    A simple gate to ensure evaluation only proceeds if the model and data are valid.
    """
    def __init__(self, model: nn.Module, device: str):
        self.model = model
        self.device = device
        self.model.eval()

    def verify(self) -> bool:
        """Perform a sanity check on the model."""
        try:
            # Dummy input check
            dummy_input = torch.randint(0, 1000, (1, 10)).to(self.device)
            with torch.no_grad():
                _ = self.model(dummy_input)
            return True
        except Exception:
            return False

def _load_gsm8k() -> Tuple[List[str], List[str]]:
    """
    Load GSM8K dataset and extract questions and answers.
    Uses streaming to handle large datasets without OOM.
    """
    try:
        # Load in streaming mode to avoid downloading full dataset to disk immediately
        dataset = load_dataset("gsm8k", "main", split="test", streaming=True)
        questions = []
        answers = []
        
        # We will sample a subset for evaluation to respect time constraints if full set is too large
        # However, the task implies a full runner. We iterate.
        count = 0
        for item in dataset:
            questions.append(item['question'])
            # Extract the answer which is usually at the end after "####"
            answer_str = item['answer']
            # Clean up answer: extract the final number
            match = re.search(r'####\s*([\d,]+)', answer_str)
            if match:
                answers.append(match.group(1).replace(',', ''))
            else:
                # Fallback if regex fails, though standard GSM8K format is reliable
                answers.append(answer_str)
            count += 1
            # Optional: limit for strict time budgets, but task asks for the runner logic.
            # We will process all available in the stream if feasible.
        
        return questions, answers
    except Exception as e:
        raise RuntimeError(f"Failed to load GSM8K dataset: {e}")

def _load_arc_challenge() -> Tuple[List[str], List[str]]:
    """
    Load ARC-Challenge dataset.
    """
    try:
        dataset = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test", streaming=True)
        questions = []
        answers = []
        
        for item in dataset:
            questions.append(item['question'])
            # Answer key is the correct answer option (A, B, C, D)
            # The dataset usually has 'answerKey'
            if 'answerKey' in item:
                answers.append(item['answerKey'])
            else:
                # Fallback logic if structure differs slightly
                answers.append("A") 
        
        return questions, answers
    except Exception as e:
        raise RuntimeError(f"Failed to load ARC-Challenge dataset: {e}")

def _load_wikitext2() -> Tuple[List[str], int]:
    """
    Load Wikitext-2 dataset for ECE (Expected Calibration Error) or Perplexity.
    For ECE, we need predictions and true labels. Here we treat it as a text completion task
    to compute log-likelihoods for calibration analysis.
    """
    try:
        dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="test", streaming=True)
        texts = []
        for item in dataset:
            if item['text'].strip():
                texts.append(item['text'])
        return texts, 0 # Placeholder for length if needed
    except Exception as e:
        raise RuntimeError(f"Failed to load Wikitext-2 dataset: {e}")

def compute_gsm8k_accuracy(model: nn.Module, device: str = "cpu", max_samples: Optional[int] = None) -> float:
    """
    Compute accuracy on GSM8K.
    Strategy: Generate answer, parse final number, compare to ground truth.
    """
    verifier = VerificationGate(model, device)
    if not verifier.verify():
        raise ValueError("Model failed verification gate.")

    questions, ground_truths = _load_gsm8k()
    
    if max_samples:
        questions = questions[:max_samples]
        ground_truths = ground_truths[:max_samples]

    if not questions:
        return 0.0

    correct = 0
    total = len(questions)
    
    # Simple prompting for GSM8K: "Question: ... Answer: "
    prompt_prefix = "Question: "
    prompt_suffix = "\nAnswer: "

    # Tokenizer is assumed to be available or we use a simple tokenization if not provided.
    # Since the task doesn't specify a tokenizer import, we assume the model has a tokenizer
    # or we use a standard one. However, to keep it self-contained without external tokenizer deps
    # not in the API surface, we will use a mock tokenization strategy or assume the model
    # accepts text input if it's a high-level wrapper.
    # Given the constraints, we will implement a standard inference loop assuming `model`
    # can be called with token IDs. We need a tokenizer.
    # Since no tokenizer is in the API surface, we will use a simple heuristic:
    # We will assume the model is a standard GPT-2 style and use `transformers` tokenizer
    # if available, otherwise we raise a clear error.
    
    try:
        from transformers import GPT2Tokenizer
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
    except ImportError:
        raise ImportError("Transformers library and GPT2Tokenizer required for GSM8K evaluation.")

    for i, q in enumerate(tqdm(questions, desc="GSM8K Eval")):
        full_prompt = f"{prompt_prefix}{q}{prompt_suffix}"
        inputs = tokenizer(full_prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            # Generate up to 100 tokens
            outputs = model.generate(
                inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_new_tokens=100,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract the generated answer part
        if prompt_suffix in generated_text:
            generated_answer = generated_text.split(prompt_suffix)[-1].strip()
        else:
            generated_answer = generated_text.strip()

        # Parse the number from generated answer
        match = re.search(r'####\s*([\d,]+)|(\d+)', generated_answer)
        if match:
            pred_val = match.group(1) or match.group(2)
            if pred_val:
                pred_val = pred_val.replace(',', '')
                if pred_val == ground_truths[i]:
                    correct += 1
            else:
                # Fallback: check if the whole string matches
                if generated_answer == ground_truths[i]:
                    correct += 1
        else:
            # Check exact match if regex fails
            if generated_answer == ground_truths[i]:
                correct += 1

    return correct / total if total > 0 else 0.0

def compute_arc_challenge_accuracy(model: nn.Module, device: str = "cpu", max_samples: Optional[int] = None) -> float:
    """
    Compute accuracy on ARC-Challenge.
    Strategy: Multiple choice. Compute log-probability of each option and pick the highest.
    """
    verifier = VerificationGate(model, device)
    if not verifier.verify():
        raise ValueError("Model failed verification gate.")

    questions, ground_truths = _load_arc_challenge()

    if max_samples:
        questions = questions[:max_samples]
        ground_truths = ground_truths[:max_samples]

    if not questions:
        return 0.0

    correct = 0
    total = len(questions)

    try:
        from transformers import GPT2Tokenizer
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
    except ImportError:
        raise ImportError("Transformers library and GPT2Tokenizer required for ARC evaluation.")

    # ARC dataset structure in HuggingFace:
    # questions, choices (dict of labels to text), answerKey
    # We need to fetch choices as well.
    # Re-load to get choices
    try:
        dataset = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test", streaming=True)
        choices_list = []
        for item in dataset:
            choices_list.append(item['choices'])
            if len(choices_list) == total:
                break
    except Exception:
        raise RuntimeError("Could not retrieve choices for ARC-Challenge.")

    for i, q in enumerate(tqdm(questions, desc="ARC Eval")):
        choices = choices_list[i]
        labels = choices['label'] # ['A', 'B', 'C', 'D']
        texts = choices['text']   # [text_A, text_B, ...]
        
        log_probs = []
        for label, text in zip(labels, texts):
            prompt = f"Question: {q}\nAnswer: {text}"
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                # Shift logits to align with tokens (next token prediction)
                # We want the log prob of the generated tokens (the answer text)
                # Since we provided the full answer text, we compute log prob of the whole sequence?
                # Better: compute log prob of the answer text given the question.
                # Input: "Question: ... Answer: " -> Target: "text"
                # We'll compute log likelihood of the answer text.
                
                # Simple approach: compute log prob of the answer tokens
                # We need to mask the question part
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = inputs['input_ids'][..., 1:].contiguous()
                
                # Create a mask for the answer part
                # This is tricky without exact tokenization alignment.
                # Alternative: just compute log prob of the answer string as a continuation
                # Let's use a simpler metric: log prob of the answer tokens
                # We will just take the last token's log prob for a quick heuristic or sum over the answer.
                # For a robust implementation:
                # We will compute the average log probability of the answer tokens.
                
                # Re-tokenize just the answer to get indices
                answer_tokens = tokenizer(text, return_tensors="pt", add_special_tokens=False)['input_ids'].to(device)
                
                # We need to run the model on the question + "Answer: " to get the context, then feed answer tokens.
                # This is complex to do in a single loop without a dedicated eval harness.
                # Simplified heuristic: Compute log prob of the answer text given the prompt.
                
                full_prompt = f"Question: {q}\nAnswer: {text}"
                inputs = tokenizer(full_prompt, return_tensors="pt").to(device)
                
                # Run forward pass
                outputs = model(**inputs)
                logits = outputs.logits
                
                # Calculate log likelihood of the answer part
                # The answer part starts after the prompt
                # We assume the tokenizer splits the prompt and answer consistently.
                # We will approximate by taking the log prob of the answer tokens relative to the context.
                
                # A robust way:
                # context = "Question: {q}\nAnswer: "
                # context_ids = tokenizer(context, return_tensors="pt").input_ids
                # answer_ids = tokenizer(text, return_tensors="pt", add_special_tokens=False).input_ids
                # combined = torch.cat([context_ids, answer_ids], dim=1)
                # ... run model ...
                # ... compute log prob of answer_ids ...
                
                context = f"Question: {q}\nAnswer: "
                context_ids = tokenizer(context, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
                answer_ids = tokenizer(text, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
                
                combined_ids = torch.cat([context_ids, answer_ids], dim=1)
                
                outputs = model(combined_ids)
                logits = outputs.logits
                
                # Log probs for answer tokens
                # logits shape: [1, seq_len, vocab]
                # We want log probs for tokens at positions [len(context), len(context)+len(answer)-1]
                start_idx = context_ids.shape[1]
                end_idx = start_idx + answer_ids.shape[1]
                
                # Select logits for the answer positions
                answer_logits = logits[:, start_idx-1:end_idx-1, :] # Shifted by 1 for next token
                
                # Get the log probs
                log_probs_answer = F.log_softmax(answer_logits, dim=-1)
                
                # Gather the log prob of the actual answer tokens
                # answer_ids shape: [1, len]
                # We need to gather log_probs_answer[0, i, answer_ids[0, i+1]]
                
                token_log_probs = []
                for t_idx in range(answer_ids.shape[1]):
                    # The token at position t_idx in answer_ids corresponds to log_prob at t_idx in answer_logits
                    # Wait, answer_logits is shifted.
                    # log_prob for token at t_idx is at logits[t_idx-1] if we consider next token prediction.
                    # Let's just compute the log prob of the answer tokens given the context.
                    # We use the standard method:
                    # loss = CrossEntropy(logits, labels) -> sum over positions
                    # We want the sum of log probs.
                    
                    # Simpler: just take the log prob of the first token of the answer as a proxy? No.
                    # Let's do the full sum.
                    # We need to align: logits[t] predicts token[t+1].
                    # We want log prob of answer_ids[0, t] given context + answer_ids[0, t-1].
                    # This is complex to implement perfectly in a single file without a library.
                    # We will use a standard approximation:
                    # Compute the average log probability of the answer tokens.
                    
                    # Re-run with standard method:
                    # inputs = tokenizer(context + text, return_tensors="pt").to(device)
                    # outputs = model(**inputs)
                    # shift_logits = outputs.logits[..., :-1, :].contiguous()
                    # shift_labels = inputs.input_ids[..., 1:].contiguous()
                    # mask = torch.zeros_like(shift_labels, dtype=torch.bool)
                    # mask[:, len(context_ids[0]):] = True # Mask for answer part
                    # ... compute log prob ...
                    
                    pass # Placeholder for complex logic, using a simpler heuristic for now
                
                # Heuristic: Log prob of the first token of the answer
                # This is often sufficient for multiple choice if the model is confident.
                # We'll compute the log prob of the answer text given the question.
                # Using a simpler method:
                # Calculate log likelihood of the answer text
                # We'll use the `compute_log_likelihood` helper if we had one, but we don't.
                # We will assume the model is good and just pick the answer with the highest log prob of the first token.
                
                # Let's try a different approach: generate the answer and see if it matches.
                # But ARC is multiple choice, generation is noisy.
                # We will compute the log probability of the answer string.
                
                # Fallback to a simpler metric:
                # Just compute the log prob of the answer text.
                # We will approximate by taking the mean log prob of the answer tokens.
                
                # Implementation of log prob calculation:
                # We need to get the log prob of the answer tokens.
                # We will use the fact that the model predicts the next token.
                # We will compute the log prob of the answer tokens given the context.
                
                # Let's use a standard trick:
                # prompt = f"Question: {q}\nAnswer: "
                # answer = text
                # full_text = prompt + answer
                # inputs = tokenizer(full_text, return_tensors="pt").to(device)
                # outputs = model(**inputs)
                # logits = outputs.logits
                # shift_logits = logits[..., :-1, :].contiguous()
                # shift_labels = inputs.input_ids[..., 1:].contiguous()
                # 
                # # Create a mask for the answer part
                # prompt_len = len(tokenizer(prompt, return_tensors="pt").input_ids[0])
                # mask = torch.zeros_like(shift_labels, dtype=torch.bool)
                # mask[:, prompt_len:] = True
                # 
                # # Calculate log probs
                # log_probs = F.log_softmax(shift_logits, dim=-1)
                # # Gather log probs for the answer tokens
                # selected_log_probs = log_probs[mask]
                # # Average log prob
                # avg_log_prob = selected_log_probs.mean().item()
                # log_probs.append(avg_log_prob)
                
                # We will implement this logic here:
                prompt = f"Question: {q}\nAnswer: "
                full_text = prompt + text
                inputs = tokenizer(full_text, return_tensors="pt").to(device)
                outputs = model(**inputs)
                logits = outputs.logits
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = inputs.input_ids[..., 1:].contiguous()
                
                prompt_len = len(tokenizer(prompt, return_tensors="pt").input_ids[0])
                mask = torch.zeros_like(shift_labels, dtype=torch.bool)
                mask[:, prompt_len:] = True
                
                log_probs = F.log_softmax(shift_logits, dim=-1)
                # We need to sum the log probs for the answer tokens
                # The answer tokens are at positions where mask is True
                # We need to gather the log prob of the correct token at each position
                # log_probs shape: [1, seq_len-1, vocab]
                # shift_labels shape: [1, seq_len-1]
                # We want log_probs[0, i, shift_labels[0, i]] for i where mask[0, i] is True
                
                # This is computationally heavy to do in a loop, but we do it once per option.
                # We'll use gather
                # log_probs_gathered = log_probs.gather(2, shift_labels.unsqueeze(-1)).squeeze(-1)
                # selected_log_probs = log_probs_gathered[mask]
                # avg_log_prob = selected_log_probs.mean().item()
                
                # To avoid memory issues, we'll do it in chunks or just take the mean.
                # Let's do it.
                log_probs_gathered = log_probs.gather(2, shift_labels.unsqueeze(-1)).squeeze(-1)
                selected_log_probs = log_probs_gathered[mask]
                if selected_log_probs.numel() > 0:
                    avg_log_prob = selected_log_probs.mean().item()
                else:
                    avg_log_prob = -1e9
                log_probs.append(avg_log_prob)

        best_idx = np.argmax(log_probs)
        best_label = labels[best_idx]
        if best_label == ground_truths[i]:
            correct += 1

    return correct / total if total > 0 else 0.0

def compute_wikitext2_ece(model: nn.Module, device: str = "cpu", max_samples: Optional[int] = None) -> float:
    """
    Compute Expected Calibration Error (ECE) on Wikitext-2.
    Strategy: Compute log-likelihoods for text segments and bin by confidence.
    ECE measures the gap between average confidence and accuracy.
    For language models, "accuracy" is often replaced by "perplexity" or "next-token accuracy".
    Here we will compute the ECE of the model's predicted probabilities for the next token.
    We will bin the next-token probabilities and compare the average probability in the bin
    to the empirical accuracy (1 if the predicted token is correct, 0 otherwise).
    """
    verifier = VerificationGate(model, device)
    if not verifier.verify():
        raise ValueError("Model failed verification gate.")

    texts, _ = _load_wikitext2()
    if max_samples:
        texts = texts[:max_samples]

    if not texts:
        return 0.0

    try:
        from transformers import GPT2Tokenizer
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
    except ImportError:
        raise ImportError("Transformers library and GPT2Tokenizer required for Wikitext-2 evaluation.")

    # Bins for ECE
    n_bins = 10
    bin_accs = [0.0] * n_bins
    bin_confidences = [0.0] * n_bins
    bin_counts = [0] * n_bins

    for text in tqdm(texts, desc="Wikitext-2 ECE"):
        # Tokenize the text
        # We will evaluate on the next token prediction for each token in the text
        # We need to skip the last token as there is no next token
        inputs = tokenizer(text, return_tensors="pt").to(device)
        input_ids = inputs['input_ids']
        
        if input_ids.shape[1] < 2:
            continue
        
        # Run model
        with torch.no_grad():
            outputs = model(input_ids)
            logits = outputs.logits
        
        # Log probs
        log_probs = F.log_softmax(logits, dim=-1)
        
        # Shift for next token prediction
        # logits[i] predicts input_ids[i+1]
        # We want to compare the predicted token with the actual next token
        for t in range(input_ids.shape[1] - 1):
            # Get the predicted distribution for the next token
            # logits at position t predicts token at t+1
            dist = log_probs[0, t, :] # [vocab]
            pred_token = torch.argmax(dist)
            confidence = torch.exp(dist[pred_token]).item()
            
            # Actual next token
            actual_token = input_ids[0, t+1].item()
            
            is_correct = (pred_token.item() == actual_token)
            
            # Bin by confidence
            bin_idx = min(int(confidence * n_bins), n_bins - 1)
            
            bin_accs[bin_idx] += 1 if is_correct else 0
            bin_confidences[bin_idx] += confidence
            bin_counts[bin_idx] += 1

    # Compute ECE
    ece = 0.0
    total_tokens = sum(bin_counts)
    if total_tokens == 0:
        return 0.0

    for i in range(n_bins):
        if bin_counts[i] > 0:
            avg_confidence = bin_confidences[i] / bin_counts[i]
            avg_accuracy = bin_accs[i] / bin_counts[i]
            ece += (bin_counts[i] / total_tokens) * abs(avg_confidence - avg_accuracy)

    return ece

def run_all_benchmarks(model: nn.Module, device: str = "cpu") -> Dict[str, float]:
    """
    Run all benchmarks and return results.
    """
    results = {}
    
    # GSM8K
    try:
        results['gsm8k_accuracy'] = compute_gsm8k_accuracy(model, device)
    except Exception as e:
        results['gsm8k_accuracy'] = float('nan')
        print(f"Error in GSM8K evaluation: {e}")
    
    # ARC-Challenge
    try:
        results['arc_accuracy'] = compute_arc_challenge_accuracy(model, device)
    except Exception as e:
        results['arc_accuracy'] = float('nan')
        print(f"Error in ARC evaluation: {e}")
    
    # Wikitext-2 ECE
    try:
        results['wikitext2_ece'] = compute_wikitext2_ece(model, device)
    except Exception as e:
        results['wikitext2_ece'] = float('nan')
        print(f"Error in Wikitext-2 evaluation: {e}")
    
    return results