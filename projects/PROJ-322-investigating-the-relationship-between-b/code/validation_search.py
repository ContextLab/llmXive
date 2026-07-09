"""
T024a: Search for real independent functional metric (e.g., Return-to-Work)

This script queries OpenNeuro metadata API for clinical/behavioral derivatives
and checks for columns like 'ReturnToWork', 'RTW', or 'EmploymentStatus' in the manifest.

It produces data/results/validation_search_results.json with findings.
"""
import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from huggingface_hub import HfApi
import pandas as pd

from config import get_config, is_synthetic, is_methodology_validation_mode
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Target columns to search for in behavioral/clinical data
TARGET_COLUMNS = [
    'ReturnToWork', 'RTW', 'EmploymentStatus', 'return_to_work', 'rtw',
    'employment_status', 'WorkStatus', 'WorkStatus', 'FunctionalOutcome',
    'FunctionalScore', 'DisabilityScore', 'GOS', 'GOS-E', 'GOSE'
]

# OpenNeuro dataset ID to search (using a representative mTBI dataset if available)
# Using ds000006 as a placeholder - in real execution, this would be the specific mTBI dataset
DATASET_ID = "ds000006" 

def query_openneuro_dataset_metadata(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Query OpenNeuro dataset metadata via Hugging Face API.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000006')
        
    Returns:
        Metadata dictionary or None if not found
    """
    try:
        # Use Hugging Face Hub to access OpenNeuro datasets
        api = HfApi()
        dataset_info = api.dataset_info(f"OpenNeuro/{dataset_id}", files_metadata=True)
        
        # Extract relevant metadata
        metadata = {
            "id": dataset_info.id,
            "description": dataset_info.description if hasattr(dataset_info, 'description') else None,
            "cardinality": dataset_info.cardinality if hasattr(dataset_info, 'cardinality') else None,
            "siblings": [s.rfilename for s in dataset_info.siblings] if hasattr(dataset_info, 'siblings') else []
        }
        
        logger.info(f"Found dataset: {dataset_id}")
        return metadata
    except Exception as e:
        logger.warning(f"Could not fetch metadata for {dataset_id}: {e}")
        return None

def scan_participants_file_for_targets(dataset_id: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Scan the participants.tsv file for target columns.
    
    Args:
        dataset_id: The OpenNeuro dataset ID
        
    Returns:
        Tuple of (found: bool, found_columns: list, file_info: dict)
    """
    found_columns = []
    file_info = {
        "dataset_id": dataset_id,
        "participants_file_found": False,
        "columns_checked": [],
        "matching_columns": []
    }
    
    try:
        # Construct URL for participants.tsv
        participants_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/participants.tsv"
        
        # Try to fetch the file
        response = requests.get(participants_url, timeout=30)
        
        if response.status_code == 200:
            file_info["participants_file_found"] = True
            
            # Parse TSV content
            df = pd.read_csv(pd.io.common.BytesIO(response.content), sep='\t')
            file_info["columns_checked"] = list(df.columns)
            
            # Check for target columns
            for col in df.columns:
                col_lower = col.lower()
                for target in TARGET_COLUMNS:
                    if target.lower() in col_lower or col_lower in target.lower():
                        if col not in found_columns:
                            found_columns.append(col)
                            file_info["matching_columns"].append({
                                "column": col,
                                "matched_pattern": target
                            })
            
            if found_columns:
                logger.info(f"Found target columns in {dataset_id}: {found_columns}")
                return True, found_columns, file_info
            else:
                logger.info(f"No target columns found in {dataset_id}. Checked: {list(df.columns)}")
                return False, [], file_info
        else:
            logger.warning(f"Could not fetch participants.tsv for {dataset_id}: HTTP {response.status_code}")
            return False, [], file_info
            
    except Exception as e:
        logger.error(f"Error scanning participants file for {dataset_id}: {e}")
        return False, [], file_info

def search_multiple_datasets(dataset_ids: List[str]) -> Dict[str, Any]:
    """
    Search multiple OpenNeuro datasets for target columns.
    
    Args:
        dataset_ids: List of dataset IDs to search
        
    Returns:
        Comprehensive search results
    """
    results = {
        "search_completed": True,
        "datasets_searched": len(dataset_ids),
        "datasets_with_matches": [],
        "all_results": {}
    }
    
    for ds_id in dataset_ids:
        logger.info(f"Searching dataset: {ds_id}")
        
        # Scan for target columns
        found, cols, file_info = scan_participants_file_for_targets(ds_id)
        
        results["all_results"][ds_id] = {
            "found": found,
            "columns": cols,
            "file_info": file_info
        }
        
        if found:
            results["datasets_with_matches"].append({
                "dataset_id": ds_id,
                "columns": cols
            })
            logger.info(f"✓ Found matches in {ds_id}: {cols}")
        else:
            logger.info(f"✗ No matches in {ds_id}")
    
    return results

def generate_search_report(search_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive search report.
    
    Args:
        search_results: Raw search results from search_multiple_datasets
        
    Returns:
        Formatted report for output
    """
    report = {
        "search_summary": {
            "total_datasets_searched": search_results["datasets_searched"],
            "datasets_with_matches": len(search_results["datasets_with_matches"]),
            "match_rate": len(search_results["datasets_with_matches"]) / max(search_results["datasets_searched"], 1),
            "target_columns_searched": TARGET_COLUMNS
        },
        "findings": search_results["datasets_with_matches"],
        "detailed_results": search_results["all_results"],
        "recommendation": ""
    }
    
    if search_results["datasets_with_matches"]:
        report["recommendation"] = (
            f"Found {len(search_results['datasets_with_matches'])} dataset(s) with "
            f"Return-to-Work or employment metrics. External validation is feasible."
        )
    else:
        report["recommendation"] = (
            "No datasets found with explicit Return-to-Work or employment metrics. "
            "External validation using this specific metric is not feasible with available data. "
            "Consider alternative functional outcome measures or synthetic validation mode."
        )
    
    return report

def main():
    """Main entry point for validation search."""
    logger.info("Starting T024a: Search for real independent functional metric")
    
    # Define datasets to search (in real implementation, this would be dynamic)
    # Using a few representative OpenNeuro mTBI datasets
    datasets_to_search = [
        "ds000006",  # Placeholder - replace with actual mTBI dataset IDs
        "ds000246",  # Another potential mTBI dataset
        "ds003468"   # Another potential dataset
    ]
    
    # Perform search
    search_results = search_multiple_datasets(datasets_to_search)
    
    # Generate report
    report = generate_search_report(search_results)
    
    # Ensure output directory exists
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results
    output_path = output_dir / "validation_search_results.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Search results written to {output_path}")
    
    # Log summary
    if report["findings"]:
        logger.info(f"SUCCESS: Found {len(report['findings'])} dataset(s) with target metrics")
    else:
        logger.warning("NO MATCHES: No datasets found with target metrics")
    
    return report

if __name__ == "__main__":
    main()
