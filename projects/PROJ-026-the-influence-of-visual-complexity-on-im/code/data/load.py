import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional

from ..config import get_project_root, get_data_path

def load_response_logs(logs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw response logs from the specified path.
    
    Args:
        logs_path: Path to the raw logs directory or specific file.
        
    Returns:
        DataFrame containing the loaded response logs.
    """
    if logs_path is None:
        data_path = get_data_path()
        logs_path = data_path / "raw" / "responses"
    
    if logs_path.is_file():
        files = [logs_path]
    elif logs_path.is_dir():
        files = list(logs_path.glob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found in {logs_path}")
    else:
        raise FileNotFoundError(f"Path not found: {logs_path}")
    
    dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not read {file}: {e}", file=sys.stderr)
    
    if not dfs:
        raise ValueError("No valid data files found to load.")
    
    return pd.concat(dfs, ignore_index=True)

def generate_synthetic_response_logs(
    output_path: Path,
    n_participants: int = 100,
    n_trials: int = 40,
    seed: int = 42
) -> None:
    """
    Generate synthetic response logs for CI/testing purposes.
    
    Args:
        output_path: Path to save the synthetic logs.
        n_participants: Number of synthetic participants.
        n_trials: Number of trials per participant.
        seed: Random seed for reproducibility.
    """
    import numpy as np
    np.random.seed(seed)
    
    records = []
    for p_id in range(1, n_participants + 1):
        for t_id in range(1, n_trials + 1):
            # Simulate reaction times (normal distribution, truncated)
            rt = np.random.normal(500, 100)
            rt = np.clip(rt, 300, 2000)
            
            # Simulate correctness (90% correct)
            is_correct = 1 if np.random.random() > 0.1 else 0
            
            # Simulate session (1 or 2)
            session_id = 1 if t_id <= n_trials // 2 else 2
            
            records.append({
                "participant_id": f"P{p_id:03d}",
                "session_id": session_id,
                "trial_id": t_id,
                "reaction_time": rt,
                "is_correct": is_correct,
                "timestamp": "2023-01-01T12:00:00"
            })
    
    df = pd.DataFrame(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic logs at {output_path}")

def main() -> int:
    """Main entry point for data loading script."""
    parser = argparse.ArgumentParser(description="Load or generate response logs.")
    parser.add_argument("--null-effect", action="store_true", help="Generate synthetic data for CI.")
    parser.add_argument("--output", type=str, help="Output path for synthetic data.")
    parser.add_argument("--input", type=str, help="Input path for real data.")
    
    args = parser.parse_args()
    
    if args.null_effect:
        if not args.output:
            args.output = str(get_data_path() / "raw" / "responses" / "synthetic_logs.csv")
        generate_synthetic_response_logs(Path(args.output))
    else:
        if not args.input:
            args.input = str(get_data_path() / "raw" / "responses")
        try:
            df = load_response_logs(Path(args.input))
            print(f"Loaded {len(df)} rows from {args.input}")
        except Exception as e:
            print(f"Error loading data: {e}", file=sys.stderr)
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
