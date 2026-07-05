"""
Data Acquisition Module for Chemo Biomarker Discovery.

This module handles the downloading of TCGA HTSeq-Counts and clinical data
from HuggingFace mirrors for at least 3 tumor types.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import (
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    RESULTS_DIR,
    STATE_DIR,
    TCGA_HUGGINGFACE_ORG,
    MIN_TCGA_TUMOR_TYPES,
    RANDOM_SEED
)
from src.utils import (
    setup_logging,
    calculate_checksum,
    generate_checksums_for_directory,
    ensure_path_exists,
    get_file_size_mb
)

# Configure logging
logger = setup_logging("data_acquisition")

# Default TCGA tumor types to download (must be >= 3)
# Using common cancer types with available RNA-seq and clinical data
DEFAULT_TCGA_TYPES = [
    "TCGA-BRCA",  # Breast Invasive Carcinoma
    "TCGA-LUAD",  # Lung Adenocarcinoma
    "TCGA-COAD",  # Colon Adenocarcinoma
    "TCGA-KIRC",  # Kidney Renal Clear Cell Carcinoma
    "TCGA-LIHC"   # Liver Hepatocellular Carcinoma
]

def download_from_huggingface(dataset_name: str, output_dir: Path, force: bool = False) -> bool:
    """
    Download a dataset from HuggingFace Hub.

    Args:
        dataset_name: The HuggingFace dataset identifier (e.g., "TCGA-BRCA-Data")
        output_dir: Directory to save the downloaded files
        force: If True, re-download even if files exist

    Returns:
        True if download was successful, False otherwise
    """
    try:
        # Lazy import to avoid heavy imports if not needed
        from huggingface_hub import snapshot_download

        ensure_path_exists(output_dir)

        # Check if files already exist
        if not force and any(output_dir.iterdir()):
            logger.info(f"Files already exist in {output_dir}, skipping download.")
            return True

        # Download the dataset
        logger.info(f"Downloading {dataset_name} from HuggingFace...")
        snapshot_download(
            repo_id=dataset_name,
            repo_type="dataset",
            local_dir=str(output_dir),
            local_dir_use_symlinks=False,
            force_download=force
        )

        # Verify download
        files = list(output_dir.glob("*"))
        if not files:
            logger.error(f"Downloaded directory {output_dir} is empty.")
            return False

        logger.info(f"Successfully downloaded {len(files)} files to {output_dir}")
        return True

    except ImportError:
        logger.error("huggingface_hub is not installed. Please install it via: pip install huggingface_hub")
        return False
    except Exception as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        return False

def verify_response_labels(clinical_data_path: Path) -> bool:
    """
    Verify that clinical data contains response labels (RECIST/CR/PR).

    Args:
        clinical_data_path: Path to the clinical data file

    Returns:
        True if response labels are found, False otherwise
    """
    if not clinical_data_path.exists():
        logger.warning(f"Clinical data file not found: {clinical_data_path}")
        return False

    try:
        # Try to read as CSV first, then TSV
        import pandas as pd

        if clinical_data_path.suffix == '.csv':
            df = pd.read_csv(clinical_path)
        elif clinical_data_path.suffix == '.tsv':
            df = pd.read_csv(clinical_data_path, sep='\t')
        else:
            # Try to detect separator
            with open(clinical_data_path, 'r') as f:
                first_line = f.readline()
                if '\t' in first_line:
                    df = pd.read_csv(clinical_data_path, sep='\t')
                else:
                    df = pd.read_csv(clinical_data_path)

        # Check for common response label columns
        response_columns = [
            'response_label', 'clinical_response', 'best_overall_response',
            'recist_response', 'cr_pr_status', 'response'
        ]

        found_column = None
        for col in response_columns:
            if col.lower() in [c.lower() for c in df.columns]:
                found_column = col
                break

        if found_column:
            logger.info(f"Found response label column: {found_column}")
            return True
        else:
            logger.warning(f"No response label column found in {clinical_data_path}. Available columns: {list(df.columns)}")
            return False

    except Exception as e:
        logger.error(f"Error verifying response labels in {clinical_data_path}: {e}")
        return False

def update_state_artifact_hashes(state_dir: Path, tumor_type: str, file_path: Path) -> None:
    """
    Update the state/artifact_hashes.yaml file with new file hashes.

    Args:
        state_dir: Path to the state directory
        tumor_type: The tumor type identifier
        file_path: Path to the file to hash
    """
    import yaml

    state_file = state_dir / "artifact_hashes.yaml"
    ensure_path_exists(state_dir)

    # Load existing state or create new
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception:
            state_data = {}
    else:
        state_data = {}

    # Initialize tumor type entry
    if tumor_type not in state_data:
        state_data[tumor_type] = {}

    # Calculate and store hash
    file_hash = calculate_checksum(file_path)
    state_data[tumor_type][file_path.name] = {
        "hash": file_hash,
        "size_mb": get_file_size_mb(file_path),
        "updated_at": str(Path(file_path).stat().st_mtime)
    }

    # Write back to file
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

    logger.info(f"Updated state artifact hashes for {tumor_type}")

def download_tcga_data(
    tumor_types: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Download TCGA HTSeq-Counts and clinical data for specified tumor types.

    Args:
        tumor_types: List of TCGA tumor type identifiers (e.g., "TCGA-BRCA")
        output_dir: Directory to save downloaded data (defaults to config)
        force: If True, re-download existing files

    Returns:
        Dictionary with download results and metadata
    """
    if tumor_types is None:
        tumor_types = DEFAULT_TCGA_TYPES[:MIN_TCGA_TUMOR_TYPES]  # Ensure at least 3

    if len(tumor_types) < MIN_TCGA_TUMOR_TYPES:
        logger.warning(f"Requested {len(tumor_types)} tumor types, but minimum is {MIN_TCGA_TUMOR_TYPES}. "
                     f"Proceeding with {len(tumor_types)} types.")

    if output_dir is None:
        output_dir = DATA_RAW_DIR / "tcga"

    ensure_path_exists(output_dir)

    results = {
        "success": True,
        "downloaded_types": [],
        "failed_types": [],
        "files_downloaded": [],
        "checksums_updated": [],
        "feasibility_met": False
    }

    for tumor_type in tumor_types:
        logger.info(f"Processing tumor type: {tumor_type}")

        # Define subdirectory for this tumor type
        tumor_dir = output_dir / tumor_type
        ensure_path_exists(tumor_dir)

        # Construct HuggingFace dataset name
        # Assuming format: TCGA-{TUMOR_TYPE}-Data
        dataset_name = f"{TCGA_HUGGINGFACE_ORG}/{tumor_type}-Data"

        # Attempt download
        success = download_from_huggingface(dataset_name, tumor_dir, force)

        if success:
            # Verify the download contains expected files
            count_files = list(tumor_dir.glob("*counts*")) or list(tumor_dir.glob("*HTSeq*"))
            clinical_files = list(tumor_dir.glob("*clinical*")) or list(tumor_dir.glob("*clinical*"))

            if count_files and clinical_files:
                logger.info(f"Found {len(count_files)} count files and {len(clinical_files)} clinical files for {tumor_type}")

                # Verify response labels in clinical data
                clinical_path = clinical_files[0]
                if verify_response_labels(clinical_path):
                    results["downloaded_types"].append(tumor_type)
                    results["files_downloaded"].extend([str(f) for f in count_files + clinical_files])

                    # Update state with checksums
                    for file_path in count_files + clinical_files:
                        update_state_artifact_hashes(STATE_DIR, tumor_type, file_path)
                        results["checksums_updated"].append(str(file_path))
                else:
                    logger.warning(f"No valid response labels found for {tumor_type}. Skipping.")
                    results["failed_types"].append(tumor_type)
            else:
                logger.error(f"Expected files not found in {tumor_dir}")
                results["failed_types"].append(tumor_type)
        else:
            logger.error(f"Failed to download {tumor_type}")
            results["failed_types"].append(tumor_type)

    # Check feasibility gate: must have >= 3 valid tumor types
    results["feasibility_met"] = len(results["downloaded_types"]) >= MIN_TCGA_TUMOR_TYPES

    if not results["feasibility_met"]:
        logger.error(f"Feasibility gate failed: Only {len(results['downloaded_types'])} valid tumor types found. "
                   f"Minimum required: {MIN_TCGA_TUMOR_TYPES}")

        # Write feasibility gate status
        feasibility_file = DATA_PROCESSED_DIR.parent / "data" / "feasibility_gate.json"
        ensure_path_exists(feasibility_file.parent)

        with open(feasibility_file, 'w') as f:
            json.dump({
                "status": "halted",
                "reason": "insufficient_tcga_types",
                "downloaded_count": len(results["downloaded_types"]),
                "required_count": MIN_TCGA_TUMOR_TYPES,
                "downloaded_types": results["downloaded_types"],
                "failed_types": results["failed_types"]
            }, f, indent=2)

        results["success"] = False

    return results

def main():
    """
    Main entry point for data acquisition.
    """
    logger.info("Starting TCGA data acquisition...")

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Download TCGA data from HuggingFace")
    parser.add_argument("--types", nargs="+", help="TCGA tumor types to download (e.g., TCGA-BRCA TCGA-LUAD)")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files")
    args = parser.parse_args()

    tumor_types = args.types if args.types else None
    force = args.force

    # Execute download
    results = download_tcga_data(tumor_types=tumor_types, force=force)

    # Log summary
    logger.info("=" * 50)
    logger.info("Download Summary:")
    logger.info(f"  Success: {results['success']}")
    logger.info(f"  Downloaded types: {len(results['downloaded_types'])}")
    logger.info(f"  Failed types: {len(results['failed_types'])}")
    logger.info(f"  Feasibility met: {results['feasibility_met']}")

    if results["downloaded_types"]:
        logger.info(f"  Types: {', '.join(results['downloaded_types'])}")
    if results["failed_types"]:
        logger.warning(f"  Failed: {', '.join(results['failed_types'])}")

    # Return success/failure code
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main()
