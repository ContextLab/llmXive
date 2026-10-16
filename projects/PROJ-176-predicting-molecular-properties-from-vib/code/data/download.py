"""
Data download module for T103.
Downloads QM9 and IR spectra, aligns them via InChIKey, and computes selection bias.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd
from scipy import stats

def download_qm9(output_dir: Optional[Path] = None) -> Path:
    """Download QM9 dataset using qm9pack."""
    import qm9pack
    if output_dir is None:
        output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verified real source recipe
    df = qm9pack.get_data('qm9')
    out_path = output_dir / "qm9.parquet"
    # Ensure pyarrow is used for parquet support
    df.to_parquet(out_path, engine='pyarrow')
    return out_path

def download_ir_spectra(output_dir: Optional[Path] = None) -> Path:
    """Download IR spectra dataset using datasets library."""
    from datasets import load_dataset
    if output_dir is None:
        output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verified real source: lamblador/ir_spectra
    ds = load_dataset("lamblador/ir_spectra", split="train")
    df = ds.to_pandas()
    
    out_path = output_dir / "ir_spectra.parquet"
    df.to_parquet(out_path, engine='pyarrow')
    return out_path

def align_datasets(qm9_df: pd.DataFrame, ir_df: pd.DataFrame, key: str = 'InChIKey') -> Tuple[pd.DataFrame, int]:
    """Align QM9 and IR spectra datasets on InChIKey."""
    # Normalize key column names to handle potential case differences
    qm9_cols = {c: c.replace('inchikey', 'InChIKey').replace('InchiKey', 'InChIKey') for c in qm9_df.columns}
    ir_cols = {c: c.replace('inchikey', 'InChIKey').replace('InchiKey', 'InChIKey') for c in ir_df.columns}
    
    qm9_df = qm9_df.rename(columns=qm9_cols)
    ir_df = ir_df.rename(columns=ir_cols)

    if key not in qm9_df.columns or key not in ir_df.columns:
        raise KeyError(f"Alignment key {key} not found in datasets. QM9 cols: {list(qm9_df.columns)}, IR cols: {list(ir_df.columns)}")
        
    merged = pd.merge(qm9_df, ir_df, on=key, how='inner')
    discarded = len(qm9_df) - len(merged)
    return merged, discarded

def compute_selection_bias(full_df: pd.DataFrame, aligned_df: pd.DataFrame, properties: list) -> Dict[str, Any]:
    """Compute KS-test statistics to detect selection bias in aligned subset."""
    bias_stats = {}
    for prop in properties:
        if prop not in full_df.columns or prop not in aligned_df.columns:
            continue
        # KS test: Null hypothesis is that the two samples are drawn from the same distribution
        s, p = stats.ks_2samp(full_df[prop], aligned_df[prop])
        bias_stats[prop] = {
            "statistic": float(s),
            "p_value": float(p)
        }
    return bias_stats

def save_aligned_data(aligned_df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Save aligned DataFrame to a parquet file for T104."""
    if output_path is None:
        output_path = Path("data/processed") / "aligned_data.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligned_df.to_parquet(output_path, engine='pyarrow')
    return output_path

def main():
    """Main entry point for the data download and alignment script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting data download and alignment")

    try:
        # 1. Download raw files
        qm9_path = download_qm9()
        ir_path = download_ir_spectra()
        logger.info(f"Downloaded QM9 to {qm9_path} and IR spectra to {ir_path}")

        # 2. Load and align
        qm9_df = pd.read_parquet(qm9_path, engine='pyarrow')
        ir_df = pd.read_parquet(ir_path, engine='pyarrow')
        
        aligned_df, discarded = align_datasets(qm9_df, ir_df)
        matched = len(aligned_df)
        logger.info(f"Alignment complete: Matched={matched}, Discarded={discarded}")

        # 3. Verify match count (Acceptance Scenario: matched >= 129,000)
        if matched < 129000:
            raise RuntimeError(f"Insufficient matches found: {matched} < 129000")

        # 4. Compute selection bias for target properties
        # Using verified QM9 property names from the data source
        target_props = ['Dipole_debye', 'Polarizability_bohr3', 'HOMO_LUMO_gap_au']
        bias_stats = compute_selection_bias(qm9_df, aligned_df, target_props)
        logger.info("Selection bias KS-tests computed.")

        # 5. Write alignment report
        report = {
            "matched": matched,
            "discarded": discarded,
            "selection_bias_stats": bias_stats
        }
        report_path = Path("data/processed/alignment_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Alignment report saved to {report_path}")

        # 6. Save aligned dataset for next phase (T104)
        save_aligned_data(aligned_df)

    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()