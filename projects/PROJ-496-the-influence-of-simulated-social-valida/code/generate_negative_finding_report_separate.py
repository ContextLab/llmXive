"""
Module to generate the 'Negative Finding Report' for the 'Separate Datasets Found' scenario.

This script is executed ONLY IF T015 detects 'Sim-Only' or 'Real-Only' status.
It reads the search results from data/results/dataset_search_results.csv,
filters for the specific categories, and generates a detailed PDF report
listing the identified datasets.
"""
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from config import get_env_var
from logger import get_logger
from report_generator import generate_negative_finding_report as generate_base_report

logger = get_logger(__name__)


def load_search_results(file_path: str) -> List[Dict[str, Any]]:
    """
    Load the dataset search results from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing search results.
        
    Returns:
        List of dictionaries representing each dataset row.
    """
    results = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Search results file not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def filter_separate_datasets(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Filter the search results to separate 'Sim-Only' and 'Real-Only' datasets.
    
    Args:
        results: List of all dataset search results.
        
    Returns:
        Dictionary with keys 'sim_only' and 'real_only' containing lists of datasets.
    """
    sim_only = []
    real_only = []
    
    for row in results:
        status = row.get('status', '').strip()
        if status == 'Sim-Only':
            sim_only.append(row)
        elif status == 'Real-Only':
            real_only.append(row)
            
    return {
        'sim_only': sim_only,
        'real_only': real_only
    }


def generate_separate_finding_report(
    output_path: str,
    sim_only_datasets: List[Dict[str, Any]],
    real_only_datasets: List[Dict[str, Any]],
    search_summary: Optional[str] = None
) -> bool:
    """
    Generate a PDF report for the 'Separate Datasets Found' scenario.
    
    This report explicitly lists the identified 'Sim-Only' and 'Real-Only'
    dataset IDs, titles, and URLs.
    
    Args:
        output_path: Path where the PDF report will be saved.
        sim_only_datasets: List of datasets with 'Sim-Only' status.
        real_only_datasets: List of datasets with 'Real-Only' status.
        search_summary: Optional summary string of the search performed.
        
    Returns:
        True if report generation was successful, False otherwise.
    """
    try:
        # Prepare data for the report generator
        report_data = {
            'scenario': 'Separate Datasets Found',
            'description': (
                "No single dataset was found containing both social feedback manipulation "
                "and social anxiety measures. However, separate datasets were identified: "
                "one set containing only simulated feedback (Sim-Only) and another set "
                "containing only real feedback (Real-Only). This report lists these candidates."
            ),
            'sections': [
                {
                    'title': 'Sim-Only Datasets',
                    'datasets': sim_only_datasets,
                    'empty_message': "No 'Sim-Only' datasets were found."
                },
                {
                    'title': 'Real-Only Datasets',
                    'datasets': real_only_datasets,
                    'empty_message': "No 'Real-Only' datasets were found."
                }
            ]
        }
        
        if search_summary:
            report_data['search_summary'] = search_summary
            
        # Use the existing report generator utility
        generate_base_report(output_path, report_data)
        
        logger.info(f"Successfully generated separate finding report: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate separate finding report: {e}")
        return False


def main():
    """
    Main entry point for generating the 'Separate Datasets Found' report.
    
    Expects the search results CSV to be at:
    data/results/dataset_search_results.csv
    
    Outputs the report to:
    data/results/negative_finding_report_separate.pdf
    """
    # Define paths
    project_root = Path(get_env_var('PROJECT_ROOT', '.'))
    search_results_path = project_root / 'data' / 'results' / 'dataset_search_results.csv'
    output_path = project_root / 'data' / 'results' / 'negative_finding_report_separate.pdf'
    
    logger.info("Starting generation of 'Separate Datasets Found' report...")
    
    # Load search results
    try:
        results = load_search_results(str(search_results_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
        
    # Filter for separate datasets
    separate_datasets = filter_separate_datasets(results)
    
    # Check if we actually have separate datasets
    if not separate_datasets['sim_only'] and not separate_datasets['real_only']:
        logger.warning(
            "No 'Sim-Only' or 'Real-Only' datasets found. "
            "This report generation may be unnecessary. "
            "Proceeding anyway to generate an empty report."
        )
        
    # Generate the report
    success = generate_separate_finding_report(
        output_path=str(output_path),
        sim_only_datasets=separate_datasets['sim_only'],
        real_only_datasets=separate_datasets['real_only'],
        search_summary="Search performed for keywords: social, feedback, validation, anxiety"
    )
    
    if not success:
        logger.error("Report generation failed.")
        sys.exit(1)
        
    logger.info("Report generation completed successfully.")


if __name__ == "__main__":
    main()