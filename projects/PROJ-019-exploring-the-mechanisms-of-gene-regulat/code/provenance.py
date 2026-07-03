"""
Provenance tracking for the gene regulation pipeline.
Records dataset sources, accession IDs, and download timestamps.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from code.config import DATA_PROCESSED_DIR

PROVENANCE_FILE = Path(DATA_PROCESSED_DIR) / "provenance.json"

def initialize_provenance() -> Dict[str, Any]:
    """
    Initialize a new provenance record.
    """
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
        "jaspar_version": None,
        "encode_accessions": {}
    }

def load_provenance() -> Dict[str, Any]:
    """
    Load existing provenance or initialize new if not found.
    """
    if PROVENANCE_FILE.exists():
        with open(PROVENANCE_FILE, 'r') as f:
            return json.load(f)
    return initialize_provenance()

def save_provenance(provenance: Optional[Dict[str, Any]] = None) -> None:
    """
    Save provenance to disk.
    """
    if provenance is None:
        provenance = load_provenance()
    
    # Ensure parent directory exists
    PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(PROVENANCE_FILE, 'w') as f:
        json.dump(provenance, f, indent=2)

def add_encode_accession(cell_type: str, accession: str, file_path: str) -> None:
    """
    Add an ENCODE accession ID to the provenance record.
    """
    provenance = load_provenance()
    
    if "encode_accessions" not in provenance:
        provenance["encode_accessions"] = {}
    
    provenance["encode_accessions"][cell_type] = {
        "accession": accession,
        "file_path": file_path,
        "downloaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    save_provenance(provenance)

def set_jaspar_version(version: str) -> None:
    """
    Set the JASPAR database version used.
    """
    provenance = load_provenance()
    provenance["jaspar_version"] = version
    provenance["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_provenance(provenance)

def get_provenance_report() -> Dict[str, Any]:
    """
    Generate a summary report of the provenance.
    """
    provenance = load_provenance()
    
    report = {
        "created_at": provenance.get("created_at"),
        "jaspar_version": provenance.get("jaspar_version"),
        "datasets": {},
        "total_encode_accessions": len(provenance.get("encode_accessions", {}))
    }
    
    for cell_type, info in provenance.get("encode_accessions", {}).items():
        report["datasets"][cell_type] = {
            "accession": info.get("accession"),
            "file_path": info.get("file_path"),
            "downloaded_at": info.get("downloaded_at")
        }
    
    return report
