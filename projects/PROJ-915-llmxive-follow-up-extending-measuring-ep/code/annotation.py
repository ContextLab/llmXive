import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import statsmodels.stats.inter_rater as irr

from config import get_config
from validation import update_pipeline_log

class DataFlowError(Exception):
    pass

def generate_survey_payload(features_file: Path, output_path: Path) -> None:
    """Generate survey payload for human raters."""
    if not features_file.exists():
        raise FileNotFoundError(f"Features file not found: {features_file}")
    
    df = pd.read_csv(features_file)
    payload = []
    for _, row in df.iterrows():
        payload.append({
            "prompt_id": row["prompt_id"],
            "raw_text": row.get("raw_text", ""),
            "extracted_features": {
                "modal_verb_count": row.get("modal_verb_count", 0),
                "citation_count": row.get("citation_count", 0)
            }
        })
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    
    logging.info(f"Generated survey payload: {output_path}")

def generate_recruitment_instructions(output_path: Path) -> None:
    """Generate recruitment instructions for researchers."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("# Human Pilot Recruitment Instructions\n\n")
        f.write("## Steps:\n")
        f.write("1. Recruit >= 50 raters via Prolific or similar platform.\n")
        f.write("2. Distribute the survey payload (data/raw/survey_payload.json).\n")
        f.write("3. Collect raw data into data/raw/human_pilot_raw.csv.\n")
        f.write("4. Ensure columns: prompt_id, rater_id, authority_density_score.\n")
    
    logging.info(f"Generated recruitment instructions: {output_path}")

def verify_manual_pilot_completion(raw_file: Path) -> bool:
    """Verify manual pilot data exists and is valid."""
    if not raw_file.exists():
        return False
    
    try:
        df = pd.read_csv(raw_file)
        required_cols = ["prompt_id", "rater_id", "authority_density_score"]
        return all(col in df.columns for col in required_cols)
    except Exception:
        return False

def load_pilot_data(raw_file: Path, output_path: Path) -> pd.DataFrame:
    """Load and validate manual pilot data."""
    if not verify_manual_pilot_completion(raw_file):
        raise DataFlowError("Manual pilot data invalid or missing.")
    
    df = pd.read_csv(raw_file)
    df.to_csv(output_path, index=False)
    logging.info(f"Loaded pilot data: {output_path}")
    return df

def clean_pilot_data(df: pd.DataFrame, agreement_threshold: float = 0.8) -> pd.DataFrame:
    """Clean pilot data by removing raters with <80% agreement on control items."""
    # Placeholder: In real implementation, compute agreement on control items
    # For now, assume all data is valid if it has >= 50 rows
    if len(df) < 50:
        raise DataFlowError(f"Insufficient data after cleaning: {len(df)} rows.")
    return df

def compute_annotation_correlation(features_file: Path, pilot_file: Path) -> Dict[str, float]:
    """Compute correlation between features and human ratings."""
    features_df = pd.read_csv(features_file)
    pilot_df = pd.read_csv(pilot_file)
    
    # Merge on prompt_id
    merged = pd.merge(features_df, pilot_df, on="prompt_id", how="inner")
    
    if len(merged) == 0:
        raise DataFlowError("No overlapping data between features and pilot.")
    
    # Compute correlation
    corr, _ = pearsonr(merged["modal_verb_count"], merged["authority_density_score"])
    kappa = irr.cohenkappa(merged[["rater_id", "authority_density_score"]].values)
    
    return {
        "correlation_coefficient": float(corr),
        "cohen_kappa": float(kappa)
    }

def run_validation_gate(correlation: Dict[str, float]) -> bool:
    """Run validation gate: r > 0.6 AND kappa > 0.7."""
    return correlation["correlation_coefficient"] > 0.6 and correlation["cohen_kappa"] > 0.7

def generate_validation_report(passed: bool, output_path: Path) -> None:
    """Generate validation gate report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("# Human Pilot Validation Report\n\n")
        f.write(f"Status: {'PASS' if passed else 'FAIL'}\n")
    
    logging.info(f"Generated validation report: {output_path}")

def generate_contingency_report(output_path: Path) -> None:
    """Generate contingency report for failed pilot."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("# Contingency Report\n\n")
        f.write("Human pilot validation failed. Pipeline aborted. Manual intervention required.\n")
    
    logging.info(f"Generated contingency report: {output_path}")

def handle_pilot_failure():
    """Handle pilot failure."""
    generate_contingency_report(Path("data/results/contingency_report.md"))
    raise DataFlowError("Human pilot validation failed.")

def run_validation_gate_pipeline():
    """Main validation gate pipeline."""
    # Generate survey payload
    generate_survey_payload(Path("data/processed/features.csv"), Path("data/raw/survey_payload.json"))
    generate_recruitment_instructions(Path("docs/recruitment_instructions.md"))
    
    # Wait for manual step (in real pipeline, this would block)
    raw_file = Path("data/raw/human_pilot_raw.csv")
    if not verify_manual_pilot_completion(raw_file):
        raise DataFlowError("Manual pilot data not yet available. Waiting...")
    
    # Load and clean
    cleaned_df = load_pilot_data(raw_file, Path("data/interim/human_pilot_raw_loaded.csv"))
    cleaned_df = clean_pilot_data(cleaned_df)
    cleaned_df.to_csv(Path("data/interim/human_pilot_cleaned.csv"), index=False)
    
    # Compute correlation
    correlation = compute_annotation_correlation(Path("data/processed/features.csv"), Path("data/interim/human_pilot_cleaned.csv"))
    
    with open(Path("data/results/feature_correlation_and_kappa.json"), "w") as f:
        json.dump(correlation, f, indent=2)
    
    # Run gate
    passed = run_validation_gate(correlation)
    generate_validation_report(passed, Path("data/results/feature_validation_report.md"))
    
    if not passed:
        handle_pilot_failure()
    
    # Log result
    update_pipeline_log("human_pilot", "success" if passed else "failed", str(correlation))

def main():
    """Entry point for annotation script."""
    run_validation_gate_pipeline()

if __name__ == "__main__":
    main()