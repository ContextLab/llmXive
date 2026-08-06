import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
from datasets import load_dataset
import logging

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils import setup_logging, get_logger

logger = get_logger(__name__)

REQUIRED_FEATURES = {
    "timestamped_responses": {"timestamp", "response_time", "date"},
    "error_logs": {"is_error", "error_type", "incorrect"},
    "hint_requests": {"hint_count", "hint_requested", "num_hints"},
    "interaction_features": {"problem_id", "skill_id", "user_id", "interaction_type"}
}

def ensure_directories():
    """Ensure required data directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def load_assistments_dataset() -> Optional[pd.DataFrame]:
    """Load ASSISTments dataset from HuggingFace."""
    try:
        # Using a known public ASSISTments dataset identifier
        dataset = load_dataset("cfh/assistments", split="train", streaming=True)
        df = pd.DataFrame(dataset)
        logger.info(f"Loaded ASSISTments dataset: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load ASSISTments dataset: {e}")
        return None

def load_oulad_dataset() -> Optional[pd.DataFrame]:
    """Load OULAD dataset from HuggingFace."""
    try:
        # Using a verified OULAD dataset identifier
        dataset = load_dataset("openlearning/openlearning", split="train", streaming=True)
        df = pd.DataFrame(dataset)
        logger.info(f"Loaded OULAD dataset: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load OULAD dataset: {e}")
        return None

def verify_features(df: pd.DataFrame, dataset_name: str) -> bool:
    """Verify presence of required interaction features."""
    missing_features = []
    for category, features in REQUIRED_FEATURES.items():
        if not any(f in df.columns for f in features):
            missing_features.append(f"{category}: {features}")
    
    if missing_features:
        logger.error(f"Dataset {dataset_name} missing required features: {missing_features}")
        return False
    
    logger.info(f"Dataset {dataset_name} verified with all required features")
    return True

def save_dataset(df: pd.DataFrame, filename: str):
    """Save processed dataset to data/raw."""
    output_path = Path("data/raw") / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved dataset to {output_path}")

def load_and_verify_datasets() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load and verify both ASSISTments and OULAD datasets."""
    ensure_directories()
    
    assistments_df = load_assistments_dataset()
    if assistments_df is not None:
        if not verify_features(assistments_df, "ASSISTments"):
            logger.warning("ASSISTments dataset verification failed")
        else:
            save_dataset(assistments_df, "assistments_processed.csv")
    
    oulad_df = load_oulad_dataset()
    if oulad_df is not None:
        if not verify_features(oulad_df, "OULAD"):
            logger.warning("OULAD dataset verification failed")
        else:
            save_dataset(oulad_df, "oulad_processed.csv")
    
    return assistments_df, oulad_df

def validate_golden_set() -> bool:
    """
    Phase 0 "Golden Set" validation.
    Checks for data/processed/golden_set.csv with 'expert_load_score' OR concurrent self-reports.
    Exits with specific error if missing or invalid.
    """
    golden_set_path = Path("data/processed/golden_set.csv")
    
    if not golden_set_path.exists():
        error_msg = (
            "CRITICAL: Golden Set validation failed. "
            f"File '{golden_set_path}' does not exist. "
            "The pipeline requires an external expert-labeled dataset for validation. "
            "Please fetch the external data manually or run T006b to create the golden set."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    try:
        df = pd.read_csv(golden_set_path)
    except Exception as e:
        error_msg = (
            f"CRITICAL: Failed to read Golden Set file '{golden_set_path}': {e}"
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # Check for required validation target columns
    has_expert_score = "expert_load_score" in df.columns
    has_self_report = any(col in df.columns for col in ["self_report_load", "concurrent_self_report", "tlx_score"])
    
    if not has_expert_score and not has_self_report:
        error_msg = (
            "CRITICAL: Golden Set validation failed. "
            f"File '{golden_set_path}' exists but lacks required validation targets. "
            "Expected columns: 'expert_load_score' OR concurrent self-reports "
            "('self_report_load', 'concurrent_self_report', 'tlx_score'). "
            "The dataset must contain expert-labeled interactions for model validation."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # Check minimum sample size
    min_samples = 50
    if len(df) < min_samples:
        error_msg = (
            f"CRITICAL: Golden Set validation failed. "
            f"Insufficient sample size: {len(df)} rows. "
            f"Minimum required: {min_samples} expert-labeled interactions."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    logger.info(f"Golden Set validated successfully: {len(df)} samples with valid targets")
    return True

def main():
    """Main entry point for data loading and validation."""
    setup_logging()
    
    logger.info("Starting data loading and validation pipeline")
    
    # Load and verify public datasets
    load_and_verify_datasets()
    
    # Validate Golden Set (Phase 0 requirement)
    validate_golden_set()
    
    logger.info("Data loading and validation completed successfully")

if __name__ == "__main__":
    main()