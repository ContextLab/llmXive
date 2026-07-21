"""
Module to create a stratified sample for human annotation.
Selects 50 tasks from the filtered dataset, stratified by constraint_count.
"""
import argparse
import os
import sys
import random
from pathlib import Path
import pandas as pd
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, get_paths, get_dataset_config

def load_filtered_tasks(input_path: Path) -> pd.DataFrame:
    """Load filtered tasks from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def bin_constraint(count: int) -> str:
    """Bin constraint count into categories: 5, 6, 7, 8+."""
    if count < 5:
        return "0-4"  # Should not happen in filtered data
    elif count == 5:
        return "5"
    elif count == 6:
        return "6"
    elif count == 7:
        return "7"
    else:
        return "8+"

def select_random_sample_stratified(df: pd.DataFrame, sample_size: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    Select a stratified random sample of tasks.
    Stratifies by constraint_count bins: 5, 6, 7, 8+.
    """
    random.seed(seed)
    
    # Create bin column
    df['constraint_bin'] = df['constraint_count'].apply(bin_constraint)
    
    # Calculate sample size per bin (proportional)
    bin_counts = df['constraint_bin'].value_counts()
    total = len(df)
    
    # Ensure we don't exceed available data in any bin
    sample_per_bin = {}
    remaining = sample_size
    
    # Sort bins to ensure consistent sampling order
    bins = sorted(bin_counts.index)
    
    # Calculate proportional allocation
    for bin_name in bins:
        bin_size = bin_counts[bin_name]
        proportion = bin_size / total
        allocated = int(round(proportion * sample_size))
        # Ensure we don't allocate more than available
        allocated = min(allocated, bin_size)
        sample_per_bin[bin_name] = allocated
        remaining -= allocated
    
    # Distribute remaining samples
    for bin_name in bins:
        if remaining <= 0:
            break
        if sample_per_bin[bin_name] < bin_counts[bin_name]:
            sample_per_bin[bin_name] += 1
            remaining -= 1
    
    # Sample from each bin
    sampled_dfs = []
    for bin_name, count in sample_per_bin.items():
        bin_df = df[df['constraint_bin'] == bin_name]
        if count > 0 and len(bin_df) > 0:
            sampled_dfs.append(bin_df.sample(n=min(count, len(bin_df)), random_state=seed))
    
    if not sampled_dfs:
        return pd.DataFrame()
    
    result = pd.concat(sampled_dfs, ignore_index=True)
    return result

def save_annotation_sample(sample_df: pd.DataFrame, output_path: Path):
    """Save annotation sample to CSV with required columns."""
    # Select required columns
    required_cols = ['task_id', 'raw_prompt', 'constraint_list']
    
    # Handle missing columns gracefully
    available_cols = [col for col in required_cols if col in sample_df.columns]
    
    if 'task_id' not in available_cols:
        raise ValueError("Sample DataFrame must contain 'task_id' column.")
    
    # Add constraint_list if not present (derive from progressive_constraints)
    if 'constraint_list' not in available_cols and 'progressive_constraints' in sample_df.columns:
        def parse_constraints(constraints_field):
            if isinstance(constraints_field, str):
                try:
                    return json.loads(constraints_field)
                except:
                    return []
            return constraints_field if isinstance(constraints_field, list) else []
        
        sample_df['constraint_list'] = sample_df['progressive_constraints'].apply(parse_constraints)
        available_cols.append('constraint_list')
    
    if 'raw_prompt' not in available_cols and 'prompt' in sample_df.columns:
        sample_df['raw_prompt'] = sample_df['prompt']
        available_cols.append('raw_prompt')
    
    # Select and save
    output_df = sample_df[available_cols]
    output_df.to_csv(output_path, index=False)
    print(f"Saved annotation sample with {len(output_df)} tasks to {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create stratified annotation sample")
    parser.add_argument('--input', type=str, required=True, help="Input filtered tasks CSV")
    parser.add_argument('--output', type=str, help="Output annotation sample CSV")
    parser.add_argument('--sample-size', type=int, default=50, help="Number of tasks to sample")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    paths = get_paths()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else paths.DATA_PROCESSED / "annotation_sample.csv"
    
    try:
        print(f"Loading tasks from {input_path}...")
        df = load_filtered_tasks(input_path)
        
        print(f"Selecting stratified sample of {args.sample_size} tasks...")
        sample = select_random_sample_stratified(df, args.sample_size, args.seed)
        
        print(f"Saving annotation sample to {output_path}...")
        save_annotation_sample(sample, output_path)
        
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()