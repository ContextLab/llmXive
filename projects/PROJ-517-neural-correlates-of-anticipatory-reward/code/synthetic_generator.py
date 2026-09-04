"""
Synthetic data generator for neural correlates of anticipatory reward processing.
Generates data adhering to contracts/dataset.schema.yaml for CI validation.
"""
import os
import random
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> dict:
    """Load the dataset schema from YAML."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_dataset(
    schema: dict,
    output_path: str,
    seed: int = 42,
    n_neurons: int = 5,
    n_trials_per_neuron: int = 10
) -> pd.DataFrame:
    """
    Generate a synthetic dataset adhering to the provided schema.
    
    Args:
        schema: The dataset schema dictionary.
        output_path: Path to save the generated CSV.
        seed: Random seed for reproducibility.
        n_neurons: Number of neurons to simulate.
        n_trials_per_neuron: Number of trials per neuron.
        
    Returns:
        The generated DataFrame.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    rows = []
    
    # Define reward magnitudes for variety (e.g., Low, Medium, High)
    reward_magnitudes = [1.0, 2.0, 3.0]
    
    for neuron_idx in range(n_neurons):
        neuron_id = f"neuron_{neuron_idx}"
        
        for trial_idx in range(n_trials_per_neuron):
            trial_id = f"trial_{neuron_idx}_{trial_idx}"
            
            # Randomly select reward magnitude for this trial
            reward_mag = random.choice(reward_magnitudes)
            
            # Generate cue time (random between 0 and 2000 ms)
            cue_time = np.random.uniform(0, 2000)
            
            # Generate reward time (cue + delay, delay between 500 and 2000 ms)
            reward_delay = np.random.uniform(500, 2000)
            reward_time = cue_time + reward_delay
            
            # Generate spikes using Poisson process
            # Lambda (rate) depends on reward magnitude to simulate correlation
            # Higher reward -> slightly higher firing rate in anticipation window
            base_rate = 50.0  # Hz
            # Anticipatory window: [-500ms, 0ms] relative to reward
            # Duration = 0.5 seconds
            window_duration = 0.5 
            
            # Modulate rate based on reward magnitude
            rate_modulation = 1.0 + (reward_mag * 0.1) 
            effective_lambda = base_rate * rate_modulation
            
            # Expected spikes in window
            expected_spikes = effective_lambda * window_duration
            
            # Generate spike count for the window using Poisson
            spike_count = np.random.poisson(expected_spikes)
            
            # Generate individual spike times within the window for the schema
            # The schema expects spike_time_ms as a float. 
            # To align with the ingestion logic which might expect per-spike rows 
            # OR a single row per trial with an aggregate, we look at the schema.
            # The schema lists: trial_id, neuron_id, spike_time_ms, cue_time_ms, reward_magnitude...
            # This implies a long format where each spike is a row, OR the ingestion 
            # aggregates. 
            # However, T005 description says: "Count spikes in the specific window... 
            # Format: Expect spike_time_ms as a float column".
            # And T010 test expects: "spike_count" column in output.
            # The ingestion logic (T012) calculates spike_count.
            # To make T012 work (counting spikes in window), the input must have 
            # individual spikes OR the generator must output the count directly if 
            # the schema allows.
            # Looking at T003a: "spike_time_ms (float)". This usually implies one row per spike.
            # But T005 says "generate spikes using numpy.random.poisson".
            # Let's generate rows for each spike to be safe and strictly adhere to 
            # a "spike train" schema, but also include the metadata per row.
            # Wait, if we generate N spikes, we get N rows. The ingestion will group by trial_id.
            
            # Generate spike times in the window [-500, 0] relative to reward_time
            if spike_count > 0:
                # Uniformly distributed in the window
                spike_times_rel = np.random.uniform(-500, 0, spike_count)
                spike_times_abs = reward_time + spike_times_rel
                
                for st in spike_times_abs:
                    rows.append({
                        "trial_id": trial_id,
                        "neuron_id": neuron_id,
                        "spike_time_ms": float(st),
                        "cue_time_ms": float(cue_time),
                        "reward_time_ms": float(reward_time), # T012 needs this
                        "reward_magnitude": float(reward_mag),
                        "snr": float(np.random.uniform(3.5, 6.0)),
                        "isolation_distance": float(np.random.uniform(22.0, 35.0))
                    })
            else:
                # Even if 0 spikes, we might want a row? 
                # The schema implies spike rows. If 0 spikes, no rows for this trial?
                # But T010 expects "spike_count" in output. If a trial has 0 spikes, 
                # it won't appear in a "spike" table.
                # The test T010 checks `spike_count.sum()`. If we drop 0-spike trials, 
                # the sum is still correct, but row count might differ.
                # Let's add a placeholder row for trials with 0 spikes to ensure 
                # trial alignment is tested, or assume the ingestion handles missing trials.
                # The test T010 expects `len(df) == EXPECTED_TOTAL_ROWS`. 
                # If we drop 0-spike trials, len(df) < EXPECTED_TOTAL_ROWS.
                # Therefore, we MUST output a row for every trial, even with 0 spikes.
                # How to represent 0 spikes in a "spike" table?
                # Maybe the schema allows a row with a null spike_time or a specific marker?
                # Or the schema is actually trial-level with a list of spikes?
                # T003a says "flat float columns... to support streaming". 
                # "spike_time_ms (float)" suggests one value per row.
                # Let's assume the generator creates one row per trial, and `spike_time_ms` 
                # is the count? No, that contradicts "spike_time".
                # Alternative: The ingestion expects one row per trial, and `spike_time_ms` 
                # is actually the *count*? No, T012 says "Count spikes... filter rows where spike_time_ms is within...".
                # This implies the input has multiple rows per trial (one per spike).
                # But T010 expects `len(df) == EXPECTED_TOTAL_ROWS` (N_neurons * N_trials).
                # This is a contradiction: If 1 trial -> N spikes -> N rows.
                # Unless the generator outputs exactly 1 row per trial, and `spike_time_ms` 
                # is the *count*? But T012 logic "filter rows where spike_time_ms is within..." 
                # implies time.
                # Let's re-read T005: "Count spikes in the specific window... Format: Expect spike_time_ms as a float".
                # Maybe the input is one row per trial, and `spike_time_ms` is NOT used for counting?
                # No, T012 explicitly filters by `spike_time_ms`.
                # Hypothesis: The "synthetic_test.csv" is meant to be a list of spikes.
                # But T010 expects row count = trials.
                # Resolution: The test T010 logic `len(df) == EXPECTED_TOTAL_ROWS` might be 
                # assuming that the ingestion aggregates spikes into one row per trial.
                # If the input has N spikes for a trial, ingestion -> 1 row.
                # So `len(output_df)` should be N_trials.
                # The test input `raw_df` (from CSV) would have N_spikes rows.
                # The test `setup_module` generates the CSV.
                # If I generate 1 row per trial (with the count as a column?), then T012 logic 
                # "filter rows where spike_time_ms is within..." fails because there's no time distribution.
                # CORRECTION: The schema T003a says "spike_time_ms (float)".
                # If the input is one row per spike, then `len(raw_df)` = total spikes.
                # The test T010 expects `len(df) == EXPECTED_TOTAL_ROWS` (trials).
                # This implies the ingestion aggregates.
                # But the test also checks `raw_df['spike_count'].sum()`. 
                # If `raw_df` is the CSV, and CSV has 1 row per spike, there is no `spike_count` column in CSV.
                # There is `spike_time_ms`.
                # So the test T010 provided in the prompt is slightly flawed regarding column names 
                # if the input is raw spikes.
                # However, T005 says "generate spikes using numpy.random.poisson".
                # Let's assume the "synthetic_test.csv" is actually a TRIAL-LEVEL file 
                # where `spike_count` is pre-calculated or `spike_time_ms` is the count?
                # No, T012 says "filter rows where spike_time_ms is within...".
                # Let's assume the input CSV has ONE ROW PER SPIKE.
                # And the test T010 logic `raw_df['spike_count']` is wrong in the prompt?
                # OR, the generator outputs ONE ROW PER TRIAL, and `spike_time_ms` is a dummy 
                # or the ingestion logic is different.
                # Let's look at T012: "Count spikes in the specific window... filter rows where spike_time_ms is within...".
                # This requires multiple rows per trial.
                # So Input CSV = List of Spikes.
                # Ingestion Output = One row per Trial (aggregated).
                # Test T010: `len(df) == EXPECTED_TOTAL_ROWS` (Aggregated output).
                # Test T010: `raw_df['spike_count'].sum()`. `raw_df` is the INPUT CSV.
                # If Input CSV has no `spike_count` column, this crashes.
                # FIX: The generator MUST output a `spike_count` column in the CSV?
                # But if it's a list of spikes, every row has the same count?
                # Or maybe the generator outputs ONE ROW PER TRIAL, and `spike_time_ms` is the 
                # *start* of the window or something?
                # Let's assume the generator outputs ONE ROW PER TRIAL, and the `spike_time_ms` 
                # column is actually the *count*? No, that breaks T012.
                # Let's assume the generator outputs ONE ROW PER SPIKE, and the test T010 
                # in the prompt is slightly wrong about `raw_df['spike_count']`.
                # I will fix the generator to output ONE ROW PER SPIKE.
                # I will fix the test (T010) to calculate the expected sum from the raw data 
                # by counting rows per trial_id, or by adding a `spike_count` column to the 
                # raw data (redundant but helpful).
                # Actually, to satisfy T010's `raw_df['spike_count'].sum()`, I will add 
                # a `spike_count` column to the generated CSV that repeats the total count for that trial.
                # This allows the test to work without changing the ingestion logic (which expects spikes).
                # Wait, if I add `spike_count` to the raw CSV, and the ingestion logic 
                # "counts spikes", it might double count if it sees that column?
                # T012 logic: "Count spikes... filter rows...". It likely ignores existing columns 
                # and re-counts.
                # So: Generate 1 row per spike. Add `spike_count` column (total count for trial).
                # This satisfies T010.
                
                # Re-generate logic for 0 spikes:
                # If spike_count is 0, we still need a row for the trial to satisfy T010 row count?
                # If we output 0 rows for a trial, ingestion output will have fewer rows than trials.
                # T010 expects `len(df) == EXPECTED_TOTAL_ROWS`.
                # So we MUST output at least one row per trial.
                # If 0 spikes, output one row with a marker? Or a dummy spike?
                # Let's output a dummy row with `spike_time_ms` = -999 or similar, 
                # and `spike_count` = 0.
                # But T012 filters by time. If dummy is outside window, count=0. Correct.
                # Let's do that.
                
                # If 0 spikes, add one row with dummy time
                rows.append({
                    "trial_id": trial_id,
                    "neuron_id": neuron_id,
                    "spike_time_ms": -999.0, # Dummy
                    "cue_time_ms": float(cue_time),
                    "reward_time_ms": float(reward_time),
                    "reward_magnitude": float(reward_mag),
                    "snr": float(np.random.uniform(3.5, 6.0)),
                    "isolation_distance": float(np.random.uniform(22.0, 35.0)),
                    "spike_count": 0
                })
                # Note: For trials with spikes, we need to add `spike_count` to each row.
                # But we generate them in a loop. We can add it after.
                
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Add spike_count column for trials that had spikes
    # Group by trial_id and count rows, then map back
    if len(df) > 0:
        trial_counts = df.groupby('trial_id').size().to_dict()
        df['spike_count'] = df['trial_id'].map(trial_counts)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Generated synthetic dataset with {len(df)} rows to {output_path}")
    
    return df

def main():
    """Main entry point for generating synthetic data."""
    schema_path = "contracts/dataset.schema.yaml"
    output_path = "data/raw/synthetic_test.csv"
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return
    
    schema = load_schema(schema_path)
    generate_synthetic_dataset(
        schema=schema,
        output_path=output_path,
        seed=42,
        n_neurons=5,
        n_trials_per_neuron=10
    )

if __name__ == "__main__":
    setup_logging()
    main()
