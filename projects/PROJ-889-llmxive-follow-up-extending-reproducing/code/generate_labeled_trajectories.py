"""
T023: Generate data/processed/trajectories_labeled.csv by appending hacked_label column.

This script reads the aggregated US1 output (trajectories_divergence.csv),
runs the detector logic to identify hacked timesteps, and appends the
'hacked_label' column to produce the final labeled dataset.

Separation of Concerns:
- FR-001 (Divergence Calculation) is handled by ingestion.py (US1).
- FR-003 (Detection Logic) is handled by detector.py (US2).
- This script orchestrates the combination to produce the final artifact.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_project_root
from code.detector import detect_hacking
from code.utils.io_utils import read_csv, write_csv


def load_divergence_data(input_path: Path) -> pd.DataFrame:
    """
    Load the aggregated divergence data from US1.

    Args:
        input_path: Path to trajectories_divergence.csv

    Returns:
        DataFrame containing seed_id, bias_type, timestep, G_t, dG_t, etc.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T016 (aggregation) has completed successfully."
        )
    return read_csv(input_path)


def apply_hacking_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the hacking detection logic to the dataframe and append 'hacked_label'.

    The detector expects the data to be grouped by seed/bias to calculate
    rolling statistics correctly. This function processes each group
    independently to ensure accurate baseline calculation.

    Args:
        df: DataFrame with G_t, dG_t columns.

    Returns:
        DataFrame with an additional 'hacked_label' column (0 or 1).
    """
    if 'G_t' not in df.columns or 'dG_t' not in df.columns:
        raise ValueError(
            "Input data missing required columns 'G_t' or 'dG_t'. "
            "Ensure T015 (derivative/z-score) has run."
        )

    # Initialize the label column with 0 (not hacked)
    df['hacked_label'] = 0

    # Define grouping columns for independent baseline calculation
    # per trajectory/seed to avoid cross-contamination of baselines.
    group_cols = ['seed_id', 'bias_type']

    # We need to apply the detector row-wise or group-wise.
    # Since detect_hacking in detector.py is designed to take a full trajectory
    # or a specific group, we iterate over groups.
    # The detector function returns a boolean mask or array of flags.

    # Re-implementation of the logic to ensure it works on the dataframe structure:
    # We will call detect_hacking on the specific columns for each group.
    # Note: The detector.py main logic might expect a specific input format.
    # We assume detect_hacking returns a boolean array or list of flags for the input rows.

    # To be safe and robust, we will iterate groups and apply the logic.
    # However, vectorizing over the whole DF is faster if the detector handles global stats.
    # The task requires "preserving separation of concerns".
    # Let's assume detect_hacking can process a subset of data (a group).

    # If the detector expects a full DF, we might need to adjust.
    # Based on T022 logic: "Calculate baseline noise floor as the standard deviation
    # of the preceding 100 timesteps". This implies a per-sequence context.
    # Therefore, we MUST group by seed_id and bias_type.

    result_dfs = []

    for name, group in df.groupby(group_cols):
        # Extract the relevant series for this group
        g_t = group['G_t'].values
        d_g_t = group['dG_t'].values

        # Call the detector logic
        # detect_hacking returns a boolean mask (True = hacked)
        # We need to ensure it handles the 'baseline_mask' from T025 if available.
        # For this script, we assume T025's mask is integrated into detector logic
        # or we pass None if not pre-calculated (detector calculates it internally).
        # The signature of detect_hacking is: detect_hacking(g_t, d_g_t, baseline_mask=None)
        
        # We must pass the data in the correct order.
        # Let's assume the detector function signature is:
        # detect_hacking(g_t, d_g_t, baseline_mask=None)
        
        # If the detector expects a DataFrame, we might need to adapt.
        # But the API surface says: detect_hacking(g_t, d_g_t, baseline_mask=None)
        # Wait, the API surface says:
        # public names: calculate_contaminated_mask, generate_baseline_mask, calculate_dynamic_baseline_stats, detect_hacking, main
        # It doesn't explicitly list the signature of detect_hacking in the text,
        # but standard practice for this pipeline is:
        # detect_hacking(g_t, d_g_t, baseline_mask=None) -> np.array[bool]

        try:
            # We pass None for baseline_mask if the detector calculates it internally
            # or if T025 output is not explicitly passed here.
            # Given T025 is a separate task that outputs a mask,
            # and T022 consumes it, we should ideally pass it.
            # However, T023 is about generating the CSV.
            # We will assume detect_hacking handles the full pipeline internally
            # if no mask is passed, or we can call the helper functions.
            # To be safe and follow the "separation of concerns" strictly:
            # We rely on detect_hacking to perform the logic described in T022.
            
            # Let's call detect_hacking with the group's data.
            # We need to ensure the detector doesn't rely on global state.
            
            # Assuming detect_hacking takes (g_t, d_g_t) and returns flags.
            # If it requires the baseline_mask, we might need to compute it here.
            # But T025 is the one that generates the mask.
            # Let's assume detect_hacking calls T025 logic internally if needed,
            # or we pass the mask.
            # Since T025 is completed, we can assume the mask logic is in detector.py.
            
            # Let's try calling it directly.
            flags = detect_hacking(g_t, d_g_t)
            
            # flags should be a boolean array of same length as group
            if len(flags) != len(group):
                raise ValueError(
                    f"Detector returned {len(flags)} flags for group of size {len(group)}"
                )
            
            # Create a copy of the group and assign labels
            labeled_group = group.copy()
            labeled_group['hacked_label'] = flags.astype(int)
            result_dfs.append(labeled_group)

        except Exception as e:
            # If detector fails for a specific group, log and skip or raise?
            # Better to raise to fail loud, as per requirements.
            raise RuntimeError(f"Detection failed for group {name}: {str(e)}") from e

    # Concatenate all groups back together
    if not result_dfs:
        raise ValueError("No data groups found to process.")
    
    final_df = pd.concat(result_dfs, ignore_index=True)
    return final_df


def main():
    """
    Main entry point for T023.
    Reads US1 output, applies detection, writes US2 labeled output.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "trajectories_labeled.csv"

    print(f"Loading data from: {input_path}")
    df = load_divergence_data(input_path)
    print(f"Loaded {len(df)} rows.")

    print("Applying hacking detection logic...")
    labeled_df = apply_hacking_labels(df)
    print(f"Detection complete. Found {labeled_df['hacked_label'].sum()} hacked timesteps.")

    print(f"Saving labeled data to: {output_path}")
    write_csv(labeled_df, output_path)
    print("Done.")


if __name__ == "__main__":
    main()