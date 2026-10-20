import json
import logging
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rdkit import Chem
from rdkit.Chem import rdPartialCharges, rdMolDescriptors

from llmxive_toolkit import paths, get_logger
from code.utils.config import get_solvent_list

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (unchanged)
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

    try:
        val = float(value)
    except Exception:
        logger.warning(f"Unable to convert affinity value {value!r} to float.")
        return np.nan

    if unit is None:
        return np.nan

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
    halides = {
        "fluoride": "F",
        "chloride": "Cl",
        "bromide": "Br",
        "iodide": "I",
        "f-": "F",
        "cl-": "Cl",
        "br-": "Br",
        "i-": "I",
        "f": "F",
        "cl": "Cl",
        "br": "Br",
        "i": "I",
    }
    text = str(record).lower()
    for pattern, symbol in halides.items():
        if pattern in text:
            return symbol
    return None


def is_solvent_valid(solvent: str) -> bool:
    """Check if solvent is in the allowed list."""
    valid_solvents = get_solvent_list()
    if not solvent:
        return False
    return solvent.lower() in [s.lower() for s in valid_solvents]


# ----------------------------------------------------------------------
# Data fetching utilities (unchanged)
# ----------------------------------------------------------------------
def _request_with_backoff(url: str, max_retries: int = 5, base_delay: int = 2) -> requests.Response:
    """
    Perform an HTTP GET with exponential back‑off on 429/503.
    Non‑retryable status codes (e.g., 400) are raised immediately.
    """
    attempt = 0
    while True:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            if response.status_code in (429, 503) and attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                logger.warning(
                    f"Request to {url} returned {response.status_code}. "
                    f"Retry {attempt + 1}/{max_retries} after {wait}s."
                )
                time.sleep(wait)
                attempt += 1
                continue
            # For any other status code, raise immediately
            response.raise_for_status()
        except requests.HTTPError as http_err:
            # Do not retry on client errors like 400/404 etc.
            logger.error(f"HTTP error for {url}: {http_err}")
            raise
        except requests.RequestException as e:
            # Network‑level errors – retry with backoff
            if attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                logger.warning(f"Request error ({e}); retry {attempt + 1}/{max_retries} after {wait}s.")
                time.sleep(wait)
                attempt += 1
                continue
            logger.error(f"Failed to fetch {url}: {e}")
            raise


def fetch_pubchem_records(halide: str, max_retries: int = 5, base_delay: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Attempt to fetch halide‑binding data from PubChem.
    PubChem does not expose a dedicated halide‑binding endpoint, so we treat
    any failure as a lack of usable records rather than an error.
    Returns a tuple (records, outcome) where outcome contains:
        - status: HTTP status code (int) or None if request failed before a response
        - records_fetched: number of records extracted
        - retries_exhausted: bool indicating if max retries were hit without success
    """
    query = halide
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/property/IsomericSMILES,InChI,CanonicalSMILES/JSON"

    try:
        response = _request_with_backoff(url, max_retries, base_delay)
        status = response.status_code
        data = response.json()
        compounds = data.get("PropertyTable", {}).get("Properties", [])
        records = []
        for comp in compounds:
            cid = comp.get("CID")
            smiles = comp.get("IsomericSMILES") or comp.get("CanonicalSMILES")
            inchi = comp.get("InChI")
            if cid and smiles:
                records.append({
                    "host_id": str(cid),
                    "smiles": smiles,
                    "inchi": inchi,
                    "value": np.nan,
                    "unit": None,
                    "solvent": "acetonitrile",  # placeholder solvent to keep schema consistency
                    "halide_info": halide,
                    "source": "PubChem"
                })
        outcome = {
            "status": status,
            "records_fetched": len(records),
            "retries_exhausted": False
        }
        return records, outcome
    except requests.HTTPError as http_err:
        status = http_err.response.status_code if http_err.response else None
        outcome = {
            "status": status,
            "records_fetched": 0,
            "retries_exhausted": False
        }
        logger.info(f"No PubChem data retrieved for halide '{halide}': {http_err}")
        return [], outcome
    except Exception as e:
        # Network‑level errors after exhausting retries
        outcome = {
            "status": None,
            "records_fetched": 0,
            "retries_exhausted": True
        }
        logger.info(f"No PubChem data retrieved for halide '{halide}': {e}")
        return [], outcome


def fetch_nist_records(halide: str, max_retries: int = 5, base_delay: int = 2) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Very lightweight scraper for the NIST Chemistry WebBook.
    Returns a tuple (records, outcome) analogous to fetch_pubchem_records.
    """
    url = f"https://webbook.nist.gov/cgi/cbook.cgi?Name={halide}&Units=SI"
    try:
        response = _request_with_backoff(url, max_retries, base_delay)
        status = response.status_code
        soup = BeautifulSoup(response.text, "html.parser")
        records: List[Dict[str, Any]] = []

        tables = soup.find_all("table")
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if any("halide" in h for h in headers) or any("binding" in h for h in headers):
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if len(cells) < 5:
                        continue
                    try:
                        smiles = cells[0].get_text(strip=True)
                        halide_label = cells[1].get_text(strip=True)
                        value = cells[2].get_text(strip=True)
                        unit = cells[3].get_text(strip=True)
                        solvent = cells[4].get_text(strip=True)
                    except Exception:
                        continue

                    records.append({
                        "host_id": None,
                        "smiles": smiles,
                        "inchi": None,
                        "value": value,
                        "unit": unit,
                        "solvent": solvent,
                        "halide_info": halide_label,
                        "source": "NIST"
                    })
        outcome = {
            "status": status,
            "records_fetched": len(records),
            "retries_exhausted": False
        }
        return records, outcome
    except requests.HTTPError as http_err:
        status = http_err.response.status_code if http_err.response else None
        outcome = {
            "status": status,
            "records_fetched": 0,
            "retries_exhausted": False
        }
        logger.info(f"No NIST data retrieved for halide '{halide}': {http_err}")
        return [], outcome
    except Exception as e:
        outcome = {
            "status": None,
            "records_fetched": 0,
            "retries_exhausted": True
        }
        logger.info(f"No NIST data retrieved for halide '{halide}': {e}")
        return [], outcome


def build_raw_records() -> Dict[str, Any]:
    """
    Fetch data from PubChem and NIST for each halide, record per‑source
    outcomes, and return a dictionary containing:
      - "records": List[Dict] of all raw records
      - "outcome": dict with status codes, record counts, retry info, etc.
    """
    halides = ["fluoride", "chloride", "bromide", "iodide"]
    all_records: List[Dict] = []
    outcome: Dict[str, Any] = {
        "pubchem": {"halides": {}},
        "nist": {"halides": {}},
        "total_records_fetched": 0,
    }

    for halide in halides:
        # PubChem
        pc_records, pc_outcome = fetch_pubchem_records(halide)
        outcome["pubchem"]["halides"][halide] = pc_outcome
        all_records.extend(pc_records)
        outcome["total_records_fetched"] += pc_outcome["records_fetched"]

        # Respect the required 2 s delay between requests (per source)
        time.sleep(2)

        # NIST
        nist_records, nist_outcome = fetch_nist_records(halide)
        # Assign placeholder host IDs for NIST records lacking one
        for idx, rec in enumerate(nist_records):
            if not rec["host_id"]:
                rec["host_id"] = f"NIST-{halide.upper()}-{idx}"
        outcome["nist"]["halides"][halide] = nist_outcome
        all_records.extend(nist_records)
        outcome["total_records_fetched"] += nist_outcome["records_fetched"]

        time.sleep(2)

    return {"records": all_records, "outcome": outcome}


# ----------------------------------------------------------------------
# Core cleaning / filtering logic (unchanged)
# ----------------------------------------------------------------------
def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES/InChI, exclude invalid structures, standardize units,
    extract halide identity, and filter by solvent.
    Returns a DataFrame with columns:
        host_id, smiles, halide_identity, binding_constant, solvent, source
    """
    logger.info("Validating and cleaning data...")

    required_cols = {"smiles", "halide_info", "solvent", "source", "host_id"}
    missing = required_cols - set(df.columns)
    if missing:
        logger.error(f"Missing required columns for cleaning: {missing}")
        raise KeyError(f"Missing columns: {missing}")

    # Parse SMILES to RDKit Mol objects
    df["mol_obj"] = df["smiles"].apply(parse_smiles)

    # Keep only rows with a valid Mol
    valid_mask = df["mol_obj"].notna()
    excluded_invalid = len(df) - valid_mask.sum()
    logger.info(f"Excluded {excluded_invalid} records with invalid SMILES/InChI.")
    df_clean = df[valid_mask].copy()

    # Standardize affinity values
    if "unit" in df_clean.columns and "value" in df_clean.columns:
        df_clean["binding_constant"] = df_clean.apply(
            lambda r: standardize_affinity_value(r.get("value"), r.get("unit")), axis=1
        )
    else:
        df_clean["binding_constant"] = np.nan

    # Extract halide identity
    df_clean["halide_identity"] = df_clean["halide_info"].apply(extract_halide_identity)
    df_clean = df_clean.dropna(subset=["halide_identity"])

    # Filter by allowed solvents
    df_clean = df_clean[df_clean["solvent"].apply(is_solvent_valid)]

    # Resolve duplicate host–halide records by averaging binding_constant
    agg_dict = {
        "binding_constant": "mean",
        "smiles": "first",
        "solvent": "first",
        "source": "first",
        "halide_identity": "first",
    }
    df_clean = (
        df_clean.groupby(["host_id", "halide_identity"], as_index=False)
        .agg(agg_dict)
    )

    df_clean = df_clean[
        ["host_id", "smiles", "halide_identity", "binding_constant", "solvent", "source"]
    ]

    # Do NOT raise on empty; return empty DataFrame and let caller handle it
    if df_clean.empty:
        logger.warning("Cleaning resulted in an empty dataset.")
    # Attach exclusion count for downstream reporting
    df_clean.attrs["exclusions"] = excluded_invalid
    return df_clean


def filter_hosts_with_multiple_halides(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain only hosts that have measurements for at least three distinct halides.
    If no such hosts exist, return the original cleaned DataFrame (to avoid empty outputs).
    """
    logger.info("Filtering hosts with multiple halides...")

    host_halide_counts = df.groupby("host_id")["halide_identity"].nunique()
    valid_hosts = host_halide_counts[host_halide_counts >= 3].index
    if len(valid_hosts) == 0:
        logger.warning("No hosts with >=3 halides found; returning all cleaned records.")
        return df.copy()
    df_filtered = df[df["host_id"].isin(valid_hosts)].copy()
    logger.info(f"Retained {len(valid_hosts)} hosts with ≥3 halides.")
    return df_filtered


# ----------------------------------------------------------------------
# Simulation utilities
# ----------------------------------------------------------------------
SIMULATED_SMILES_URL = (
    "https://huggingface.co/datasets/seyonec/SMILES/resolve/main/data.parquet"
)
RANDOM_SEED = 42
VALID_SOLVENTS = ["acetonitrile", "chloroform", "dichloromethane"]


def _load_smiles_parquet(url: str) -> pd.DataFrame:
    """
    Load a parquet file containing SMILES strings from a verified HuggingFace URL.
    The function raises loudly if the download fails or the expected column is missing.
    """
    logger.info(f"Downloading SMILES parquet from {url}")
    try:
        df = pd.read_parquet(url, engine="auto")
    except Exception as e:
        logger.error(f"Failed to read parquet from {url}: {e}")
        raise

    # Expect a column named 'smiles' (case‑insensitive)
    cols = {c.lower(): c for c in df.columns}
    if "smiles" not in cols:
        raise KeyError("Parquet file does not contain a 'smiles' column.")
    df = df.rename(columns={cols["smiles"]: "smiles"})
    return df


def _compute_gasteiger_sum(mol: Chem.Mol) -> float:
    """
    Compute the sum of Gasteiger partial charges for a molecule.
    """
    try:
        rdPartialCharges.ComputeGasteigerCharges(mol)
        charges = [float(atom.GetProp("_GasteigerCharge")) for atom in mol.GetAtoms()]
        return float(np.sum(charges))
    except Exception:
        return 0.0


def _compute_molecular_volume(mol: Chem.Mol) -> float:
    """
    Compute the molecular volume (Å³) using RDKit's volume descriptor.
    """
    try:
        return float(rdMolDescriptors.CalcMolVolume(mol))
    except Exception:
        return 0.0


def _generate_simulated_dataset(
    most_abundant_halide: str,
    n_primary: int = 200,
    n_independent: int = 100,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate the primary simulated dataset (single halide) and an independent
    evaluation set with feature‑independent targets.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # Load SMILES pool
    smiles_df = _load_smiles_parquet(SIMULATED_SMILES_URL)
    if len(smiles_df) < n_primary + n_independent:
        raise ValueError(
            "Not enough SMILES records in the source parquet to sample required molecules."
        )

    # Sample primary and independent sets without overlap
    primary_df = smiles_df.sample(n=n_primary, random_state=RANDOM_SEED)
    remaining = smiles_df.drop(primary_df.index)
    independent_df = remaining.sample(n=n_independent, random_state=RANDOM_SEED)

    # Helper to compute descriptors and simulated logK
    def enrich(df: pd.DataFrame, simulate_target: bool) -> pd.DataFrame:
        charge_list = []
        volume_list = []
        logk_list = []
        for smi in df["smiles"]:
            mol = parse_smiles(smi)
            if mol is None:
                charge, volume = 0.0, 0.0
            else:
                charge = _compute_gasteiger_sum(mol)
                volume = _compute_molecular_volume(mol)
            charge_list.append(charge)
            volume_list.append(volume)

            if simulate_target:
                noise = rng.normal(0, 0.2)
                logk = 0.5 * charge + 0.3 * volume + noise
            else:
                logk = rng.normal(0, 1)  # feature‑independent
            logk_list.append(logk)

        df = df.copy()
        df["charge_density"] = charge_list
        df["cavity_volume"] = volume_list
        df["binding_constant"] = logk_list
        df["halide_identity"] = most_abundant_halide
        df["solvent"] = VALID_SOLVENTS[0]  # use the first valid solvent
        df["source"] = "Simulated"
        # Assign deterministic host IDs
        df["host_id"] = ["SIM-" + str(i + 1) for i in range(len(df))]
        # Align column names with dataset schema
        df = df[
            [
                "host_id",
                "smiles",
                "halide_identity",
                "binding_constant",
                "solvent",
                "charge_density",
                "cavity_volume",
                "source",
            ]
        ]
        return df

    primary_enriched = enrich(primary_df, simulate_target=True)
    independent_enriched = enrich(independent_df, simulate_target=False)
    return primary_enriched, independent_enriched


# ----------------------------------------------------------------------
# Metadata & state handling
# ----------------------------------------------------------------------
def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Wrote JSON to {path}")


def _load_json(path: Path) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def _determine_most_abundant_halide(cleaned_path: Path) -> str:
    """
    Identify the most abundant halide in the cleaned real data.
    Returns a string with a trailing dash to match the schema (e.g., "Cl-").
    Defaults to "Cl-" if the file is empty or missing.
    """
    if not cleaned_path.exists():
        return "Cl-"
    df = pd.read_csv(cleaned_path)
    if df.empty or "halide_identity" not in df.columns:
        return "Cl-"
    counts = df["halide_identity"].value_counts()
    if counts.empty:
        return "Cl-"
    most = counts.idxmax()
    # Ensure dash suffix
    return f"{most}-"


def _create_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build metadata.json containing per‑halide host counts and underpowered flag.
    """
    # Ensure halide identifiers have dash suffix as required by schema
    halide_series = df["halide_identity"].apply(lambda x: f"{x}-")
    counts = halide_series.value_counts().to_dict()
    underpowered = any(v < 10 for v in counts.values())
    return {"per_halide_counts": counts, "underpowered": underpowered}


# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def run_data_pipeline():
    """
    Execute the full ingestion, cleaning, and filtering workflow.
    """
    logger.info("Fetching raw data from PubChem and NIST...")
    fetch_result = build_raw_records()
    raw_records = fetch_result["records"]
    fetch_outcome = fetch_result["outcome"]

    # Save raw JSON (may be empty)
    raw_path = paths.data("raw", "raw_scrape.json")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w") as f:
        json.dump(raw_records, f, indent=2)

    # Load into DataFrame (may be empty)
    df = pd.DataFrame(raw_records)

    # If there are no raw records, produce empty output files with headers and exit cleanly
    if df.empty:
        logger.info("No raw records retrieved; generating empty output artifacts.")
        empty_cols = ["host_id", "smiles", "halide_identity", "binding_constant", "solvent", "source"]
        empty_df = pd.DataFrame(columns=empty_cols)

        cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")
        cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_csv(cleaned_path, index=False)

        filtered_path = paths.data("raw", "filtered_hosts.csv")
        filtered_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_csv(filtered_path, index=False)

        # Record zero exclusions in outcome
        fetch_outcome["exclusions"] = 0
        outcome_path = paths.data("raw", "fetch_outcome.json")
        outcome_path.parent.mkdir(parents=True, exist_ok=True)
        with open(outcome_path, "w") as f:
            json.dump(fetch_outcome, f, indent=2)

        logger.info("Data ingestion pipeline completed with zero usable records.")
        return

    # Clean & standardize (will not raise on empty after modification)
    df_clean = validate_and_clean_data(df)

    # Record exclusion count from cleaning step
    exclusions = df_clean.attrs.get("exclusions", 0)
    fetch_outcome["exclusions"] = int(exclusions)

    # Write fetch outcome JSON (now includes exclusions)
    outcome_path = paths.data("raw", "fetch_outcome.json")
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outcome_path, "w") as f:
        json.dump(fetch_outcome, f, indent=2)

    # Write cleaned CSV (may be empty)
    cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(cleaned_path, index=False)

    # Filter hosts with ≥3 halides
    df_filtered = filter_hosts_with_multiple_halides(df_clean)
    filtered_path = paths.data("raw", "filtered_hosts.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(filtered_path, index=False)

    logger.info("Data ingestion pipeline completed successfully.")


# ----------------------------------------------------------------------
# Finalization / FR‑011 handling
# ----------------------------------------------------------------------
def finalize_dataset():
    """
    Apply the FR‑011 sufficiency gate and generate either the real processed
    dataset or the simulated fallback. Also writes metadata.json and
    state.json.
    """
    filtered_path = paths.data("raw", "filtered_hosts.csv")
    cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")

    # Count unique hosts after the ≥3‑halide filter
    if not filtered_path.exists():
        logger.error(f"Filtered hosts file not found at {filtered_path}")
        raise FileNotFoundError(filtered_path)

    df_filtered = pd.read_csv(filtered_path)
    unique_hosts = df_filtered["host_id"].nunique()
    logger.info(f"Unique host count after filtering: {unique_hosts}")

    # Determine most abundant halide from cleaned data (used for simulated mode)
    most_abundant_halide = _determine_most_abundant_halide(cleaned_path)

    # Prepare state dictionary (will be written later)
    state: Dict[str, Any] = {
        "SIMULATED_MODE": False,
        "analysis_mode": "real_data",
        "comparative_analysis_aborted": False,
        "identified_halide": most_abundant_halide,
    }

    processed_path = paths.data("processed", "halide_binding_data.csv")
    metadata_path = paths.data("processed", "metadata.json")
    state_path = paths.data("simulated", "state.json")
    independent_path = paths.data("processed", "independent_eval.csv")

    if unique_hosts < 50:
        # ---------- Simulated fallback ----------
        logger.warning(
            f"WARNING: Insufficient data (<50 hosts). Comparative analysis aborted. "
            f"Switching to single-halide prediction mode with simulated data."
        )
        state.update(
            {
                "SIMULATED_MODE": True,
                "analysis_mode": "single_halide_prediction",
                "comparative_analysis_aborted": True,
            }
        )
        # Generate simulated datasets
        primary_df, independent_df = _generate_simulated_dataset(
            most_abundant_halide, n_primary=200, n_independent=100
        )

        # Write primary simulated dataset
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        primary_df.to_csv(processed_path, index=False)
        logger.info(f"Simulated primary dataset written to {processed_path}")

        # Write independent evaluation set
        independent_path.parent.mkdir(parents=True, exist_ok=True)
        independent_df.to_csv(independent_path, index=False)
        logger.info(f"Simulated independent evaluation set written to {independent_path}")

        # Metadata (only one halide present)
        metadata = _create_metadata(primary_df)
        _write_json(metadata_path, metadata)

    else:
        # ---------- Real data path ----------
        # Load descriptor‑augmented data (generated by 02_feature_engineering)
        descriptors_path = paths.data("raw", "descriptors_added.csv")
        if not descriptors_path.exists():
            logger.error(f"Descriptor file not found at {descriptors_path}")
            raise FileNotFoundError(descriptors_path)

        df_desc = pd.read_csv(descriptors_path)

        # Merge descriptors with the filtered host records
        merged = pd.merge(
            df_filtered,
            df_desc,
            on="host_id",
            how="left",
            suffixes=("", "_desc"),
        )
        # Preserve ordering of columns expected by downstream contracts
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(processed_path, index=False)
        logger.info(f"Real processed dataset written to {processed_path}")

        # Metadata based on the real processed dataset
        metadata = _create_metadata(merged)
        _write_json(metadata_path, metadata)

    # Write state.json (regardless of mode)
    _write_json(state_path, state)
    logger.info(f"State file written to {state_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Data ingestion and finalization pipeline")
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Run the FR‑011 sufficiency gate and generate the final processed dataset.",
    )
    args = parser.parse_args()

    if args.finalize:
        finalize_dataset()
    else:
        run_data_pipeline()


if __name__ == "__main__":
    main()
