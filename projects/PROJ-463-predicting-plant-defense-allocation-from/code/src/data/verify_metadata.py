"""
Metadata Verification Module (T011a)

Verifies downloaded FASTQ files against FR-001 requirements (tissue, herbivore type, replicates)
by fetching metadata from NCBI E-utilities.
"""
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode

import requests

# Import from project API
from src.utils.logger import get_logger
from src.utils.config import get_data_path
from src.utils.schemas import ManifestEntry

# Constants
NCBI_EUTILITIES_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_ESUMMARY_URL = f"{NCBI_EUTILITIES_BASE}/esummary.fcgi"
NCBI_EFETCH_URL = f"{NCBI_EUTILITIES_BASE}/efetch.fcgi"
NCBI_EPOST_URL = f"{NCBI_EUTILITIES_BASE}/epost.fcgi"

# Required metadata fields per FR-001
REQUIRED_FIELDS = ["tissue", "herbivore_type", "replicates"]
MIN_REPLICATES = 2

logger = get_logger(__name__)


def fetch_sra_metadata(accession_id: str, retries: int = 3, delay: float = 1.0) -> Optional[Dict[str, Any]]:
    """
    Fetch SRA metadata for a given accession ID using NCBI E-utilities.

    Args:
        accession_id: SRA accession ID (e.g., SRR123456)
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Dictionary containing metadata or None if fetch fails
    """
    for attempt in range(retries):
        try:
            # First, post the ID to get a WebEnv session
            post_params = {
                "db": "sra",
                "id": accession_id,
                "retmode": "json"
            }
            post_response = requests.post(NCBI_EPOST_URL, data=post_params, timeout=30)
            post_response.raise_for_status()
            post_data = post_response.json()

            webenv = post_data.get("webenv")
            query_key = post_data.get("querykey")

            if not webenv or not query_key:
                logger.error(f"Failed to get WebEnv for {accession_id}: {post_data}")
                return None

            # Now fetch summary using the WebEnv
            summary_params = {
                "db": "sra",
                "webenv": webenv,
                "querykey": query_key,
                "retmode": "json",
                "rettype": "xml"  # Request XML for detailed info
            }

            response = requests.get(NCBI_ESUMMARY_URL, params=summary_params, timeout=30)
            response.raise_for_status()

            # Parse the XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            metadata = {}
            # Extract study info
            docsum = root.find(".//DocSum")
            if docsum is not None:
                for item in docsum.findall("Item"):
                    item_name = item.get("Name")
                    if item_name:
                        metadata[item_name] = item.text

            # Extract specific fields from Study attributes if available
            study_attrs = root.find(".//Attributes")
            if study_attrs is not None:
                for attr in study_attrs.findall("Attribute"):
                    attr_name = attr.get("attribute_name")
                    if attr_name:
                        metadata[attr_name] = attr.text

            logger.info(f"Successfully fetched metadata for {accession_id}")
            return metadata

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {accession_id}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Failed to fetch metadata for {accession_id} after {retries} attempts")
                return None
        except Exception as e:
            logger.error(f"Error parsing metadata for {accession_id}: {e}")
            return None

    return None


def extract_required_metadata(sra_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required metadata fields from SRA metadata.

    Args:
        sra_metadata: Raw metadata from NCBI

    Returns:
        Dictionary with extracted fields
    """
    extracted = {}

    # Map SRA metadata fields to our required fields
    # Note: Field names may vary, so we check common variations
    tissue_map = ["tissue", "organ", "organism_part", "source"]
    herbivore_map = ["herbivore", "herbivore_type", "treatment", "stressor"]
    replicate_map = ["replicate", "replicates", "n", "sample_size"]

    for field in sra_metadata:
        field_lower = field.lower()
        value = sra_metadata[field]

        if any(t in field_lower for t in tissue_map):
            extracted["tissue"] = value
        elif any(h in field_lower for h in herbivore_map):
            extracted["herbivore_type"] = value
        elif any(r in field_lower for r in replicate_map):
            try:
                extracted["replicates"] = int(value)
            except (ValueError, TypeError):
                # Try to count if it's a list
                if isinstance(value, list):
                    extracted["replicates"] = len(value)
                else:
                    extracted["replicates"] = 1

    # If replicates not found, default to 1
    if "replicates" not in extracted:
        extracted["replicates"] = 1

    return extracted


def verify_metadata_requirements(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify that metadata meets FR-001 requirements.

    Args:
        metadata: Extracted metadata dictionary

    Returns:
        Tuple of (is_valid, list_of_exclusion_reasons)
    """
    reasons = []

    # Check for required fields
    for field in REQUIRED_FIELDS:
        if field not in metadata or not metadata[field]:
            reasons.append(f"Missing required field: {field}")

    # Check replicates
    if "replicates" in metadata:
        if metadata["replicates"] < MIN_REPLICATES:
            reasons.append(f"Insufficient replicates: {metadata['replicates']} < {MIN_REPLICATES}")

    # Check tissue is not empty
    if "tissue" in metadata and (not metadata["tissue"] or metadata["tissue"].strip() == ""):
        reasons.append("Tissue field is empty or whitespace")

    # Check herbivore type is present
    if "herbivore_type" in metadata and (not metadata["herbivore_type"] or metadata["herbivore_type"].strip() == ""):
        reasons.append("Herbivore type field is empty or whitespace")

    return len(reasons) == 0, reasons


def verify_fastq_metadata(
    manifest_path: str,
    output_path: str,
    mode: str = "real"
) -> Dict[str, Any]:
    """
    Main verification function for T011a.

    Reads manifest from T011, fetches metadata for each accession,
    verifies against FR-001, and generates a verification report.

    Args:
        manifest_path: Path to the manifest file from T011
        output_path: Path to write the verification report
        mode: "real" or "synthetic"

    Returns:
        Verification report dictionary
    """
    data_path = Path(get_data_path())

    # Load manifest
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        # Try relative to data_path
        manifest_file = data_path / manifest_path
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_file, "r") as f:
        manifest_data = json.load(f)

    # Handle both list and dict formats
    if isinstance(manifest_data, dict) and "entries" in manifest_data:
        entries = manifest_data["entries"]
    elif isinstance(manifest_data, list):
        entries = manifest_data
    else:
        raise ValueError("Invalid manifest format")

    report = {
        "verification_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_studies": len(entries),
        "verified_studies": [],
        "excluded_studies": [],
        "exclusion_summary": {},
        "mode": mode
    }

    for entry in entries:
        accession_id = entry.get("accession_id")
        if not accession_id:
            logger.warning(f"Skipping entry without accession_id: {entry}")
            continue

        logger.info(f"Verifying metadata for {accession_id}")

        if mode == "synthetic":
            # For synthetic mode, assume valid but log it
            report["verified_studies"].append({
                "accession_id": accession_id,
                "status": "verified",
                "metadata": {"note": "synthetic_mode_skip_verification"}
            })
            continue

        # Fetch metadata
        sra_metadata = fetch_sra_metadata(accession_id)
        if not sra_metadata:
            exclusion_entry = {
                "accession_id": accession_id,
                "status": "excluded",
                "reason": "Failed to fetch metadata from NCBI"
            }
            report["excluded_studies"].append(exclusion_entry)
            continue

        # Extract required fields
        extracted_metadata = extract_required_metadata(sra_metadata)

        # Verify requirements
        is_valid, reasons = verify_metadata_requirements(extracted_metadata)

        if is_valid:
            report["verified_studies"].append({
                "accession_id": accession_id,
                "status": "verified",
                "metadata": extracted_metadata
            })
            logger.info(f"✓ {accession_id} passed verification")
        else:
            exclusion_entry = {
                "accession_id": accession_id,
                "status": "excluded",
                "reasons": reasons,
                "available_metadata": extracted_metadata
            }
            report["excluded_studies"].append(exclusion_entry)

            # Update exclusion summary
            for reason in reasons:
                if reason not in report["exclusion_summary"]:
                    report["exclusion_summary"][reason] = 0
                report["exclusion_summary"][reason] += 1

            logger.warning(f"✗ {accession_id} excluded: {reasons}")

    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Verification report written to {output_path}")
    logger.info(f"Total: {report['total_studies']}, Verified: {len(report['verified_studies'])}, Excluded: {len(report['excluded_studies'])}")

    return report


def main():
    """CLI entry point for metadata verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify metadata for downloaded FASTQ files (T011a)")
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/sra_manifest.json",
        help="Path to the manifest file from T011"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/metadata_verification_report.json",
        help="Path to write the verification report"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["real", "synthetic"],
        default="real",
        help="Operation mode: 'real' fetches from NCBI, 'synthetic' skips verification"
    )

    args = parser.parse_args()

    try:
        report = verify_fastq_metadata(args.manifest, args.output, args.mode)

        # Exit with error if any studies were excluded
        if report["excluded_studies"]:
            logger.warning(f"Verification completed with {len(report['excluded_studies'])} excluded studies")
            # Don't exit with error - the pipeline can continue with verified studies
            # but logs the exclusions for review
        else:
            logger.info("All studies passed verification")

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise


if __name__ == "__main__":
    main()
