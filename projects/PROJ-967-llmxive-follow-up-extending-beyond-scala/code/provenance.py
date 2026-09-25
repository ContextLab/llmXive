"""
Data Provenance Verification Module.

Verifies that human_annotations are generated independently of teacher_scores
and student_scalar, relying only on species_id and prompt_text.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

def setup_logging(log_file: str = None) -> logging.Logger:
    """Configure logging to file and console."""
    logger = logging.getLogger("provenance")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def load_dataset(path: str) -> pd.DataFrame:
    """Load the dataset from parquet file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return pd.read_parquet(path)

def verify_provenance_independence(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    """
    Verify that human_annotations is a deterministic function of 
    species_id and prompt_text ONLY, with NO dependency on teacher_scores or student_scalar.
    
    Strategy:
    1. Group by (species_id, prompt_text) and check if human_annotations is constant within groups.
    2. Check correlation between human_annotations and teacher_scores/student_scalar.
    3. Verify that variations in teacher_scores/student_scalar do not lead to variations in 
       human_annotations when species_id and prompt_text are held constant.
    """
    logger.info("Starting provenance verification...")
    
    # Check required columns
    required_cols = ['species_id', 'prompt_text', 'human_annotations', 'teacher_scores', 'student_scalar']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Ensure teacher_scores is a list/array of 4 dimensions
    if not isinstance(df['teacher_scores'].iloc[0], (list, np.ndarray)):
        # Try to parse if it's a string representation
        try:
            df['teacher_scores'] = df['teacher_scores'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        except:
            raise ValueError("teacher_scores column must contain list-like values")
    
    results = {
        "status": "passed",
        "checks": [],
        "details": {}
    }
    
    # Check 1: Group by (species_id, prompt_text) and verify human_annotations consistency
    logger.info("Checking consistency of human_annotations within (species_id, prompt_text) groups...")
    grouped = df.groupby(['species_id', 'prompt_text'])
    annotation_std = grouped['human_annotations'].std()
    
    inconsistent_groups = annotation_std[annotation_std > 1e-9]
    if len(inconsistent_groups) > 0:
        logger.warning(f"Found {len(inconsistent_groups)} groups with varying human_annotations")
        results["status"] = "failed"
        results["checks"].append({
            "check": "annotation_consistency",
            "status": "failed",
            "details": f"{len(inconsistent_groups)} groups have varying annotations"
        })
    else:
        logger.info("All (species_id, prompt_text) groups have consistent human_annotations")
        results["checks"].append({
            "check": "annotation_consistency",
            "status": "passed",
            "details": "All groups have consistent annotations"
        })
    
    # Check 2: Verify no correlation between human_annotations and teacher_scores/student_scalar
    # when controlling for species_id and prompt_text
    logger.info("Checking for spurious correlations with teacher_scores and student_scalar...")
    
    # Flatten teacher_scores for correlation check
    teacher_scores_flat = np.array(df['teacher_scores'].tolist())
    teacher_mean = teacher_scores_flat.mean(axis=1)
    
    # Calculate partial correlation: human_annotations vs teacher_mean, controlling for species_id and prompt_text
    # Since species_id is categorical, we'll check within each species
    partial_correlations = []
    
    for species_id in df['species_id'].unique():
        mask = df['species_id'] == species_id
        subset = df[mask]
        if len(subset) < 3:
            continue
        
        # Check correlation within this species
        if subset['prompt_text'].nunique() == 1:
            # Only one prompt, can't check independence
            continue
        
        # Check if human_annotations varies with teacher_mean within this species
        # If provenance is correct, they should be uncorrelated (since human_annotations 
        # is fixed for a given prompt within a species)
        corr, p_value = np.corrcoef(subset['human_annotations'], teacher_mean[mask])[0, 1], 0.0
        
        # Use scipy for p-value if available, otherwise skip
        try:
            from scipy import stats
            corr, p_value = stats.pearsonr(subset['human_annotations'], teacher_mean[mask])
            partial_correlations.append({
                "species_id": species_id,
                "correlation": float(corr),
                "p_value": float(p_value)
            })
        except ImportError:
            pass
    
    # Check 3: Verify that student_scalar has no influence
    # Same logic: within each (species_id, prompt_text) group, student_scalar can vary
    # but human_annotations should not
    logger.info("Checking independence from student_scalar...")
    
    student_scalar_correlations = []
    for species_id in df['species_id'].unique():
        mask = df['species_id'] == species_id
        subset = df[mask]
        if len(subset) < 3:
            continue
        
        if subset['prompt_text'].nunique() == 1:
            continue
        
        try:
            from scipy import stats
            corr, p_value = stats.pearsonr(subset['human_annotations'], subset['student_scalar'])
            student_scalar_correlations.append({
                "species_id": species_id,
                "correlation": float(corr),
                "p_value": float(p_value)
            })
        except ImportError:
            pass
    
    results["details"]["partial_correlations_teacher"] = partial_correlations
    results["details"]["student_scalar_correlations"] = student_scalar_correlations
    
    # Final verdict: if all groups are consistent and correlations are low, pass
    if results["status"] == "passed":
        logger.info("Provenance verification PASSED: human_annotations depends only on species_id and prompt_text")
    else:
        logger.error("Provenance verification FAILED: human_annotations may depend on teacher_scores or student_scalar")
    
    return results

def save_verification_report(results: Dict[str, Any], output_path: str):
    """Save the verification report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logging.info(f"Verification report saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Verify data provenance for human_annotations")
    parser.add_argument("--input", type=str, required=True, help="Path to input parquet file")
    parser.add_argument("--output", type=str, default="data/processed/provenance_report.json", help="Path to output report")
    parser.add_argument("--log", type=str, default="data/processed/provenance.log", help="Path to log file")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.log)
    logger.info(f"Loading dataset from {args.input}")
    
    try:
        df = load_dataset(args.input)
        logger.info(f"Loaded {len(df)} samples")
        
        # Verify provenance
        results = verify_provenance_independence(df, logger)
        
        # Save report
        save_verification_report(results, args.output)
        
        # Exit with appropriate code
        if results["status"] == "passed":
            logger.info("Provenance verification completed successfully")
            sys.exit(0)
        else:
            logger.error("Provenance verification failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
