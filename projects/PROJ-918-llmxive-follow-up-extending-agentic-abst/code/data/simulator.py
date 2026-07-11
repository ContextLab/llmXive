"""
Synthetic Agent Simulator (Fallback for T011).

Generates a synthetic dataset mimicking the "Agentic Abstention" benchmark.
Used ONLY when the real benchmark is unavailable.

Produces:
- task_id
- search_count
- error_freq
- tokens
- turns
- abstention_label (ground truth)
"""
import os
import logging
from pathlib import Path
import numpy as np
import pandas as pd

def run_synthetic_simulator(
    output_dir: Path,
    output_filename: str,
    seed: int,
    logger: logging.Logger
) -> Optional[Path]:
    """
    Generates synthetic data for the Agentic Abstention task.
    
    Logic:
    - Simulate 1000 tasks.
    - Search count ~ Poisson(5)
    - Error freq ~ Beta(2, 5) scaled
    - Tokens ~ Normal(200, 50)
    - Turns ~ Normal(10, 3)
    - Abstention Label: 1 if (tokens > 250 AND turns > 12) OR (error_freq > 0.3), else 0.
    """
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(seed)
    logger.info("Generating synthetic dataset...")

    n_samples = 1000

    # Generate features
    search_count = np.random.poisson(5, n_samples)
    error_freq = np.random.beta(2, 5, n_samples) # 0 to 1 range
    tokens = np.random.normal(200, 50, n_samples)
    turns = np.random.normal(10, 3, n_samples)

    # Ensure non-negative
    tokens = np.maximum(tokens, 50)
    turns = np.maximum(turns, 1)

    # Generate ground truth label based on heuristic rules (mimicking the Oracle)
    # High tokens + high turns OR high error frequency -> Abstention (1)
    abstention_label = np.where(
        (tokens > 250) & (turns > 12) | (error_freq > 0.3),
        1, 0
    )

    df = pd.DataFrame({
        'task_id': [f"synthetic_{i:04d}" for i in range(n_samples)],
        'search_count': search_count,
        'error_freq': error_freq,
        'tokens': tokens.astype(int),
        'turns': turns.astype(int),
        'abstention_label': abstention_label
    })

    output_path = output_dir / output_filename
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data written to {output_path}")

    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw", help="Output directory")
    parser.add_argument("--output-filename", default="synthetic_abstention.csv", help="Output filename")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    run_synthetic_simulator(
        output_dir=Path(args.output_dir),
        output_filename=args.output_filename,
        seed=args.seed,
        logger=logger
    )
