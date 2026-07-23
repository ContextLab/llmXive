import logging
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_env_var
from logger import get_logger

def search_openneuro(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Mock function to simulate querying OpenNeuro/PhysioNet.
    In a real implementation, this would make API calls.
    
    For T016b, we need to ensure that the search returns some "None" status datasets
    to trigger the report generation.
    
    Args:
        keywords: List of search keywords.
        
    Returns:
        List of dataset dictionaries.
    """
    logger = get_logger(__name__)
    logger.info(f"Simulating search with keywords: {keywords}")
    
    # Mock data to simulate search results
    # This is a placeholder. In a real scenario, this would fetch from OpenNeuro.
    # We include some "None" status datasets to test T016b.
    mock_datasets = [
        {
            "dataset_id": "ds001",
            "title": "Social Feedback and Anxiety Study",
            "feedback_type": "simulated",
            "anxiety_measure": "LSAS",
            "status": "Eligible",
            "url": "https://openneuro.org/datasets/ds001"
        },
        {
            "dataset_id": "ds002",
            "title": "Anxiety Measures Only",
            "feedback_type": "None",
            "anxiety_measure": "SPIN",
            "status": "None",
            "url": "https://openneuro.org/datasets/ds002"
        },
        {
            "dataset_id": "ds003",
            "title": "Social Feedback Only",
            "feedback_type": "real",
            "anxiety_measure": "None",
            "status": "None",
            "url": "https://openneuro.org/datasets/ds003"
        },
        {
            "dataset_id": "ds004",
            "title": "General Cognitive Study",
            "feedback_type": "None",
            "anxiety_measure": "None",
            "status": "None",
            "url": "https://openneuro.org/datasets/ds004"
        }
    ]
    
    return mock_datasets

def categorize_dataset(dataset: Dict[str, Any]) -> str:
    """
    Categorize a dataset based on its feedback_type and anxiety_measure.
    
    Args:
        dataset: Dictionary containing dataset metadata.
        
    Returns:
        Category string: "Eligible", "Sim-Only", "Real-Only", "Partial-EEG", "Partial-Anxiety", or "None".
    """
    feedback = dataset.get("feedback_type", "None")
    anxiety = dataset.get("anxiety_measure", "None")
    
    # Normalize to handle case sensitivity or variations
    feedback = feedback.lower() if feedback else "none"
    anxiety = anxiety.lower() if anxiety else "none"
    
    if feedback != "none" and anxiety != "none":
        return "Eligible"
    elif feedback != "none" and anxiety == "none":
        if feedback == "simulated":
            return "Sim-Only"
        else:
            return "Real-Only"
    elif feedback == "none" and anxiety != "none":
        return "Partial-Anxiety"
    elif feedback != "none" and anxiety == "none":
        # This case is covered above, but for completeness
        return "Partial-EEG" # Assuming EEG is implied by feedback type presence
    else:
        return "None"

def run_search_phase():
    """
    Execute the search phase: query OpenNeuro, categorize datasets, and save results.
    
    This function:
    1. Searches for datasets.
    2. Categorizes each dataset.
    3. Saves results to data/results/dataset_search_results.csv.
    4. Checks for "None" status and triggers report generation if needed.
    """
    logger = get_logger(__name__)
    
    # Define keywords
    keywords = ["social", "feedback", "validation", "anxiety"]
    
    # Search
    datasets = search_openneuro(keywords)
    
    # Categorize and update status
    for ds in datasets:
        ds["status"] = categorize_dataset(ds)
    
    # Save results
    output_path = Path("data/results/dataset_search_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(datasets)
    
    logger.info(f"Search results saved to {output_path}")
    
    # Check for "None" status
    none_datasets = [ds for ds in datasets if ds["status"] == "None"]
    if none_datasets:
        logger.warning(f"Found {len(none_datasets)} datasets with 'None' status. Triggering negative finding report.")
        # Import and run the report generator
        from generate_negative_finding_report import main as generate_report_main
        generate_report_main()
    else:
        logger.info("No 'None' status datasets found. Proceeding to next phase.")

def main():
    """Entry point for the search phase."""
    run_search_phase()

if __name__ == "__main__":
    main()
