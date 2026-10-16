"""
Data download module.
Provides functions to download QM9 and IR spectra datasets.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

def download_qm9(output_dir: Optional[Path] = None) -> Path:
    """Download QM9 dataset using qm9pack."""
    import qm9pack
    if output_dir is None:
        output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    df = qm9pack.get_data('qm9')
    out_path = output_dir / "qm9.parquet"
    df.to_parquet(out_path)
    return out_path

def download_ir_spectra(output_dir: Optional[Path] = None) -> Path:
    """Download IR spectra dataset using datasets library."""
    from datasets import load_dataset
    if output_dir is None:
        output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("lamblador/ir_spectra", split="train")
    # Convert to pandas DataFrame if needed
    if hasattr(ds, "to_pandas"):
        df = ds.to_pandas()
    else:
        # Fallback: construct DataFrame from dict records
        df = pd.DataFrame(ds)
    out_path = output_dir / "ir_spectra.parquet"
    df.to_parquet(out_path)
    return out_path

def align_datasets(qm9_df: pd.DataFrame, ir_df: pd.DataFrame, key: str = 'InChIKey') -> Tuple[pd.DataFrame, int]:
    """Align QM9 and IR spectra datasets on InChIKey."""
    merged = pd.merge(qm9_df, ir_df, on=key, how='inner')
    discarded = len(qm9_df) + len(ir_df) - 2 * len(merged)
    return merged, discarded

def save_aligned_data(aligned_df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Save aligned DataFrame to a parquet file."""
    if output_path is None:
        output_path = Path("data/processed") / "aligned_data.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligned_df.to_parquet(output_path)
    return output_path

def main():
    """Main entry point for the data download script."""
    logger = logging.getLogger(__name__)
    logger.info("Starting data download and alignment")
    qm9_path = download_qm9()
    ir_path = download_ir_spectra()
    qm9_df = pd.read_parquet(qm9_path)
    ir_df = pd.read_parquet(ir_path)
    aligned_df, discarded = align_datasets(qm9_df, ir_df)
    save_aligned_data(aligned_df)
    logger.info(f"Alignment complete, discarded {discarded} records")

if __name__ == "__main__":
    main()
