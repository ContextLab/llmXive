"""
Metadata Verification Module for Plant Defense Allocation Pipeline.

This module verifies that downloaded FASTQ files (or synthetic data) match
the requirements defined in FR-001 (tissue, herbivore type, replicates)
BEFORE preprocessing begins.

It fetches metadata from NCBI E-utilities for real data or generates
a report for synthetic data modes.
"""

import os
import sys
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import project utilities from the existing API surface
from src.utils.config import get_data_path, get_seed
from src.utils.logger import get_logger
from src.utils.schemas import RNASeqStudy

# Initialize logger
logger = get_logger(__name__)

# Constants
NCBI_EMAIL = "plant-defense-pipeline@example.com"  # Required by NCBI
NCBI_TOOL = "llmXive-plant-defense-pipeline"
RATE_LIMIT_DELAY = 0.34  # seconds between requests

# Herbivory keywords for classification
CHEWING_KEYWORDS = ['chewing', 'biting', 'leaf-eating', 'defoliation']
PIERCING_KEYWORDS = ['piercing', 'sucking', 'phloem', 'xylem', 'aphid', 'whitefly']


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.warning(f"File not found for checksum: {file_path}")
        return "FILE_NOT_FOUND"


def fetch_sra_metadata(accession_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an SRA accession using NCBI E-utilities.

    Args:
        accession_id: The SRA or GEO accession ID (e.g., GSE12345, SRR123456).

    Returns:
        Dictionary containing metadata fields or None if fetch fails.
    """
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET

    # Determine database and term based on ID prefix
    if accession_id.startswith("GSE"):
        db = "gds"
        term = accession_id
    elif accession_id.startswith("SRP") or accession_id.startswith("ERP") or accession_id.startswith("DRP"):
        db = "sra"
        term = accession_id
    elif accession_id.startswith("SRR"):
        db = "sra"
        term = accession_id
    else:
        # Default to GDS/GEO search if prefix is ambiguous
        db = "gds"
        term = accession_id

    # Construct URL
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": db,
        "id": accession_id,
        "retmode": "xml",
        "email": NCBI_EMAIL,
        "tool": NCBI_TOOL
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        logger.info(f"Fetching metadata for {accession_id} from {db}...")
        time.sleep(RATE_LIMIT_DELAY)
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        # Parse XML based on database
        metadata = {
            "accession_id": accession_id,
            "species": None,
            "tissue": None,
            "treatment": None,
            "replicates": 0,
            "raw_xml": accession_id # Placeholder to avoid storing massive XML
        }

        if db == "gds":
            # Extract Organism (Species)
            org_elem = root.find(".//Organism")
            if org_elem is not None:
                metadata["species"] = org_elem.text

            # Extract attributes for Tissue and Treatment
            # GDS XML structure varies, looking for common tags
            for attr in root.iter("Attribute"):
                tag_name = attr.get("tag_name", "")
                value = attr.text or ""

                if "organ" in tag_name.lower() or "tissue" in tag_name.lower():
                    if not metadata["tissue"]:
                        metadata["tissue"] = value
                elif "treatment" in tag_name.lower() or "condition" in tag_name.lower():
                    if not metadata["treatment"]:
                        metadata["treatment"] = value

            # Count replicates (samples)
            samples = root.findall(".//Sample")
            metadata["replicates"] = len(samples) if samples else 0

        elif db == "sra":
            # SRA XML structure
            exp_set = root.find(".//EXPERIMENT_SET")
            if exp_set is not None:
                for exp in exp_set.findall("EXPERIMENT"):
                    # Try to find attributes
                    for attr in exp.iter("ATTRIBUTE"):
                        tag = attr.get("tag", "")
                        val = attr.text or ""
                        if "organism" in tag.lower():
                            metadata["species"] = val
                        elif "organ" in tag.lower() or "tissue" in tag.lower():
                            if not metadata["tissue"]:
                                metadata["tissue"] = val
                        elif "treatment" in tag.lower() or "condition" in tag.lower():
                            if not metadata["treatment"]:
                                metadata["treatment"] = val

            # Count runs as replicates
            runs = root.findall(".//RUN_SET/RUN")
            metadata["replicates"] = len(runs) if runs else 0

        return metadata

    except Exception as e:
        logger.error(f"Failed to fetch metadata for {accession_id}: {e}")
        return None


def extract_required_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and extract required fields for verification.

    Args:
        metadata: Raw metadata dictionary from fetch_sra_metadata.

    Returns:
        Normalized dictionary with required fields.
    """
    species = metadata.get("species")
    treatment = metadata.get("treatment")
    tissue = metadata.get("tissue")
    replicates = metadata.get("replicates", 0)

    # Classify herbivore type if treatment is available
    herbivore_type = "unknown"
    if treatment:
        treatment_lower = treatment.lower()
        if any(kw in treatment_lower for kw in CHEWING_KEYWORDS):
            herbivore_type = "chewing"
        elif any(kw in treatment_lower for kw in PIERCING_KEYWORDS):
            herbivore_type = "piercing-sucking"
        elif "herbivore" in treatment_lower or "insect" in treatment_lower:
            # Default to chewing if generic insect mentioned but not specific
            herbivore_type = "chewing"

    return {
        "accession_id": metadata.get("accession_id"),
        "species": species,
        "tissue": tissue,
        "treatment": treatment,
        "herbivore_type": herbivore_type,
        "replicates": replicates,
        "raw_metadata": metadata
    }


def verify_metadata_requirements(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify extracted metadata against FR-001 requirements.

    Requirements:
    1. Tissue metadata must be present.
    2. Biological replicates must be >= 2.
    3. Herbivore treatment label should be present (not 'unknown' if possible).

    Args:
        extracted: Normalized metadata dictionary.

    Returns:
        Verification result dictionary.
    """
    issues = []
    status = "PASS"

    # Check Tissue
    if not extracted.get("tissue"):
        issues.append("Missing tissue metadata")
        status = "FAIL"

    # Check Replicates
    if extracted.get("replicates", 0) < 2:
        issues.append(f"Insufficient replicates: {extracted.get('replicates')} (required >= 2)")
        status = "FAIL"

    # Check Herbivore Type
    if extracted.get("herbivore_type") == "unknown":
        issues.append("Herbivore type could not be determined from treatment metadata")
        # This is a warning, not necessarily a hard fail depending on strictness,
        # but for FR-001 we flag it.
        if status == "PASS":
            status = "WARNING"

    return {
        "status": status,
        "issues": issues,
        "included": status != "FAIL"
    }


def verify_fastq_metadata(accession_id: str, fastq_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify metadata for a specific FASTQ file/accession.

    Args:
        accession_id: The study accession ID.
        fastq_path: Optional path to the FASTQ file to verify existence.

    Returns:
        Verification report for this study.
    """
    report = {
        "accession_id": accession_id,
        "file_exists": False,
        "file_checksum": None,
        "metadata": None,
        "verification": None
    }

    # Check file existence if path provided
    if fastq_path and os.path.exists(fastq_path):
        report["file_exists"] = True
        report["file_checksum"] = calculate_sha256(fastq_path)

    # Fetch metadata
    metadata = fetch_sra_metadata(accession_id)
    if metadata:
        extracted = extract_required_metadata(metadata)
        verification = verify_metadata_requirements(extracted)
        report["metadata"] = extracted
        report["verification"] = verification
    else:
        report["verification"] = {
            "status": "FAIL",
            "issues": ["Failed to fetch metadata from NCBI"],
            "included": False
        }

    return report


def verify_synthetic_metadata(accession_id: str, synthetic_data_path: str) -> Dict[str, Any]:
    """
    Generate a verification report for synthetic data.

    Args:
        accession_id: Synthetic accession ID (e.g., SYNTH_001).
        synthetic_data_path: Path to the synthetic data file.

    Returns:
        Verification report for synthetic data.
    """
    report = {
        "accession_id": accession_id,
        "mode": "synthetic",
        "real_data_available": False,
        "file_exists": os.path.exists(synthetic_data_path),
        "file_checksum": calculate_sha256(synthetic_data_path) if os.path.exists(synthetic_data_path) else None,
        "metadata": {
            "accession_id": accession_id,
            "species": "Arabidopsis thaliana", # Default synthetic species
            "tissue": "Leaf",
            "treatment": "Chewing Herbivory (Simulated)",
            "herbivore_type": "chewing",
            "replicates": 3,
            "raw_metadata": {}
        },
        "verification": {
            "status": "PASS",
            "issues": [],
            "included": True
        }
    }
    return report


def save_verification_report(reports: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the aggregated verification report to a JSON file.

    Args:
        reports: List of individual study verification reports.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    final_report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_studies": len(reports),
        "included_studies": sum(1 for r in reports if r.get("verification", {}).get("included", False)),
        "excluded_studies": sum(1 for r in reports if not r.get("verification", {}).get("included", False)),
        "studies": reports
    }

    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Verification report saved to {output_path}")


def main():
    """
    Main entry point for metadata verification.
    Reads configuration to determine mode (real/synthetic) and accession IDs.
    """
    # Determine mode and inputs
    # For this task, we assume the orchestrator (T011) has set up the environment
    # or we are running in synthetic mode by default if no real data is found.

    config_path = get_data_path()
    data_root = Path(config_path)
    
    # Check for real data manifest
    real_manifest_path = data_root / "manifests" / "real_data_manifest.json"
    synthetic_manifest_path = data_root / "manifests" / "synthetic_manifest.json"
    output_path = data_root / "processed" / "metadata_verification_report.json"

    reports = []

    if real_manifest_path.exists():
        logger.info("Real data manifest found. Verifying real data...")
        with open(real_manifest_path, "r") as f:
            manifest = json.load(f)
        
        # Extract accession IDs from manifest
        accession_ids = [entry["accession_id"] for entry in manifest.get("entries", [])]
        
        for acc_id in accession_ids:
            # Construct expected FASTQ path
            fastq_path = data_root / "raw" / f"{acc_id}.fastq.gz"
            report = verify_fastq_metadata(acc_id, str(fastq_path))
            reports.append(report)
    elif synthetic_manifest_path.exists():
        logger.info("Synthetic data manifest found. Verifying synthetic data...")
        with open(synthetic_manifest_path, "r") as f:
            manifest = json.load(f)
        
        # Extract accession ID
        acc_id = manifest.get("accession_id", "SYNTH_001")
        synthetic_file = data_root / "synthetic" / f"{acc_id}_tpm.csv" # Synthetic TPM file
        
        report = verify_synthetic_metadata(acc_id, str(synthetic_file))
        reports.append(report)
    else:
        # Fallback: No data found. Generate a report indicating no data.
        logger.warning("No real or synthetic data manifest found. Generating empty report.")
        reports.append({
            "accession_id": "NONE",
            "mode": "none",
            "real_data_available": False,
            "verification": {
                "status": "FAIL",
                "issues": ["No data source found"],
                "included": False
            }
        })

    # Save report
    save_verification_report(reports, str(output_path))

    # Check for failures
    excluded_count = sum(1 for r in reports if not r.get("verification", {}).get("included", False))
    if excluded_count > 0 and any(r.get("mode") != "synthetic" for r in reports):
        logger.warning(f"{excluded_count} studies excluded due to metadata issues.")
        # Do not raise SystemExit here to allow the pipeline to potentially continue 
        # with synthetic data or other studies, but log the issue clearly.
        # However, if ALL real studies are excluded, we might want to stop.
        if all(r.get("mode") == "real" for r in reports) and excluded_count == len(reports):
            logger.error("All real studies excluded. Pipeline cannot proceed with real data.")
            # sys.exit(1) # Optional: strict mode

    logger.info("Metadata verification complete.")


if __name__ == "__main__":
    main()