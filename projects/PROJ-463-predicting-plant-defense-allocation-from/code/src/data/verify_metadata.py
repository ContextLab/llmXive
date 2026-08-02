import os
import sys
import json
import time
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing project modules
from src.utils.config import get_housekeeping_genes, get_data_path
from src.utils.logger import setup_logging, get_logger
from src.utils.schemas import RNASeqStudy

# Configure logger
logger = get_logger(__name__)

def fetch_sra_metadata(accession_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a given SRA accession from NCBI E-utilities.
    This is a simplified fetcher. In a production environment, this would
    handle retries, error checking, and parsing of the full XML/JSON response.
    """
    logger.info(f"Fetching metadata for {accession_id} from NCBI E-utilities")
    
    # Base URL for E-utilities
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    # Parameters
    params = {
        "db": "sra",
        "id": accession_id,
        "retmode": "json"
    }
    
    import requests
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and accession_id in data["result"]:
            return data["result"][accession_id]
        else:
            logger.warning(f"No result found for {accession_id} in response")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession_id}: {e}")
        return {}

def extract_required_metadata(sra_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required metadata fields from SRA metadata.
    Maps SRA fields to our internal schema requirements.
    """
    extracted = {
        "accession_id": sra_metadata.get("accession", ""),
        "species": "",
        "tissue": "",
        "treatment": "",
        "replicates": 0,
        "source_url": sra_metadata.get("study_accession", "")
    }
    
    # Extract organism (species)
    if "organism" in sra_metadata:
        extracted["species"] = sra_metadata["organism"]
        
    # Extract sample attributes (tissue, treatment)
    # SRA metadata structure can vary, so we check common locations
    sample_attributes = sra_metadata.get("attributes", [])
    for attr in sample_attributes:
        if isinstance(attr, dict):
            tag = attr.get("tag", "").lower()
            value = attr.get("value", "")
            
            if "tissue" in tag or "organ" in tag:
                extracted["tissue"] = value
            elif "treatment" in tag or "condition" in tag or "factor" in tag:
                extracted["treatment"] = value
            elif "replicate" in tag:
                try:
                    extracted["replicates"] = int(value)
                except ValueError:
                    extracted["replicates"] = 1
    
    # If we couldn't find replicates in attributes, estimate from study
    if extracted["replicates"] == 0:
        # This is a fallback estimate; real logic might parse study design
        extracted["replicates"] = 1 
        
    return extracted

def verify_metadata_requirements(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify that metadata meets FR-001 requirements:
    1. Tissue metadata must be present
    2. Biological replicates must be >= 2
    3. Treatment labels must be present (herbivore type)
    """
    issues = []
    
    # Check tissue
    if not metadata.get("tissue"):
        issues.append("Missing tissue metadata")
        
    # Check replicates
    if metadata.get("replicates", 0) < 2:
        issues.append(f"Insufficient biological replicates: {metadata.get('replicates', 0)} (required >= 2)")
        
    # Check treatment
    if not metadata.get("treatment"):
        issues.append("Missing treatment/herbivore type metadata")
        
    return len(issues) == 0, issues

def verify_fastq_metadata(fastq_path: Path, accession_id: str) -> Dict[str, Any]:
    """
    Verify FASTQ file metadata and structure.
    For this task, we primarily rely on the SRA metadata fetch.
    We also check that the file exists and is readable.
    """
    report = {
        "accession_id": accession_id,
        "file_exists": fastq_path.exists(),
        "file_readable": False,
        "metadata_fetched": False,
        "metadata_valid": False,
        "issues": []
    }
    
    if not report["file_exists"]:
        report["issues"].append(f"FASTQ file not found: {fastq_path}")
        return report
        
    # Try to open the file (it's gzipped)
    try:
        import gzip
        with gzip.open(fastq_path, 'rt') as f:
            # Read first few lines to verify format
            for i, line in enumerate(f):
                if i > 3:
                    break
        report["file_readable"] = True
    except Exception as e:
        report["issues"].append(f"FASTQ file not readable: {e}")
        return report
        
    # Fetch and verify SRA metadata
    sra_meta = fetch_sra_metadata(accession_id)
    if not sra_meta:
        report["issues"].append("Failed to fetch SRA metadata from NCBI")
        return report
        
    report["metadata_fetched"] = True
    
    # Extract and verify required fields
    extracted = extract_required_metadata(sra_meta)
    valid, issues = verify_metadata_requirements(extracted)
    
    report["extracted_metadata"] = extracted
    report["metadata_valid"] = valid
    report["issues"].extend(issues)
    
    return report

def verify_synthetic_metadata(synthetic_manifest_path: Path) -> Dict[str, Any]:
    """
    Verify synthetic data metadata structure.
    This is used when running in synthetic mode.
    """
    report = {
        "mode": "synthetic",
        "file_exists": synthetic_manifest_path.exists(),
        "metadata_valid": False,
        "issues": []
    }
    
    if not report["file_exists"]:
        report["issues"].append(f"Synthetic manifest not found: {synthetic_manifest_path}")
        return report
        
    try:
        with open(synthetic_manifest_path, 'r') as f:
            manifest = json.load(f)
            
        # Check for required fields
        required_fields = ["accession_id", "organism", "source_type"]
        missing = [f for f in required_fields if f not in manifest]
        
        if missing:
            report["issues"].append(f"Missing required fields in synthetic manifest: {missing}")
        else:
            report["metadata_valid"] = True
            report["extracted_metadata"] = {
                "accession_id": manifest.get("accession_id", ""),
                "species": manifest.get("organism", ""),
                "tissue": "synthetic_tissue",
                "treatment": "synthetic_treatment",
                "replicates": 3  # Synthetic data typically has fixed replicates
            }
    except json.JSONDecodeError as e:
        report["issues"].append(f"Invalid JSON in synthetic manifest: {e}")
        
    return report

def save_verification_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the verification report to the specified path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report saved to {output_path}")

def main():
    """
    Main entry point for metadata verification.
    Usage: python src/data/verify_metadata.py --mode [real|synthetic] --accession_ids [id1,id2,...]
    """
    parser = argparse.ArgumentParser(description="Verify metadata for downloaded FASTQ files")
    parser.add_argument("--mode", choices=["real", "synthetic"], required=True,
                      help="Mode: real (fetch from NCBI) or synthetic (check manifest)")
    parser.add_argument("--accession_ids", type=str, required=False,
                      help="Comma-separated list of accession IDs (required for real mode)")
    parser.add_argument("--synthetic_manifest", type=str, required=False,
                      help="Path to synthetic manifest (required for synthetic mode)")
    parser.add_argument("--output", type=str, default="data/processed/metadata_verification_report.json",
                      help="Output path for verification report")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    output_path = Path(args.output)
    data_path = get_data_path()
    
    overall_report = {
        "mode": args.mode,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "studies": [],
        "summary": {
            "total_studies": 0,
            "valid_studies": 0,
            "invalid_studies": 0,
            "excluded_studies": []
        }
    }
    
    if args.mode == "real":
        if not args.accession_ids:
            logger.error("Accession IDs required for real mode")
            sys.exit(1)
            
        accession_list = [aid.strip() for aid in args.accession_ids.split(",")]
        
        for accession_id in accession_list:
            # Construct expected FASTQ path
            fastq_path = data_path / "raw" / f"{accession_id}.fastq.gz"
            
            logger.info(f"Verifying metadata for {accession_id}")
            verification = verify_fastq_metadata(fastq_path, accession_id)
            
            overall_report["studies"].append(verification)
            overall_report["summary"]["total_studies"] += 1
            
            if verification["metadata_valid"]:
                overall_report["summary"]["valid_studies"] += 1
            else:
                overall_report["summary"]["invalid_studies"] += 1
                overall_report["summary"]["excluded_studies"].append({
                    "accession_id": accession_id,
                    "reasons": verification["issues"]
                })
                
    elif args.mode == "synthetic":
        if not args.synthetic_manifest:
            logger.error("Synthetic manifest path required for synthetic mode")
            sys.exit(1)
            
        manifest_path = Path(args.synthetic_manifest)
        verification = verify_synthetic_metadata(manifest_path)
        
        overall_report["studies"].append(verification)
        overall_report["summary"]["total_studies"] += 1
        
        if verification["metadata_valid"]:
            overall_report["summary"]["valid_studies"] += 1
        else:
            overall_report["summary"]["invalid_studies"] += 1
            overall_report["summary"]["excluded_studies"].append({
                "accession_id": "SYNTH_001",
                "reasons": verification["issues"]
            })
            
    # Save the report
    save_verification_report(overall_report, output_path)
    
    # Check if any studies were invalid
    if overall_report["summary"]["invalid_studies"] > 0:
        logger.warning(f"{overall_report['summary']['invalid_studies']} studies failed metadata verification")
        
        # Write flag file for human intervention
        flag_path = Path(data_path) / "manifests" / "human_input_needed.flag"
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        with open(flag_path, 'w') as f:
            f.write(f"Metadata verification failed for {overall_report['summary']['invalid_studies']} studies.\n")
            f.write("Please review the report and resolve issues before proceeding.\n")
        
        logger.info(f"Flag written to {flag_path}")
        sys.exit(1)
        
    logger.info("All studies passed metadata verification")
    sys.exit(0)

if __name__ == "__main__":
    main()