import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml

def load_huggingface_data(dataset_name: str = "chemistry/dts-sn1") -> pd.DataFrame:
    """Load data from HuggingFace datasets."""
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_name, split="train")
        return ds.to_pandas()
    except Exception as e:
        raise RuntimeError(f"Failed to load HuggingFace dataset {dataset_name}: {e}")

def load_uci_data() -> pd.DataFrame:
    """Load SN subset from UCI as fallback."""
    try:
        from ucimlrepo import fetch_ucirepo
        # Placeholder for actual UCI dataset ID
        # This is a fallback mechanism
        raise NotImplementedError("UCI fallback not implemented yet")
    except Exception as e:
        raise RuntimeError(f"Failed to load UCI data: {e}")

def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw columns to standard schema."""
    mapped = df.copy()
    # Standardize column names
    if "smiles" in mapped.columns:
        mapped["smiles"] = mapped["smiles"]
    if "rate" in mapped.columns:
        mapped["rate_constant"] = mapped["rate"].abs()
    if "substrate" in mapped.columns:
        mapped["substrate_class"] = mapped["substrate"].str.lower()
    return mapped

def save_exclusion_report(exclusions: List[Dict[str, Any]], output_path: str):
    """Save exclusion report to CSV."""
    df = pd.DataFrame(exclusions)
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for data ingestion."""
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_huggingface_data()
        df = map_columns(df)
        output_path = data_dir / "raw_sn1_data.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved raw data to {output_path}")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
