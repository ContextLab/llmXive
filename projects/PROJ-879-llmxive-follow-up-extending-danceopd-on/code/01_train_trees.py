"""
Data splitting logic for User Story 2: Train and Evaluate Static Decision Trees.

Consumes `data/processed/teacher_routing_dataset.parquet` and produces
`data/processed/train_split.parquet` and `data/processed/test_split.parquet`.
"""
import argparse
import sys
import json
import hashlib
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
from sklearn.model_selection import train_test_split

# Import from project utils
from utils.config import get_config, get_path
from utils.check_weights import calculate_sha256
from utils.vulture_runner import main as vulture_main


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def load_dataset() -> pd.DataFrame:
    """
    Load the teacher routing dataset from the processed directory.
    
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the dataset is empty or missing required columns.
    """
    config = get_config()
    input_path = get_path("TEACHER_ROUTING_DATASET_PATH")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(
            f"Input dataset not found at {input_path}. "
            "Please ensure T014 (data extraction) has been completed."
        )
    
    df = pd.read_parquet(input_path)
    
    if df.empty:
        raise ValueError(f"Dataset at {input_path} is empty.")
    
    required_columns = ["prompt_embedding", "noise_level", "routing_label", "velocity_vector"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset missing required columns: {missing_cols}. "
            f"Found columns: {df.columns.tolist()}"
        )
    
    print(f"Loaded dataset with {len(df)} rows from {input_path}")
    return df


def split_data(
    df: pd.DataFrame, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into training and testing sets.
    
    Args:
        df: The input dataframe.
        test_size: Proportion of the dataset to include in the test split.
        random_state: Seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    # We stratify on the target variable (routing_label) to ensure class balance
    if "routing_label" not in df.columns:
        # Fallback if label is missing, though load_data should have caught this
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
    else:
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state,
            stratify=df["routing_label"]
        )
    
    print(f"Split data: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df


def save_splits(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame
) -> Tuple[Path, Path]:
    """
    Save the train and test splits to parquet files.
    
    Args:
        train_df: Training dataframe.
        test_df: Test dataframe.
        
    Returns:
        Tuple of (train_path, test_path).
    """
    output_dir = get_path("PROCESSED_DATA_DIR")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    train_path = Path(output_dir) / "train_split.parquet"
    test_path = Path(output_dir) / "test_split.parquet"
    
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    print(f"Saved train split to {train_path}")
    print(f"Saved test split to {test_path}")
    
    return train_path, test_path


def validate_splits(train_path: Path, test_path: Path) -> Dict[str, Any]:
    """
    Validate the split files and generate a metadata report.
    
    Args:
        train_path: Path to train split.
        test_path: Path to test split.
        
    Returns:
        Dictionary containing validation metadata.
    """
    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_df)
    
    # Check for label overlap issues (optional sanity check)
    train_labels = set(train_df["routing_label"].unique())
    test_labels = set(test_df["routing_label"].unique())
    
    report = {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "train_labels": list(train_labels),
        "test_labels": list(test_labels),
        "train_sha256": calculate_sha256(str(train_path)),
        "test_sha256": calculate_sha256(str(test_path)),
        "status": "success"
    }
    
    return report


def save_validation_report(report: Dict[str, Any], output_dir: Path) -> Path:
    """
    Save the validation report to a JSON file.
    
    Args:
        report: The validation report dictionary.
        output_dir: Directory to save the report.
        
    Returns:
        Path to the saved report.
    """
    report_path = output_dir / "split_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Saved validation report to {report_path}")
    return report_path


def run_data_splitting() -> Dict[str, Any]:
    """
    Main orchestration function for data splitting.
    
    Returns:
        Dictionary containing the result of the operation.
    """
    try:
        # 1. Load
        df = load_dataset()
        
        # 2. Split
        train_df, test_df = split_data(df)
        
        # 3. Save
        train_path, test_path = save_splits(train_df, test_df)
        
        # 4. Validate
        output_dir = Path(train_path).parent
        report = validate_splits(train_path, test_path)
        report_path = save_validation_report(report, output_dir)
        
        return {
            "status": "completed",
            "train_path": str(train_path),
            "test_path": str(test_path),
            "report_path": str(report_path)
        }
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        print(f"Unexpected error during splitting: {e}", file=sys.stderr)
        return {"status": "failed", "error": str(e)}


def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Split teacher routing dataset.")
    parser.add_argument(
        "--test-size", 
        type=float, 
        default=0.2, 
        help="Proportion of data for testing (default: 0.2)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Random seed for splitting (default: 42)"
    )
    
    # We allow overriding via args, but default to config if not provided
    args = parser.parse_args()
    
    result = run_data_splitting()
    
    if result["status"] == "completed":
        print("Data splitting completed successfully.")
        sys.exit(0)
    else:
        print(f"Data splitting failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()