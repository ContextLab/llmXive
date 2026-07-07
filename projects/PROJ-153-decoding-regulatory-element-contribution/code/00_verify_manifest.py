import os
import sys
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
import yaml

def check_ncbi_accession(accession_id):
    """
    Checks if an accession ID exists in NCBI E-utilities.
    Returns True if found, False otherwise.
    """
    if not accession_id:
        return False
    
    # Use E-utilities esearch to check existence
    # Database: sra or gds
    # We try 'sra' first, then 'gds' or 'geo'
    databases = ['sra', 'gds', 'geo']
    
    for db in databases:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={db}&term={accession_id}[Accession]&retmode=json&retmax=1"
        try:
            req = Request(url, headers={'User-Agent': 'llmXive-pipeline/1.0'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'result' in data and 'ids' in data['result']:
                    if len(data['result']['ids']) > 0:
                        return True
        except Exception:
            continue
    
    return False

def verify_manifest(manifest_path):
    """
    Loads the manifest.yaml and verifies all SRA/GEO accessions.
    Returns (is_valid, error_message)
    """
    if not os.path.exists(manifest_path):
        return False, f"Manifest file not found: {manifest_path}"
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        return False, f"Failed to parse manifest.yaml: {e}"
    
    if 'datasets' not in manifest:
        return False, "Manifest missing 'datasets' key"
    
    errors = []
    verified_count = 0
    total_count = 0

    print(f"Verifying {len(manifest['datasets'])} datasets...")

    for dataset in manifest['datasets']:
        dataset_type = dataset.get('type', 'Unknown')
        study_acc = dataset.get('study_accession', '')
        runs = dataset.get('runs', [])
        
        # Verify Study Accession
        if study_acc:
            total_count += 1
            if check_ncbi_accession(study_acc):
                print(f"  [OK] Study {study_acc} ({dataset_type})")
                verified_count += 1
            else:
                errors.append(f"Study accession {study_acc} ({dataset_type}) not found in NCBI.")
        
        # Verify Run Accessions (SRA)
        for run in runs:
            sra_id = run.get('sra', '')
            if sra_id:
                total_count += 1
                if check_ncbi_accession(sra_id):
                    print(f"  [OK] Run {sra_id} ({dataset_type})")
                    verified_count += 1
                else:
                    errors.append(f"SRA Run {sra_id} ({dataset_type}) not found in NCBI.")
    
    if errors:
        return False, "\n".join(errors)
    
    print(f"Verification complete: {verified_count}/{total_count} accessions verified.")
    return True, "All accessions verified successfully."

def main():
    manifest_path = Path(__file__).parent / "manifest.yaml"
    if not manifest_path.exists():
        print("ERROR: manifest.yaml not found in code/ directory.")
        sys.exit(1)
    
    is_valid, message = verify_manifest(str(manifest_path))
    
    if not is_valid:
        print("\nCRITICAL ERROR: Manifest verification failed.")
        print(message)
        print("\nThe pipeline must abort because data integrity (FR-001) cannot be guaranteed.")
        sys.exit(1)
    else:
        print("\nManifest verification passed. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
