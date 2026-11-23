import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from code.utils.logging import get_logger

logger = get_logger(__name__)

def validate_age(study: Dict[str, Any]) -> bool:
    """Validate age range is within 6-12."""
    age_range = study.get("age_range", {})
    if not age_range:
        return False
    min_age = age_range.get("min")
    max_age = age_range.get("max")
    if min_age is None or max_age is None:
        return False
    return 6 <= min_age <= 12 and 6 <= max_age <= 12

def validate_asd_diagnosis(study: Dict[str, Any]) -> bool:
    """Validate diagnosis is ASD."""
    diagnosis = study.get("diagnosis")
    return diagnosis == "ASD"

def validate_outcomes(study: Dict[str, Any]) -> bool:
    """Validate outcomes contain social skill measures."""
    outcomes = study.get("outcomes", [])
    if not outcomes:
        return False
    for outcome in outcomes:
        if isinstance(outcome, str):
            lower_outcome = outcome.lower()
            if "social skill" in lower_outcome:
                return True
            if any(m in lower_outcome for m in ["srs", "abc", "ssis", "pep"]):
                return True
    return False

def validate_blinding_status(study: Dict[str, Any]) -> bool:
    """Validate blinding status fields exist (even if null/unknown)."""
    # We accept studies where blinding info is missing (flag as 'unknown')
    # We only fail if the study structure is fundamentally broken
    return True

def log_excluded_study(study_id: str, reason: str, output_dir: Path) -> None:
    """Log excluded study to JSONL file."""
    log_file = output_dir / "excluded_studies.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "study_id": study_id,
        "reason": reason,
        "timestamp": timestamp
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def filter_included_studies(studies: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    """Filter studies based on inclusion criteria."""
    included = []
    for study in studies:
        study_id = study.get("id", "unknown")
        
        # Check age range (6-12)
        if not validate_age(study):
            log_excluded_study(study_id, "INVALID_AGE_RANGE", output_dir)
            continue
        
        # Check ASD diagnosis
        if not validate_asd_diagnosis(study):
            log_excluded_study(study_id, "INVALID_DIAGNOSIS", output_dir)
            continue
        
        # Check outcomes
        if not validate_outcomes(study):
            log_excluded_study(study_id, "INVALID_OUTCOME", output_dir)
            continue
        
        included.append(study)
    
    return included

def handle_multi_arm_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split control groups proportionally for multi-arm studies."""
    # Placeholder for multi-arm logic - returns studies as-is for now
    return studies

def clean_studies(studies: List[Dict[str, Any]], output_dir: Path) -> pd.DataFrame:
    """Main cleaning pipeline: validate, filter, and format studies."""
    logger.info(f"Starting cleaning pipeline for {len(studies)} studies")
    
    # Filter included studies
    included_studies = filter_included_studies(studies, output_dir)
    logger.info(f"Filtered to {len(included_studies)} included studies")
    
    # Handle multi-arm studies
    processed_studies = handle_multi_arm_studies(included_studies)
    
    # Convert to DataFrame
    df = pd.DataFrame(processed_studies)
    
    # Ensure required columns exist with defaults
    required_cols = [
        "id", "title", "registry", "age_range", "diagnosis", 
        "outcomes", "intervention_components", "delivery_format", 
        "social_skill_domain", "follow_up", "abstract_text",
        "domain_notes", "blinded_assessment_flag", "rater_type"
    ]
    
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns
    df = df[[c for c in required_cols if c in df.columns]]
    
    logger.info(f"Cleaning pipeline complete. Output shape: {df.shape}")
    return df

def main():
    """Entry point for cleaner script."""
    import argparse
    from code.utils.config import get_data_path

    parser = argparse.ArgumentParser(description="Clean study data")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing raw JSON files")
    parser.add_argument("--output", type=str, required=True, help="Output directory for cleaned CSV")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading studies from {input_dir}")
    
    # Load all JSON files from input directory
    studies = []
    for json_file in input_dir.glob("*.json"):
        if "mock" not in str(json_file):  # Skip mock data in production
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    studies.extend(data)
                elif isinstance(data, dict):
                    studies.append(data)
    
    logger.info(f"Loaded {len(studies)} studies")
    
    if not studies:
        logger.warning("No studies found to clean")
        # Create empty CSV with schema
        df = pd.DataFrame(columns=[
            "id", "title", "registry", "age_range", "diagnosis", 
            "outcomes", "intervention_components", "delivery_format", 
            "social_skill_domain", "follow_up", "abstract_text",
            "domain_notes", "blinded_assessment_flag", "rater_type"
        ])
        output_file = output_dir / "cleaned_studies.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Created empty CSV at {output_file}")
        return

    # Run cleaning pipeline
    df = clean_studies(studies, output_dir)
    
    # Save to CSV
    output_file = output_dir / "cleaned_studies.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Saved cleaned studies to {output_file}")

if __name__ == "__main__":
    main()
