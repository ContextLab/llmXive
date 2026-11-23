"""
Data Preprocessing Pipeline for Molecular Descriptor Analysis (T010-T015).

Sanitizes molecular structures with RDKit (remove salts, fix valences,
log and exclude molecules the sanitizer rejects, e.g. exotic elements),
filters for the targets of interest, deduplicates SMILES, samples,
calculates 2D descriptors, and writes the validated processed CSV.
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, SaltRemover

# Make sibling utils importable when run as: python code/data/preprocess.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import RANDOM_SEED, MAX_MEMORY_GB  # noqa: E402
from utils.logging import get_logger, log_pipeline_step  # noqa: E402
from utils.update_state import update_state, compute_file_hash  # noqa: E402

# Suppress RDKit warnings for cleaner logs (failures are logged explicitly)
RDLogger.DisableLog("rdApp.*")

logger = get_logger(__name__)

PROJECT_ID = "PROJ-066-investigating-correlations-between-molec"
SCHEMA_PATH = PROJECT_ROOT / "code" / "contracts" / "molecule.schema.yaml"
RAW_DB_PATH = PROJECT_ROOT / "data" / "raw" / "chembl_33.db"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "molecules_processed.csv"
SAMPLE_STATS_PATH = PROJECT_ROOT / "data" / "processed" / "sample_stats.json"

DEFAULT_MAX_MOLECULES = 15000
TARGET_KEYWORDS = ["oral", "bioavailability", "papp", "permeability", "clearance"]

DESCRIPTOR_FUNCTIONS = {
    "TPSA": Descriptors.TPSA,
    "logP": Descriptors.MolLogP,
    "MW": Descriptors.MolWt,
    "NumRotatableBonds": Descriptors.NumRotatableBonds,
    "NumHDonors": Descriptors.NumHDonors,
    "NumHAcceptors": Descriptors.NumHAcceptors,
    "RingCount": Descriptors.RingCount,
}


class DataInsufficiencyError(Exception):
    """Raised when the dataset sample size is insufficient after reduction."""
    pass


# --- Schema helpers -------------------------------------------------------

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and return the JSON/YAML schema for validation."""
    if not Path(schema_path).exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def _required_columns_from_schema(schema: Dict[str, Any]) -> List[str]:
    """Extract required column names from either schema layout."""
    if not isinstance(schema, dict):
        return []
    if isinstance(schema.get("required_columns"), list):
        return list(schema["required_columns"])
    props = schema.get("properties")
    if isinstance(props, dict):
        required = schema.get("required", list(props.keys()))
        return [c for c in required if c in props]
    return []


def validate_dataframe_against_schema(
    df: pd.DataFrame, schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Validate a DataFrame against a schema definition. Returns (is_valid, errors)."""
    errors: List[str] = []
    required = _required_columns_from_schema(schema)
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    for col in required:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values.")
    if "SMILES" in df.columns:
        invalid = df[~df["SMILES"].apply(lambda s: Chem.MolFromSmiles(s) is not None)]
        if not invalid.empty:
            errors.append(f"Found {len(invalid)} rows with invalid SMILES structures.")
    return len(errors) == 0, errors


# --- Helper to normalize column names from the raw ChEMBL export ---------

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    The raw ChEMBL SQLite export may use different column names for SMILES
    or target descriptors. This helper looks for common alternatives and
    renames them to the canonical names expected by the pipeline.
    """
    # Map common SMILES column names to the expected 'SMILES'
    smiles_candidates = [c for c in df.columns if "smiles" in c.lower()]
    if "SMILES" not in df.columns and smiles_candidates:
        chosen = smiles_candidates[0]
        df = df.rename(columns={chosen: "SMILES"})
        logger.info(f"Renamed column '{chosen}' to 'SMILES' for pipeline compatibility.")

    # Map common target/value column names to 'Experimental_Value'
    target_candidates = [c for c in df.columns if "value" in c.lower() or "result" in c.lower()]
    if "Experimental_Value" not in df.columns and target_candidates:
        chosen = target_candidates[0]
        df = df.rename(columns={chosen: "Experimental_Value"})
        logger.info(f"Renamed column '{chosen}' to 'Experimental_Value'.")

    # Ensure a generic 'Target' column exists for stratification if possible
    if "Target" not in df.columns:
        possible_target = [c for c in df.columns if "type" in c.lower() or "standard_type" in c.lower()]
        if possible_target:
            df = df.rename(columns={possible_target[0]: "Target"})
            logger.info(f"Renamed column '{possible_target[0]}' to 'Target' for stratified sampling.")
    return df


# --- Core pipeline functions ---------------------------------------------

def sanitize_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize molecules using RDKit: remove salts, fix valences, and
    log/remove invalid structures (including 'exotic elements' where the
    RDKit sanitizer fails).

    Args:
        df: DataFrame with a 'SMILES' column.

    Returns:
        Cleaned DataFrame with only valid molecules.
    """
    logger.info("Starting molecule sanitization (T010)...")
    log_pipeline_step("T010", "sanitize_molecules")

    remover = SaltRemover.SaltRemover()

    valid_rows: List[Dict[str, Any]] = []
    invalid_count = 0
    salt_only_count = 0

    for idx, row in df.iterrows():
        smiles = row.get("SMILES")
        if not isinstance(smiles, str) or not smiles.strip():
            invalid_count += 1
            logger.warning(f"Row {idx}: empty/missing SMILES, excluded.")
            continue
        try:
            # MolFromSmiles applies full sanitization (valence checks etc.)
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_count += 1
                logger.warning(
                    f"Row {idx}: RDKit sanitizer failed for SMILES "
                    f"(invalid valence / exotic element): {smiles!r} -> excluded."
                )
                continue

            # Remove salts / counterions, keep the parent structure
            mol_clean = remover.StripMol(mol, dontRemoveEverything=True)
            if mol_clean is None or mol_clean.GetNumAtoms() == 0:
                salt_only_count += 1
                logger.warning(f"Row {idx}: only salt fragments present, excluded.")
                continue

            # Re-sanitize the stripped molecule to fix any valence issues
            Chem.SanitizeMol(mol_clean)

            new_row = row.to_dict()
            new_row["SMILES"] = Chem.MolToSmiles(mol_clean)
            valid_rows.append(new_row)
        except Exception as e:  # RDKit sanitizer failure (exotic elements etc.)
            invalid_count += 1
            logger.warning(
                f"Row {idx}: sanitization error ({e}); SMILES {smiles!r} excluded."
            )

    logger.info(
        f"Sanitization complete: kept {len(valid_rows)}, removed "
        f"{invalid_count} invalid structures and {salt_only_count} salt-only rows."
    )
    if not valid_rows:
        raise DataInsufficiencyError(
            "No valid molecules remained after sanitization."
        )
    return pd.DataFrame(valid_rows)


def filter_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset for the targets of interest (oral bioavailability,
    Papp / permeability, clearance) and remove rows with missing targets.

    Args:
        df: DataFrame with a 'Target' (or description) column.

    Returns:
        Filtered DataFrame.
    """
    logger.info("Filtering for target molecules (T011)...")
    log_pipeline_step("T011", "filter_targets")

    desc_col = next(
        (c for c in ["Target", "Description", "Assay_Description", "Standard_Type"]
         if c in df.columns),
        None,
    )
    if desc_col is None:
        logger.warning("No target/description column found; returning original data.")
        return df

    mask = df[desc_col].astype(str).str.lower().str.contains(
        "|".join(TARGET_KEYWORDS), na=False
    )
    filtered = df[mask].copy()
    # Remove rows with missing experimental values (FR-002)
    if "Experimental_Value" in filtered.columns:
        filtered = filtered.dropna(subset=["Experimental_Value"])
    logger.info(f"Target filtering complete. Retained {len(filtered)} rows.")
    return filtered


def deduplicate_smiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate SMILES by retaining the most recent assay date; if
    dates match, average the conflicting experimental values (FR-009).

    Args:
        df: DataFrame with 'SMILES' and (optionally) 'Assay_Date' columns.

    Returns:
        Deduplicated DataFrame.
    """
    logger.info("Deduplicating molecules by SMILES (T012)...")
    log_pipeline_step("T012", "deduplicate_smiles")

    if "SMILES" not in df.columns:
        return df

    date_col = next(
        (c for c in ["Assay_Date", "Date", "Publication_Date"] if c in df.columns),
        None,
    )

    work = df.copy()
    if date_col is not None:
        # Assay_Date may be a year (int/float) or a date string
        if pd.api.types.is_numeric_dtype(work[date_col]):
            work["_date"] = pd.to_datetime(
                work[date_col].astype("Int64").astype(str) + "-01-01",
                errors="coerce",
            )
        else:
            work["_date"] = pd.to_datetime(work[date_col], errors="coerce")

    kept: List[Dict[str, Any]] = []
    for smiles, group in work.groupby("SMILES", sort=False):
        if date_col is not None and group["_date"].notna().any():
            max_date = group["_date"].max()
            candidates = group[group["_date"] == max_date]
        else:
            candidates = group
        if len(candidates) == 1:
            row = candidates.iloc[0].to_dict()
        else:
            # Dates match (or unknown): average conflicting experimental values
            row = candidates.iloc[0].to_dict()
            if "Experimental_Value" in candidates.columns:
                row["Experimental_Value"] = float(
                    pd.to_numeric(candidates["Experimental_Value"], errors="coerce").mean()
                )
            logger.info(
                f"Duplicate SMILES with matching dates: averaged "
                f"{len(candidates)} experimental values for {smiles!r}."
            )
        kept.append(row)

    deduped = pd.DataFrame(kept)
    if "_date" in deduped.columns:
        deduped = deduped.drop(columns=["_date"])
    logger.info(f"Deduplication complete. Retained {len(deduped)} unique SMILES.")
    return deduped.reset_index(drop=True)


def sample_dataset(df: pd.DataFrame, target_size: Optional[int] = None) -> pd.DataFrame:
    """
    Perform stratified random sampling with memory safety checks (T013).

    target_size = min(MAX_MOLECULES, available_rows). Raises
    DataInsufficiencyError if the final sample has fewer than 100 rows.
    """
    logger.info("Performing dataset sampling (T013)...")
    log_pipeline_step("T013", "sample_dataset")

    available_rows = len(df)
    if target_size is None:
        target_size = DEFAULT_MAX_MOLECULES
    target_size = min(target_size, available_rows)

    # Memory safety: ~1 KB per row, keep well under MAX_MEMORY_GB
    max_safe_rows = (MAX_MEMORY_GB - 1) * 1024 * 1024
    target_size = min(target_size, max_safe_rows)

    if target_size < 100:
        raise DataInsufficiencyError("Data Insufficiency: Sample size < 100")

    strat_col = "Target" if "Target" in df.columns else None
    if strat_col and df[strat_col].nunique() > 1:
        n_strata = df[strat_col].nunique()
        sampled = df.groupby(strat_col, group_keys=False).apply(
            lambda x: x.sample(
                n=max(1, min(int(np.ceil(target_size / n_strata)), len(x))),
                random_state=RANDOM_SEED,
            )
        )
        # Trim to target size if group rounding overshot
        if len(sampled) > target_size:
            sampled = sampled.sample(n=target_size, random_state=RANDOM_SEED)
    else:
        sampled = df.sample(n=target_size, random_state=RANDOM_SEED)

    sampled = sampled.reset_index(drop=True)
    if len(sampled) < 100:
        raise DataInsufficiencyError("Data Insufficiency: Sample size < 100")

    # Record the final sample size for reproducibility (Constitution Principle I)
    SAMPLE_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "final_sample_size": int(len(sampled)),
        "available_rows_before_sampling": int(available_rows),
        "target_size_requested": int(target_size),
        "random_seed": RANDOM_SEED,
    }
    SAMPLE_STATS_PATH.write_text(json.dumps(stats, indent=2))
    update_state(
        project_id=PROJECT_ID,
        artifacts=[{
            "artifact_path": str(SAMPLE_STATS_PATH.relative_to(PROJECT_ROOT)),
            "hash": compute_file_hash(SAMPLE_STATS_PATH),
            "source": "preprocess.sample_dataset",
        }],
    )
    logger.info(f"Sampling complete. Selected {len(sampled)} rows.")
    return sampled


def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 2D molecular descriptors (TPSA, logP, MW, rotatable bonds,
    H-bond donors/acceptors, ring count) for all molecules (T014, FR-003).
    """
    logger.info("Calculating molecular descriptors (T014)...")
    log_pipeline_step("T014", "calculate_descriptors")

    desc_rows = []
    for smiles in df["SMILES"]:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            desc_rows.append({k: np.nan for k in DESCRIPTOR_FUNCTIONS})
        else:
            desc_rows.append({k: func(mol) for k, func in DESCRIPTOR_FUNCTIONS.items()})

    desc_df = pd.DataFrame(desc_rows)
    result = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    # Drop rows with missing descriptors (invalid structures)
    before = len(result)
    result = result.dropna(subset=list(DESCRIPTOR_FUNCTIONS.keys())).reset_index(drop=True)
    logger.info(
        f"Descriptor calculation complete: {len(DESCRIPTOR_FUNCTIONS)} columns added, "
        f"{before - len(result)} rows dropped for uncomputable descriptors."
    )
    return result


def write_processed_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Validate each row against the molecule schema DURING the write loop,
    then write the processed CSV and record its hash via update_state (T015).
    """
    logger.info("Validating and writing processed data (T015)...")
    log_pipeline_step("T015", "write_processed_data")

    schema = load_schema(SCHEMA_PATH)
    required = _required_columns_from_schema(schema)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept_rows: List[Dict[str, Any]] = []
    excluded = 0
    for _, row in df.iterrows():
        ok = True
        for col in required:
            if col not in df.columns or pd.isna(row.get(col)):
                ok = False
                break
        if ok and "SMILES" in df.columns:
            if not isinstance(row.get("SMILES"), str) or Chem.MolFromSmiles(row["SMILES"]) is None:
                ok = False
        if ok and "Experimental_Value" in df.columns:
            try:
                float(row["Experimental_Value"])
            except (TypeError, ValueError):
                ok = False
        if ok:
            kept_rows.append(row.to_dict())
        else:
            excluded += 1

    if excluded:
        logger.warning(f"Excluded {excluded} rows failing row-level schema validation.")
    if not kept_rows:
        raise DataInsufficiencyError("All rows failed schema validation; nothing to write.")

    out_df = pd.DataFrame(kept_rows)
    out_df.to_csv(output_path, index=False)

    update_state(
        project_id=PROJECT_ID,
        artifacts=[{
            "artifact_path": str(output_path.relative_to(PROJECT_ROOT)),
            "hash": compute_file_hash(output_path),
            "source": "preprocess.write_processed_data",
        }],
    )
    logger.info(f"Processed data written to {output_path} ({len(out_df)} rows).")


def main() -> None:
    """Main entry point: Load -> Sanitize -> Filter -> Dedup -> Sample -> Descriptors -> Write."""
    parser = argparse.ArgumentParser(description="Preprocess ChEMBL molecular data")
    parser.add_argument(
        "--max-samples",
        default=str(DEFAULT_MAX_MOLECULES),
        help="Maximum number of molecules to retain after sampling (int).",
    )
    args = parser.parse_args()

    # Convert max-samples to int, falling back to default on bad input
    try:
        max_samples = int(args.max_samples)
    except ValueError:
        logger.warning(
            f"Invalid --max-samples value '{args.max_samples}'; using default {DEFAULT_MAX_MOLECULES}."
        )
        max_samples = DEFAULT_MAX_MOLECULES

    logger.info("Starting Preprocessing Pipeline")
    log_pipeline_step("T010", "preprocess_pipeline")

    if not RAW_DB_PATH.exists():
        raise FileNotFoundError(
            f"Raw database not found: {RAW_DB_PATH}. Please run T009 (download.py) first."
        )

    conn = sqlite3.connect(str(RAW_DB_PATH))
    try:
        df = pd.read_sql_query("SELECT * FROM activities", conn)
    finally:
        conn.close()

    if df.empty:
        raise DataInsufficiencyError("No data loaded from database.")
    logger.info(f"Loaded {len(df)} raw activity rows from {RAW_DB_PATH}")

    # Normalize column names to expected canonical ones
    df = _normalize_columns(df)

    df = sanitize_molecules(df)
    df = filter_targets(df)
    df = deduplicate_smiles(df)
    df = sample_dataset(df, target_size=max_samples)
    df = calculate_descriptors(df)
    write_processed_data(df, PROCESSED_DATA_PATH)

    logger.info("Preprocessing Pipeline completed successfully.")
    log_pipeline_step("T010", "preprocess_pipeline", status="completed")
    print(f"Processed dataset written to {PROCESSED_DATA_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    main()