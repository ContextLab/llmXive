import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
from code.config import get_project_root
from code.detector import apply_hacking_labels

def load_divergence_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the aggregated divergence data from the processed directory.
    
    Args:
        input_path: Optional path to the input CSV. Defaults to the project's
                    processed trajectories_divergence.csv.
                    
    Returns:
        A pandas DataFrame containing the divergence metrics.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if input_path is None:
        project_root = get_project_root()
        input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T016 (aggregation) has been completed successfully."
        )
    
    df = pd.read_csv(input_path)
    
    required_columns = ['seed_id', 'bias_type', 'timestep', 'G_t', 'dG_t']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Input file missing required columns: {missing_cols}. "
            "Expected columns from T016/T021 output."
        )
        
    return df

def apply_hacking_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append the 'hacked_label' boolean column to the dataframe based on
    the detector logic defined in code/detector.py.
    
    This function delegates the actual labeling logic to apply_hacking_labels
    from the detector module to ensure consistency with the detection thresholds.
    
    Args:
        df: The dataframe containing divergence metrics (G_t, dG_t, etc.).
        
    Returns:
        The dataframe with an additional 'hacked_label' column (True/False).
    """
    # Delegate to the detector module's labeling logic to ensure
    # the same thresholds and baseline exclusion logic (from T025) are applied.
    # The detector module expects the dataframe to have the necessary columns.
    labeled_df = apply_hacking_labels(df)
    
    # Ensure the column is boolean as per schema requirements
    labeled_df['hacked_label'] = labeled_df['hacked_label'].astype(bool)
    
    return labeled_df

def main():
    """
    Main entry point for T023: Generate labeled trajectories.
    
    1. Loads data from data/processed/trajectories_divergence.csv.
    2. Applies hacking labels using the detector logic.
    3. Saves the result to data/processed/trajectories_labeled.csv.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "trajectories_labeled.csv"
    
    print(f"Starting T023: Generating labeled trajectories...")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    
    try:
        # Load the divergence data (T016 output)
        df = load_divergence_data(str(input_path))
        print(f"Loaded {len(df)} rows from {input_path.name}")
        
        # Apply hacking labels (T022 logic)
        labeled_df = apply_hacking_labels(df)
        print(f"Applied hacking labels. Count of hacked timesteps: {labeled_df['hacked_label'].sum()}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the result
        labeled_df.to_csv(output_path, index=False)
        print(f"Successfully saved labeled trajectories to {output_path}")
        
        # Verify output schema
        if 'hacked_label' not in labeled_df.columns:
            raise RuntimeError("Schema validation failed: 'hacked_label' column missing in output.")
            
        if not labeled_df['hacked_label'].dtype == bool:
            print(f"Warning: 'hacked_label' dtype is {labeled_df['hacked_label'].dtype}, coercing to bool.")
            labeled_df['hacked_label'] = labeled_df['hacked_label'].astype(bool)
            
        print("T023 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(2)
    except ValueError as e:
        print(f"ERROR: Invalid data format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected failure - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()