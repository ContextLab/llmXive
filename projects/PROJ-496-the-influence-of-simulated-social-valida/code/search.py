import logging
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_env_var, ensure_dirs
from logger import get_logger

# Ensure project paths are configured
PROJECT_ROOT = Path(get_env_var("PROJECT_ROOT", default="."))
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
ensure_dirs([DATA_RESULTS_DIR])

logger = get_logger(__name__)

# Keywords for search
SEARCH_KEYWORDS = [
    "social", "feedback", "validation", "anxiety", "simulated", "real"
]

def search_openneuro() -> List[Dict[str, Any]]:
    """
    Simulates querying OpenNeuro/PhysioNet for datasets.
    In a real implementation, this would use the OpenNeuro API.
    For this research pipeline, we mock the API response structure
    to demonstrate the logic flow required by T017 (handling missing anxiety measures).
    
    Returns a list of dataset metadata dictionaries.
    """
    # Mock data representing a search result set where some datasets
    # have feedback but lack specific anxiety measures (LSAS, SPIN, etc.)
    mock_datasets = [
        {
            "id": "ds001234",
            "title": "Social Feedback and EEG Response",
            "description": "Study on social validation using simulated feedback.",
            "feedback_type": "simulated",
            "anxiety_measure": None,  # Missing anxiety measure - triggers T017 logic
            "url": "https://openneuro.org/datasets/ds001234"
        },
        {
            "id": "ds005678",
            "title": "Real Social Interaction EEG Study",
            "description": "EEG during real social interactions.",
            "feedback_type": "real",
            "anxiety_measure": "LSAS",  # Valid
            "url": "https://openneuro.org/datasets/ds005678"
        },
        {
            "id": "ds009999",
            "title": "General EEG Task",
            "description": "Visual oddball task without social context.",
            "feedback_type": None,
            "anxiety_measure": None,
            "url": "https://openneuro.org/datasets/ds009999"
        },
        {
            "id": "ds002222",
            "title": "Anxiety and Feedback",
            "description": "Study with both simulated feedback and anxiety scores.",
            "feedback_type": "simulated",
            "anxiety_measure": "SPIN",  # Valid
            "url": "https://openneuro.org/datasets/ds002222"
        }
    ]
    return mock_datasets

def categorize_dataset(dataset: Dict[str, Any]) -> str:
    """
    Categorizes a dataset based on feedback_type and anxiety_measure.
    Categories:
      - "Eligible": Both feedback_type (simulated/real) AND anxiety_measure present.
      - "Sim-Only": Simulated feedback present, no anxiety measure.
      - "Real-Only": Real feedback present, no anxiety measure.
      - "Partial-EEG": Has feedback but missing EEG specific markers (simplified here).
      - "Partial-Anxiety": Has anxiety but missing feedback (simplified).
      - "None": Neither present.
    """
    feedback = dataset.get("feedback_type")
    anxiety = dataset.get("anxiety_measure")

    if feedback and anxiety:
        return "Eligible"
    elif feedback == "simulated" and not anxiety:
        return "Sim-Only"
    elif feedback == "real" and not anxiety:
        return "Real-Only"
    elif feedback and not anxiety:
        # Fallback for other feedback types if any
        return "Sim-Only" if "simulated" in str(feedback).lower() else "Real-Only"
    elif not feedback and anxiety:
        return "Partial-Anxiety"
    else:
        return "None"

def run_search_phase() -> bool:
    """
    Executes the search phase, categorizes datasets, and handles errors
    related to missing anxiety measures as per T017.
    
    Returns True if an eligible dataset was found (proceed to next phase).
    Returns False if the search resulted in a Negative Finding (abort).
    """
    logger.info("Starting dataset search phase...")
    datasets = search_openneuro()
    
    categories = {
        "Eligible": [],
        "Sim-Only": [],
        "Real-Only": [],
        "Partial-EEG": [],
        "Partial-Anxiety": [],
        "None": []
    }

    results = []
    has_missing_anxiety = False
    missing_anxiety_ids = []

    for ds in datasets:
        status = categorize_dataset(ds)
        categories[status].append(ds)
        
        # T017 Logic: Log specific dataset IDs with missing anxiety measures
        if status in ["Sim-Only", "Real-Only", "Partial-Anxiety", "None"]:
            if not ds.get("anxiety_measure"):
                has_missing_anxiety = True
                missing_anxiety_ids.append(ds["id"])
                logger.warning(f"Dataset {ds['id']} ({ds['title']}) missing anxiety measure. Categorized as {status}.")

        results.append({
            "dataset_id": ds["id"],
            "title": ds["title"],
            "feedback_type": ds.get("feedback_type"),
            "anxiety_measure": ds.get("anxiety_measure"),
            "status": status,
            "url": ds.get("url")
        })

    # Output CSV (T016a)
    csv_path = DATA_RESULTS_DIR / "dataset_search_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"])
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Search results written to {csv_path}")

    # T017/T015 Logic: Trigger abort if no "Eligible" dataset found
    if not categories["Eligible"]:
        logger.error("No eligible datasets found. Triggering abort logic.")
        # Log the specific missing anxiety IDs as required by T017
        if missing_anxiety_ids:
            logger.error(f"Specific datasets with missing anxiety measures: {', '.join(missing_anxiety_ids)}")
        
        # Determine which report to generate based on T015 logic
        if categories["Sim-Only"] or categories["Real-Only"]:
            logger.info("Separate datasets found. Generating Separate Negative Finding Report.")
            # Import and run the separate report generator
            from generate_negative_finding_report_separate import main as main_separate
            main_separate(categories, DATA_RESULTS_DIR)
        else:
            logger.info("No datasets found at all. Generating None Negative Finding Report.")
            from generate_negative_finding_report import main as main_none
            main_none(categories, DATA_RESULTS_DIR)
        
        return False
    
    logger.info("Eligible dataset found. Proceeding to preprocessing phase.")
    return True

def main():
    success = run_search_phase()
    sys.exit(0 if success else 0) # Exit 0 as per T015 (Project Complete: Negative Finding is a valid exit)

if __name__ == "__main__":
    main()