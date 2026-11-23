import sys
from pathlib import Path
import csv
import logging
from typing import List, Dict, Any, Optional

from config import get_env_var
from logger import get_logger
from report_generator import generate_negative_finding_report

# Ensure the report generator module is importable from the same directory
# If this script is run as a module, we assume the project root is in sys.path
# or we adjust it.
try:
    from report_generator import generate_negative_finding_report
except ImportError:
    # Fallback if running as a script without proper path setup
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from report_generator import generate_negative_finding_report

def load_search_results(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load the dataset search results from a CSV file.
    
    Args:
        csv_path: Path to the CSV file containing search results.
        
    Returns:
        A list of dictionaries, each representing a dataset row.
    """
    datasets = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Search results file not found: {csv_path}")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            datasets.append(row)
    return datasets

def main():
    """
    Main entry point for generating the Negative Finding Report (None status).
    
    This function:
    1. Loads search results from data/results/dataset_search_results.csv.
    2. Filters for datasets with status "None".
    3. Generates a PDF report summarizing the search and the data gap.
    4. Writes the report to data/results/negative_finding_report_v1.pdf.
    """
    logger = get_logger(__name__)
    
    # Define paths
    search_results_path = Path("data/results/dataset_search_results.csv")
    output_pdf_path = Path("data/results/negative_finding_report_v1.pdf")
    
    # Ensure output directory exists
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading search results from {search_results_path}")
    try:
        all_datasets = load_search_results(str(search_results_path))
    except FileNotFoundError as e:
        logger.error(f"Failed to load search results: {e}")
        sys.exit(1)
    
    # Filter for "None" status datasets
    none_datasets = [d for d in all_datasets if d.get('status') == 'None']
    
    if not none_datasets:
        logger.warning("No datasets with 'None' status found. Report generation may be unnecessary or empty.")
        # Still generate a report indicating no "None" status datasets were found, 
        # or exit? The task says "Trigger Condition: Execute ONLY IF T015 detects 'None' status".
        # If T015 detects 'None' status, then this function is called. 
        # If the CSV is empty or has no 'None' status, it implies T015 logic might be inconsistent.
        # We proceed to generate the report with an empty list to reflect the state.
    
    logger.info(f"Found {len(none_datasets)} datasets with 'None' status.")
    
    # Prepare summary data
    search_summary = {
        "total_datasets_searched": len(all_datasets),
        "none_status_count": len(none_datasets),
        "search_keywords": ["social", "feedback", "validation", "anxiety"], # From T012
        "data_gap_statement": (
            "No eligible datasets were found that contain both social feedback manipulation "
            "and social anxiety measures. This represents a critical data gap preventing "
            "the proposed analysis of the influence of simulated social validation on neural "
            "responses to novel information."
        )
    }
    
    # Generate the report
    logger.info(f"Generating Negative Finding Report at {output_pdf_path}")
    try:
        generate_negative_finding_report(
            output_path=str(output_pdf_path),
            search_summary=search_summary,
            none_datasets=none_datasets,
            report_type="none"
        )
        logger.info("Report generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
