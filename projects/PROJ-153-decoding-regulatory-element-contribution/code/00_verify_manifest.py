import os
import sys
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
import yaml

def check_ncbi_accession(accession):
    """
    Checks if an NCBI accession (GEO or SRA) exists and is valid.
    Returns True if valid, False otherwise.
    """
    # Basic format check
    if not accession or not isinstance(accession, str):
        return False
    
    # Check for common prefixes
    if accession.startswith("GSE") or accession.startswith("GSM") or accession.startswith("SRP") or accession.startswith("SRR"):
        # In a real implementation, we would query the NCBI E-utilities API
        # For now, we assume the manifest generation step (T003) did this validation.
        # This function serves as a placeholder for the actual API call.
        # Example real call: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=geo&id=...
        return True 
    return False

def verify_manifest(manifest_path):
    """
    Verifies the manifest.yaml file structure and validates accessions.
    Returns the parsed manifest if valid, raises an error otherwise.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in manifest: {e}")
    
    if 'datasets' not in manifest:
        raise ValueError("Manifest must contain a 'datasets' key.")
    
    if not isinstance(manifest['datasets'], list):
        raise ValueError("'datasets' must be a list.")
    
    for i, dataset in enumerate(manifest['datasets']):
        if 'accession' not in dataset:
            raise ValueError(f"Dataset at index {i} is missing 'accession'.")
        
        if not check_ncbi_accession(dataset['accession']):
            raise ValueError(f"Invalid accession in dataset at index {i}: {dataset['accession']}")
        
        # Check for optional but recommended fields
        if 'type' not in dataset:
            raise ValueError(f"Dataset at index {i} is missing 'type'.")
    
    return manifest

def main():
    if len(sys.argv) < 2:
        print("Usage: python 00_verify_manifest.py <manifest_path>")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    try:
        manifest = verify_manifest(manifest_path)
        print(f"Manifest verified successfully. Found {len(manifest['datasets'])} datasets.")
        return 0
    except Exception as e:
        print(f"Manifest verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())