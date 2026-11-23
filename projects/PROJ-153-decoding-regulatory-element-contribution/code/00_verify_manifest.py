import os
import sys
import json
import time
import re
from pathlib import Path
from urllib.request import urlopen, Request
import yaml

def check_ncbi_accession(accession):
    """
    Checks if an NCBI accession (GEO or SRA) is valid and NOT a placeholder.
    
    Rules:
    1. Must start with GSE, GSM, SRP, or SRR.
    2. Must NOT be a pattern like 'GSE####' where # is a digit (placeholder).
    3. Must NOT be 'GSE000000' or similar zero-filled placeholders.
    4. Performs a lightweight existence check via NCBI E-utilities if possible.
    
    Returns:
        tuple: (is_valid: bool, reason: str)
    """
    if not accession or not isinstance(accession, str):
        return False, "Accession is empty or not a string."
    
    accession = accession.strip()
    
    # Check for valid prefixes
    valid_prefixes = ("GSE", "GSM", "SRP", "SRR")
    if not any(accession.startswith(p) for p in valid_prefixes):
        return False, f"Invalid prefix. Must start with {valid_prefixes}."
    
    # Check for placeholder patterns (e.g., GSE1234, GSE####, GSE000000)
    # A placeholder is typically a generic pattern or a very low number often used in docs
    # We strictly reject if it looks like a template: GSE followed by 4 digits or fewer, 
    # or if it matches a regex of "GSE" + 4-5 digits that are likely placeholders in context.
    # However, the prompt specifically says "abort if any accession is a placeholder (e.g., GSE####)".
    # We interpret "GSE####" as a literal placeholder string or a pattern of generic digits.
    # Real accessions are usually GSE + 5-7 digits.
    
    # Regex to detect obvious placeholders: GSE followed by exactly 4 digits (common doc placeholder)
    # or a string containing "####"
    if "####" in accession:
        return False, "Accession contains placeholder pattern '####'."
    
    # Check for GSE followed by exactly 4 digits (often used as examples like GSE1234)
    # Real GEO series are typically GSE + 5 to 7 digits.
    match = re.match(r"^(GSE|GSM|SRP|SRR)(\d+)$", accession)
    if match:
        prefix, number = match.groups()
        if len(number) < 5:
            return False, f"Accession '{accession}' looks like a placeholder (too short, < 5 digits)."
        
        # Additional check: GSE000000, GSE00001, etc. are likely placeholders
        if int(number) == 0:
            return False, f"Accession '{accession}' is zero-filled placeholder."
    
    # Attempt to verify existence via NCBI E-utilities (ESummary)
    # This is a lightweight check to ensure the accession exists in the database.
    # We use a timeout to prevent hanging.
    try:
        db = "geo" if prefix in ("GSE", "GSM") else "sra"
        # Map prefix to DB
        if prefix.startswith("SR"):
            db = "sra"
            # For SRA, the ID is the accession number without prefix for some calls, 
            # but esummary accepts the accession.
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db={db}&id={accession}&retmode=json"
        else:
            # For GEO, the ID is the accession
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=geo&id={accession}&retmode=json"
        
        req = Request(url)
        req.add_header('User-Agent', 'llmXive-pipeline/1.0 (research-impl)')
        
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check if response contains an error or empty result
            if db == "sra":
                if 'result' not in data or accession not in data['result']:
                    return False, f"NCBI SRA returned no data for {accession}."
            else: # geo
                if 'result' not in data or accession not in data['result']:
                    return False, f"NCBI GEO returned no data for {accession}."
                
            # If we get here, the accession exists
            return True, "Accession verified via NCBI."
            
    except Exception as e:
        # If network fails, we might still consider it valid if format is perfect,
        # but the task says "abort if... missing".
        # If we can't reach NCBI, we can't confirm it's not missing.
        # However, for robustness in CI, we might want to be strict.
        # Given the instruction "abort if... missing", we should fail if we can't verify.
        # But if the format is valid and it's a real-looking accession, we might warn.
        # Strict interpretation: If we can't verify existence, we assume it might be missing.
        # However, a network error shouldn't necessarily kill the whole pipeline if the ID looks real.
        # Let's be strict: if we can't verify, we raise an error unless it's a known format.
        # Actually, the prompt says "abort if... missing". If we can't check, we don't know.
        # Best approach: If format is valid and length is correct, assume valid but log warning?
        # No, the task says "abort if... missing". We must be sure.
        # If network is down, we can't be sure. But typically, we assume the runner has internet.
        # Let's treat network failure as a fatal error for the verification step.
        return False, f"Could not verify accession via NCBI (network error): {e}"

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
    
    if len(manifest['datasets']) == 0:
        raise ValueError("Manifest 'datasets' list is empty.")
    
    errors = []
    for i, dataset in enumerate(manifest['datasets']):
        if 'accession' not in dataset:
            errors.append(f"Dataset at index {i} is missing 'accession'.")
            continue
        
        accession = dataset['accession']
        is_valid, reason = check_ncbi_accession(accession)
        
        if not is_valid:
            errors.append(f"Dataset at index {i} (Accession: {accession}) is invalid: {reason}")
        
        if 'type' not in dataset:
            errors.append(f"Dataset at index {i} is missing 'type'.")
    
    if errors:
        error_msg = "Manifest verification failed with the following errors:\n" + "\n".join(errors)
        raise ValueError(error_msg)
    
    return manifest

def main():
    if len(sys.argv) < 2:
        print("Usage: python 00_verify_manifest.py <manifest_path>")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    try:
        manifest = verify_manifest(manifest_path)
        print(f"Manifest verified successfully. Found {len(manifest['datasets'])} valid datasets.")
        return 0
    except Exception as e:
        print(f"Manifest verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())