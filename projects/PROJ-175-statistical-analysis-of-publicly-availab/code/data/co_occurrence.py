"""
Task T015: Co-occurrence Matrix Construction

Builds the global co-occurrence matrix C from processed ingredient pairs.
Applies log-transform with epsilon smoothing derived from T049.
Outputs data/processed/co_occurrence_matrix.parquet.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
import numpy as np
from tqdm import tqdm

# Ensure project root is in path for imports if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def load_epsilon_config():
    """Load epsilon value from T049 configuration."""
    config_path = PROJECT_ROOT / "data" / "zero_handling_log.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Zero handling log not found at {config_path}. "
            "Run T049 to generate epsilon configuration."
        )
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    if "epsilon" not in config:
        raise ValueError("Epsilon value not found in zero_handling_log.json")
    
    return config["epsilon"]

def load_ingredient_pairs():
    """
    Load the normalized ingredient pairs from T014/T013 processing.
    Expects data/processed/ingredient_pairs.parquet or .csv.
    """
    parquet_path = PROJECT_ROOT / "data" / "processed" / "ingredient_pairs.parquet"
    csv_path = PROJECT_ROOT / "data" / "processed" / "ingredient_pairs.csv"
    
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            f"Ingredient pairs file not found. "
            f"Expected {parquet_path} or {csv_path}. "
            "Run T014 preprocessing first."
        )
    
    # Validate required columns
    required_cols = ["ingredient_a", "ingredient_b", "co_occurrence_count"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in ingredient pairs: {missing_cols}")
    
    return df

def build_cooccurrence_matrix(df, epsilon):
    """
    Build the global co-occurrence matrix C and apply log-transform.
    
    C_log = log(C + epsilon)
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ingredient_a, ingredient_b, co_occurrence_count
    epsilon : float
        Smoothing parameter for log transform
    
    Returns
    -------
    pd.DataFrame
        Matrix in long format: ingredient_a, ingredient_b, log_co_occurrence
    """
    # Create unique ingredient list
    all_ingredients = pd.concat([df["ingredient_a"], df["ingredient_b"]]).unique()
    ingredient_to_idx = {ing: idx for idx, ing in enumerate(all_ingredients)}
    n_ingredients = len(all_ingredients)
    
    print(f"Building co-occurrence matrix for {n_ingredients} unique ingredients...")
    
    # Initialize sparse matrix using dictionary for memory efficiency
    # We'll store only non-zero entries
    cooccurrence_dict = {}
    
    # Process in chunks to monitor memory
    chunk_size = 100000
    total_rows = len(df)
    
    for start_idx in tqdm(range(0, total_rows, chunk_size), desc="Processing pairs"):
        chunk = df.iloc[start_idx:start_idx + chunk_size]
        
        for _, row in chunk.iterrows():
            ing_a = row["ingredient_a"]
            ing_b = row["ingredient_b"]
            count = row["co_occurrence_count"]
            
            # Skip zero counts if any
            if count <= 0:
                continue
            
            # Store symmetric pairs (only one direction in dict, expand later)
            pair_key = tuple(sorted([ing_a, ing_b]))
            if pair_key not in cooccurrence_dict:
                cooccurrence_dict[pair_key] = count
            else:
                # Sum counts if same pair appears multiple times
                cooccurrence_dict[pair_key] += count
    
    # Convert to DataFrame
    rows = []
    for (ing_a, ing_b), count in cooccurrence_dict.items():
        rows.append({
            "ingredient_a": ing_a,
            "ingredient_b": ing_b,
            "raw_co_occurrence": count,
            "log_co_occurrence": np.log(count + epsilon)
        })
    
    result_df = pd.DataFrame(rows)
    
    # Log statistics
    print(f"Matrix built: {len(result_df)} unique ingredient pairs")
    print(f"Log transform applied with epsilon={epsilon}")
    print(f"Log co-occurrence range: [{result_df['log_co_occurrence'].min():.4f}, {result_df['log_co_occurrence'].max():.4f}]")
    
    return result_df

def save_output(df, output_path):
    """
    Save the co-occurrence matrix to parquet format.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with log_co_occurrence
    output_path : Path
        Path to save the parquet file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    
    print(f"Co-occurrence matrix saved to {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Log metadata
    metadata = {
        "output_file": str(output_path),
        "num_pairs": len(df),
        "columns": list(df.columns),
        "log_co_occurrence_stats": {
            "min": float(df["log_co_occurrence"].min()),
            "max": float(df["log_co_occurrence"].max()),
            "mean": float(df["log_co_occurrence"].mean()),
            "std": float(df["log_co_occurrence"].std())
        }
    }
    
    metadata_path = output_path.parent / "co_occurrence_matrix_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def main():
    """Main execution function for T015."""
    print("=" * 60)
    print("Task T015: Building Co-occurrence Matrix with Log Transform")
    print("=" * 60)
    
    # Ensure processed directory exists
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Load epsilon configuration from T049
        print("\n[1/3] Loading epsilon configuration...")
        epsilon = load_epsilon_config()
        print(f"✓ Epsilon loaded: {epsilon}")
        
        # Step 2: Load ingredient pairs from preprocessing
        print("\n[2/3] Loading ingredient pairs...")
        df_pairs = load_ingredient_pairs()
        print(f"✓ Loaded {len(df_pairs)} ingredient pairs")
        
        # Step 3: Build co-occurrence matrix with log transform
        print("\n[3/3] Building co-occurrence matrix...")
        df_matrix = build_cooccurrence_matrix(df_pairs, epsilon)
        
        # Step 4: Save output
        output_path = processed_dir / "co_occurrence_matrix.parquet"
        metadata = save_output(df_matrix, output_path)
        
        print("\n" + "=" * 60)
        print("T015 COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Output: {output_path}")
        print(f"Pairs processed: {metadata['num_pairs']}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        print("Prerequisite tasks may not have completed successfully.")
        return 1
    except ValueError as e:
        print(f"\n✗ ERROR: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
