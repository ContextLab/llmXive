"""
NCBI Metadata Fetcher for Honeybee CCD Study.

Fetches metadata ONLY from NCBI BioProject PRJNA639195 (CCD) and PRJNA566029 (Healthy)
to determine sample size and Varroa coverage. Does NOT download FASTQ files.

Implements FR-001: Data Source Verification and FR-012: Power Analysis Input.
"""
import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Constants
CCD_PROJECT = "PRJNA639195"
HEALTHY_PROJECT = "PRJNA566029"
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "ncbi_metadata_only.json"
FETCH_LOG = OUTPUT_DIR / "ncbi_fetch_log.json"

# Error codes
ERR_SAMPLE_SIZE_INSUFFICIENT = "ERR_SAMPLE_SIZE_INSUFFICIENT"
SSL_VERIFY_FAILED = "SSL Verification Failed"

def check_ssl_verification() -> bool:
    """
    Validates SSL certificates using a verified CA bundle.
    Returns True if verification passes, False otherwise.
    """
    try:
        # Use certifi bundle for consistent SSL verification
        import ssl
        import certifi
        
        context = ssl.create_default_context(cafile=certifi.where())
        # Test connection to NCBI
        with context.wrap_socket(__import__('socket').create_connection(("eutils.ncbi.nlm.nih.gov", 443)), server_hostname="eutils.ncbi.nlm.nih.gov") as sock:
            return True
    except Exception as e:
        print(f"SSL Verification Failed: {e}", file=sys.stderr)
        return False

def fetch_project_metadata(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a specific BioProject using entrez-direct (efetch).
    Returns parsed JSON metadata or None on failure.
    """
    # First, get SRA accessions for this BioProject
    esearch_cmd = [
        "esearch", "-db", "sra", "-query", f"{project_id}[BioProject]"
    ]
    
    try:
        # Run esearch to get accession IDs
        search_result = subprocess.run(
            esearch_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        # Parse the XML to get IDs (simplified: assume esearch returns ID list)
        # In practice, we might need to parse XML or use -format tab
        id_list_cmd = [
            "xtract", "-pattern", "Id", "-element", "Id"
        ]
        id_result = subprocess.run(
            id_list_cmd,
            input=search_result.stdout,
            capture_output=True,
            text=True,
            check=True
        )
        
        accession_ids = id_result.stdout.strip().split('\n')
        if not accession_ids or (len(accession_ids) == 1 and not accession_ids[0]):
            print(f"No SRA accessions found for {project_id}", file=sys.stderr)
            return None
        
        # Fetch detailed metadata for each accession
        all_metadata = []
        for acc in accession_ids:
            efetch_cmd = [
                "efetch", "-db", "sra", "-id", acc, "-format", "json"
            ]
            try:
                fetch_result = subprocess.run(
                    efetch_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60
                )
                meta = json.loads(fetch_result.stdout)
                all_metadata.append(meta)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to fetch metadata for {acc}: {e}", file=sys.stderr)
                continue
        
        return {
            "project_id": project_id,
            "accession_count": len(all_metadata),
            "accessions": all_metadata
        }
        
    except subprocess.TimeoutExpired:
        print(f"Timeout fetching metadata for {project_id}", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error fetching metadata for {project_id}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error fetching {project_id}: {e}", file=sys.stderr)
        return None

def extract_sample_info(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant sample information from fetched metadata.
    """
    samples = []
    project_id = metadata.get("project_id", "Unknown")
    
    for accession_data in metadata.get("accessions", []):
        # Navigate the JSON structure to find sample info
        # This structure varies by NCBI response, so we handle common patterns
        run_info = accession_data.get("runs", {}).get("run", [])
        if isinstance(run_info, dict):
            run_info = [run_info]
        
        for run in run_info:
            sample_ref = run.get("attributes", {})
            if isinstance(sample_ref, list):
                # Convert list of dicts to dict if needed
                attrs = {}
                for item in sample_ref:
                    if isinstance(item, dict):
                        key = item.get("tag", "")
                        val = item.get("value", "")
                        attrs[key] = val
                sample_ref = attrs
            
            sample_info = {
                "accession": run.get("accession", "Unknown"),
                "instrument_platform": run.get("model", "Unknown"),
                "ccd_status": sample_ref.get("ccd_status", "Unknown"),
                "varroa_load": sample_ref.get("varroa_load", "Unknown"),
                "geographic_region": sample_ref.get("geographic_region", "Unknown"),
                "library_strategy": run.get("library_strategy", "WGS")
            }
            samples.append(sample_info)
    
    return samples

def validate_ccd_criteria(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Validate samples against CCD criteria (FR-011).
    Returns counts of valid CCD, valid Healthy, and ambiguous samples.
    """
    ccd_count = 0
    healthy_count = 0
    ambiguous_count = 0
    
    for sample in samples:
        status = sample.get("ccd_status", "").lower()
        if status in ["ccd", "colony collapse", "cccd"]:
            ccd_count += 1
        elif status in ["healthy", "control", "normal"]:
            healthy_count += 1
        else:
            ambiguous_count += 1
    
    return {
        "ccd": ccd_count,
        "healthy": healthy_count,
        "ambiguous": ambiguous_count,
        "total": len(samples)
    }

def calculate_varroa_coverage(samples: List[Dict[str, Any]]) -> float:
    """
    Calculate the percentage of samples with Varroa data.
    """
    if not samples:
        return 0.0
    
    with_varroa = sum(1 for s in samples if s.get("varroa_load") not in ["Unknown", None, ""])
    return (with_varroa / len(samples)) * 100

def main():
    """
    Main entry point for metadata fetch.
    """
    parser = argparse.ArgumentParser(
        description="Fetch metadata from NCBI BioProjects for CCD study"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(OUTPUT_FILE),
        help="Output path for metadata JSON"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=str(FETCH_LOG),
        help="Output path for fetch log"
    )
    
    args = parser.parse_args()
    output_path = Path(args.output)
    log_path = Path(args.log)
    
    # Ensure output directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # SSL Hard-Stop
    if not check_ssl_verification():
        print(f"{SSL_VERIFY_FAILED}: Could not verify SSL certificates.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Fetching metadata for {CCD_PROJECT} and {HEALTHY_PROJECT}...")
    
    # Fetch metadata for both projects
    ccd_meta = fetch_project_metadata(CCD_PROJECT)
    healthy_meta = fetch_project_metadata(HEALTHY_PROJECT)
    
    if not ccd_meta and not healthy_meta:
        print("Failed to fetch metadata from both projects. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    # Combine samples
    all_samples = []
    if ccd_meta:
        all_samples.extend(extract_sample_info(ccd_meta))
    if healthy_meta:
        all_samples.extend(extract_sample_info(healthy_meta))
    
    if not all_samples:
        print("No samples found in metadata. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    # Validate CCD criteria
    validation = validate_ccd_criteria(all_samples)
    varroa_coverage = calculate_varroa_coverage(all_samples)
    
    # Log fetch details
    fetch_log = {
        "ccd_project": CCD_PROJECT,
        "healthy_project": HEALTHY_PROJECT,
        "ccd_runs_found": ccd_meta["accession_count"] if ccd_meta else 0,
        "healthy_runs_found": healthy_meta["accession_count"] if healthy_meta else 0,
        "total_samples": len(all_samples),
        "validation": validation,
        "varroa_coverage_percent": varroa_coverage,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Write fetch log
    with open(log_path, "w") as f:
        json.dump(fetch_log, f, indent=2)
    
    print(f"Fetch complete. Found {len(all_samples)} total samples.")
    print(f"CCD: {validation['ccd']}, Healthy: {validation['healthy']}, Ambiguous: {validation['ambiguous']}")
    print(f"Varroa coverage: {varroa_coverage:.1f}%")
    
    # Sample Count Check (FR-012)
    n_samples = len(all_samples)
    if n_samples < 80:
        print(f"{ERR_SAMPLE_SIZE_INSUFFICIENT}: Only {n_samples} samples found. Minimum required: 80.", file=sys.stderr)
        sys.exit(1)
    
    # Prepare output metadata
    output_data = {
        "ccd_project_id": CCD_PROJECT,
        "healthy_project_id": HEALTHY_PROJECT,
        "n_samples": n_samples,
        "ccd_count": validation["ccd"],
        "healthy_count": validation["healthy"],
        "ambiguous_count": validation["ambiguous"],
        "varroa_coverage_percent": varroa_coverage,
        "samples": all_samples,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Write output
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Metadata written to {output_path}")
    print(f"Log written to {log_path}")
    
    # Verify output exists
    if not output_path.exists():
        print(f"Error: Output file {output_path} was not created.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()