import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sklearn.datasets import fetch_openml

from llmxive_toolkit import paths, get_logger
from config.loader import load_schema_map

# Import optional HuggingFace datasets library; will raise if not installed
try:
    from datasets import load_dataset
except ImportError as e:
    load_dataset = None  # type: ignore

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
RESEARCH_MD_PATH = Path("specs/001-predicting-the-impact-of-laser-surface-t/research.md")
REQUIRED_COLUMNS = [
    "pulse_duration",
    "power",
    "scanning_speed",
    "wear_rate",
]

MERGED_CSV_PATH = paths.data("intermediate", "merged.csv")
SOURCE_VALIDATION_JSON_PATH = paths.results("source_validation.json")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _parse_research_md(md_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the research.md file and extract a list of source dictionaries.
    Each dictionary contains: name, type, verified, url (optional), dataset_id (optional), notes.
    """
    if not md_path.exists():
        raise FileNotFoundError(f"research.md not found at {md_path}")

    sources: List[Dict[str, Any]] = []
    with md_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the table header line (contains "Source Name")
    table_started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "Source Name" in stripped:
            table_started = True
            continue
        if table_started:
            # End of table when a line without leading '|' appears
            if not stripped.startswith("|"):
                break
            # Split columns; the first and last are empty due to leading/trailing '|'
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if len(parts) != 5:
                continue  # malformed line; skip
            name, src_type, verified, url_id, notes = parts
            # Clean URL/ID field – may contain <br> separated entries
            url = None
            dataset_id = None
            for sub in url_id.split("<br>"):
                sub = sub.strip()
                if sub.startswith("http"):
                    url = sub
                elif sub.lower().startswith("dataset id:"):
                    dataset_id = sub.split(":", 1)[1].strip()
            sources.append(
                {
                    "name": name,
                    "type": src_type,
                    "verified": verified.lower() == "true",
                    "url": url,
                    "dataset_id": dataset_id,
                    "notes": notes,
                }
            )
    return sources

def _download_openml(dataset_id: str) -> pd.DataFrame:
    """
    Download a dataset from OpenML given its numeric ID.
    Returns a pandas DataFrame.
    """
    logger.info(f"Fetching OpenML dataset id={dataset_id}")
    try:
        result = fetch_openml(data_id=int(dataset_id), as_frame=True)
        df = result.frame
        if df is None:
            raise RuntimeError(f"OpenML returned no DataFrame for id {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        raise

def _download_huggingface(dataset_id: str) -> pd.DataFrame:
    """
    Download a HuggingFace dataset given its repo identifier.
    Returns a pandas DataFrame constructed from the 'train' split (or first split).
    """
    if load_dataset is None:
        raise ImportError(
            "HuggingFace 'datasets' library is not installed. Install it to fetch HF datasets."
        )
    logger.info(f"Fetching HuggingFace dataset id={dataset_id}")
    try:
        ds = load_dataset(dataset_id, split="train")
        df = pd.DataFrame(ds)
        return df
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace dataset {dataset_id}: {e}")
        raise

def _download_raw_csv(url: str) -> pd.DataFrame:
    """
    Download a raw CSV file from a URL using pandas.read_csv.
    """
    logger.info(f"Downloading raw CSV from {url}")
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        logger.error(f"Failed to download CSV from {url}: {e}")
        raise

def _apply_schema_mapping(df: pd.DataFrame, schema_map: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Rename columns in df according to schema_map.
    schema_map maps canonical column name -> list of possible source column names.
    The first matching source column is renamed to the canonical name.
    """
    rename_dict: Dict[str, str] = {}
    existing_cols = set(df.columns)
    for canonical, aliases in schema_map.items():
        for alias in aliases:
            if alias in existing_cols:
                rename_dict[alias] = canonical
                break
    if rename_dict:
        logger.info(f"Renaming columns: {rename_dict}")
        df = df.rename(columns=rename_dict)
    return df

def _resolve_source_dataframe(src: Dict[str, Any]) -> pd.DataFrame:
    """
    Determine the appropriate download method for a source entry and return the DataFrame.
    This function now recognises local CSV paths (either via `url` or `dataset_id` that
    correspond to a file under `data/raw/`) and treats them as raw CSVs.
    """
    name = src["name"]
    src_type = src["type"].lower()
    url = src.get("url")
    dataset_id = src.get("dataset_id")

    logger.info(f"Resolving source '{name}' (type={src_type})")

    # Helper to check if a string points to an existing file
    def _is_existing_file(path_str: str) -> bool:
        if not path_str:
            return False
        p = Path(path_str)
        return p.is_file()

    # 1. Direct CSV URL or local file
    if src_type == "tabular" and url:
        # If the URL looks like an HTTP URL, use pandas read_csv over the web.
        # Otherwise, treat it as a local path.
        if url.lower().startswith("http"):
            return _download_raw_csv(url)
        elif _is_existing_file(url):
            return _download_raw_csv(url)
        else:
            logger.error(f"URL for source '{name}' does not point to an existing file: {url}")
            raise FileNotFoundError(f"CSV file not found for source '{name}' at {url}")

    # 2. Dataset ID that points to a local CSV under data/raw/
    if dataset_id:
        # Try OpenML if the ID is numeric
        if dataset_id.isdigit():
            return _download_openml(dataset_id)
        # Check for a local CSV file named <dataset_id>.csv inside data/raw/
        local_path = Path("data") / "raw" / f"{dataset_id}.csv"
        if local_path.is_file():
            return _download_raw_csv(str(local_path))
        # Fallback to HuggingFace loader
        return _download_huggingface(dataset_id)

    # If we reach this point, we cannot resolve the source.
    raise RuntimeError(f"Unable to resolve source '{name}'. No valid URL or dataset_id provided.")

def fetch_sources() -> None:
    """
    Core implementation for T002.
    - Reads static sources from research.md.
    - Downloads each source (real data only).
    - Applies schema mapping from schema_map.json.
    - Concatenates all sources, adds a 'source_id' column.
    - Validates presence of required LST columns; aborts loudly if missing.
    - Writes merged.csv and source_validation.json.
    """
    logger.info("Starting fetch_sources")
    sources = _parse_research_md(RESEARCH_MD_PATH)
    if len(sources) < 1:
        logger.error("No data sources defined in research.md")
        raise RuntimeError("data_schema_mismatch: no sources defined")

    data_frames: List[pd.DataFrame] = []
    source_ids: List[str] = []

    for src in sources:
        name = src["name"]
        logger.info(f"Processing source '{name}'")
        df = _resolve_source_dataframe(src)

        # Load schema map and rename columns
        schema_map = load_schema_map()
        df = _apply_schema_mapping(df, schema_map)

        # Add source identifier column
        df["source_id"] = name
        data_frames.append(df)
        source_ids.append(name)

    if not data_frames:
        logger.error("No usable data frames were loaded from any source.")
        raise RuntimeError("data_schema_mismatch: no usable sources")

    # Concatenate all sources
    merged_df = pd.concat(data_frames, ignore_index=True, sort=False)

    # Validate required columns
    missing_required = [col for col in REQUIRED_COLUMNS if col not in merged_df.columns]
    if missing_required:
        logger.error(f"Missing required columns after merging: {missing_required}")
        raise RuntimeError(
            f"data_schema_mismatch: required columns missing {missing_required}"
        )

    # Ensure output directories exist
    MERGED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_VALIDATION_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write merged CSV
    merged_df.to_csv(MERGED_CSV_PATH, index=False)
    logger.info(f"Merged dataset written to {MERGED_CSV_PATH}")

    # Prepare source validation JSON
    validation: Dict[str, Any] = {
        "source_count": len(source_ids),
        "source_ids": source_ids,
        "warnings": [],
    }
    if len(source_ids) < 3:
        validation["warnings"].append("data_source_limitation")
        logger.warning(
            f"Only {len(source_ids)} distinct sources found; <3 triggers warning."
        )
    # Write validation JSON
    with SOURCE_VALIDATION_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)
    logger.info(f"Source validation written to {SOURCE_VALIDATION_JSON_PATH}")

def main() -> int:
    """
    Entry point for the ingestion subcommand.
    Returns an exit code compatible with the pipeline conventions.
    """
    try:
        fetch_sources()
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        # Propagate failure with non‑zero exit code
        return 1

if __name__ == "__main__":
    sys.exit(main())
