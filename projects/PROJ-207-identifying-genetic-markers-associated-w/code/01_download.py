"""
Fetch genomic data from NCBI BioProject PRJNA566029 with SSL verification.

Implements FR-001: Data must be fetched from a verified source with SSL.
Halts with clear error on SSL failure unless fallback is explicitly configured.
"""
import os
import sys
import ssl
import argparse
from pathlib import Path
import requests
from typing import Optional

# Constants
PROJECT_ID = "PRJNA566029"
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov"
BIOPROJECT_API = f"{NCBI_BASE_URL}/nuccore"
OUTPUT_DIR = Path("data/raw")
FALLBACK_ENV = "NCBI_FALLBACK_TO_SYNTHETIC"

def check_ssl_verification() -> bool:
    """
    Attempt a basic SSL handshake with NCBI to verify SSL is working.
    Returns True if successful, False otherwise.
    """
    try:
        # Create a context that enforces SSL verification
        context = ssl.create_default_context()
        # Attempt to connect to NCBI
        with requests.get(BIOPROJECT_API, params={"term": PROJECT_ID}, 
                          verify=True, timeout=30, stream=True) as r:
            r.raise_for_status()
            return True
    except requests.exceptions.SSLError as e:
        print(f"ERROR: SSL verification failed when connecting to NCBI: {e}", file=sys.stderr)
        return False
    except requests.exceptions.RequestException as e:
        # Network errors (non-SSL) might still allow proceeding if fallback is set
        # but we strictly check SSL first.
        print(f"WARNING: Network error during SSL check: {e}", file=sys.stderr)
        return False

def fetch_biomaterial_list(project_id: str, output_dir: Path) -> Optional[Path]:
    """
    Fetch the list of available files for the BioProject.
    Returns the path to the downloaded manifest if successful.
    """
    # Construct the search for SRA run info or assembly files
    # We aim to get the run accession list which contains download URLs
    search_url = f"{NCBI_BASE_URL}/sra/sra-instant/redirect/ftp/sra"
    
    # For this implementation, we fetch the run metadata which lists the SRA files
    # NCBI SRA Toolkit 'prefetch' or 'fasterq-dump' usually requires the .sra files.
    # We will download the run info table which contains the FTP paths.
    run_info_url = "https://sra-download.ncbi.nlm.nih.gov/traces/sra05/06/SRA000001/ERR/ERR000001"
    
    # A more robust approach for Python without CLI tools:
    # Use the SRA Run Selector API or direct FTP listing if possible.
    # Here we attempt to fetch the RunInfo table from the project.
    
    api_url = "https://www.ncbi.nlm.nih.gov/sra/docs/submit-formats/"
    
    # Direct approach: Fetch the run list for the project via Entrez E-utilities
    # This requires the project to have SRA runs associated.
    entrez_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "sra",
        "term": f"{project_id}[BioProject]",
        "retmode": "json",
        "retmax": 1000
    }
    
    try:
        response = requests.get(entrez_url, params=params, verify=True, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
            print(f"ERROR: No SRA runs found for BioProject {project_id}", file=sys.stderr)
            return None
        
        run_ids = data["esearchresult"]["idlist"]
        if not run_ids:
            print(f"ERROR: No SRA runs found for BioProject {project_id}", file=sys.stderr)
            return None

        # Fetch run details to get FTP paths
        # We construct the URL to get the run info in a tabular format
        # NCBI provides a TSV for run info
        run_info_params = {
            "db": "sra",
            "id": ",".join(run_ids),
            "rettype": "runinfo",
            "retmode": "text"
        }
        run_info_resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", 
                                     params=run_info_params, verify=True, timeout=60)
        run_info_resp.raise_for_status()
        
        # Save the raw run info
        manifest_path = output_dir / f"{project_id}_run_info.tsv"
        with open(manifest_path, "w") as f:
            f.write(run_info_resp.text)
        
        print(f"Successfully downloaded run info manifest: {manifest_path}")
        return manifest_path

    except requests.exceptions.SSLError as e:
        print(f"CRITICAL: SSL verification failed during data fetch: {e}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch data from NCBI: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch data from NCBI BioProject PRJNA566029")
    parser.add_argument("--force-synthetic", action="store_true", 
                        help="Skip SSL check and proceed to synthetic path (for testing)")
    args = parser.parse_args()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Check SSL Verification
    if not args.force_synthetic:
        if not check_ssl_verification():
            fallback_config = os.environ.get(FALLBACK_ENV, "").lower()
            if fallback_config in ("1", "true", "yes"):
                print(f"SSL verification failed, but {FALLBACK_ENV} is set. Proceeding to synthetic path.")
                # In a real pipeline, this might trigger T009/T013 logic
                # For this task, we just signal the fallback state
                with open(OUTPUT_DIR / "download_status.txt", "w") as f:
                    f.write("FALLBACK_TO_SYNTHETIC\n")
                return 0
            else:
                print("CRITICAL: SSL verification failed and fallback is not configured. Halting pipeline.", file=sys.stderr)
                sys.exit(1)

    # 2. Fetch Data
    print(f"Fetching data for BioProject {PROJECT_ID}...")
    manifest = fetch_biomaterial_list(PROJECT_ID, OUTPUT_DIR)
    
    if manifest is None:
        print("ERROR: Failed to retrieve data manifest. Pipeline cannot proceed.", file=sys.stderr)
        sys.exit(1)

    # 3. Record success
    with open(OUTPUT_DIR / "download_status.txt", "w") as f:
        f.write("SUCCESS\n")
    
    print(f"Data fetch complete. Manifest saved to {manifest}")
    return 0

if __name__ == "__main__":
    sys.exit(main())