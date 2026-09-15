import os
import sys
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import requests
from chemparse import parse_formula

# Project imports
from config import get_config_value, initialize_config
from logger import setup_citation_logger
from contracts.schemas import CeramicEntry

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Setup specific logger for URL verification
def setup_url_verification_logger():
    logger = logging.getLogger("url_verification")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOGS_DIR / "url_verification.log")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

url_verification_logger = setup_url_verification_logger()

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/models",
        "data/results",
        "data/reports",
        "logs",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def validate_url_reachability(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Check if a URL is reachable and returns a 200 OK status.
    Returns (is_reachable, status_message).
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, f"URL reachable: {response.status_code}"
        else:
            return False, f"URL returned status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def validate_source_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate source citations (URLs/DOIs) against primary sources.
    Logs failures to logs/citation_validation.log.
    """
    logger = setup_citation_logger()
    valid_citations = []
    for citation in citations:
        url = citation.get("url") or citation.get("doi")
        if not url:
            logger.warning(f"Citation missing URL/DOI: {citation}")
            continue

        is_reachable, message = validate_url_reachability(url)
        if is_reachable:
            logger.info(f"Citation validation for {url}: {message}")
            valid_citations.append(citation)
        else:
            logger.warning(f"Citation validation for {url}: {message}")
    return valid_citations

def verify_nist_url(url: str = None) -> bool:
    """
    Verify the reachability of the NIST Ceramic Data repository URL.
    Uses requests to check status code 200.
    Logs result to logs/url_verification.log.
    Returns True if reachable, False otherwise.
    """
    if url is None:
        # Default NIST Materials Data API endpoint or landing page
        url = "https://materialsdata.nist.gov/bitstream/handle/11115/209/CeramicReliabilityData.csv"
    
    is_reachable, message = validate_url_reachability(url)
    
    if is_reachable:
        url_verification_logger.info(f"NIST URL verification for {url}: SUCCESS - {message}")
    else:
        url_verification_logger.warning(f"NIST URL verification for {url}: FAILED - {message}")
    
    return is_reachable

def derive_primary_anion_cation_group(composition: str) -> str:
    """
    Parse composition string to identify primary anion and cation groups.
    Example: 'Al2O3' -> 'O-Al' (Anion-Cation order)
    """
    try:
        parsed = parse_formula(composition)
        elements = list(parsed.keys())
        if len(elements) < 2:
            return "Unknown"
        
        # Simple heuristic: assume last element is anion (common for oxides/nitrides)
        # In reality, this needs a more robust chemistry parser, but for now:
        anion = elements[-1]
        cation = elements[0]
        
        # Map element symbols to group names (simplified)
        # This is a placeholder; a full implementation would use periodictable
        return f"{anion}-{cation}"
    except Exception as e:
        logging.warning(f"Failed to parse composition {composition}: {e}")
        return "Unknown"

def validate_entry(entry: Dict[str, Any]) -> bool:
    """Validate a single ceramic entry against the CeramicEntry schema."""
    try:
        CeramicEntry(**entry)
        return True
    except Exception as e:
        logging.warning(f"Invalid entry: {e}")
        return False

def validate_no_missing_primary_predictors(df: pd.DataFrame) -> bool:
    """
    Validate that essential descriptors have no missing values.
    Returns True if all primary predictors are present.
    """
    primary_predictors = [
        "mean_atomic_radius",
        "electronegativity_std",
        "valence_electron_concentration",
        "cation_size_variance",
    ]
    for col in primary_predictors:
        if col not in df.columns:
            logging.error(f"Missing primary predictor column: {col}")
            return False
        if df[col].isnull().any():
            logging.error(f"Missing values in primary predictor: {col}")
            return False
    return True

def flag_high_variance_ranges(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Exclude entries where range width exceeds threshold (e.g., > 50% of midpoint).
    Assumes 'range_original' and 'weibull_modulus' (midpoint) exist.
    """
    if "range_original" not in df.columns or "weibull_modulus" not in df.columns:
        logging.warning("Range columns not found; skipping high-variance filtering.")
        return df

    # Extract range width if stored as a tuple or string
    # Placeholder logic: assumes 'range_original' is a string like "10-20"
    def get_range_width(val):
        if pd.isna(val):
            return 0
        if isinstance(val, str) and "-" in val:
            try:
                parts = val.split("-")
                return float(parts[1]) - float(parts[0])
            except:
                return 0
        return 0

    df["range_width"] = df["range_original"].apply(get_range_width)
    df["midpoint"] = df["weibull_modulus"]
    
    # Filter out rows where width > threshold * midpoint
    mask = df["range_width"] <= (threshold * df["midpoint"])
    return df[mask].copy()

def generate_data_availability_report(count: int, path: str = "data/reports/data_availability_report.json"):
    """
    Generate a JSON report on data availability.
    """
    report = {
        "total_entries": count,
        "status": "insufficient" if count < 30 else "sufficient",
        "message": f"Total entries: {count}. {'Insufficient for power analysis (N < 30).' if count < 30 else 'Sufficient for analysis.'}"
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return path

def validate_data_gap(count: int):
    """
    Validate data gap: if count < 30, generate report and exit.
    If 30 <= count < 50, log warning.
    """
    if count < 30:
        report_path = generate_data_availability_report(count)
        print(f"Power Limitation: Insufficient data (N < 30). Report: {report_path}", file=sys.stderr)
        sys.exit(1)
    elif count < 50:
        logging.warning(f"Small dataset (30 <= N < 50). Hold-out validation will be used.")

def main():
    """Main entry point for ingestion script."""
    initialize_config()
    ensure_output_dirs()

    # Example: Verify NIST URL
    nist_url = "https://materialsdata.nist.gov/bitstream/handle/11115/209/CeramicReliabilityData.csv"
    is_ok = verify_nist_url(nist_url)
    if not is_ok:
        logging.error("NIST URL verification failed. Cannot proceed with data fetch.")
        sys.exit(1)

    # Additional ingestion logic would go here...
    print("Ingestion pipeline initialized successfully.")

if __name__ == "__main__":
    main()