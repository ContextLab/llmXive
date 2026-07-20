import os
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from utils import get_atomic_radius, get_vec, get_electronegativity
from exceptions import PowerWarning

logger = logging.getLogger(__name__)

def load_raw_data(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)

def filter_bcc_carbon(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["structure"] == "BCC") & (df["solute"] == "C")]

def enforce_provenance(df: pd.DataFrame) -> pd.DataFrame:
    # Exclude if both flags are missing or False? 
    # Spec: "exclude entries missing microstructure_controlled/single_crystal flags"
    # Interpretation: Keep if (microstructure_controlled is True OR single_crystal is True)
    # and not missing.
    mask = df["microstructure_controlled"].notna() & df["single_crystal"].notna()
    df = df[mask]
    mask = (df["microstructure_controlled"] == True) | (df["single_crystal"] == True)
    return df[mask]

def normalize_atomic_fractions(df: pd.DataFrame, elements: List[str]) -> pd.DataFrame:
    # Normalize columns in elements to sum to 1.0 per row
    for col in elements:
        if col in df.columns:
            total = df[col].sum()
            if total > 0:
                df[col] = df[col] / total
    return df

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    # Placeholder for descriptor computation logic
    # Assuming elements are in columns Fe, Cr, etc.
    elements = [c for c in df.columns if c not in ["structure", "solute", "diffusion_coefficient", "microstructure_controlled", "single_crystal"]]
    
    atomic_radii = []
    vecs = []
    electronegativities = []
    
    for idx, row in df.iterrows():
        radii = []
        vec_list = []
        en_list = []
        for el in elements:
            val = row[el]
            if val > 0:
                r = get_atomic_radius(el)
                v = get_vec(el)
                e = get_electronegativity(el)
                if r: radii.append(r)
                if v is not None: vec_list.append(v)
                if e: en_list.append(e)
        
        if len(radii) > 1:
            atomic_radii.append(np.var(radii))
        else:
            atomic_radii.append(0.0)
        
        if len(vec_list) > 0:
            vecs.append(np.mean(vec_list))
        else:
            vecs.append(0.0)

        if len(en_list) > 1:
            electronegativities.append(np.std(en_list))
        else:
            electronegativities.append(0.0)

    df["atomic_radius_variance"] = atomic_radii
    df["VEC"] = vecs
    df["electronegativity_spread"] = electronegativities
    return df

def apply_log_transformation(df: pd.DataFrame) -> pd.DataFrame:
    df["diffusion_coefficient_log"] = np.log10(df["diffusion_coefficient"])
    return df

def clean_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    return df

def main():
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).parent.parent
    raw_file = root / "data" / "raw" / "melidc.parquet"
    out_dir = root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_cleaned.csv"

    if not raw_file.exists():
        logger.error("Raw data not found. Run 01_download.py first.")
        sys.exit(1)

    df = load_raw_data(raw_file)
    df = filter_bcc_carbon(df)
    df = enforce_provenance(df)
    elements = [c for c in df.columns if c not in ["structure", "solute", "diffusion_coefficient", "microstructure_controlled", "single_crystal"]]
    df = normalize_atomic_fractions(df, elements)
    df = compute_descriptors(df)
    df = apply_log_transformation(df)
    df = clean_and_finalize(df)

    if len(df) < 30:
        logger.warning("PowerWarning: Dataset size < 30. LOOCV will be used.")
    
    df.to_csv(out_file, index=False)
    logger.info(f"Saved cleaned data to {out_file}")

if __name__ == "__main__":
    main()
