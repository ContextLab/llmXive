import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from llmxive_toolkit import paths, get_logger
from code.utils.config import get_solvent_list
from code.utils.validators import ensure_schema_file_exists

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def standardize_affinity_value(value: Any, unit: str) -> float:
    """
    Standardize affinity values to log K.
    Assumes input is either log K or ΔG (kcal/mol).
    ΔG = -RT ln K  =>  log10 K = -ΔG / (2.303 * RT)
    At 298K, 2.303 * R * T ≈ 1.364 kcal/mol
    """
    if pd.isna(value):
        return np.nan

    val = float(value)
    if unit.lower() in ["logk", "log_k", "log"]:
        return val
    elif unit.lower() in ["dg", "deltag", "kcal/mol"]:
        # Convert ΔG to log K
        return -val / 1.364
    else:
        logger.warning(f"Unknown unit {unit} for value {val}. Returning NaN.")
        return np.nan


def parse_smiles(smiles: str) -> Optional[Chem.Mol]:
    """Parse SMILES string to RDKit Mol object."""
    if not smiles or pd.isna(smiles):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None


def parse_inchi(inchi: str) -> Optional[Chem.Mol]:
    """Parse InChI string to RDKit Mol object."""
    if not inchi or pd.isna(inchi):
        return None
    try:
        mol = Chem.MolFromInchi(inchi)
        return mol
    except Exception:
        return None


def extract_halide_identity(record: Dict[str, Any]) -> Optional[str]:
    """Extract halide identity (F, Cl, Br, I) from record."""
    halides = [
        "fluoride",
        "chloride",
        "bromide",
        "iodide",
        "f-",
        "cl-",
        "br-",
        "i-",
        "f",
        "cl",
        "br",
        "i",
    ]
    text = str(record).lower()
    for h in halides:
        if h in text:
            if "fluoride" in h or h == "f":
                return "F"
            if "chloride" in h or h == "cl":
                return "Cl"
            if "bromide" in h or h == "br":
                return "Br"
            if "iodide" in h or h == "i":
                return "I"
    return None


def is_solvent_valid(solvent: str) -> bool:
    """Check if solvent is in the allowed list."""
    valid_solvents = get_solvent_list()
    if not solvent:
        return False
    return solvent.lower() in [s.lower() for s in valid_solvents]


def calculate_rdkit_descriptors_for_sim(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate basic descriptors for simulated data generation.
    Returns charge_density and cavity_volume approximations.
    """
    if mol is None:
        return {"charge_density": 0.0, "cavity_volume": 0.0}

    # Approximation: charge_density ~ (H-bond donors) / (Molecular Weight)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    mw = Descriptors.MolWt(mol)
    charge_density = hbd / (mw + 1e-6)

    # Use TPSA directly as a proxy for cavity volume (no arbitrary scaling)
    cavity_volume = Descriptors.TPSA(mol)
    return {"charge_density": charge_density, "cavity_volume": cavity_volume}


# ----------------------------------------------------------------------
# Data fetching utilities
# ----------------------------------------------------------------------
def fetch_pubchem_records(halide: str, max_retries: int = 3, base_delay: int = 2) -> List[pcp.Compound]:
    """
    Fetch compounds from PubChem for a given halide name using PubChemPy,
    with exponential back‑off on HTTP 429/503 errors.
    """
    attempt = 0
    while True:
        try:
            compounds = pcp.get_compounds(halide, 'name')
            return compounds
        except Exception as e:
            # PubChemPy may raise a generic exception; inspect for HTTP status if possible
            response = getattr(e, "response", None)
            status = getattr(response, "status_code", None)
            if status in (429, 503) and attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                logger.warning(
                    f"PubChem request for '{halide}' returned {status}. "
                    f"Retry {attempt + 1}/{max_retries} after {wait}s."
                )
                time.sleep(wait)
                attempt += 1
                continue
            logger.error(f"Failed to fetch PubChem data for halide '{halide}': {e}")
            raise


def build_raw_records() -> List[Dict[str, Any]]:
    """
    Build a list of raw record dictionaries by querying PubChem for each halide.
    Each record contains:
        - smiles
        - host_id (PubChem CID)
        - value (None, placeholder for binding constant)
        - unit (None)
        - solvent (set to a permitted default)
        - halide_info (the halide string used for the query)
    """
    halides = ["Cl-", "Br-", "I-"]  # Fluoride often has many hits; limit to three for speed
    records: List[Dict[str, Any]] = []

    for halide in halides:
        compounds = fetch_pubchem_records(halide)
        logger.info(f"Fetched {len(compounds)} compounds for halide '{halide}'.")
        for comp in compounds:
            smiles = getattr(comp, "isomeric_smiles", None)
            if not smiles:
                continue  # skip entries without SMILES
            record = {
                "smiles": smiles,
                "host_id": str(comp.cid),
                "value": None,
                "unit": None,
                "solvent": "acetonitrile",  # allowed solvent placeholder
                "halide_info": halide,
            }
            records.append(record)

        # Respect the required 2 s delay between requests
        time.sleep(2)

    return records


# ----------------------------------------------------------------------
# Core cleaning / filtering logic
# ----------------------------------------------------------------------
def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES/InChI, exclude invalid structures, standardize units,
    extract halide identity, and filter by solvent.
    """
    logger.info("Validating and cleaning data...")

    # Ensure SMILES column exists
    if "smiles" not in df.columns and "SMILES" not in df.columns:
        smiles_col = next((c for c in df.columns if "smiles" in c.lower()), None)
        if smiles_col:
            df["smiles"] = df[smiles_col]
        else:
            logger.warning("No SMILES column found. Skipping structure validation.")
            return df

    # Parse SMILES to RDKit Mol objects
    df["mol_obj"] = df["smiles"].apply(parse_smiles)

    # Keep only rows with a valid Mol
    valid_mask = df["mol_obj"].notna()
    df_clean = df[valid_mask].copy()
    logger.info(f"Filtered {len(df) - len(df_clean)} invalid structures.")

    # Standardize affinity values
    if "unit" in df_clean.columns:
        df_clean["logK_std"] = df_clean.apply(
            lambda r: standardize_affinity_value(r.get("value"), r.get("unit")), axis=1
        )
    elif "logK" in df_clean.columns:
        df_clean["logK_std"] = df_clean["logK"]
    elif "value" in df_clean.columns:
        df_clean["logK_std"] = df_clean["value"]
    else:
        logger.warning("No affinity value column found.")
        df_clean["logK_std"] = np.nan

    # Extract halide identity
    df_clean["halide"] = df_clean.apply(extract_halide_identity, axis=1)
    df_clean = df_clean.dropna(subset=["halide"])

    # Filter by allowed solvents
    if "solvent" in df_clean.columns:
        df_clean = df_clean[df_clean["solvent"].apply(is_solvent_valid)]

    # Resolve duplicate host–halide records by averaging logK_std
    if not df_clean.empty:
        agg_dict = {
            "logK_std": "mean",
            "smiles": "first",
            "solvent": "first",
            "halide": "first",
        }
        df_clean = (
            df_clean.groupby(["host_id", "halide"], as_index=False)
            .agg(agg_dict)
        )

    # Drop helper columns
    df_clean = df_clean.drop(columns=["mol_obj"])
    return df_clean


def filter_hosts_with_multiple_halides(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain only hosts that have measurements for at least three distinct halides.
    """
    logger.info("Filtering hosts with multiple halides...")

    if "host_id" not in df.columns:
        logger.warning("No host_id column found. Skipping host filtering.")
        return df

    host_halide_counts = df.groupby("host_id")["halide"].nunique()
    valid_hosts = host_halide_counts[host_halide_counts >= 3].index
    df_filtered = df[df["host_id"].isin(valid_hosts)]
    logger.info(f"Retained {len(valid_hosts)} hosts with ≥3 halides.")
    return df_filtered


def get_most_abundant_halide(df: pd.DataFrame) -> str:
    """Return the halide with the highest occurrence in the dataset."""
    if "halide" not in df.columns or df.empty:
        return "F"  # default fallback
    return df["halide"].value_counts().idxmax()


def generate_simulated_data(
    df_descriptors: pd.DataFrame, target_halide: str, n_rows: int = 100
) -> pd.DataFrame:
    """
    Generate synthetic data based on real descriptor statistics.
    Formula: logK_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)
    """
    logger.info(f"Generating {n_rows} rows of simulated data for halide {target_halide}...")
    required_cols = {"charge_density", "cavity_volume", "smiles"}
    if not required_cols.issubset(df_descriptors.columns):
        logger.error("Missing required descriptor columns for simulation.")
        raise ValueError("Descriptor columns missing for simulation.")

    # Sample rows (with replacement if needed)
    if len(df_descriptors) < n_rows:
        sample_indices = np.random.choice(len(df_descriptors), size=n_rows, replace=True)
        base_df = df_descriptors.iloc[sample_indices].reset_index(drop=True)
    else:
        base_df = df_descriptors.head(n_rows).reset_index(drop=True)

    noise = np.random.normal(0, 0.2, n_rows)
    base_df["logK_std"] = (
        0.5 * base_df["charge_density"] + 0.3 * base_df["cavity_volume"] + noise
    )
    base_df["halide"] = target_halide
    base_df["source"] = "simulated"
    return base_df


def log_simulated_warning():
    """Emit the exact warning required for simulated‑mode activation."""
    logger.warning(
        "WARNING: Insufficient data (<50 hosts). Comparative analysis aborted. Switching to single-halide prediction mode with simulated data."
    )


def run_data_sufficiency_logic(df_filtered: pd.DataFrame) -> bool:
    """
    Determine whether the dataset meets the minimum host count.
    Writes SIMULATED_MODE flag to data/simulated/state.json.
    Returns True if simulated mode should be activated.
    """
    state_path = paths.data("simulated", "state.json")
    unique_hosts = (
        df_filtered["host_id"].nunique() if "host_id" in df_filtered.columns else 0
    )
    is_simulated = unique_hosts < 50

    state = {
        "SIMULATED_MODE": is_simulated,
        "analysis_mode": "single_halide_prediction"
        if is_simulated
        else "comparative_analysis",
        "comparative_analysis_aborted": is_simulated,
        "host_count": int(unique_hosts),
        "threshold": 50,
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    if is_simulated:
        log_simulated_warning()
    return is_simulated


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def run_data_pipeline():
    """
    Execute the full ingestion, cleaning, filtering, and (if needed)
    simulation workflow.
    """
    # 1. Fetch raw data from PubChem
    logger.info("Fetching raw data from PubChem...")
    raw_records = build_raw_records()
    if not raw_records:
        raise RuntimeError("No records fetched from PubChem; aborting pipeline.")

    raw_path = paths.data("raw", "raw_scrape.json")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w") as f:
        json.dump(raw_records, f, indent=2)

    # 2. Load into DataFrame
    df = pd.DataFrame(raw_records)

    # 3. Clean & standardize
    df_clean = validate_and_clean_data(df)
    cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False)

    # 4. Filter hosts with ≥3 halides
    df_filtered = filter_hosts_with_multiple_halides(df_clean)
    filtered_path = paths.data("raw", "filtered_hosts.csv")
    df_filtered.to_csv(filtered_path, index=False)

    # 5. Check data sufficiency & possibly generate simulated data
    is_simulated = run_data_sufficiency_logic(df_filtered)

    if is_simulated:
        # Ensure descriptor file exists; if not, compute from cleaned data
        desc_path = paths.data("raw", "descriptors_added.csv")
        if desc_path.is_file():
            df_desc = pd.read_csv(desc_path)
        else:
            logger.info(
                "descriptors_added.csv not found. Computing descriptors from cleaned data."
            )
            df_desc = df_clean.copy()
            df_desc["mol_obj"] = df_desc["smiles"].apply(parse_smiles)
            descriptor_series = df_desc["mol_obj"].apply(calculate_rdkit_descriptors_for_sim)
            df_desc["charge_density"] = descriptor_series.apply(
                lambda d: d["charge_density"]
            )
            df_desc["cavity_volume"] = descriptor_series.apply(
                lambda d: d["cavity_volume"]
            )
            df_desc = df_desc.drop(columns=["mol_obj"])
            df_desc.to_csv(desc_path, index=False)

        target_halide = get_most_abundant_halide(df_clean)
        df_sim = generate_simulated_data(df_desc, target_halide, n_rows=100)
        sim_path = paths.data("simulated", "temp_simulated_data.csv")
        df_sim.to_csv(sim_path, index=False)

    logger.info("Data ingestion pipeline completed successfully.")


def main():
    run_data_pipeline()


if __name__ == "__main__":
    main()
