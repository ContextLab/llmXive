import logging
import csv
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_env_var, ensure_dirs
from logger import get_logger
from utils import verify_real_data_source

# Configure logging
logger = get_logger(__name__)

# Constants
SEARCH_RESULTS_CSV = "data/results/dataset_search_results.csv"
CATEGORIZATION_LOG = "data/results/categorization_log.json"
NEGATIVE_REPORT_PATH = "data/results/negative_finding_report_v1.pdf"

def parse_dataset_metadata(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse dataset metadata to detect feedback_type and anxiety_measure.
    """
    description = dataset.get("description", "").lower()
    title = dataset.get("title", "").lower()
    custom_metadata = dataset.get("custom_metadata", {})

    feedback_type = "None"
    anxiety_measure = "None"

    # Detect feedback type
    if any(kw in description or kw in title for kw in ["simulated feedback", "simulated social validation", "fake feedback", "simulated validation"]):
        feedback_type = "simulated"
    elif any(kw in description or kw in title for kw in ["real feedback", "real social validation", "genuine feedback", "real validation"]):
        feedback_type = "real"
    elif any(kw in description or kw in title for kw in ["mixed feedback"]):
        feedback_type = "mixed"

    # Detect anxiety measure
    anxiety_keywords = ["lsas", "spin", "social anxiety scale", "anxiety measure", "scid"]
    for kw in anxiety_keywords:
        if kw in description or kw in title:
            anxiety_measure = kw.upper() if kw != "social anxiety scale" else "SAS"
            break

    return {
        "dataset_id": dataset.get("id", "unknown"),
        "title": dataset.get("label", dataset.get("title", "Unknown")),
        "feedback_type": feedback_type,
        "anxiety_measure": anxiety_measure,
        "url": dataset.get("url", dataset.get("downloadUrl", ""))
    }

def search_openneuro() -> List[Dict[str, Any]]:
    """
    Query OpenNeuro for EEG datasets with social feedback and anxiety measures.
    """
    # Simulated query for demonstration; in real implementation, use OpenNeuro API
    # Example: https://api.openneuro.org/datasets?modalities=EEG&query=social+feedback+anxiety
    # For now, returning a mock list that would be populated by actual API calls
    return [
        {
            "id": "ds001234",
            "label": "Social Feedback and Anxiety Study",
            "description": "EEG study with simulated social feedback and LSAS measures.",
            "url": "https://openneuro.org/datasets/ds001234"
        },
        {
            "id": "ds005678",
            "label": "Real Social Validation EEG",
            "description": "EEG study with real social validation and SPIN measures.",
            "url": "https://openneuro.org/datasets/ds005678"
        }
    ]

def search_physionet() -> List[Dict[str, Any]]:
    """
    Query PhysioNet for EEG datasets.
    """
    # Simulated query for demonstration
    return []

def search_zenodo() -> List[Dict[str, Any]]:
    """
    Query Zenodo for EEG datasets.
    """
    # Simulated query for demonstration
    return [
        {
            "id": "zenodo.123456",
            "label": "Social Anxiety and EEG Dataset",
            "description": "Dataset with simulated feedback and anxiety measures.",
            "url": "https://zenodo.org/record/123456"
        }
    ]

def categorize_dataset(metadata: Dict[str, Any]) -> str:
    """
    Categorize dataset based on presence of feedback_type and anxiety_measure.
    """
    feedback = metadata.get("feedback_type", "None")
    anxiety = metadata.get("anxiety_measure", "None")

    if feedback != "None" and anxiety != "None":
        return "Eligible"
    elif feedback != "None" and anxiety == "None":
        return "Sim-Only"
    elif feedback == "None" and anxiety != "None":
        return "Partial-Anxiety"
    elif feedback in ["real", "mixed"] and anxiety == "None":
        return "Real-Only"
    elif feedback == "None" and anxiety == "None":
        return "None"
    else:
        return "Partial-EEG"

def run_search_phase():
    """
    Execute the full search phase: query sources, categorize, log, and handle results.
    """
    ensure_dirs()
    logger.info("Starting dataset search phase...")

    # Query all sources
    openneuro_datasets = search_openneuro()
    physionet_datasets = search_physionet()
    zenodo_datasets = search_zenodo()

    all_datasets = openneuro_datasets + physionet_datasets + zenodo_datasets
    logger.info(f"Found {len(all_datasets)} candidate datasets.")

    # Parse and categorize
    categorized = {
        "Eligible": [],
        "Sim-Only": [],
        "Real-Only": [],
        "Partial-EEG": [],
        "Partial-Anxiety": [],
        "None": []
    }

    results_list = []

    for ds in all_datasets:
        metadata = parse_dataset_metadata(ds)
        status = categorize_dataset(metadata)

        # T058: Fail-Loud Enforcement
        # If marked "Eligible" but verify_real_data_source fails, re-categorize as "Partial-EEG" or "Partial-Anxiety"
        if status == "Eligible":
            try:
                # Verify the real data source is accessible
                verify_real_data_source(metadata["dataset_id"], metadata["url"])
                logger.info(f"Dataset {metadata['dataset_id']} verified successfully.")
            except (RuntimeError, Exception) as e:
                logger.warning(f"Dataset {metadata['dataset_id']} failed real data verification: {e}. Re-categorizing.")
                # Re-categorize based on what is missing (feedback or anxiety)
                # Since it was "Eligible", it had both, but now the data is unreachable.
                # We treat this as "Partial-EEG" (data unavailable) for safety.
                status = "Partial-EEG"
                metadata["status"] = status
                metadata["verification_error"] = str(e)

        categorized[status].append(metadata)
        results_list.append({
            "dataset_id": metadata["dataset_id"],
            "title": metadata["title"],
            "feedback_type": metadata["feedback_type"],
            "anxiety_measure": metadata["anxiety_measure"],
            "status": status,
            "url": metadata["url"]
        })

    # Write categorization log
    with open(CATEGORIZATION_LOG, "w") as f:
        json.dump(categorized, f, indent=2)
    logger.info(f"Categorization log written to {CATEGORIZATION_LOG}")

    # Write CSV results
    with open(SEARCH_RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"])
        writer.writeheader()
        writer.writerows(results_list)
    logger.info(f"Search results written to {SEARCH_RESULTS_CSV}")

    # T015: Abort Logic & Router
    if len(categorized["Eligible"]) == 0:
        logger.warning("No eligible datasets found. Triggering negative finding report.")
        # Trigger report generation
        from generate_negative_finding_report import main as generate_report_main
        generate_report_main()
        sys.exit(0)  # Success in triggering report
    else:
        logger.info(f"Found {len(categorized['Eligible'])} eligible datasets. Proceeding to next phase.")
        # In a real pipeline, we would pass the eligible dataset IDs to the next phase
        # For now, just log
        for ds in categorized["Eligible"]:
            logger.info(f"Eligible: {ds['dataset_id']} - {ds['title']}")

def main():
    """
    Entry point for search.py.
    """
    logging.basicConfig(level=logging.INFO)
    run_search_phase()

if __name__ == "__main__":
    main()