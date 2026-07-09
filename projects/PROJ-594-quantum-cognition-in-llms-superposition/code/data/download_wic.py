"""
Download the WiC (Words in Context) dataset from SuperGLUE.

This script fetches the real WiC dataset using the Hugging Face `datasets` library
and saves it to `data/raw/wic_dataset.parquet` for downstream processing.

Requirements:
    datasets>=2.14.0

Output:
    data/raw/wic_dataset.parquet: A parquet file containing the full WiC dataset
                                  with train, validation, and test splits.
"""
import os
import sys

# Ensure the code directory is in the path for relative imports if run as a module
# but primarily designed to be run as a script from the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datasets import load_dataset
import pandas as pd

def download_wic(output_path: str = "data/raw/wic_dataset.parquet") -> None:
    """
    Fetches the WiC dataset from SuperGLUE and saves it as a Parquet file.

    Args:
        output_path: Relative path from project root where the file will be saved.
    """
    print(f"Fetching WiC dataset from SuperGLUE...")
    
    try:
        # Load the WiC dataset from the SuperGLUE collection
        # This fetches the real data from the Hugging Face Hub
        dataset = load_dataset("super_glue", "wic")
    except Exception as e:
        print(f"ERROR: Failed to load dataset from 'super_glue' 'wic'.")
        print(f"Reason: {e}")
        print("Ensure the 'datasets' package is installed and you have internet access.")
        raise SystemExit(1)

    if not dataset:
        raise RuntimeError("Dataset loaded but appears empty.")

    print(f"Dataset loaded successfully. Splits: {list(dataset.keys())}")

    # Ensure the output directory exists
    full_output_path = os.path.join(project_root, output_path)
    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)

    # Convert to a single DataFrame for easier downstream processing if needed,
    # or save per split. The task implies a single artifact for the dataset.
    # We will save the entire dataset object to parquet (HuggingFace supports this)
    # or flatten it into a single table if splits are not needed separately in the file.
    # Given the requirement for a "real file", saving the concatenated data or 
    # a dict of splits is valid. We'll save a single parquet with a 'split' column.
    
    df_list = []
    for split_name, split_data in dataset.items():
        df = split_data.to_pandas()
        df['split'] = split_name
        df_list.append(df)
    
    combined_df = pd.concat(df_list, ignore_index=True)
    
    print(f"Saving combined dataset to {full_output_path}...")
    combined_df.to_parquet(full_output_path, index=False)

    print(f"Success! Dataset saved to {full_output_path}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Columns: {list(combined_df.columns)}")

if __name__ == "__main__":
    # Default output path as per project conventions
    output_file = "data/raw/wic_dataset.parquet"
    download_wic(output_file)
