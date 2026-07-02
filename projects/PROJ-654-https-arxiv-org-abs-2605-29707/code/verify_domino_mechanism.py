import json
import os
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from datasets import load_dataset

# Ensure deterministic behavior for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Configuration
MAX_SAMPLES = 50  # Small sample for CPU speed
MAX_SEQ_LEN = 64  # Truncate sequences for speed
BLOCK_SIZE = 4    # Speculative decoding block size
DEVICE = "cpu"

@dataclass
class Results:
    baseline_acceptance_rate: float
    domino_acceptance_rate: float
    baseline_kl_div: float
    domino_kl_div: float
    improvement_pct: float

class SimpleDominoHead(nn.Module):
    """
    A lightweight head that mimics the Domino paper's causal refinement.
    It takes the parallel draft embeddings and refines them based on the
    prefix context (causal dependency).
    
    Simplification: Instead of a full GRU/Transformer, we use a single
    linear projection conditioned on the previous token's hidden state.
    """
    def __init__(self, hidden_dim: int, vocab_size: int):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        # Simple causal correction: Input = [draft_embedding, prev_token_embedding]
        # Output = Correction logits
        self.causal_proj = nn.Linear(hidden_dim * 2, vocab_size)
        
    def forward(self, draft_logits: torch.Tensor, prev_hidden: torch.Tensor) -> torch.Tensor:
        """
        draft_logits: [batch, block_size, vocab]
        prev_hidden: [batch, hidden_dim] (context from before the block)
        """
        # Expand prev_hidden to match block_size
        prev_hidden_exp = prev_hidden.unsqueeze(1).expand(-1, draft_logits.size(1), -1)
        
        # Concatenate draft logits (as features) and context
        # Note: In real Domino, this is more complex, but this captures the "decoupling" logic:
        # We take the parallel draft and add a causal correction term.
        combined = torch.cat([draft_logits, prev_hidden_exp], dim=-1)
        
        # Project to vocab size
        correction = self.causal_proj(combined)
        
        # Add correction to original logits
        refined_logits = draft_logits + correction
        return refined_logits

def load_models():
    """Loads tiny models for CPU execution."""
    print("Loading tiny models for CPU execution...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Target model (larger proxy)
    target_model = AutoModelForCausalLM.from_pretrained("gpt2")
    target_model.eval()
    target_model.to(DEVICE)
    
    # Draft model (smaller proxy)
    draft_model = AutoModelForCausalLM.from_pretrained("distilgpt2")
    draft_model.eval()
    draft_model.to(DEVICE)
    
    # Initialize Domino Head
    hidden_dim = draft_model.config.hidden_size
    domino_head = SimpleDominoHead(hidden_dim, tokenizer.vocab_size)
    domino_head.eval()
    domino_head.to(DEVICE)
    
    return tokenizer, target_model, draft_model, domino_head, hidden_dim

def load_sampled_dataset(max_samples: int):
    """Loads a small slice of GSM8K."""
    print(f"Loading {max_samples} samples from GSM8K...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
        # Select first N samples
        dataset = dataset.select(range(min(max_samples, len(dataset))))
        return dataset
    except Exception as e:
        # Fallback to a simple synthetic-like text if HF fails, but keep it REAL text
        # (Simulating a small real dataset if the download fails, though we try HF first)
        print(f"Warning: Could not load GSM8K. Using a small static real-text sample. Error: {e}")
        return [
            {"question": "If I have 3 apples and buy 2 more, how many do I have?", "answer": "5"},
            {"question": "What is 2 + 2?", "answer": "4"},
            {"question": "Calculate 10 * 10.", "answer": "100"},
        ] * 20 # Repeat to fill

def get_draft_and_target_distributions(prompt: str, tokenizer, target_model, draft_model, domino_head, hidden_dim):
    """
    Simulates the speculative decoding step:
    1. Draft model generates a block in parallel (simplified as one forward pass).
    2. Target model generates the same block.
    3. Domino Head refines the draft distribution.
    4. Compare acceptance rates.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    
    # 1. Get Context (previous hidden state) for the Domino Head
    # We take the last hidden state of the prompt as the "prefix context"
    with torch.no_grad():
        # Target context
        target_out = target_model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
        target_hidden = target_out.hidden_states[-1][:, -1, :] # Last token of prompt
        
        # Draft context (for parallel draft, we might use the same or a different one)
        draft_out = draft_model(input_ids=input_ids, attention_mask=attention_mask)
        draft_hidden = draft_out.last_hidden_state[:, -1, :]
    
    # 2. Simulate Parallel Drafting (Simplified: Generate next BLOCK_SIZE tokens)
    # In reality, this is complex. Here we simulate the *distribution* of the draft
    # by running the draft model for BLOCK_SIZE steps autoregressively (since it's tiny)
    # but we treat it as the "parallel draft" distribution source.
    
    draft_logits_list = []
    current_ids = input_ids.clone()
    
    for i in range(BLOCK_SIZE):
        with torch.no_grad():
            out = draft_model(input_ids=current_ids, attention_mask=attention_mask)
            logits = out.logits[:, -1, :] # Logits for the next token
            draft_logits_list.append(logits)
            # Sample one token to continue the sequence for the next step (simplified simulation)
            next_token = torch.argmax(logits, dim=-1, keepdim=True)
            current_ids = torch.cat([current_ids, next_token], dim=1)
            attention_mask = torch.cat([attention_mask, torch.ones_like(next_token)], dim=1)
    
    draft_logits_block = torch.stack(draft_logits_list, dim=1) # [1, block_size, vocab]
    
    # 3. Apply Domino Head (Causal Refinement)
    # The head takes the draft logits and the prefix context (target_hidden)
    refined_logits = domino_head(draft_logits_block, target_hidden)
    
    # 4. Get Target Distribution for the SAME block (Ground Truth)
    # We run the target model for BLOCK_SIZE steps to get the "correct" distributions
    target_logits_list = []
    current_ids = input_ids.clone()
    
    for i in range(BLOCK_SIZE):
        with torch.no_grad():
            out = target_model(input_ids=current_ids, attention_mask=attention_mask)
            logits = out.logits[:, -1, :]
            target_logits_list.append(logits)
            next_token = torch.argmax(logits, dim=-1, keepdim=True)
            current_ids = torch.cat([current_ids, next_token], dim=1)
            attention_mask = torch.cat([attention_mask, torch.ones_like(next_token)], dim=1)
    
    target_logits_block = torch.stack(target_logits_list, dim=1) # [1, block_size, vocab]
    
    # 5. Calculate Metrics
    # A. KL Divergence (Draft vs Target)
    # B. Acceptance Rate (Simulated: probability that Draft == Target)
    
    def calculate_metrics(draft_logits, target_logits):
        # Softmax to get probabilities
        draft_probs = torch.softmax(draft_logits, dim=-1)
        target_probs = torch.softmax(target_logits, dim=-1)
        
        # KL Divergence: D_KL(Target || Draft) -> How much info is lost?
        # Lower is better.
        kl_div = torch.nn.functional.kl_div(
            torch.log(draft_probs + 1e-9), 
            target_probs, 
            reduction='batchmean'
        ).item()
        
        # Simulated Acceptance Rate:
        # In speculative decoding, we accept a token if it matches the target sample.
        # Here we estimate the probability of agreement.
        # P(Agree) = Sum_t (min(P_draft(t), P_target(t)))
        agreement_prob = torch.minimum(draft_probs, target_probs).sum(dim=-1).mean().item()
        
        return kl_div, agreement_prob
    
    baseline_kl, baseline_acc = calculate_metrics(draft_logits_block, target_logits_block)
    domino_kl, domino_acc = calculate_metrics(refined_logits, target_logits_block)
    
    return {
        "baseline_kl": baseline_kl,
        "baseline_acc": baseline_acc,
        "domino_kl": domino_kl,
        "domino_acc": domino_acc
    }

def main():
    print("Starting Domino Mechanism Verification...")
    print(f"Device: {DEVICE}")
    
    # 1. Load Models
    tokenizer, target_model, draft_model, domino_head, hidden_dim = load_models()
    
    # 2. Load Data
    dataset = load_sampled_dataset(MAX_SAMPLES)
    
    results = []
    total_baseline_acc = 0.0
    total_domino_acc = 0.0
    total_baseline_kl = 0.0
    total_domino_kl = 0.0
    
    print(f"Processing {len(dataset)} samples...")
    
    for i, item in enumerate(dataset):
        # Extract prompt (question)
        prompt = item.get("question", str(item))
        if not prompt:
            continue
            
        try:
            metrics = get_draft_and_target_distributions(
                prompt, tokenizer, target_model, draft_model, domino_head, hidden_dim
            )
            results.append({
                "sample_idx": i,
                "baseline_acc": metrics["baseline_acc"],
                "domino_acc": metrics["domino_acc"],
                "baseline_kl": metrics["baseline_kl"],
                "domino_kl": metrics["domino_kl"]
            })
            
            total_baseline_acc += metrics["baseline_acc"]
            total_domino_acc += metrics["domino_acc"]
            total_baseline_kl += metrics["baseline_kl"]
            total_domino_kl += metrics["domino_kl"]
            
        except Exception as e:
            print(f"Error processing sample {i}: {e}")
            continue
            
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{len(dataset)} samples...")

    # 3. Aggregate Results
    n_samples = len(results)
    if n_samples == 0:
        print("No results generated.")
        return

    avg_baseline_acc = total_baseline_acc / n_samples
    avg_domino_acc = total_domino_acc / n_samples
    avg_baseline_kl = total_baseline_kl / n_samples
    avg_domino_kl = total_domino_kl / n_samples
    
    # Improvement in Acceptance Rate (Higher is better)
    acc_improvement = ((avg_domino_acc - avg_baseline_acc) / avg_baseline_acc) * 100
    # Improvement in KL (Lower is better)
    kl_improvement = ((avg_baseline_kl - avg_domino_kl) / avg_baseline_kl) * 100

    print("\n" + "="*50)
    print("DOMINO MECHANISM VERIFICATION RESULTS")
    print("="*50)
    print(f"Samples Processed: {n_samples}")
    print(f"Baseline (Parallel Draft) Acceptance Rate: {avg_baseline_acc:.4f}")
    print(f"Domino (Refined Draft) Acceptance Rate:    {avg_domino_acc:.4f}")
    print(f"  -> Improvement: {acc_improvement:.2f}%")
    print(f"Baseline KL Divergence: {avg_baseline_kl:.4f}")
    print(f"Domino KL Divergence:   {avg_domino_kl:.4f}")
    print(f"  -> Improvement (Lower KL): {kl_improvement:.2f}%")
    print("="*50)
    
    # 4. Write Outputs
    os.makedirs("data", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    
    # Save detailed results
    with open("data/results.json", "w") as f:
        json.dump({
            "summary": {
                "baseline_acceptance_rate": avg_baseline_acc,
                "domino_acceptance_rate": avg_domino_acc,
                "acceptance_improvement_pct": acc_improvement,
                "baseline_kl_div": avg_baseline_kl,
                "domino_kl_div": avg_domino_kl,
                "kl_improvement_pct": kl_improvement,
                "samples_processed": n_samples
            },
            "details": results
        }, f, indent=2)
    
    # Save CSV for easy inspection
    with open("data/results.csv", "w") as f:
        f.write("sample_idx,baseline_acc,domino_acc,baseline_kl,domino_kl\n")
        for r in results:
            f.write(f"{r['sample_idx']},{r['baseline_acc']:.6f},{r['domino_acc']:.6f},{r['baseline_kl']:.6f},{r['domino_kl']:.6f}\n")
            
    print(f"Results saved to data/results.json and data/results.csv")

if __name__ == "__main__":
    main()
