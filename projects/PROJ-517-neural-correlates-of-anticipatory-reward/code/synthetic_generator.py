"""
Synthetic Data Generator for Neural Correlates of Anticipatory Reward Processing.

Generates a synthetic dataset adhering to `contracts/dataset.schema.yaml`
for CI validation purposes.

Output: data/raw/synthetic_test.csv
"""
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def load_schema(schema_path: str) -> dict:
    """Load the dataset schema from YAML."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def generate_synthetic_dataset(
    seed: int = 42,
    n_neurons: int = 5,
    n_trials_per_neuron: int = 40,
    output_path: str = "data/raw/synthetic_test.csv",
    schema_path: str = "contracts/dataset.schema.yaml",
) -> pd.DataFrame:
    """
    Generate a synthetic dataset adhering to the project schema.
    
    Parameters
    ----------
    seed : int
        Random seed for reproducibility.
    n_neurons : int
        Number of distinct neurons to simulate.
    n_trials_per_neuron : int
        Number of trials per neuron (ensures >= 30 per reward level if balanced).
    output_path : str
        Path to save the generated CSV.
    schema_path : str
        Path to the schema definition file.
        
    Returns
    -------
    pd.DataFrame
        The generated dataset.
    """
    # Load schema to ensure adherence
    schema = load_schema(schema_path)
    required_fields = list(schema.get("properties", {}).keys())
    
    # Validate required fields exist in our generation logic
    # Expected fields based on T006 context:
    # trial_id, neuron_id, spike_timestamps, reward_magnitude, cue_timestamps, spike_sorting_metadata
    
    random.seed(seed)
    np.random.seed(seed)
    
    data = []
    trial_counter = 0
    
    reward_levels = [0.0, 0.5, 1.0]  # Three reward magnitudes
    
    for neuron_idx in range(n_neurons):
        neuron_id = f"neuron_{neuron_idx:03d}"
        
        # Generate spike sorting metadata (static per neuron for simplicity)
        snr = np.random.uniform(5.0, 15.0)
        isolation_dist = np.random.uniform(25.0, 40.0)
        spike_sorting_metadata = {
            "snr": round(snr, 2),
            "isolation_distance": round(isolation_dist, 2),
            "l_ratio": round(np.random.uniform(0.0, 0.1), 4),
            "d_prime": round(np.random.uniform(1.0, 3.0), 2)
        }
        
        # Balance trials across reward levels to ensure >= 30 per level
        trials_per_level = n_trials_per_neuron // len(reward_levels)
        
        for reward_mag in reward_levels:
            for _ in range(trials_per_level):
                trial_counter += 1
                trial_id = f"trial_{trial_counter:05d}"
                
                # Simulate cue and reward timestamps (relative to trial start)
                # Cue at -2000ms, Reward at -500ms relative to trial end (or 0ms)
                # Let's define trial start at 0, cue at 2000ms, reward at 2500ms
                cue_ts = 2000 + np.random.uniform(-50, 50)
                reward_ts = 2500 + np.random.uniform(-50, 50)
                
                # Ensure delay >= 500ms (Constraint from T013d)
                delay = reward_ts - cue_ts
                if delay < 500:
                    cue_ts = reward_ts - 600
                
                # Generate synthetic spike timestamps
                # Base firing rate ~ 20Hz, modulated by reward (higher reward -> slightly higher rate)
                base_rate = 20.0
                reward_modulation = reward_mag * 5.0  # Up to 5Hz increase
                rate = base_rate + reward_modulation + np.random.normal(0, 2)
                
                # Simulate spikes in a 2-second window ([-1000ms, 1000ms] relative to reward)
                # Window: [reward_ts - 1000, reward_ts + 1000]
                window_start = reward_ts - 1000
                window_end = reward_ts + 1000
                window_duration = (window_end - window_start) / 1000.0  # seconds
                
                n_spikes = np.random.poisson(rate * window_duration)
                
                if n_spikes > 0:
                    spike_ts_list = np.sort(
                        np.random.uniform(window_start, window_end, n_spikes)
                    ).tolist()
                    spike_timestamps = [round(ts, 2) for ts in spike_ts_list]
                else:
                    spike_timestamps = []
                
                # Construct record
                record = {
                    "trial_id": trial_id,
                    "neuron_id": neuron_id,
                    "spike_timestamps": spike_timestamps,
                    "reward_magnitude": reward_mag,
                    "cue_timestamps": [round(cue_ts, 2)],
                    "spike_sorting_metadata": spike_sorting_metadata
                }
                
                # Verify against schema keys
                for key in required_fields:
                    if key not in record:
                        raise ValueError(f"Missing required field: {key}")
                
                data.append(record)
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    # Note: Lists and dicts in columns are saved as string representations by default in pandas
    # This is acceptable for CSV ingestion in this context, or we could serialize to JSON strings
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} trials for {n_neurons} neurons.")
    print(f"Saved to {output_path}")
    
    return df


def main():
    """Entry point for the synthetic data generator."""
    # Paths relative to project root
    schema_path = "contracts/dataset.schema.yaml"
    output_path = "data/raw/synthetic_test.csv"
    
    # Check if schema exists
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}. "
                                "Please ensure T006 (Create contracts/dataset.schema.yaml) is completed first.")
    
    generate_synthetic_dataset(
        seed=42,
        n_neurons=5,
        n_trials_per_neuron=40,  # Ensures ~13 per reward level per neuron, total > 30 per level
        output_path=output_path,
        schema_path=schema_path
    )


if __name__ == "__main__":
    main()
