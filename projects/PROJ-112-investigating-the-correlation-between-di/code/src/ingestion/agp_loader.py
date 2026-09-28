import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

from src.utils.logger import get_logger

def get_project_root() -> Path:
    """Returns the project root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback if .git not found (common in CI/Docker)
    return Path(__file__).resolve().parents[3]

def verify_url(url: str) -> bool:
    """
    Verifies that a URL is reachable.
    In a real implementation, this would perform a HEAD request.
    For this implementation, we assume the URL is valid if it starts with http.
    """
    return url.startswith("http")

def ensure_qiita_token() -> str:
    """
    Ensures that the QIITA API token is present in the environment.
    Raises RuntimeError if not found.
    """
    token = os.getenv("QIITA_API_TOKEN")
    if not token:
        raise RuntimeError(
            "QIITA_API_TOKEN environment variable is not set. "
            "Please set it to access the Qiita API."
        )
    return token

def calculate_file_checksum(file_path: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksum(file_path: Path, checksum: str, state_file: Path) -> None:
    """Records the checksum of a file in the state/artifact_hashes.json."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if state_file.exists():
        with open(state_file, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[file_path.name] = checksum

    with open(state_file, "w") as f:
        json.dump(data, f, indent=2)

def fetch_sample_mapping(otu_table_id: str) -> pd.DataFrame:
    """
    Fetches the sample mapping (metadata) for a given OTU table ID from Qiita.
    This is a placeholder for the actual API call logic.
    """
    # In a real implementation, this would use requests to fetch from Qiita
    # For now, we assume the raw file is already downloaded and parse it locally
    # as per the task flow where T012 downloads the raw file first.
    raise NotImplementedError(
        "Direct API fetching is not implemented. "
        "This function assumes T012 has downloaded the raw TSV."
    )

def fetch_otu_table(otu_table_id: str) -> pd.DataFrame:
    """
    Fetches the OTU table (taxon abundance) for a given OTU table ID from Qiita.
    """
    raise NotImplementedError(
        "Direct API fetching is not implemented. "
        "This function assumes T012 has downloaded the raw TSV."
    )

def fetch_agp_data(otu_table_id: str, output_path: Path) -> None:
    """
    Fetches AGP data and writes it to output_path.
    This function is expected to be called by the ingestion pipeline.
    """
    raise NotImplementedError(
        "Direct API fetching is not implemented. "
        "This function assumes T012 has downloaded the raw TSV."
    )

def parse_agp_raw(
    raw_file_path: Path,
    output_taxa_path: Path,
    output_metadata_path: Path,
    logger: logging.Logger,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parses the downloaded raw AGP TSV file to separate taxon abundance matrix and metadata.
    
    FR-001 Requirement:
    - Extract 16S rRNA amplicon tables (Taxa)
    - Extract metadata fields (Sample Metadata)
    
    The raw file is expected to be a wide-format TSV where:
    - Rows are samples
    - Columns are: sample_id, metadata_cols..., taxon_cols...
    
    We distinguish columns by naming convention or position.
    Typically, taxon columns start with 'OTU_' or contain taxonomic strings.
    Metadata columns are non-numeric or have specific prefixes.
    
    This implementation assumes a standard AGP format where:
    - The first column is 'sample_id'
    - Columns starting with 'OTU_' are taxon abundances.
    - All other columns are metadata.
    
    Args:
        raw_file_path: Path to the raw downloaded TSV.
        output_taxa_path: Path to save the taxon abundance matrix.
        output_metadata_path: Path to save the metadata.
        logger: Logger instance.
    
    Returns:
        Tuple of (taxa_df, metadata_df)
    """
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Raw AGP file not found: {raw_file_path}")

    logger.info(f"Parsing AGP raw data from {raw_file_path}")

    # Read the raw file
    # AGP data is often large, so we might need chunking, but for parsing structure
    # we assume it fits in memory or use dask if needed. Here we use pandas.
    try:
        df = pd.read_csv(raw_file_path, sep="\t", low_memory=False)
    except Exception as e:
        raise RuntimeError(f"Failed to read raw AGP file: {e}")

    if df.empty:
        raise ValueError("Raw AGP file is empty.")

    # Identify Taxon Columns
    # Heuristic: Columns starting with 'OTU_' or containing '.' (taxonomy)
    # In AGP, OTU tables usually have columns like 'OTU_1', 'OTU_2', etc.
    taxon_columns = [col for col in df.columns if col.startswith("OTU_")]
    
    if not taxon_columns:
        # Fallback: Try to detect numeric columns that are not metadata
        # This is risky, so we log a warning.
        logger.warning("No columns starting with 'OTU_' found. Attempting numeric detection.")
        # Assume first col is ID, rest are data? No, too risky.
        raise ValueError(
            "Could not identify taxon columns. Expected columns starting with 'OTU_'."
        )

    # Identify Metadata Columns
    # Everything else except the ID column and taxon columns
    id_col = "sample_id"
    if id_col not in df.columns:
        # Try to find a column named 'sample_id' case-insensitively
        matching_cols = [c for c in df.columns if c.lower() == "sample_id"]
        if matching_cols:
            id_col = matching_cols[0]
        else:
            raise ValueError("Could not find 'sample_id' column.")

    metadata_columns = [col for col in df.columns if col not in taxon_columns and col != id_col]

    # Split DataFrames
    taxa_df = df[[id_col] + taxon_columns].copy()
    metadata_df = df[[id_col] + metadata_columns].copy()

    # Ensure ID is the index for easier joining later, or keep as column
    # For now, keep as column to match typical "wide" format expectations
    taxa_df = taxa_df.set_index(id_col)
    metadata_df = metadata_df.set_index(id_col)

    # Validate Data
    # Check for non-numeric values in taxa (should be counts)
    # We can't easily validate all rows without converting, but we can check dtypes
    # Convert to numeric, coercing errors to NaN (which we might want to drop later)
    for col in taxon_columns:
        taxa_df[col] = pd.to_numeric(taxa_df[col], errors="coerce")
    
    # Drop rows with NaN in taxon columns? Or fill with 0?
    # Usually, 0 is appropriate for missing OTU counts.
    taxa_df = taxa_df.fillna(0)

    # Write outputs
    output_taxa_path.parent.mkdir(parents=True, exist_ok=True)
    output_metadata_path.parent.mkdir(parents=True, exist_ok=True)

    taxa_df.to_csv(output_taxa_path, sep="\t")
    metadata_df.to_csv(output_metadata_path, sep="\t")

    logger.info(f"Saved taxon abundance matrix to {output_taxa_path}")
    logger.info(f"Saved metadata to {output_metadata_path}")
    logger.info(f"Found {len(taxon_columns)} taxa and {len(metadata_columns)} metadata columns.")

    return taxa_df.reset_index(), metadata_df.reset_index()

def run_agp_parsing(
    raw_file_path: Path,
    output_taxa_path: Path,
    output_metadata_path: Path,
    logger: Optional[logging.Logger] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Wrapper to run the AGP parsing logic.
    """
    if logger is None:
        logger = get_logger("agp_loader")
    
    return parse_agp_raw(raw_file_path, output_taxa_path, output_metadata_path, logger)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse AGP raw data into taxa and metadata.")
    parser.add_argument(
        "--raw-file",
        type=Path,
        required=True,
        help="Path to the raw AGP TSV file downloaded by T012.",
    )
    parser.add_argument(
        "--output-taxa",
        type=Path,
        required=True,
        help="Path to save the taxon abundance matrix.",
    )
    parser.add_argument(
        "--output-metadata",
        type=Path,
        required=True,
        help="Path to save the metadata.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    logger = get_logger("agp_loader")
    logger.setLevel(getattr(logging, args.log_level))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    try:
        run_agp_parsing(
            raw_file_path=args.raw_file,
            output_taxa_path=args.output_taxa,
            output_metadata_path=args.output_metadata,
            logger=logger,
        )
        logger.info("AGP parsing completed successfully.")
    except Exception as e:
        logger.error(f"AGP parsing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()