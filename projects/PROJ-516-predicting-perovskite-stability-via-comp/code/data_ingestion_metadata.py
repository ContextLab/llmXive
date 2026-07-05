import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_uncertainty(uncertainty_str: Optional[str]) -> Dict[str, Any]:
    """
    Parse uncertainty string (e.g., '±5°C', '±10°C', '5') into a structured object.
    Returns a dict with 'value' (float) and 'unit' (str).
    If parsing fails or input is None, returns default uncertainty (10.0, '°C').
    """
    if not uncertainty_str:
        return {"value": 10.0, "unit": "°C", "source": "default"}

    # Clean and extract number
    cleaned = str(uncertainty_str).replace("±", "").replace("°C", "").replace("°", "").strip()
    match = re.search(r"([\d.]+)", cleaned)

    if match:
        try:
            val = float(match.group(1))
            return {"value": val, "unit": "°C", "source": "parsed"}
        except ValueError:
            logger.warning(f"Could not parse numeric value from: {uncertainty_str}")
            return {"value": 10.0, "unit": "°C", "source": "default"}

    logger.warning(f"Could not extract uncertainty from: {uncertainty_str}")
    return {"value": 10.0, "unit": "°C", "source": "default"}


def extract_instrument_model(metadata_field: Optional[str]) -> str:
    """
    Extract instrument model from metadata string.
    Looks for patterns like 'TGA Q500', 'STA 449', etc.
    Returns 'unknown' if not found.
    """
    if not metadata_field:
        return "unknown"

    # Common TGA instrument patterns
    patterns = [
        r"(TGA\s+\w+)",
        r"(STA\s+\w+)",
        r"(SDT\s+\w+)",
        r"(Pyris\s+\w+)",
        r"(Q\d+)",
        r"(449\s+\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, metadata_field, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return "unknown"


def process_metadata_entries(
    df: pd.DataFrame,
    metadata_col: str = "instrument_metadata",
    uncertainty_col: str = "uncertainty"
) -> List[Dict[str, Any]]:
    """
    Process a DataFrame of perovskite entries to extract structured metadata.
    Returns a list of dictionaries adhering to contracts/metadata.schema.yaml.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return []

    processed = []
    for idx, row in df.iterrows():
        entry = {
            "entry_id": row.get("entry_id", f"unknown_{idx}"),
            "formula": row.get("formula", "unknown"),
            "T_d": float(row.get("T_d", 0.0)),
            "instrument_model": extract_instrument_model(row.get(metadata_col)),
            "uncertainty": parse_uncertainty(row.get(uncertainty_col)),
            "source_citation": row.get("source_citation", "unknown"),
            "validated": bool(row.get("validated", False))
        }
        processed.append(entry)

    return processed


def main():
    """
    Main entry point for T013b: Write parsed instrumentation metadata to data/raw/metadata.json.
    Reads from data/raw/nrel_perovskites.csv (output of T012) and writes to data/raw/metadata.json.
    """
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "raw" / "nrel_perovskites.csv"
    output_path = project_root / "data" / "raw" / "metadata.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T012 (data_ingestion.py) first to generate the input CSV.")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading input from: {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Processing {len(df)} entries...")
    metadata_entries = process_metadata_entries(df)

    logger.info(f"Writing {len(metadata_entries)} entries to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata_entries, f, indent=2)

    logger.info("Metadata extraction complete.")


if __name__ == "__main__":
    main()
