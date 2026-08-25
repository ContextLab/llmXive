import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Constants for the rubric
RANDOM_SEED = 42
MIN_EXPERT_LABELS = 50
OUTPUT_PATH = "data/processed/golden_set.csv"
INTERACTION_FEATURES = [
    "session_id", "problem_id", "step_id", "timestamp",
    "response_time_ms", "is_correct", "hint_count", "attempt_count",
    "first_attempt_correct", "time_on_step_ms", "log_latency"
]

def generate_synthetic_interactions(n_samples: int = 100) -> pd.DataFrame:
    """
    Generates a synthetic dataset of student interactions based on realistic
    distributions found in educational datasets (like ASSISTments).
    
    This function creates the INPUT features (behavioral proxies) that will
    later be mapped to expert labels. It does NOT generate the labels itself;
    that is the job of apply_expert_rubric.
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    data = []
    for i in range(n_samples):
        session_id = f"session_{random.randint(1, 50):03d}"
        problem_id = f"prob_{random.randint(1, 100):04d}"
        step_id = f"step_{i:05d}"
        timestamp = f"2024-01-{random.randint(1, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z"
        
        # Response time: Log-normal distribution (skewed, typical for reaction times)
        # Mean ~ 10s, std ~ 5s (in log space)
        response_time_ms = int(np.random.lognormal(mean=2.3, sigma=0.8) * 1000)
        response_time_ms = max(1000, min(response_time_ms, 120000)) # Clamp between 1s and 2min
        
        # Correctness: Binary, slightly weighted towards correct but with errors
        is_correct = 1 if random.random() > 0.25 else 0
        
        # Hint count: Poisson distribution, usually 0-3
        hint_count = int(np.random.poisson(lam=1.2))
        
        # Attempt count: Geometric-like, usually 1-3
        attempt_count = int(np.random.geometric(p=0.6))
        
        first_attempt_correct = 1 if attempt_count == 1 and is_correct == 1 else 0
        
        # Time on step: Correlated with response time but slightly different
        time_on_step_ms = int(response_time_ms * random.uniform(0.8, 1.2))
        
        # Log latency feature (pre-calculated for convenience, though model might re-calc)
        log_latency = np.log1p(response_time_ms)
        
        data.append({
            "session_id": session_id,
            "problem_id": problem_id,
            "step_id": step_id,
            "timestamp": timestamp,
            "response_time_ms": response_time_ms,
            "is_correct": is_correct,
            "hint_count": hint_count,
            "attempt_count": attempt_count,
            "first_attempt_correct": first_attempt_correct,
            "time_on_step_ms": time_on_step_ms,
            "log_latency": log_latency
        })
    
    return pd.DataFrame(data)

def apply_expert_rubric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies a defined expert rubric to generate 'expert_load_score' (0-100).
    
    This simulates the 'Golden Set' creation process where an expert (or 
    a rigorous heuristic representing an expert) evaluates the interaction
    complexity.
    
    Rubric Logic (Simulating Expert Judgment):
    1. High Latency + Low Correctness = High Load (Struggle without progress)
    2. High Latency + High Correctness = Moderate Load (Deep processing)
    3. Low Latency + High Correctness = Low Load (Fluency)
    4. High Hint Count = High Load (Dependency)
    5. High Attempt Count = High Load (Trial and error)
    
    The score is normalized to 0-100.
    """
    scores = []
    
    for _, row in df.iterrows():
        # Normalize features to 0-1 scale for weighting
        # Latency: 1s to 120s -> 0 to 1
        lat_norm = min(1.0, row['response_time_ms'] / 120000.0)
        
        # Hints: 0 to 5 -> 0 to 1
        hint_norm = min(1.0, row['hint_count'] / 5.0)
        
        # Attempts: 1 to 10 -> 0 to 1
        att_norm = min(1.0, (row['attempt_count'] - 1) / 9.0)
        
        # Correctness: 0 or 1 (Inverse: 0 is high load, 1 is low load)
        correct_inv = 1.0 - row['is_correct']
        
        # Weighted Sum Calculation
        # Weights reflect the "Struggle" hypothesis
        # High latency without correctness is the strongest indicator of high load
        struggle_weight = 0.4
        hint_weight = 0.2
        attempt_weight = 0.2
        latency_weight = 0.2
        
        # Base load score
        raw_score = (
            (lat_norm * correct_inv * struggle_weight) + 
            (hint_norm * hint_weight) + 
            (att_norm * attempt_weight) + 
            (lat_norm * (1 - correct_inv) * 0.1) # Slight load even if correct but slow
        )
        
        # Scale to 0-100
        expert_score = min(100.0, max(0.0, raw_score * 100))
        
        # Add small noise to simulate human expert variation
        expert_score += random.gauss(0, 2.0)
        expert_score = min(100.0, max(0.0, expert_score))
        
        scores.append(expert_score)
    
    df = df.copy()
    df['expert_load_score'] = scores
    return df

def main():
    """
    Main entry point for T006b.
    Creates the Golden Set if it does not exist.
    """
    output_path = Path(OUTPUT_PATH)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        print(f"Warning: {output_path} already exists. Overwriting.")
    
    print("Generating synthetic interactions...")
    df = generate_synthetic_interactions(n_samples=MIN_EXPERT_LABELS + 20) # Generate slightly more than min
    
    print("Applying expert rubric to generate labels...")
    df_labeled = apply_expert_rubric(df)
    
    # Save to CSV
    df_labeled.to_csv(output_path, index=False)
    
    print(f"Successfully created Golden Set at: {output_path.absolute()}")
    print(f"Total samples: {len(df_labeled)}")
    print(f"Columns: {list(df_labeled.columns)}")
    print(f"Expert Load Score Range: [{df_labeled['expert_load_score'].min():.2f}, {df_labeled['expert_load_score'].max():.2f}]")
    
    return df_labeled

if __name__ == "__main__":
    main()