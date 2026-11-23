import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

from code.config import get_project_root
from code.utils.io_utils import load_csv, save_csv

def identify_contaminated_segments(df: pd.DataFrame, window_size: int = 20) -> List[Tuple[int, int]]:
    """
    Identify contiguous segments of timesteps where the ground-truth label is 'hacked'
    AND the segment duration exceeds the sliding window size.

    Logic:
    1. Flag a timestep as an 'event' if G(t) > 3 * MAD(G).
    2. Identify contiguous segments of 'hacked' ground-truth labels.
    3. Filter segments where duration > window_size.
    4. Return list of (start_idx, end_idx) tuples.

    Args:
        df: DataFrame containing 'hacked_label' (bool) and 'G(t)' (float).
        window_size: The sliding window size (default 20).

    Returns:
        List of (start, end) tuples representing contaminated segments.
    """
    if 'hacked_label' not in df.columns or 'G(t)' not in df.columns:
        raise ValueError("DataFrame must contain 'hacked_label' and 'G(t)' columns.")

    # Step 1: Identify 'hacking events' based on G(t) > 3 * MAD(G)
    # This is used to confirm the nature of the segment, but the mask generation
    # is primarily driven by the duration of the 'hacked' label segment.
    # The spec says: "To identify 'hacking events' for duration calculation, flag a timestep... if G(t) > 3 * MAD(G)"
    # This implies we might need to ensure the segment consists of actual events,
    # or simply use this to define what counts as a valid 'hacked' segment if labels are noisy.
    # However, T031 produces 'hacked_label'. The spec says: "Identify contiguous segments... where ground-truth label is 'hacked'".
    # The G(t) condition seems to be a secondary validation or definition of 'event' for the segment.
    # Interpretation: A segment is contaminated if it is a contiguous block of 'hacked' labels
    # AND its length > window_size. The G(t) > 3*MAD is likely a check to ensure these are indeed
    # significant deviations, but the primary filter is the label duration.
    # Let's strictly follow: "Identify contiguous segments... where ground-truth label is 'hacked' AND segment duration > window_size".
    # The G(t) condition is mentioned as "To identify 'hacking events' for duration calculation".
    # This might mean we only count a 'hacked' label as part of the duration if G(t) > 3*MAD?
    # Or it means we use G(t) to detect events if labels are missing?
    # Given T031 produces labels, we assume labels are the ground truth.
    # Re-reading: "flag a timestep as an 'event' if G(t) > 3 * MAD(G)... Identify contiguous segments... where ground-truth label is 'hacked'".
    # This phrasing is slightly ambiguous. It likely means:
    # 1. Calculate MAD of G(t).
    # 2. A 'hacking event' is defined as a timestep where G(t) > 3*MAD.
    # 3. A 'contaminated segment' is a contiguous run of timesteps that are BOTH 'hacked' (label) AND 'events' (G(t) condition)?
    # OR: The duration calculation is only valid if the segment consists of events?
    # Let's assume the strictest interpretation that ensures robustness:
    # We look for contiguous runs of 'hacked' labels. We verify that these runs contain significant G(t) deviations.
    # Actually, the most logical flow for "contamination exclusion" is:
    # If a long period is labeled 'hacked', it contaminates the baseline.
    # The G(t) > 3*MAD condition is likely a filter to ensure we don't flag noise as a long segment.
    # Let's implement:
    # 1. Compute MAD of G(t).
    # 2. Create a boolean mask `is_event` where G(t) > 3 * MAD.
    # 3. Combine with `hacked_label`: `is_contaminated_candidate = hacked_label & is_event`.
    # 4. Find contiguous segments of `is_contaminated_candidate`.
    # 5. Filter segments where length > window_size.

    g_values = df['G(t)'].values
    mad = np.median(np.abs(g_values - np.median(g_values)))
    if mad == 0:
        # If MAD is 0, no deviation. No events.
        return []

    threshold = 3.0 * mad
    is_event = g_values > threshold
    is_hacked = df['hacked_label'].values

    # A timestep is a candidate for a contaminated segment if it is both hacked and an event
    candidate_mask = is_hacked & is_event

    # Find contiguous segments in candidate_mask
    segments = []
    if len(candidate_mask) == 0:
        return []

    in_segment = False
    start_idx = -1

    for i, val in enumerate(candidate_mask):
        if val and not in_segment:
            in_segment = True
            start_idx = i
        elif not val and in_segment:
            in_segment = False
            end_idx = i - 1
            duration = end_idx - start_idx + 1
            if duration > window_size:
                segments.append((start_idx, end_idx))

    if in_segment:
        end_idx = len(candidate_mask) - 1
        duration = end_idx - start_idx + 1
        if duration > window_size:
            segments.append((start_idx, end_idx))

    return segments

def generate_is_contaminated_mask(df: pd.DataFrame, segments: List[Tuple[int, int]]) -> pd.Series:
    """
    Generate a boolean Series 'is_contaminated' based on the identified segments.

    Args:
        df: Original DataFrame.
        segments: List of (start, end) tuples.

    Returns:
        pd.Series of booleans, True for timesteps in contaminated segments.
    """
    mask = pd.Series(False, index=df.index)
    for start, end in segments:
        mask.iloc[start:end+1] = True
    return mask

def main():
    """
    Main entry point to identify contaminated windows and append the mask to the data.
    Reads data/processed/trajectories_divergence.csv (which should have hacked_label from T031).
    Outputs data/processed/trajectories_divergence_masked.csv with is_contaminated column.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "trajectories_divergence_masked.csv"

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Ensure T031 (ground truth labels) has been run successfully.")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = load_csv(str(input_path))

    if 'hacked_label' not in df.columns:
        print("Error: 'hacked_label' column not found in input data.")
        print("Ensure T031 has been run to generate ground truth labels.")
        sys.exit(1)

    if 'G(t)' not in df.columns:
        print("Error: 'G(t)' column not found in input data.")
        sys.exit(1)

    print("Identifying contaminated segments...")
    # W=20 as per spec
    contaminated_segments = identify_contaminated_segments(df, window_size=20)
    print(f"Found {len(contaminated_segments)} contaminated segments.")

    print("Generating is_contaminated mask...")
    is_contaminated_mask = generate_is_contaminated_mask(df, contaminated_segments)
    df['is_contaminated'] = is_contaminated_mask

    print(f"Saving output to {output_path}...")
    save_csv(df, str(output_path))

    print(f"Task complete. Output saved to {output_path}")
    print(f"Total contaminated timesteps: {df['is_contaminated'].sum()}")

if __name__ == "__main__":
    main()
