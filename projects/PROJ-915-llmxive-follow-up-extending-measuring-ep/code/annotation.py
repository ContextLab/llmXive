import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
PIPELINE_LOG_PATH = PROJECT_ROOT / "pipeline_log.json"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def log_pipeline_event(stage: str, status: str, message: str = ""):
    """Log a pipeline event to pipeline_log.json."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "cumulative_seconds": 0,  # This would ideally be tracked by a timer
        "status": status,
        "message": message
    }

    log_file = PIPELINE_LOG_PATH
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

    logger.info(f"Logged event: {stage} - {status} - {message}")

def load_subset_data():
    """Load the MedMis subset from data/raw/medmis_subset.csv."""
    input_path = DATA_RAW_DIR / "medmis_subset.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Please run T013 (ingestion) first.")
    logger.info(f"Loading subset data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def load_feature_data():
    """Load features from data/processed/features.csv."""
    input_path = PROJECT_ROOT / "data" / "processed" / "features.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Required feature file not found: {input_path}. "
                                "Please run T014 (features) first.")
    logger.info(f"Loading feature data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def load_annotation_data():
    """Load existing annotation data if available."""
    input_path = DATA_RAW_DIR / "human_pilot_cached.csv"
    if input_path.exists():
        logger.info(f"Loading existing annotation data from {input_path}")
        return pd.read_csv(input_path)
    return None

def save_pilot_cache(df: pd.DataFrame, filename: str):
    """Save pilot cache to data/raw/."""
    output_path = DATA_RAW_DIR / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved pilot cache to {output_path}")
    return output_path

def generate_deterministic_pilot(n_samples: int = 50, seed: int = 42):
    """
    Generate a reproducible dataset of n=50 mock adherence labels.
    Method: Read prompt IDs from data/raw/medmis_subset.csv (T013).
    Generate adherence_label (0, 1, 2) using a deterministic function of
    linguistic features (T014) and random noise (numpy.random.seed(42)).
    Output: data/interim/human_pilot_labels_mock.csv with columns prompt_id, adherence_label.
    """
    logger.info(f"Starting deterministic mock label generation for {n_samples} samples.")
    
    # Load subset data to get prompt IDs
    try:
        subset_df = load_subset_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Load feature data to use as a basis for deterministic generation
    try:
        features_df = load_feature_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Set seed for reproducibility
    np.random.seed(seed)

    # Merge subset with features to get linguistic features for each prompt
    # Assuming 'prompt_id' is the common key
    merged_df = pd.merge(subset_df, features_df, on='prompt_id', how='inner')

    if merged_df.empty:
        raise ValueError("No matching prompt IDs found between subset and features data.")

    # Limit to n_samples
    if len(merged_df) > n_samples:
        # Take first n_samples deterministically (sorted by prompt_id to ensure reproducibility)
        merged_df = merged_df.sort_values('prompt_id').head(n_samples)
    
    logger.info(f"Using {len(merged_df)} samples for mock label generation.")

    # Determine available feature columns (excluding prompt_id and raw text)
    feature_cols = [col for col in merged_df.columns 
                    if col not in ['prompt_id', 'raw_text', 'text']]
    
    if not feature_cols:
        raise ValueError("No linguistic feature columns found in features data.")
    
    # Normalize features to [0, 1] range for scoring
    feature_matrix = merged_df[feature_cols].fillna(0).values
    min_vals = feature_matrix.min(axis=0)
    max_vals = feature_matrix.max(axis=0)
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1  # Avoid division by zero
    normalized_features = (feature_matrix - min_vals) / range_vals

    # Compute a deterministic "authority density score" based on features + noise
    # This mimics a human rater's score based on linguistic features
    noise = np.random.normal(0, 0.1, size=n_samples)
    # Weighted sum of normalized features (equal weights for simplicity)
    feature_score = np.mean(normalized_features, axis=1)
    authority_density_score = feature_score + noise
    authority_density_score = np.clip(authority_density_score, 0, 1)

    # Generate adherence_label based on authority_density_score + noise
    # Label 0: Resilient-Correct (low authority density, high resilience)
    # Label 1: Adherent (high authority density, follows misleading context)
    # Label 2: Resilient-Refusal (safety refusal)
    
    # Add some noise to the decision boundary
    decision_noise = np.random.normal(0, 0.15, size=n_samples)
    decision_scores = authority_density_score + decision_noise

    labels = np.zeros(n_samples, dtype=int)
    
    # Define thresholds for labels
    # If decision score > 0.7 -> Adherent (1)
    # If decision score < 0.3 -> Resilient-Correct (0)
    # Otherwise -> Resilient-Refusal (2)
    # This creates a distribution that mimics real-world variability
    
    for i in range(n_samples):
        if decision_scores[i] > 0.7:
            labels[i] = 1  # Adherent
        elif decision_scores[i] < 0.3:
            labels[i] = 0  # Resilient-Correct
        else:
            labels[i] = 2  # Resilient-Refusal

    # Create output DataFrame
    output_df = pd.DataFrame({
        'prompt_id': merged_df['prompt_id'].values,
        'adherence_label': labels
    })

    # Save to data/interim/human_pilot_labels_mock.csv
    output_path = DATA_INTERIM_DIR / "human_pilot_labels_mock.csv"
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved mock labels to {output_path}")

    # Also log this event
    log_pipeline_event(
        stage="T027a-MockLabels",
        status="completed",
        message=f"Generated {n_samples} deterministic mock adherence labels."
    )

    return output_df

def aggregate_rater_responses(df: pd.DataFrame):
    """Aggregate rater responses if multiple raters exist."""
    # Placeholder for future aggregation logic
    return df

def merge_data_for_correlation(features_df: pd.DataFrame, pilot_df: pd.DataFrame):
    """Merge feature data with pilot annotation data for correlation analysis."""
    merged = pd.merge(features_df, pilot_df, on='prompt_id', how='inner')
    return merged

def compute_correlations(merged_df: pd.DataFrame):
    """Compute Pearson/Spearman correlation between features and labels."""
    # Placeholder for correlation computation
    return {}

def generate_validation_report(correlation_data: dict):
    """Generate a validation report based on correlation data."""
    # Placeholder for report generation
    pass

def run_annotation_generate_pipeline():
    """Main pipeline function for generating deterministic mock labels."""
    logger.info("Starting T027a: Generate Deterministic Mock Labels Pipeline")
    try:
        df = generate_deterministic_pilot(n_samples=50, seed=42)
        logger.info("T027a pipeline completed successfully.")
        return df
    except Exception as e:
        logger.error(f"T027a pipeline failed: {str(e)}")
        log_pipeline_event(
            stage="T027a-MockLabels",
            status="failed",
            message=str(e)
        )
        raise

def run_annotation_correlation_pipeline():
    """Pipeline for correlation analysis between features and human ratings."""
    logger.info("Starting correlation analysis pipeline")
    try:
        features_df = load_feature_data()
        pilot_df = load_annotation_data()
        if pilot_df is None:
            raise FileNotFoundError("No pilot annotation data found. Run T017a first.")
        
        merged_df = merge_data_for_correlation(features_df, pilot_df)
        correlations = compute_correlations(merged_df)
        generate_validation_report(correlations)
        
        log_pipeline_event(
            stage="T017c-Correlation",
            status="completed",
            message="Correlation analysis completed."
        )
        return correlations
    except Exception as e:
        logger.error(f"Correlation pipeline failed: {str(e)}")
        log_pipeline_event(
            stage="T017c-Correlation",
            status="failed",
            message=str(e)
        )
        raise

def main():
    """Entry point for the annotation module."""
    import argparse
    parser = argparse.ArgumentParser(description="Annotation module for pilot data generation and correlation.")
    parser.add_argument("--mode", choices=["generate", "correlation"], required=True,
                        help="Mode: 'generate' for T027a, 'correlation' for T017c")
    args = parser.parse_args()

    if args.mode == "generate":
        run_annotation_generate_pipeline()
    elif args.mode == "correlation":
        run_annotation_correlation_pipeline()

if __name__ == "__main__":
    main()