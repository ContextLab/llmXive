"""
Detect label heterogeneity in plant metabolomics studies.

This script analyzes measurement_method and assay_score distributions
to detect heterogeneity in disease resistance labels.
"""
import os
import sys
import json
import glob
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when required data files are missing."""
    pass

def load_filtered_manifest(manifest_path: str = "data/raw/filtered_study_manifest.json") -> List[Dict[str, Any]]:
    """
    Load the filtered study manifest containing studies with resistance metadata.
    
    Args:
        manifest_path: Path to the filtered study manifest JSON file.
        
    Returns:
        List of study dictionaries.
        
    Raises:
        DataUnavailableError: If the manifest file is missing or invalid.
    """
    if not os.path.exists(manifest_path):
        raise DataUnavailableError(
            f"Filtered study manifest not found at {manifest_path}. "
            "Run T013c (filter_studies.py) first."
        )
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if not isinstance(manifest, list):
            raise DataUnavailableError(
                f"Expected manifest to be a list, got {type(manifest)}"
            )
        
        logger.info(f"Loaded {len(manifest)} studies from filtered manifest")
        return manifest
    except json.JSONDecodeError as e:
        raise DataUnavailableError(f"Invalid JSON in manifest: {e}")

def load_phenotype_files(study_ids: List[str], raw_data_dir: str = "data/raw") -> Dict[str, pd.DataFrame]:
    """
    Load phenotype CSV files for a list of studies.
    
    Args:
        study_ids: List of study IDs to load.
        raw_data_dir: Directory containing raw phenotype files.
        
    Returns:
        Dictionary mapping study_id to DataFrame.
        
    Raises:
        DataUnavailableError: If any required phenotype file is missing.
    """
    phenotype_data = {}
    
    for study_id in study_ids:
        phenotype_path = os.path.join(raw_data_dir, f"{study_id}_phenotype.csv")
        
        if not os.path.exists(phenotype_path):
            raise DataUnavailableError(
                f"Raw phenotype file missing for study {study_id}: {phenotype_path}. "
                "Run T012b first to download phenotype data."
            )
        
        try:
            df = pd.read_csv(phenotype_path)
            phenotype_data[study_id] = df
            logger.info(f"Loaded phenotype data for {study_id}: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            raise DataUnavailableError(f"Failed to load phenotype file for {study_id}: {e}")
    
    return phenotype_data

def analyze_heterogeneity(phenotype_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Analyze heterogeneity in measurement methods and assay scores.
    
    Heterogeneity is defined as:
    - More than 2 unique measurement methods
    - Mixed binary/ordinal scales in assay scores
    
    Args:
        phenotype_data: Dictionary mapping study_id to phenotype DataFrame.
        
    Returns:
        List of heterogeneity analysis results per study.
    """
    results = []
    
    for study_id, df in phenotype_data.items():
        # Identify relevant columns
        method_col = None
        score_col = None
        
        # Look for measurement method column
        method_candidates = ['measurement_method', 'assay_method', 'method', 'platform', 'technique']
        for col in method_candidates:
            if col in df.columns:
                method_col = col
                break
        
        # Look for assay score column
        score_candidates = ['assay_score', 'score', 'value', 'measurement', 'intensity', 'resistance_score']
        for col in score_candidates:
            if col in df.columns:
                score_col = col
                break
        
        # Analyze methods
        methods = []
        if method_col and method_col in df.columns:
            methods = sorted(df[method_col].dropna().astype(str).unique().tolist())
        
        # Analyze score types
        score_types = []
        if score_col and score_col in df.columns:
            scores = df[score_col].dropna()
            if len(scores) > 0:
                # Check if binary (only 2 unique values)
                unique_scores = scores.unique()
                if len(unique_scores) == 2:
                    score_types.append('binary')
                elif len(unique_scores) > 2:
                    # Check if numeric (ordinal) or categorical
                    try:
                        numeric_scores = pd.to_numeric(scores, errors='raise')
                        score_types.append('ordinal')
                    except (ValueError, TypeError):
                        score_types.append('categorical')
        
        # Determine heterogeneity
        heterogeneity_detected = False
        
        # Condition 1: More than 2 unique methods
        if len(methods) > 2:
            heterogeneity_detected = True
            logger.info(f"Study {study_id}: Heterogeneity detected - {len(methods)} measurement methods")
        
        # Condition 2: Mixed binary/ordinal scales
        if 'binary' in score_types and 'ordinal' in score_types:
            heterogeneity_detected = True
            logger.info(f"Study {study_id}: Heterogeneity detected - mixed binary/ordinal scores")
        
        # Condition 3: More than 2 unique score types
        if len(score_types) > 2:
            heterogeneity_detected = True
            logger.info(f"Study {study_id}: Heterogeneity detected - {len(score_types)} score types")
        
        results.append({
            'study_id': study_id,
            'heterogeneity_detected': heterogeneity_detected,
            'methods': methods,
            'score_types': score_types,
            'method_count': len(methods),
            'score_type_count': len(score_types)
        })
    
    return results

def save_report(results: List[Dict[str, Any]], output_path: str = "data/processed/heterogeneity_report.json"):
    """
    Save the heterogeneity analysis report to a JSON file.
    
    Args:
        results: List of heterogeneity analysis results.
        output_path: Path to save the JSON report.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Heterogeneity report saved to {output_path}")

def main():
    """Main entry point for the heterogeneity detection script."""
    logger.info("Starting label heterogeneity detection")
    
    try:
        # Load filtered manifest
        manifest = load_filtered_manifest()
        
        if not manifest:
            logger.warning("No studies found in filtered manifest. Creating empty report.")
            save_report([])
            return
        
        # Extract study IDs
        study_ids = [study['study_id'] for study in manifest]
        
        # Load phenotype files
        phenotype_data = load_phenotype_files(study_ids)
        
        # Analyze heterogeneity
        results = analyze_heterogeneity(phenotype_data)
        
        # Save report
        save_report(results)
        
        # Summary
        hetero_count = sum(1 for r in results if r['heterogeneity_detected'])
        logger.info(f"Heterogeneity detection complete: {hetero_count}/{len(results)} studies show heterogeneity")
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during heterogeneity detection: {e}")
        raise

if __name__ == "__main__":
    main()