import os
import random
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from logging_config import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> dict:
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_dataset(n_trials: int = 100, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic dataset adhering to the schema."""
    random.seed(seed)
    np.random.seed(seed)
    
    data = {
        "trial_id": range(n_trials),
        "neuron_id": [random.choice([1, 2, 3]) for _ in range(n_trials)],
        "spike_timestamps": [[random.uniform(0, 1) for _ in range(random.randint(1, 10))] for _ in range(n_trials)],
        "reward_magnitude": [random.choice([1, 2, 3]) for _ in range(n_trials)],
        "reward_timestamp": [0.0] * n_trials,
        "cue_timestamps": [[random.uniform(-1, -0.5)] for _ in range(n_trials)],
        "snr": [random.uniform(3.5, 6.0) for _ in range(n_trials)],
        "isolation_distance": [random.uniform(22.0, 30.0) for _ in range(n_trials)]
    }
    return pd.DataFrame(data)

def main():
    # Generate synthetic data for testing
    df = generate_synthetic_dataset()
    output_path = Path("data/raw/synthetic_test.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic dataset generated: {output_path}")

if __name__ == "__main__":
    main()
