import json
import os
import glob
import pandas as pd
from pathlib import Path
import sys

from utils import MAX_EPOCHS, CONVERGENCE_THRESHOLD

def load_training_run(file_path: str) -> dict:
    """Load a single training run JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_scalars(run_data: dict) -> dict:
    """
    Extract scalar fields from a training run dictionary.
    
    Expected input structure (from T026/T027):
    {
        "id": str,
        "loss_type": str,
        "beta": float,
        "node_count": int,
        "steps_to_convergence": int,
        "final_accuracy": float,
        "max_loss": float,
        "convergence_status": str,
        "trajectory": [...]  # List of {loss, accuracy}
    }
    
    Returns a dict with only scalar fields.
    """
    return {
        "run_id": run_data.get("id"),
        "loss_type": run_data.get("loss_type"),
        "beta": run_data.get("beta"),
        "node_count": run_data.get("node_count"),
        "steps_to_convergence": run_data.get("steps_to_convergence"),
        "final_accuracy": run_data.get("final_accuracy"),
        "max_loss": run_data.get("max_loss"),
        "convergence_status": run_data.get("convergence_status")
    }

def verify_extraction(original_data: dict, extracted: dict) -> bool:
    """
    Verify that extracted scalar fields match values in the original data.
    This ensures Single Source of Truth integrity.
    """
    checks = [
        extracted["run_id"] == original_data.get("id"),
        extracted["loss_type"] == original_data.get("loss_type"),
        extracted["beta"] == original_data.get("beta"),
        extracted["node_count"] == original_data.get("node_count"),
        extracted["steps_to_convergence"] == original_data.get("steps_to_convergence"),
        extracted["final_accuracy"] == original_data.get("final_accuracy"),
        extracted["max_loss"] == original_data.get("max_loss"),
        extracted["convergence_status"] == original_data.get("convergence_status")
    ]
    return all(checks)

def aggregate_training_runs(input_dir: str, output_path: str) -> pd.DataFrame:
    """
    Aggregate all training run JSON files into a single DataFrame.
    
    Args:
        input_dir: Path to directory containing training_run_*.json files
        output_path: Path where the CSV will be saved
        
    Returns:
        DataFrame containing scalar fields from all runs
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
    # Find all matching files
    pattern = str(input_path / "training_run_*.json")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"No training run files found matching pattern: {pattern}")
        
    all_scalars = []
    verification_errors = []
    
    for file_path in files:
        try:
            run_data = load_training_run(file_path)
            scalars = extract_scalars(run_data)
            
            # Verify extraction integrity
            if not verify_extraction(run_data, scalars):
                verification_errors.append({
                    "file": file_path,
                    "error": "Scalar extraction mismatch"
                })
                
            all_scalars.append(scalars)
            
        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}", file=sys.stderr)
            continue
    
    if not all_scalars:
        raise RuntimeError("No valid training runs could be aggregated")
        
    if verification_errors:
        print(f"Warning: {len(verification_errors)} files had extraction verification errors", 
              file=sys.stderr)
        
    df = pd.DataFrame(all_scalars)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Aggregated {len(df)} training runs to {output_path}")
    
    return df

def main():
    """Main entry point for data aggregation."""
    # Define paths based on project structure
    input_dir = "data/processed/trajectories"
    output_path = "data/processed/convergence_logs.csv"
    
    try:
        df = aggregate_training_runs(input_dir, output_path)
        
        # Print summary statistics
        print(f"\nSummary:")
        print(f"  Total runs: {len(df)}")
        print(f"  Loss types: {df['loss_type'].unique().tolist()}")
        print(f"  Beta levels: {sorted(df['beta'].unique().tolist())}")
        print(f"  Converged: {len(df[df['convergence_status'] == 'converged'])}")
        print(f"  Censored: {len(df[df['convergence_status'] == 'censored'])}")
        
        return df
        
    except Exception as e:
        print(f"Error during aggregation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
