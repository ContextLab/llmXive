"""
Synthetic data generator for neural correlates of anticipatory reward processing.

Generates a synthetic dataset adhering to contracts/dataset.schema.yaml for CI validation.
Uses flat float columns to support streaming and CPU-only constraints.

Columns:
  - trial_id: string (e.g., 'trial_0001')
  - neuron_id: string (e.g., 'neuron_01')
  - spike_time_ms: float (generated via Poisson process, lambda=50Hz)
  - cue_time_ms: float (randomly distributed)
  - reward_magnitude: float (discrete levels: 0.0, 1.0, 2.0)
  - snr: float (Signal-to-Noise Ratio, > 3.0 for valid data)
  - isolation_distance: float (spike sorting metric, > 20.0 for valid data)
"""
import os
import random
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

# Configuration constants
RANDOM_SEED = 42
LAMBDA_HZ = 50.0  # Average firing rate in Hz
TRIAL_DURATION_MS = 2000.0  # Duration of a trial in ms
NUM_TRIALS = 500  # Total number of trials to generate
NUM_NEURONS = 10  # Number of simulated neurons
REWARD_LEVELS = [0.0, 1.0, 2.0]  # Discrete reward magnitudes

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> dict:
    """
    Load the dataset schema from YAML to ensure generation compliance.
    Returns the schema dictionary.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_dataset(
    num_trials: int = NUM_TRIALS,
    num_neurons: int = NUM_NEURONS,
    seed: int = RANDOM_SEED,
    output_path: str = "data/raw/synthetic_test.csv"
) -> pd.DataFrame:
    """
    Generate a synthetic neural dataset adhering to the schema.
    
    Algorithm:
    1. Initialize random seed.
    2. Iterate through trials and neurons.
    3. For each trial-neuron pair:
       - Generate a Poisson-distributed spike count based on lambda and duration.
       - Generate specific spike timestamps uniformly within the trial duration (simplified to single representative spike time for flat schema, or average time if multiple).
       - Assign cue time and reward magnitude.
       - Assign SNR and Isolation Distance ensuring they meet validation thresholds (>3 and >20).
    
    Note: The schema requires `spike_time_ms` as a float. Since the schema is flat
    (one row per spike or one row per trial-neuron summary?), the task description
    implies a summary or specific spike representation per row.
    Given the ingestion logic (T012) filters by `spike_time_ms` relative to reward,
    we will generate ONE representative spike time per trial-neuron pair, or
    generate multiple rows if the schema implies one row per spike.
    
    Re-reading T003a/T005a: "Columns: ... spike_time_ms (float)".
    Re-reading T012: "Count spikes in the specific window... Filter rows where spike_time_ms is within..."
    This implies the dataset likely represents INDIVIDUAL SPIKES (one row per spike)
    OR a summary row per trial-neuron where spike_time_ms is the mean/median.
    
    However, standard neurophysiology data (like OpenNeuro spike data) is often
    one row per spike event. If we generate one row per spike:
    - We need to generate N spikes.
    - Each row has trial_id, neuron_id, spike_time_ms.
    
    Let's assume one row per spike event to be most realistic for the "count" logic in T012.
    T012 says: "Count spikes in the specific window...". If the input is one row per spike,
    counting is just filtering rows.
    
    Generation Plan:
    - Total spikes = num_trials * num_neurons * (LAMBDA_HZ * TRIAL_DURATION_MS / 1000.0)
    - For each spike:
      - Assign a trial_id (cycling through trials).
      - Assign a neuron_id.
      - Generate spike_time_ms uniformly in [0, TRIAL_DURATION_MS].
      - Assign cue_time_ms (randomly per trial, but constant for all spikes in that trial).
      - Assign reward_magnitude (constant per trial).
      - Assign snr/isolation_distance (constant per neuron or trial-neuron pair).
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Pre-calculate total expected spikes
    avg_spikes_per_trial_neuron = (LAMBDA_HZ * TRIAL_DURATION_MS) / 1000.0
    total_expected_spikes = int(num_trials * num_neurons * avg_spikes_per_trial_neuron)
    
    # Pre-assign trial properties (Cue time, Reward magnitude) to ensure consistency within a trial
    trial_properties = {}
    for t in range(num_trials):
        trial_id = f"trial_{t:04d}"
        cue_time = np.random.uniform(500.0, 1500.0) # Cue happens between 500ms and 1500ms
        reward_mag = np.random.choice(REWARD_LEVELS)
        trial_properties[trial_id] = {
            "cue_time_ms": cue_time,
            "reward_magnitude": reward_mag
        }
    
    # Pre-assign neuron properties (SNR, Isolation Distance)
    neuron_properties = {}
    for n in range(num_neurons):
        neuron_id = f"neuron_{n:02d}"
        # Ensure SNR > 3 and Isolation Distance > 20 to pass validation in T013e
        snr = np.random.uniform(4.0, 15.0)
        iso_dist = np.random.uniform(22.0, 50.0)
        neuron_properties[neuron_id] = {
            "snr": snr,
            "isolation_distance": iso_dist
        }
    
    data = {
        "trial_id": [],
        "neuron_id": [],
        "spike_time_ms": [],
        "cue_time_ms": [],
        "reward_magnitude": [],
        "snr": [],
        "isolation_distance": []
    }
    
    current_spike_count = 0
    # We will generate exactly total_expected_spikes rows
    # To distribute them across trials and neurons:
    # We iterate through trials, then neurons, then generate spikes for that pair.
    
    for t in range(num_trials):
        trial_id = f"trial_{t:04d}"
        t_props = trial_properties[trial_id]
        
        for n in range(num_neurons):
            neuron_id = f"neuron_{n:02d}"
            n_props = neuron_properties[neuron_id]
            
            # Number of spikes for this trial-neuron pair (Poisson)
            n_spikes = np.random.poisson(avg_spikes_per_trial_neuron)
            
            if n_spikes == 0:
                continue
            
            # Generate spike times uniformly within the trial duration
            spike_times = np.random.uniform(0.0, TRIAL_DURATION_MS, n_spikes)
            
            # Append to data lists
            for st in spike_times:
                data["trial_id"].append(trial_id)
                data["neuron_id"].append(neuron_id)
                data["spike_time_ms"].append(float(st))
                data["cue_time_ms"].append(float(t_props["cue_time_ms"]))
                data["reward_magnitude"].append(float(t_props["reward_magnitude"]))
                data["snr"].append(float(n_props["snr"]))
                data["isolation_distance"].append(float(n_props["isolation_distance"]))
                
                current_spike_count += 1
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_file, index=False)
    
    print(f"Generated {len(df)} spike events for {num_trials} trials and {num_neurons} neurons.")
    print(f"Saved to: {output_path}")
    
    return df

def main():
    """Entry point for synthetic generator."""
    schema_path = "contracts/dataset.schema.yaml"
    output_path = "data/raw/synthetic_test.csv"
    
    # Validate schema exists before generation (as per task requirement)
    try:
        schema = load_schema(schema_path)
        print(f"Schema loaded successfully from {schema_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure contracts/dataset.schema.yaml exists before running the generator.")
        return 1
    
    # Generate dataset
    df = generate_synthetic_dataset(output_path=output_path)
    
    # Basic validation of generated data
    required_cols = ["trial_id", "neuron_id", "spike_time_ms", "cue_time_ms", "reward_magnitude", "snr", "isolation_distance"]
    if not all(col in df.columns for col in required_cols):
        print("Error: Generated data missing required columns.")
        return 1
    
    # Check for flat floats (not arrays)
    if df["spike_time_ms"].apply(lambda x: isinstance(x, (list, np.ndarray))).any():
        print("Error: spike_time_ms contains arrays. Schema requires flat floats.")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
