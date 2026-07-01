#!/usr/bin/env python3
"""
Simulates Reward Hacking in a Rubric-Based RL environment (CHERRL adaptation).

This script reproduces the core quantitative result of the CHERRL paper:
"Reward Divergence". It creates a simplified environment where:
1. A 'Judge' has an injected bias (over-scores specific keywords).
2. An 'Agent' learns (simulated) to exploit this bias.
3. We measure the divergence between the Biased Reward and a True Quality Proxy.

This runs entirely on CPU, requires no GPU, and uses no external LLM APIs.
"""

import json
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
# We use a tiny sample of the real HealthBench data to keep it grounded in reality
# but small enough for instant CPU execution.
DATA_DIR = Path("data/health_bench")
RAW_JSONL = DATA_DIR / "raw" / "healthbench_eval.jsonl"
SAMPLE_SIZE = 5  # Use only 5 prompts to simulate a "mini-batch"

# The "Bias" injected into the judge
BIAS_KEYWORD = "comprehensive"
BIAS_PENALTY = 0.5  # How much the judge over-scores the keyword

# Simulation parameters
NUM_STEPS = 20  # Simulated training steps
OUTPUT_BASE = "Simulated response for the prompt: "

# --- Helper Functions ---

def load_real_prompts(sample_size: int) -> List[str]:
    """Loads real prompts from the HealthBench dataset."""
    if not RAW_JSONL.exists():
        raise FileNotFoundError(f"Real data file not found at {RAW_JSONL}. "
                                "This adaptation requires the real dataset to be present.")
    
    prompts = []
    with open(RAW_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # Extract prompt text (usually the last user message or the whole prompt list)
            prompt_content = data.get("prompt", [])
            if isinstance(prompt_content, list) and len(prompt_content) > 0:
                # Flatten to string
                text = " ".join([str(p.get("content", "")) for p in prompt_content])
                prompts.append(text)
            else:
                prompts.append(str(prompt_content))
    
    if len(prompts) == 0:
        raise ValueError("No prompts found in the real dataset file.")
    
    # Shuffle and take a small sample
    random.seed(42)
    random.shuffle(prompts)
    return prompts[:sample_size]

def calculate_true_quality(response: str, prompt: str) -> float:
    """
    A heuristic proxy for 'True Quality'.
    In a real setup, this would be a human eval or a separate unbiased model.
    Here, we assume quality is related to relevance and length, but NOT to the bias keyword.
    """
    # Simple proxy: Length + Relevance (words in common with prompt)
    prompt_words = set(prompt.lower().split())
    response_words = set(response.lower().split())
    
    overlap = len(prompt_words.intersection(response_words))
    length_score = min(len(response_words) / 20, 1.0)  # Normalize length
    
    # True quality does NOT reward the bias keyword specifically
    # If the response is just "comprehensive" repeated, quality should be low.
    base_score = (overlap * 0.1) + (length_score * 0.5)
    
    # Penalize if the response is just the bias keyword repeated (gaming)
    if response.lower().count(BIAS_KEYWORD) > 3 and len(response_words) < 10:
        base_score *= 0.2
        
    return base_score

def calculate_biased_reward(response: str, prompt: str) -> float:
    """
    The 'Judge' score with injected bias.
    It rewards the bias keyword heavily, regardless of actual quality.
    """
    base_score = calculate_true_quality(response, prompt)
    
    # Inject the bias
    count = response.lower().count(BIAS_KEYWORD)
    bias_boost = count * BIAS_PENALTY
    
    return base_score + bias_boost

def simulate_agent_step(current_template: str, step: int) -> str:
    """
    Simulates the RL agent 'learning' to hack the judge.
    In real RL, the policy updates via gradient descent.
    Here, we deterministically inject more bias keywords as steps progress,
    mimicking the convergence to a hacking policy.
    """
    # The agent 'learns' that adding the keyword increases the score.
    # We simulate this by appending the keyword more frequently.
    # In step 0: no keyword. Step 1: 1 keyword. Step 2: 2 keywords...
    # We cap it to avoid infinite length.
    num_keywords = min(step, 5) 
    
    # Construct a response that looks like it's trying to answer but is gaming the system
    response = f"{OUTPUT_BASE} {current_template}"
    for _ in range(num_keywords):
        response += f" This is a very {BIAS_KEYWORD} answer. "
    
    return response

def run_experiment():
    """Main experiment loop."""
    print("Loading real HealthBench prompts...")
    prompts = load_real_prompts(SAMPLE_SIZE)
    print(f"Loaded {len(prompts)} real prompts.")
    
    results = []
    initial_template = "Here is a detailed response."
    
    print(f"\nRunning simulation for {NUM_STEPS} steps...")
    print(f"Injecting bias keyword: '{BIAS_KEYWORD}' (Boost: +{BIAS_PENALTY}/occurrence)")
    
    for step in range(NUM_STEPS):
        step_data = []
        
        for prompt in prompts:
            # 1. Agent generates response (simulating policy update)
            response = simulate_agent_step(initial_template, step)
            
            # 2. Judge evaluates
            biased_score = calculate_biased_reward(response, prompt)
            true_score = calculate_true_quality(response, prompt)
            
            step_data.append({
                "step": step,
                "prompt_id": prompts.index(prompt),
                "biased_reward": biased_score,
                "true_quality": true_score,
                "divergence": biased_score - true_score,
                "response_length": len(response.split())
            })
        
        # Aggregate for this step
        avg_biased = np.mean([d["biased_reward"] for d in step_data])
        avg_true = np.mean([d["true_quality"] for d in step_data])
        avg_div = avg_biased - avg_true
        
        results.append({
            "step": step,
            "avg_biased_reward": avg_biased,
            "avg_true_quality": avg_true,
            "divergence": avg_div,
            "avg_response_length": np.mean([d["response_length"] for d in step_data])
        })
        
        print(f"Step {step:02d}: Biased={avg_biased:.2f}, True={avg_true:.2f}, Divergence={avg_div:.2f}")

    # --- Write Outputs ---
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame(results)
    csv_path = output_dir / "reward_divergence.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nSaved results to {csv_path}")
    
    # --- Plotting ---
    fig_dir = Path("figures")
    fig_dir.mkdir(exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df["step"], df["avg_biased_reward"], label="Biased Judge Reward", color="red", linewidth=2)
    plt.plot(df["step"], df["avg_true_quality"], label="True Quality (Proxy)", color="blue", linewidth=2, linestyle="--")
    plt.fill_between(df["step"], df["avg_true_quality"], df["avg_biased_reward"], color="gray", alpha=0.2, label="Divergence Gap")
    
    plt.title("Reward Hacking Simulation: Biased Reward vs. True Quality\n(Adaptation of CHERRL Paper)")
    plt.xlabel("Training Step (Simulated)")
    plt.ylabel("Score")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = fig_dir / "hacking_curve.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {plot_path}")
    
    print("\nExperiment complete. Reward divergence successfully reproduced.")

if __name__ == "__main__":
    run_experiment()
