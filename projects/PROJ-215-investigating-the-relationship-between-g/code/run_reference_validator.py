import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from code.reference_validator import validate_url_access, run_reference_validation
from code.config import get_output_path, ensure_directories
from code.utils.logging import get_logger

def main():
    """
    Execute the Reference-Validator Agent on external cohort URLs.
    
    This task verifies accessibility and accuracy of external cohort URLs 
    (e.g., UK Biobank, MetaHIT) before T031 (Independent Cohort Validation).
    
    Output: results/validation_urls_verified.json
    """
    logger = get_logger(__name__)
    logger.info("Starting Reference-Validator Agent (Task T030b)")
    
    # Ensure output directory exists
    ensure_directories()
    
    # Define the external cohort URLs to verify
    # These are representative URLs for major microbiome/mental health datasets
    # In a real scenario, these would be specific study access points or API endpoints
    external_cohorts: List[Dict[str, Any]] = [
        {
            "name": "UK Biobank Microbiome",
            "url": "https://www.ukbiobank.ac.uk/",
            "description": "UK Biobank - Large-scale biomedical database",
            "type": "cohort"
        },
        {
            "name": "MetaHIT",
            "url": "https://www.metahit.eu/",
            "description": "MetaHIT Project - Metagenomics of the Human Intestinal Tract",
            "type": "cohort"
        },
        {
            "name": "AGP (American Gut Project)",
            "url": "https://americangut.org/",
            "description": "American Gut Project - Citizen science microbiome study",
            "type": "cohort"
        },
        {
            "name": "Qiita Study Portal",
            "url": "https://qiita.ucsd.edu/",
            "description": "Qiita - Microbiome data analysis platform",
            "type": "portal"
        }
    ]
    
    # Run validation on all cohorts
    validation_results = run_reference_validation(external_cohorts)
    
    # Prepare output
    output_data = {
        "task_id": "T030b",
        "validation_timestamp": validation_results.get("timestamp", ""),
        "total_cohorts_checked": validation_results.get("total_cohorts", 0),
        "accessible_cohorts": validation_results.get("accessible_count", 0),
        "inaccessible_cohorts": validation_results.get("inaccessible_count", 0),
        "results": validation_results.get("details", []),
        "gate_status": "PASS" if validation_results.get("accessible_count", 0) > 0 else "FAIL"
    }
    
    # Write output to results/validation_urls_verified.json
    output_path = get_output_path("results/validation_urls_verified.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Validation complete. Results written to {output_path}")
    logger.info(f"Gate Status: {output_data['gate_status']}")
    logger.info(f"Accessible: {output_data['accessible_cohorts']}/{output_data['total_cohorts_checked']}")
    
    return output_data

if __name__ == "__main__":
    main()
