import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Seed for reproducibility
RANDOM_SEED = 42
MIN_ROWS = 50

def generate_synthetic_interactions(n_rows: int = MIN_ROWS) -> pd.DataFrame:
    """
    Generates a synthetic set of student interactions to serve as a placeholder
    for the Golden Set if external expert-labeled data is unavailable.
    
    The data simulates realistic behavioral proxies (latency, errors, hints)
    that are typically correlated with cognitive load.
    
    Columns:
      - interaction_id: Unique identifier
      - skill_id: Simulated skill category
      - response_latency: Time taken to answer (seconds)
      - is_correct: Binary correctness
      - hint_count: Number of hints requested
      - attempt_count: Number of attempts before success/fail
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    interaction_ids = [f"synth_{i:05d}" for i in range(n_rows)]
    
    # Simulate skills
    skills = ["skill_01", "skill_02", "skill_03", "skill_04", "skill_05"]
    skill_ids = [random.choice(skills) for _ in range(n_rows)]
    
    # Simulate response latency (log-normal distribution to mimic real data)
    # Mean ~ 15s, std dev ~ 10s, clipped to reasonable bounds
    latencies = np.random.lognormal(mean=2.5, sigma=0.8, size=n_rows)
    latencies = np.clip(latencies, 1.0, 120.0) # 1s to 2 mins
    
    # Simulate correctness (biased towards success, but with difficulty variance)
    # Probability of success varies by "difficulty" (simulated via skill)
    probs = [0.9 if s == "skill_01" else 0.7 if s == "skill_02" else 0.5 for s in skill_ids]
    is_correct = [random.random() < p for p in probs]
    
    # Simulate hint counts (Poisson distribution)
    # Higher hints for harder skills
    hint_rates = [2.0 if s == "skill_03" else 1.0 if s == "skill_02" else 0.5 for s in skill_ids]
    hint_counts = [int(np.random.poisson(lam=rate)) for rate in hint_rates]
    hint_counts = np.clip(hint_counts, 0, 10)
    
    # Simulate attempt counts
    attempt_counts = [1 + int(np.random.geometric(p=0.8 if c else 0.3)) for c in is_correct]
    attempt_counts = np.clip(attempt_counts, 1, 10)
    
    df = pd.DataFrame({
        "interaction_id": interaction_ids,
        "skill_id": skill_ids,
        "response_latency": latencies,
        "is_correct": is_correct,
        "hint_count": hint_counts,
        "attempt_count": attempt_counts
    })
    
    return df

def apply_expert_rubric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies a heuristic rubric to derive a synthetic 'expert_load_score' (0-100).
    
    This function simulates how an expert might label interactions based on
    behavioral proxies:
    - High latency -> Higher load
    - More hints -> Higher load
    - More attempts -> Higher load
    - Incorrect answer -> Higher load
    
    The formula is a weighted sum normalized to 0-100.
    """
    # Normalize features to 0-1 scale roughly
    # Latency: 0-60s mapped to 0-0.5
    lat_norm = df['response_latency'].clip(0, 60) / 60.0 * 0.5
    
    # Hints: 0-5 mapped to 0-0.2
    hint_norm = df['hint_count'].clip(0, 5) / 5.0 * 0.2
    
    # Attempts: 1-5 mapped to 0-0.15
    att_norm = df['attempt_count'].clip(1, 5) / 5.0 * 0.15
    
    # Correctness: 0 (correct) -> 0, 1 (incorrect) -> 0.15
    err_norm = (~df['is_correct']).astype(int) * 0.15
    
    # Combine
    load_score = (lat_norm + hint_norm + att_norm + err_norm) * 100
    
    # Clip to 0-100
    load_score = load_score.clip(0, 100)
    
    # Add a small amount of random noise to simulate human variability
    noise = np.random.normal(0, 2, len(df))
    load_score = load_score + noise
    load_score = load_score.clip(0, 100)
    
    df['expert_load_score'] = load_score.round(2)
    
    return df

def main():
    """
    Main entry point for T007b.
    Checks for existing golden set. If missing/invalid, generates synthetic.
    """
    output_path = Path("data/processed/golden_set.csv")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and is valid
    if output_path.exists():
        try:
            df = pd.read_csv(output_path)
            if 'expert_load_score' in df.columns and len(df) >= MIN_ROWS:
                # Validate range
                if df['expert_load_score'].between(0, 100).all():
                    print(f"Found valid Golden Set at {output_path} ({len(df)} rows).")
                    print("Skipping generation.")
                    return
            else:
                print(f"Found {output_path} but it is invalid (missing score or < {MIN_ROWS} rows). Regenerating.")
        except Exception as e:
            print(f"Error reading {output_path}: {e}. Regenerating.")
    
    print("Generating synthetic Golden Set...")
    
    # Generate data
    df_raw = generate_synthetic_interactions(n_rows=MIN_ROWS)
    
    # Apply rubric
    df_labeled = apply_expert_rubric(df_raw)
    
    # Select final columns
    final_cols = [
        "interaction_id", 
        "skill_id", 
        "response_latency", 
        "is_correct", 
        "hint_count", 
        "attempt_count", 
        "expert_load_score"
    ]
    df_final = df_labeled[final_cols]
    
    # Save
    df_final.to_csv(output_path, index=False)
    print(f"Successfully saved synthetic Golden Set to {output_path}")
    print(f"Rows: {len(df_final)}, Score range: [{df_final['expert_load_score'].min():.2f}, {df_final['expert_load_score'].max():.2f}]")

if __name__ == "__main__":
    main()
