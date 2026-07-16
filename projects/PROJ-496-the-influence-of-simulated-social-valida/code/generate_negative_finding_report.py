"""
Script to generate the Negative Finding Report (T016b).
This script is triggered when T015 detects no eligible datasets.
"""
import sys
from pathlib import Path
import csv

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_env_var
from logger import get_logger
from report_generator import generate_negative_finding_report

logger = get_logger(__name__)

def load_search_results(csv_path: str) -> tuple:
    """
    Load the search results CSV and categorize them into lists for the report.
    Returns: (summary_dict, none_list, sim_only_list, real_only_list)
    """
    summary = {
        "keywords": "social, feedback, validation, anxiety",
        "total_results": 0
    }
    none_datasets = []
    sim_only_datasets = []
    real_only_datasets = []

    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            summary["total_results"] = len(rows)
            
            for row in rows:
                status = row.get('status', 'None')
                ds_entry = {
                    'id': row.get('dataset_id', ''),
                    'title': row.get('title', ''),
                    'feedback_type': row.get('feedback_type', ''),
                    'anxiety_measure': row.get('anxiety_measure', ''),
                    'url': row.get('url', '')
                }
                
                if status == 'None':
                    none_datasets.append(ds_entry)
                elif status == 'Sim-Only':
                    sim_only_datasets.append(ds_entry)
                elif status == 'Real-Only':
                    real_only_datasets.append(ds_entry)
                    
    except FileNotFoundError:
        logger.error(f"Search results file not found: {csv_path}")
        # If file not found, we assume no results
        logger.warning("Proceeding with empty dataset lists.")

    return summary, none_datasets, sim_only_datasets, real_only_datasets

def main():
    """Main entry point for generating the Negative Finding Report."""
    input_csv = "data/results/dataset_search_results.csv"
    output_pdf = "data/results/negative_finding_report_v1.pdf"

    logger.info(f"Loading search results from {input_csv}")
    summary, none_datasets, sim_only_datasets, real_only_datasets = load_search_results(input_csv)

    logger.info(f"Generating Negative Finding Report: {len(none_datasets)} 'None', {len(sim_only_datasets)} 'Sim-Only', {len(real_only_datasets)} 'Real-Only'")
    
    generate_negative_finding_report(
        output_path=output_pdf,
        search_summary=summary,
        none_datasets=none_datasets,
        sim_only_datasets=sim_only_datasets if sim_only_datasets else None,
        real_only_datasets=real_only_datasets if real_only_datasets else None
    )

    logger.info(f"Report successfully generated at {output_pdf}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
