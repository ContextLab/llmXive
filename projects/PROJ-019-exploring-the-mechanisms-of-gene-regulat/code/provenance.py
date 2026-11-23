import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from code.config import DATA_PROCESSED_DIR

PROVENANCE_FILE = DATA_PROCESSED_DIR / "provenance.json"

def initialize_provenance() -> Dict[str, Any]:
    """Initialize a new provenance record."""
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "encode_accessions": [],
        "jaspar_version": None,
        "genome_build": None,
        "pipeline_version": "0.1.0"
    }

def load_provenance() -> Dict[str, Any]:
    """Load existing provenance or create new."""
    if PROVENANCE_FILE.exists():
        with open(PROVENANCE_FILE, 'r') as f:
            return json.load(f)
    return initialize_provenance()

def save_provenance(record: Dict[str, Any]) -> None:
    """Save provenance record to file."""
    PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROVENANCE_FILE, 'w') as f:
        json.dump(record, f, indent=2)

def add_encode_accession(record: Dict[str, Any], accession: str) -> None:
    """Add an ENCODE accession ID to the record."""
    if accession not in record["encode_accessions"]:
        record["encode_accessions"].append(accession)

def set_jaspar_version(record: Dict[str, Any], version: str) -> None:
    """Set the JASPAR database version."""
    record["jaspar_version"] = version

def get_provenance_report() -> Dict[str, Any]:
    """Get the current provenance report."""
    return load_provenance()
