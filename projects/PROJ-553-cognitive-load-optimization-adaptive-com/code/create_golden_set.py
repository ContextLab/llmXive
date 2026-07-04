"""
create_golden_set.py

Implements the 'create' clause of FR-001 by generating a synthetic expert-labeled
dataset (Golden Set) based on a defined rubric when external data is missing.

This script generates synthetic interaction features (latency, errors, hints, pauses)
and maps them to 'expert_load_score' (0-100) using a deterministic rubric.
The output is saved to `data/processed/golden_set.csv`.

Rubric Logic (Simulated Expert Judgment):
1. Base Score: 50.0
2. Latency Factor: High latency (> 20s) adds +15, Low latency (< 5s) subtracts -10.
3. Error Factor: Each error adds +10 (max +30).
4. Hint Factor: Each hint request adds +5 (max +20).
5. Pause Factor: Long pauses (> 10s) add +5 per pause (max +15).
6. Clamp: Final score bounded to [0, 100].

This synthetic set is intended for model training and validation (US1) when
external expert-labeled data is unavailable, acknowledging the limitation
described in T006c.
"""
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Ensure the code directory is in the path if running as a script
# but rely on the project structure for imports if part of a package
# We use relative imports logic handled by the runner or explicit path setup
if __name__ == "__main__":
    # Add parent to path for local execution if needed
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
N_SAMPLES = 100  # Generate 100 rows to satisfy >= 50 requirement
SEED = 42
OUTPUT_PATH = "data/processed/golden_set.csv"

def generate_synthetic_interactions(n: int, seed: int) -> pd.DataFrame:
    """
    Generates synthetic interaction features based on realistic distributions.
    """
    random.seed(seed)
    np.random.seed(seed)

    data = {
        "session_id": [f"syn_sess_{i:04d}" for i in range(n)],
        "item_id": [f"item_{random.randint(1, 50)}" for _ in range(n)],
        # Latency in seconds: Log-normal distribution to simulate skewed human response times
        "latency_sec": np.random.lognormal(mean=2.5, sigma=1.0, size=n),
        # Errors: Poisson distribution (mostly 0, some 1, few 2+)
        "error_count": np.random.poisson(lam=0.8, size=n),
        # Hints: Poisson distribution
        "hint_count": np.random.poisson(lam=1.2, size=n),
        # Pauses > 2s: Poisson distribution
        "pause_count": np.random.poisson(lam=1.5, size=n),
        # Correctness: Binary, correlated with errors (simplified)
        "is_correct": [1 if e == 0 and random.random() > 0.2 else 0 for e in np.random.poisson(lam=0.5, size=n)]
    }

    df = pd.DataFrame(data)

    # Ensure non-negative and reasonable bounds for simulation
    df["latency_sec"] = df["latency_sec"].clip(lower=0.5, upper=60.0)
    df["error_count"] = df["error_count"].clip(lower=0, upper=5)
    df["hint_count"] = df["hint_count"].clip(lower=0, upper=10)
    df["pause_count"] = df["pause_count"].clip(lower=0, upper=15)

    return df

def apply_expert_rubric(df: pd.DataFrame) -> pd.Series:
    """
    Applies a deterministic rubric to map interaction features to an
    'expert_load_score' (0-100). This simulates an expert's judgment
    based on observable behavioral proxies.

    Rubric:
    - Base: 50
    - Latency: >20s (+15), <5s (-10), else 0
    - Errors: +10 per error (max +30)
    - Hints: +5 per hint (max +20)
    - Pauses: +5 per pause (max +15)
    """
    scores = np.full(len(df), 50.0, dtype=float)

    # Latency contribution
    high_latency_mask = df["latency_sec"] > 20.0
    low_latency_mask = df["latency_sec"] < 5.0
    scores[high_latency_mask] += 15.0
    scores[low_latency_mask] -= 10.0

    # Error contribution (capped)
    error_contribution = df["error_count"] * 10.0
    error_contribution = error_contribution.clip(upper=30.0)
    scores += error_contribution

    # Hint contribution (capped)
    hint_contribution = df["hint_count"] * 5.0
    hint_contribution = hint_contribution.clip(upper=20.0)
    scores += hint_contribution

    # Pause contribution (capped)
    pause_contribution = df["pause_count"] * 5.0
    pause_contribution = pause_contribution.clip(upper=15.0)
    scores += pause_contribution

    # Clamp final score to [0, 100]
    return scores.clip(0.0, 100.0)

def main():
    """
    Main entry point to generate the synthetic Golden Set.
    """
    print(f"[create_golden_set] Starting generation of synthetic Golden Set...")
    print(f"[create_golden_set] Target: {OUTPUT_PATH}")

    # Ensure output directory exists
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if Path(OUTPUT_PATH).exists():
        print(f"[create_golden_set] Warning: {OUTPUT_PATH} already exists. Overwriting.")

    # Generate data
    print(f"[create_golden_set] Generating {N_SAMPLES} synthetic interactions...")
    df_interactions = generate_synthetic_interactions(N_SAMPLES, SEED)

    # Apply rubric
    print(f"[create_golden_set] Applying expert rubric to generate load scores...")
    df_interactions["expert_load_score"] = apply_expert_rubric(df_interactions)

    # Round scores to 2 decimal places
    df_interactions["expert_load_score"] = df_interactions["expert_load_score"].round(2)

    # Save to CSV
    df_interactions.to_csv(OUTPUT_PATH, index=False)

    # Verify output
    if Path(OUTPUT_PATH).exists():
        stats = df_interactions.describe()
        print(f"[create_golden_set] SUCCESS: Golden Set created at {OUTPUT_PATH}")
        print(f"[create_golden_set] Rows: {len(df_interactions)}")
        print(f"[create_golden_set] Score Range: [{df_interactions['expert_load_score'].min():.2f}, {df_interactions['expert_load_score'].max():.2f}]")
        print(f"[create_golden_set] Score Mean: {df_interactions['expert_load_score'].mean():.2f}")
        return 0
    else:
        print(f"[create_golden_set] ERROR: Failed to write file to {OUTPUT_PATH}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
