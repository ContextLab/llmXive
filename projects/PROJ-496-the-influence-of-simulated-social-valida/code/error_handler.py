"""
Error handling module for User Story 1.
Implements logic to handle missing anxiety measures, categorize datasets,
and trigger the abort directive (Negative Finding) as per Plan Override.
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_env_var
from logger import get_logger
from search import categorize_dataset
from generate_negative_finding_report import main as generate_none_report
from generate_negative_finding_report_separate import main as generate_separate_report

# Configure logger
logger = get_logger(__name__)


def handle_missing_anxiety_measures(search_results_path: Path, output_dir: Path) -> int:
    """
    Handles the scenario where datasets are found but lack necessary anxiety measures.
    
    1. Loads the search results CSV.
    2. Iterates through datasets, explicitly logging those missing anxiety measures.
    3. Categorizes them using the logic from T014 (via search.categorize_dataset).
    4. Triggers the appropriate abort report generation (T015/T016b/T016c) based on 
       the resulting categories.
    
    Args:
        search_results_path: Path to the dataset_search_results.csv file.
        output_dir: Directory where reports (PDFs) will be saved.
    
    Returns:
        0 if the abort path was successfully executed (Project Complete: Negative Finding).
        1 if an error occurred during processing.
    """
    if not search_results_path.exists():
        logger.error(f"Search results file not found: {search_results_path}")
        return 1

    logger.info(f"Processing missing anxiety measures for: {search_results_path}")
    
    # Load results
    datasets = []
    try:
        with open(search_results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                datasets.append(row)
    except Exception as e:
        logger.error(f"Failed to load search results: {e}")
        return 1

    if not datasets:
        logger.warning("No datasets found in search results. Triggering 'None' abort.")
        # Trigger "No Datasets" report
        try:
            generate_none_report(
                dataset_id="N/A", 
                title="No Datasets Found", 
                url="N/A", 
                reason="Search returned no results.",
                output_path=output_dir / "negative_finding_report_v1.pdf"
            )
            return 0
        except Exception as e:
            logger.error(f"Failed to generate 'None' report: {e}")
            return 1

    # Categorize and log missing anxiety measures
    missing_anxiety_ids = []
    category_counts = {
        "Eligible": 0,
        "Sim-Only": 0,
        "Real-Only": 0,
        "Partial-EEG": 0,
        "Partial-Anxiety": 0,
        "None": 0
    }
    
    sim_only_list = []
    real_only_list = []
    none_list = []

    for ds in datasets:
        ds_id = ds.get('dataset_id', 'Unknown')
        ds_title = ds.get('title', 'Unknown')
        ds_url = ds.get('url', '')
        
        # Determine category using the existing categorization logic
        # We assume the row has 'feedback_type' and 'anxiety_measure' columns populated or 'None'
        feedback_type = ds.get('feedback_type', 'None')
        anxiety_measure = ds.get('anxiety_measure', 'None')
        
        # Re-categorize to ensure consistency with T014 logic
        # Note: categorize_dataset expects a dict similar to the API response or a row
        # We map the CSV row to the expected structure if necessary, or pass directly if compatible.
        # Assuming the CSV row structure matches what categorize_dataset expects for the 'dataset' arg.
        category = categorize_dataset({"id": ds_id, "title": ds_title, "feedback_type": feedback_type, "anxiety_measure": anxiety_measure})
        
        category_counts[category] = category_counts.get(category, 0) + 1

        # Log specific dataset IDs missing anxiety measures
        if anxiety_measure == 'None' or anxiety_measure is None or anxiety_measure == '':
            missing_anxiety_ids.append(ds_id)
            logger.warning(f"Dataset {ds_id} ({ds_title}) is missing anxiety measures.")

        # Collect lists for report generation
        if category == "Sim-Only":
            sim_only_list.append({"id": ds_id, "title": ds_title, "url": ds_url})
        elif category == "Real-Only":
            real_only_list.append({"id": ds_id, "title": ds_title, "url": ds_url})
        elif category == "None":
            none_list.append({"id": ds_id, "title": ds_title, "url": ds_url})

    # Decision Logic (Plan Override T015)
    # If "Eligible" found, we would proceed (but this function is for error handling/abort path)
    # The task description implies we are handling the "missing" case which leads to abort.
    # However, T015 says: If "Eligible" found, proceed; ELSE, log and trigger abort.
    
    if category_counts["Eligible"] > 0:
        logger.info("Eligible datasets found. No abort required. Exiting error handler.")
        return 0 # Normal flow continues

    # If we are here, no eligible datasets were found.
    logger.info("No eligible datasets found. Triggering abort logic (Negative Finding).")

    # Determine which report to generate based on T016b vs T016c
    if category_counts["Sim-Only"] > 0 or category_counts["Real-Only"] > 0:
        # Scenario: Separate Datasets Found (T016c)
        logger.info("Scenario: Separate Datasets Found (Sim-Only or Real-Only).")
        report_path = output_dir / "negative_finding_report_separate.pdf"
        
        try:
            # Call the separate report generator
            # We pass the collected lists to the generator
            generate_separate_report(
                sim_only=sim_only_list,
                real_only=real_only_list,
                none_list=none_list, # Though T016c focuses on Sim/Real, None might be relevant context
                output_path=report_path
            )
            logger.info(f"Generated Separate Negative Finding Report: {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate separate report: {e}")
            return 1

    elif category_counts["None"] > 0 or category_counts["Partial-EEG"] > 0 or category_counts["Partial-Anxiety"] > 0:
        # Scenario: No Eligible Datasets Found (could be empty, or partials)
        # T016b: "No Eligible Datasets Found"
        logger.info("Scenario: No Eligible Datasets Found (or only partials).")
        report_path = output_dir / "negative_finding_report_v1.pdf"
        
        try:
            # We need to pass the list of "None" status datasets or all non-eligible ones
            # For T016b, the content is "Summary of search, list of 'None' status datasets"
            # If we have partials, we list them as the "gap".
            # Let's pass all non-eligible datasets as the "gap" list for the report.
            gap_list = [
                {"id": ds["dataset_id"], "title": ds["title"], "url": ds["url"]}
                for ds in datasets 
                if categorize_dataset({"id": ds["dataset_id"], "title": ds["title"], "feedback_type": ds.get("feedback_type"), "anxiety_measure": ds.get("anxiety_measure")}) != "Eligible"
            ]
            
            # Re-using the None generator but populating it with the gap list
            # The existing generate_negative_finding_report.main might need specific args.
            # Assuming it takes a list of datasets and a reason.
            generate_none_report(
                dataset_id="N/A", 
                title="No Eligible Datasets Found", 
                url="N/A", 
                reason="Search found no datasets with both simulated/real feedback and anxiety measures.",
                output_path=report_path,
                gap_datasets=gap_list
            )
            logger.info(f"Generated 'None' Negative Finding Report: {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate 'None' report: {e}")
            return 1

    else:
        logger.error("Unexpected state: No eligible, no sim-only, no real-only, no none?")
        return 1

    return 0


def main():
    """Entry point for running the error handler as a script."""
    import argparse
    from config import get_env_var

    parser = argparse.ArgumentParser(description="Handle missing anxiety measures and trigger abort.")
    parser.add_argument("--input", type=str, required=True, help="Path to dataset_search_results.csv")
    parser.add_argument("--output", type=str, default="data/results", help="Output directory for reports")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    success = handle_missing_anxiety_measures(input_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
