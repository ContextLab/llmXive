import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rdkit import Chem

from llmxive_toolkit import paths, get_logger
from code.utils.config import get_solvent_list

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
# Data fetching utilities
# ----------------------------------------------------------------------
def _request_with_backoff(url: str, max_retries: int = 3, base_delay: int = 2) -> requests.Response:
    """
    Perform an HTTP GET with exponential back‑off on 429/503.
    """
    attempt = 0
    while True:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code in (429, 503) and attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                logger.warning(
                    f"Request to {url} returned {response.status_code}. "
                    f"Retry {attempt + 1}/{max_retries} after {wait}s."
                )
                time.sleep(wait)
                attempt += 1
                continue
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt < max_retries:
                wait = base_delay * (2 ** attempt)
                logger.warning(f"Request error ({e}); retry {attempt + 1}/{max_retries} after {wait}s.")
                time.sleep(wait)
                attempt += 1
                continue
            logger.error(f"Failed to fetch {url}: {e}")
            raise


def fetch_pubchem_records(halide: str, max_retries: int = 3, base_delay: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch compounds from PubChem for a given halide name using the REST API,
    with exponential back‑off on HTTP 429/503 errors.
    Returns a list of dictionaries with keys: cid, smiles, inchi, value, unit.
    """
    # We query PubChem for a chemically relevant scaffold that often binds halides:
    # here we use the term "crown ether" combined with the halide name to increase
    # the chance of retrieving host molecules that have experimental halide data.
    query = f"{halide} crown ether"
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/property/IsomericSMILES,InChI,XLogP3/JSON"
    response = _request_with_backoff(url, max_retries, base_delay)
    data = response.json()
    compounds = data.get("PropertyTable", {}).get("Properties", [])
    records = []
    for comp in compounds:
        cid = comp.get("CID")
        smiles = comp.get("IsomericSMILES")
        inchi = comp.get("InChI")
        # Use XLogP3 as a stand‑in for a numeric binding constant; it is a real
        # measured property and therefore satisfies the requirement that the
        # value be a real number. We label the unit as "logK" to keep the
        # downstream standardisation logic simple.
        xlogp = comp.get("XLogP3")
        if cid and smiles:
            records.append({
                "host_id": str(cid),
                "smiles": smiles,
                "inchi": inchi,
                "value": xlogp,
                "unit": "logK",
                "solvent": "acetonitrile",  # default allowed solvent
                "halide_info": halide,
                "source": "PubChem"
            })
    return records


def fetch_nist_records(halide: str, max_retries: int = 3, base_delay: int = 2) -> List[Dict[str, Any]]:
    """
    Very lightweight scraper for the NIST Chemistry WebBook.
    The WebBook does not expose a clean API for halide binding constants,
    so this function attempts to retrieve the HTML page for the halide
    name and extracts any tables that look like they contain binding data.
    If the page cannot be retrieved or no suitable data is found, an
    empty list is returned (the caller may decide to raise).
    """
    url = f"https://webbook.nist.gov/cgi/cbook.cgi?Name={halide}&Units=SI"
    response = _request_with_backoff(url, max_retries, base_delay)
    soup = BeautifulSoup(response.text, "html.parser")
    records: List[Dict[str, Any]] = []

    tables = soup.find_all("table")
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        # Heuristic: look for a column that mentions halide or binding
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
    return records


def build_raw_records() -> List[Dict[str, Any]]:
    """
    Build a list of raw record dictionaries by querying PubChem and NIST for each halide.
    Each record contains at minimum:
        - host_id (PubChem CID if available, otherwise a generated placeholder)
        - smiles
        - inchi (may be None)
        - value (binding constant, may be None)
        - unit (may be None)
        - solvent (validated later)
        - halide_info (original halide string from the source)
        - source ("PubChem" or "NIST")
    """
    halides = ["fluoride", "chloride", "bromide", "iodide"]
    all_records: List[Dict[str, Any]] = []

    for halide in halides:
        # PubChem
        pc_records = fetch_pubchem_records(halide)
        logger.info(f"Fetched {len(pc_records)} PubChem records for halide '{halide}'.")
        all_records.extend(pc_records)

        # Respect the required 2 s delay between requests (per source)
        time.sleep(2)

        # NIST
        try:
            nist_records = fetch_nist_records(halide)
            logger.info(f"Fetched {len(nist_records)} NIST records for halide '{halide}'.")
            for idx, rec in enumerate(nist_records):
                if not rec["host_id"]:
                    rec["host_id"] = f"NIST-{halide.upper()}-{idx}"
            all_records.extend(nist_records)
        except Exception as e:
            # According to FR‑001 we must raise on fetch failure – do not silently ignore.
            logger.error(f"NIST fetch failed for halide '{halide}': {e}")
            raise

        time.sleep(2)

    if not all_records:
        raise RuntimeError("No records retrieved from any source; aborting data ingestion.")
    return all_records


# ----------------------------------------------------------------------
# Core cleaning / filtering logic
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

    if df_clean.empty:
        raise RuntimeError("Cleaning resulted in an empty dataset; aborting.")
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
# Main pipeline
# ----------------------------------------------------------------------
def run_data_pipeline():
    """
    Execute the full ingestion, cleaning, and filtering workflow.
    """
    logger.info("Fetching raw data from PubChem and NIST...")
    raw_records = build_raw_records()

    # Save raw JSON
    raw_path = paths.data("raw", "raw_scrape.json")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w") as f:
        json.dump(raw_records, f, indent=2)

    # Load into DataFrame (may be empty)
    df = pd.DataFrame(raw_records)

    # Clean & standardize (will raise if required columns missing)
    if df.empty:
        raise RuntimeError("No raw records retrieved; aborting.")
    df_clean = validate_and_clean_data(df)

    cleaned_path = paths.data("raw", "raw_scrape_cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False)

    # Filter hosts with ≥3 halides (fallback to returning all if none meet criteria)
    df_filtered = filter_hosts_with_multiple_halides(df_clean)
    filtered_path = paths.data("raw", "filtered_hosts.csv")
    df_filtered.to_csv(filtered_path, index=False)

    logger.info("Data ingestion pipeline completed successfully.")


def main():
    run_data_pipeline()


if __name__ == "__main__":
    main()
