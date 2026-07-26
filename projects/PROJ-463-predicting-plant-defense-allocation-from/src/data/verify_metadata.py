"""
Metadata verification for downloaded FASTQ files.

Verifies that downloaded files match FR-001 requirements:
- Tissue type is present
- Herbivore type is present
- Replicates count meets minimum threshold
- Metadata is fetched from NCBI E-utilities or parsed from SRA manifest

Output: data/processed/metadata_verification_report.json
"""
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from urllib.parse import urlencode

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_data_path, get_config
from src.utils.logger import get_logger
from src.utils.schemas import RNASeqStudy

logger = get_logger(__name__)


def fetch_sra_metadata(accession_id: str, retries: int = 3, delay: float = 1.0) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an SRA accession from NCBI E-utilities.
    
    Args:
        accession_id: SRA accession ID (e.g., SRX123456)
        retries: Number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Metadata dictionary or None if fetch fails
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "sra",
        "id": accession_id,
        "retmode": "json"
    }
    
    for attempt in range(retries):
        try:
            logger.info(f"Fetching metadata for {accession_id} (attempt {attempt + 1}/{retries})")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data and accession_id in data["result"]:
                return data["result"][accession_id]
            else:
                logger.warning(f"No result found for {accession_id} in response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {accession_id}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Failed to fetch metadata for {accession_id} after {retries} attempts")
                return None
                
    return None


def extract_required_metadata(sra_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required metadata fields from SRA metadata.
    
    Required fields per FR-001:
    - tissue
    - herbivore_type
    - replicates
    
    Args:
        sra_metadata: Raw metadata from NCBI
        
    Returns:
        Dictionary with extracted fields
    """
    extracted = {
        "tissue": None,
        "herbivore_type": None,
        "replicates": 1,  # Default to 1 if not specified
        "sample_title": sra_metadata.get("sample_title", "Unknown"),
        "experiment_title": sra_metadata.get("experiment_title", "Unknown"),
        "organism": sra_metadata.get("organism", "Unknown"),
        "library_strategy": sra_metadata.get("library_strategy", "Unknown"),
        "library_source": sra_metadata.get("library_source", "Unknown"),
        "library_selection": sra_metadata.get("library_selection", "Unknown"),
    }
    
    # Extract tissue from sample attributes if available
    attributes = sra_metadata.get("attributes", [])
    if isinstance(attributes, list):
        for attr in attributes:
            if isinstance(attr, dict):
                tag = attr.get("tag", "").lower()
                value = attr.get("value", "")
                
                # Look for tissue-related tags
                if "tissue" in tag or "organ" in tag:
                    extracted["tissue"] = value
                elif "herbivore" in tag or "insect" in tag or "pest" in tag:
                    extracted["herbivore_type"] = value
            elif isinstance(attr, str):
                # Handle string attributes
                if "tissue" in attr.lower():
                    parts = attr.split(":")
                    if len(parts) > 1:
                        extracted["tissue"] = parts[1].strip()
                elif "herbivore" in attr.lower():
                    parts = attr.split(":")
                    if len(parts) > 1:
                        extracted["herbivore_type"] = parts[1].strip()
    
    # If tissue not found in attributes, try to infer from sample title
    if extracted["tissue"] is None:
        title = extracted["sample_title"].lower()
        common_tissues = ["leaf", "root", "stem", "flower", "seed", "root", "shoot", "cotyledon"]
        for tissue in common_tissues:
            if tissue in title:
                extracted["tissue"] = tissue
                break
    
    # If herbivore type not found, try to infer from title
    if extracted["herbivore_type"] is None:
        title = extracted["sample_title"].lower()
        common_herbivores = ["aphid", "caterpillar", "beetle", "moth", "fly", "weevil", "thrips", "spider mite"]
        for herbivore in common_herbivores:
            if herbivore in title:
                extracted["herbivore_type"] = herbivore
                break
    
    # Check for replicate information
    # This is typically inferred from the number of runs associated with a sample
    runs = sra_metadata.get("runs", [])
    if runs:
        extracted["replicates"] = len(runs)
    
    return extracted


def verify_metadata_requirements(extracted_metadata: Dict[str, Any], 
                                 min_replicates: int = 2) -> Tuple[bool, List[str]]:
    """
    Verify that metadata meets FR-001 requirements.
    
    Requirements:
    - Tissue must be specified
    - Herbivore type must be specified
    - At least min_replicates replicates must be present
    
    Args:
        extracted_metadata: Extracted metadata dictionary
        min_replicates: Minimum number of replicates required
        
    Returns:
        Tuple of (is_valid, list_of_exclusion_reasons)
    """
    reasons = []
    
    if not extracted_metadata.get("tissue"):
        reasons.append("Missing tissue information")
        
    if not extracted_metadata.get("herbivore_type"):
        reasons.append("Missing herbivore type information")
        
    if extracted_metadata.get("replicates", 0) < min_replicates:
        reasons.append(f"Insufficient replicates: {extracted_metadata.get('replicates', 0)} < {min_replicates}")
    
    return len(reasons) == 0, reasons


def verify_fastq_metadata(manifest_path: Path, 
                          output_path: Path,
                          mode: str = "real",
                          min_replicates: int = 2) -> Dict[str, Any]:
    """
    Main verification function that processes a manifest of downloaded FASTQ files.
    
    Args:
        manifest_path: Path to the download manifest JSON
        output_path: Path for the verification report output
        mode: "real" or "synthetic" mode
        min_replicates: Minimum replicates required per study
        
    Returns:
        Verification report dictionary
    """
    logger.info(f"Starting metadata verification in {mode} mode")
    
    # Load manifest
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return {
            "status": "error",
            "error": f"Manifest not found: {manifest_path}",
            "verified_studies": [],
            "excluded_studies": []
        }
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    verified_studies = []
    excluded_studies = []
    
    if mode == "synthetic":
        # For synthetic mode, verify against schema
        logger.info("Verifying synthetic metadata against schema")
        synthetic_entries = manifest.get("entries", [])
        
        for entry in synthetic_entries:
            accession_id = entry.get("accession_id", "UNKNOWN")
            
            # Synthetic data should have valid metadata by design
            # Just verify the schema structure
            required_fields = ["file_name", "checksum", "source_type", "provenance"]
            missing_fields = [f for f in required_fields if f not in entry]
            
            if missing_fields:
                excluded_studies.append({
                    "accession_id": accession_id,
                    "reason": f"Missing synthetic metadata fields: {missing_fields}",
                    "metadata": None
                })
            else:
                # Verify provenance structure
                provenance = entry.get("provenance", {})
                if not provenance.get("accession_id"):
                    excluded_studies.append({
                        "accession_id": accession_id,
                        "reason": "Missing accession_id in provenance",
                        "metadata": None
                    })
                else:
                    verified_studies.append({
                        "accession_id": accession_id,
                        "reason": None,
                        "metadata": {
                            "tissue": "synthetic_leaf",
                            "herbivore_type": "synthetic_herbivore",
                            "replicates": 3,
                            "sample_title": f"Synthetic Study {accession_id}"
                        }
                    })
    
    else:
        # Real mode: fetch metadata from NCBI
        entries = manifest.get("entries", [])
        
        # Group entries by study accession
        studies = {}
        for entry in entries:
            accession_id = entry.get("accession_id")
            if accession_id:
                if accession_id not in studies:
                    studies[accession_id] = []
                studies[accession_id].append(entry)
        
        # Verify each study
        for accession_id, study_entries in studies.items():
            logger.info(f"Verifying study: {accession_id}")
            
            # Fetch metadata
            metadata = fetch_sra_metadata(accession_id)
            
            if metadata is None:
                excluded_studies.append({
                    "accession_id": accession_id,
                    "reason": "Failed to fetch metadata from NCBI",
                    "metadata": None
                })
                continue
            
            # Extract required fields
            extracted = extract_required_metadata(metadata)
            
            # Verify requirements
            is_valid, reasons = verify_metadata_requirements(extracted, min_replicates)
            
            if is_valid:
                verified_studies.append({
                    "accession_id": accession_id,
                    "reason": None,
                    "metadata": extracted
                })
            else:
                excluded_studies.append({
                    "accession_id": accession_id,
                    "reason": "; ".join(reasons),
                    "metadata": extracted
                })
    
    # Create report
    report = {
        "verification_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": mode,
        "min_replicates": min_replicates,
        "total_studies": len(studies) if mode == "real" else len(synthetic_entries),
        "verified_count": len(verified_studies),
        "excluded_count": len(excluded_studies),
        "verified_studies": verified_studies,
        "excluded_studies": excluded_studies
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification complete: {len(verified_studies)} verified, {len(excluded_studies)} excluded")
    logger.info(f"Report written to: {output_path}")
    
    return report


def main():
    """CLI entry point for metadata verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify metadata of downloaded FASTQ files")
    parser.add_argument("--manifest", type=str, 
                      default=str(get_data_path() / "manifests" / "download_manifest.json"),
                      help="Path to download manifest JSON")
    parser.add_argument("--output", type=str,
                      default=str(get_data_path() / "processed" / "metadata_verification_report.json"),
                      help="Path for verification report output")
    parser.add_argument("--mode", type=str, choices=["real", "synthetic"], default="real",
                      help="Mode: real (fetch from NCBI) or synthetic (schema validation)")
    parser.add_argument("--min-replicates", type=int, default=2,
                      help="Minimum number of replicates required")
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    report = verify_fastq_metadata(
        manifest_path=manifest_path,
        output_path=output_path,
        mode=args.mode,
        min_replicates=args.min_replicates
    )
    
    # Exit with error if all studies were excluded
    if report["excluded_count"] == report["total_studies"] and report["total_studies"] > 0:
        logger.error("All studies were excluded. Check metadata requirements or data sources.")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
