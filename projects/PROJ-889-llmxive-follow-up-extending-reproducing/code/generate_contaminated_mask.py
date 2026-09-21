import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

from config import get_project_root, DataConfig
from utils.io_utils import load_csv, save_csv, write_json
from utils.math_utils import calculate_pearson_correlation

def load_divergence_data() -> pd.DataFrame:
    """Loads the aggregated divergence data from T015."""
    data_path = get_project_root() / DataConfig.PROCESSED_DIR / "trajectories_divergence.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Required divergence data not found at {data_path}. Run T015 first.")
    return load_csv(str(data_path))

def generate_is_contaminated_mask(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the is_contaminated boolean column based on ground truth hacking events.
    
    Logic:
    1. Identify hacking events where G(t) > 3 * MAD(G).
    2. Find contiguous segments of these events.
    3. If a segment duration > sliding_window_size (W=20), mark all timesteps in that segment as contaminated.
    """
    # Ensure we have the necessary columns
    required_cols = ['G_t', 'hacked_label', 'seed_id', 'bias_type', 'timestep']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.copy()
    df['is_contaminated'] = False
    
    W = 20  # Sliding window size
    
    # Calculate MAD for G(t) to identify events
    # Group by seed and bias_type to calculate local MAD
    for (seed, bias), group in df.groupby(['seed_id', 'bias_type']):
        g_values = group['G_t'].values
        if len(g_values) == 0:
            continue
        
        median_g = np.median(g_values)
        mad_g = np.median(np.abs(g_values - median_g))
        
        # Define threshold for hacking event (3 * MAD)
        # Avoid division by zero or very small MAD
        if mad_g < 1e-9:
            threshold = 3.0
        else:
            threshold = 3.0 * mad_g
        
        # Identify event timesteps (where G(t) is significantly high)
        # Note: The spec says "flag a timestep as an 'event' if G(t) > 3 * MAD(G)"
        # However, the task description also says "Read ground-truth labels from T031".
        # Since T031 hasn't run yet (T032 is a prerequisite for T031), we must rely on the
        # statistical definition of an event (G(t) > 3*MAD) to identify potential hacking segments
        # that might contaminate the baseline if they are too long.
        
        # Actually, re-reading T025 description: "Identify contiguous segments of timesteps 
        # where the ground-truth label is 'hacked' AND the segment duration exceeds..."
        # This creates a circular dependency if T031 is required.
        # However, T025 description also says: "To identify 'hacking events' for duration calculation, 
        # flag a timestep as an 'event' if G(t) > 3 * MAD(G), as authorized by the spec's edge case handling."
        # This implies we use the statistical definition to find the segments, not the T031 labels (which don't exist yet).
        
        events = g_values > threshold
        
        # Find contiguous segments of events
        indices = np.where(events)[0]
        if len(indices) == 0:
            continue
        
        # Find breaks in contiguous indices
        breaks = np.where(np.diff(indices) > 1)[0] + 1
        segments = np.split(indices, breaks)
        
        for segment_indices in segments:
            if len(segment_indices) > W:
                # Mark these timesteps as contaminated
                # We need to map back to the dataframe indices
                segment_mask = np.zeros(len(group), dtype=bool)
                segment_mask[segment_indices] = True
                # Update the global dataframe
                mask_indices = group.index[segment_mask]
                df.loc[mask_indices, 'is_contaminated'] = True

    return df

def main():
    """Main entry point to generate and save the contaminated mask."""
    print("Loading divergence data...")
    df = load_divergence_data()
    
    print("Generating contaminated mask...")
    df_masked = generate_is_contaminated_mask(df)
    
    output_path = get_project_root() / DataConfig.PROCESSED_DIR / "trajectories_divergence_masked.csv"
    print(f"Saving to {output_path}...")
    save_csv(df_masked, str(output_path))
    
    print("Contaminated mask generation complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
