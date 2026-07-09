"""
Download the ESOL (Estimated Solubility) dataset from HuggingFace.

This script fetches the 'delaney-esol' dataset from the HuggingFace Hub,
validates the presence of the 'logS' column, and saves the raw data
to data/raw/esol_raw.csv.

Dependencies:
    pandas, requests (or huggingface_hub)
"""
import os
import sys
import pandas as pd

# Ensure we can import from the code directory if run from project root
# However, for this specific file, we rely on standard library and pandas.

def fetch_esol_dataset():
    """
    Fetches the ESOL dataset from HuggingFace datasets.
    
    Returns:
        pd.DataFrame: The raw ESOL dataset.
    
    Raises:
        RuntimeError: If the dataset cannot be fetched or 'logS' column is missing.
    """
    try:
        # We use the 'datasets' library for robust access to HuggingFace datasets
        # If not installed, we fall back to direct URL download if available,
        # but 'datasets' is the canonical way for MoleculeNet data on HF.
        from datasets import load_dataset
    except ImportError:
        print("Error: The 'datasets' library is required. "
              "Please run: pip install datasets", file=sys.stderr)
        sys.exit(1)

    print("Fetching ESOL dataset from HuggingFace...")
    try:
        # The ESOL dataset is available as 'delaney-esol' on HuggingFace
        dataset = load_dataset("delaney-esol", split="train")
    except Exception as e:
        print(f"Error fetching dataset: {e}", file=sys.stderr)
        sys.exit(1)

    # Convert to pandas DataFrame
    df = dataset.to_pandas()

    # Validate required columns
    required_columns = ['logS', 'smiles', 'measured logS']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        raise RuntimeError(f"Missing required columns in dataset: {missing_cols}")

    # Validate 'logS' column has numeric data and no NaNs in the target column
    if df['logS'].isna().any():
        print(f"Warning: {df['logS'].isna().sum()} rows have NaN in 'logS'. "
              "These will be dropped later in preprocessing, but we keep them here as raw.",
              file=sys.stderr)

    return df

def save_raw_csv(df, output_path):
    """
    Saves the DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): The dataset to save.
        output_path (str): The path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Raw ESOL dataset saved to {output_path}")
    print(f"Total rows: {len(df)}, Columns: {list(df.columns)}")

def main():
    """Main entry point for the download script."""
    output_path = "data/raw/esol_raw.csv"
    
    try:
        df = fetch_esol_dataset()
        save_raw_csv(df, output_path)
        print("Download and validation successful.")
    except RuntimeError as e:
        print(f"Failed to download or validate dataset: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
