"""
Fallback dataset generator for T015b.
Generates a synthetic dataset with [deferred] steps if the primary dataset is unavailable.
This is used ONLY when the real data source fails to load.
"""
import numpy as np
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def generate_synthetic_fallback_dataset(
    num_steps: int = 10000,
    seed: int = 42,
    flag_power_limited: bool = True
) -> pd.DataFrame:
    """
    Generates a synthetic dataset for fallback scenarios.
    
    Args:
        num_steps: Number of time steps to generate.
        seed: Random seed for reproducibility.
        flag_power_limited: Whether to mark the run as power-limited.
        
    Returns:
        DataFrame with synthetic metrics.
    """
    np.random.seed(seed)
    
    # Generate realistic-ish data
    steps = np.arange(num_steps)
    
    # Coherence: slight upward trend with noise
    coherence = 0.5 + 0.00001 * steps + np.random.normal(0, 0.05, num_steps)
    coherence = np.clip(coherence, 0, 1)
    
    # Diversity: oscillating
    diversity = 0.5 + 0.2 * np.sin(steps / 1000) + np.random.normal(0, 0.02, num_steps)
    diversity = np.clip(diversity, 0, 1)
    
    # Latency: random noise around a mean
    latency = np.random.exponential(0.01, num_steps) + 0.005
    
    # Add some [deferred] markers (simulating steps that would have been deferred)
    deferred_steps = np.random.choice(num_steps, size=int(num_steps * 0.1), replace=False)
    is_deferred = np.zeros(num_steps, dtype=bool)
    is_deferred[deferred_steps] = True
    
    df = pd.DataFrame({
        'step': steps,
        'coherence_score': coherence,
        'diversity_score': diversity,
        'step_latency': latency,
        'is_deferred': is_deferred,
        'power_limited': flag_power_limited
    })
    
    logger.warning(f"Generated synthetic fallback dataset with {num_steps} steps. "
                   f"This indicates the primary dataset was unavailable.")
    
    return df

def main():
    """CLI entry point to generate the fallback dataset."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Generate synthetic fallback dataset.")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_fallback.csv",
                        help="Output path for the synthetic dataset.")
    parser.add_argument("--steps", type=int, default=10000,
                        help="Number of steps to generate.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed.")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    df = generate_synthetic_fallback_dataset(
        num_steps=args.steps,
        seed=args.seed,
        flag_power_limited=True
    )
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False)
    logger.info(f"Synthetic fallback dataset saved to {args.output}")

if __name__ == "__main__":
    main()