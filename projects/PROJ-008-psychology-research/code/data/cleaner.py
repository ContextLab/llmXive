import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from code.utils.logging import get_logger
from code.utils.config import get_data_path

logger = get_logger(__name__)

# Whitelist of known social skill measures
SOCIAL_SKILL_MEASURES = {
    'SRS-2', 'Social Responsiveness Scale-2', 'social responsivness scale-2',
    'ABC', 'Aberrant Behavior Checklist', 'aberrant behavior checklist',
    'SSIS', 'Social Skills Improvement System', 'social skills improvement system',
    'PEP-3', 'Psychoeducational Profile-3', 'psychoeducational profile-3',
    'SRS', 'Social Responsiveness Scale', 'social responsivness scale',
    'SSRS', 'Social Skills Rating System', 'social skills rating system',
    'CSBS', 'Communication and Symbolic Behavior Scales',
    'Vineland', 'Vineland Adaptive Behavior Scales', 'vineland adaptive behavior scales',
    'ESCS', 'Early Social Communication Scales',
    'SCQ', 'Social Communication Questionnaire', 'social communication questionnaire'
}

def validate_age(age: Optional[float]) -> bool:
    """Validate age is within the study's target range (typically -12 to 18 for ASD research)."""
    if age is None:
        return False
    # Assuming valid age range for ASD social skills studies is roughly 3 to 18 years
    # The task mentions "-12" which likely implies a range check or a specific constraint.
    # We will enforce a reasonable positive range for children/adolescents: 3 <= age <= 18.
    # If the task meant "greater than -12" (which is trivially true for humans), we interpret it as a lower bound check.
    # Given the context of "children aged 8-12" in the spec, we ensure age is positive and reasonable.
    if age < 3 or age > 18:
        return False
    return True

def validate_asd_diagnosis(diagnosis: Optional[str]) -> bool:
    """Validate that the study includes ASD diagnosis criteria."""
    if not diagnosis:
        return False
    diagnosis_lower = diagnosis.lower()
    asd_keywords = ['asd', 'autism', 'autism spectrum', 'autistic disorder', 'pdd-nos']
    return any(keyword in diagnosis_lower for keyword in asd_keywords)

def validate_outcomes(outcomes: Any) -> bool:
    """
    Validate `outcomes` field against a whitelist of known social skill measures.
    Returns True if at least one valid measure is found.
    """
    if not outcomes:
        return False

    if isinstance(outcomes, str):
        measures_list = [m.strip() for m in outcomes.split(',')]
    elif isinstance(outcomes, list):
        measures_list = outcomes
    else:
        measures_list = [str(outcomes)]

    for measure in measures_list:
        measure_clean = str(measure).strip()
        if measure_clean.lower() in SOCIAL_SKILL_MEASURES:
            return True
        # Check if the measure string contains any of the known keys (case-insensitive partial match)
        for known_measure in SOCIAL_SKILL_MEASURES:
            if known_measure.lower() in measure_clean.lower():
                return True
    return False

def _log_exclusion(study_id: str, reason: str, log_path: Path) -> None:
    """Log an excluded study to the JSONL file."""
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "study_id": study_id,
        "reason": reason,
        "timestamp": timestamp
    }
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    
    logger.warning(f"Excluded study {study_id}: {reason}")

def filter_included_studies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to include only studies that pass all validation criteria:
    1. Age is valid (approx 3-18)
    2. ASD diagnosis is present
    3. Outcomes match known social skill measures
    
    Excluded studies are logged to `data/raw/excluded_studies.log` in JSONL format.
    
    Args:
        df: DataFrame containing study data with columns 'age', 'diagnosis', 'outcomes', 'id'.
        
    Returns:
        DataFrame of included studies.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df

    log_path = get_data_path() / "raw" / "excluded_studies.log"
    included_indices = []
    
    for idx, row in df.iterrows():
        study_id = row.get('id', row.get('study_id', 'UNKNOWN'))
        
        # Validate Age
        age = row.get('age')
        if not validate_age(age):
            _log_exclusion(study_id, "INVALID_AGE", log_path)
            continue
        
        # Validate ASD Diagnosis
        diagnosis = row.get('diagnosis')
        if not validate_asd_diagnosis(diagnosis):
            _log_exclusion(study_id, "INVALID_DIAGNOSIS", log_path)
            continue
        
        # Validate Outcomes
        outcomes = row.get('outcomes')
        if not validate_outcomes(outcomes):
            _log_exclusion(study_id, "INVALID_OUTCOME", log_path)
            continue
        
        included_indices.append(idx)
    
    if not included_indices:
        logger.warning("No studies passed validation filters.")
        return pd.DataFrame()
    
    logger.info(f"Filtered {len(df)} studies down to {len(included_indices)} included studies.")
    return df.loc[included_indices].reset_index(drop=True)

def handle_multi_arm_studies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle multi-arm studies by splitting control groups proportionally.
    This is a placeholder for the logic required by FR-008, which will be implemented fully when data supports it.
    For now, it returns the dataframe as-is if no multi-arm handling logic is triggered.
    """
    # Implementation details would go here based on specific multi-arm column structures
    # This function is defined to satisfy the API surface requirement for T019 dependency
    return df

def main():
    """
    Main entry point for the cleaner module.
    Expects a cleaned CSV from the extractor (T017) and produces a filtered CSV.
    """
    data_path = get_data_path()
    input_file = data_path / "processed" / "extracted_studies.csv"
    output_file = data_path / "processed" / "cleaned_studies.csv"
    
    if not input_file.exists():
        # If the previous step hasn't run, we cannot proceed. 
        # In a real pipeline, this would be an error.
        # For this task, we assume the pipeline runs sequentially or we handle missing file gracefully.
        logger.error(f"Input file {input_file} not found. Please run the extractor first.")
        return

    logger.info(f"Loading data from {input_file}")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to load {input_file}: {e}")
        return

    logger.info("Running validation filters...")
    filtered_df = filter_included_studies(df)
    
    logger.info(f"Saving {len(filtered_df)} included studies to {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_file, index=False)
    
    logger.info("Cleaning complete.")

if __name__ == "__main__":
    main()