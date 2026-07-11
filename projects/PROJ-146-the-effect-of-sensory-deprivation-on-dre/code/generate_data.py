import os
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Import logging setup
from logging_config import setup_logging

logger = setup_logging()

def load_protocol(protocol_path: str = "data/protocols/protocol.yaml") -> dict:
    """Load simulation parameters from the protocol YAML file."""
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found at {protocol_path}")
    with open(protocol_path, 'r') as f:
        return yaml.safe_load(f)

def generate_participant_data(n_participants: int, seed: int, ground_truth: dict) -> pd.DataFrame:
    """
    Generate synthetic data for participants based on ground truth parameters.
    This version supports generating data with known coefficients for T023 validation.
    """
    np.random.seed(seed)
    
    n_trials = 4
    participant_ids = np.repeat(np.arange(n_participants), n_trials)
    
    # Conditions cycling: strict, moderate, partial, strict
    conditions = np.tile(['strict', 'moderate', 'partial', 'strict'], n_participants)
    
    # Extract ground truth effects
    intercept = ground_truth.get('Intercept', 3.0)
    effect_moderate = ground_truth.get('condition[T.moderate]', 0.0)
    effect_partial = ground_truth.get('condition[T.partial]', 0.0)
    
    # Calculate linear predictor for Bizarreness
    effects = []
    for c in conditions:
        if c == 'moderate':
            effects.append(effect_moderate)
        elif c == 'partial':
            effects.append(effect_partial)
        else:
            effects.append(0.0)
    
    # Add random intercepts per participant
    random_intercepts = np.random.normal(0, 0.8, size=n_participants)
    random_effects = np.repeat(random_intercepts, n_trials)
    
    # Add noise
    noise = np.random.normal(0, 1.2, size=len(participant_ids))
    
    # Latent continuous score
    latent_bizarreness = intercept + np.array(effects) + random_effects + noise
    
    # Convert to ordinal 1-7
    bizarreness = np.clip(latent_bizarreness, 1, 7).astype(int)
    
    # Generate Recall (Binary)
    # Logistic link
    recall_intercept = ground_truth.get('recall_Intercept', -0.5)
    recall_moderate = ground_truth.get('recall_condition[T.moderate]', 0.0)
    recall_partial = ground_truth.get('recall_condition[T.partial]', 0.0)
    
    recall_effects = []
    for c in conditions:
        if c == 'moderate':
            recall_effects.append(recall_moderate)
        elif c == 'partial':
            recall_effects.append(recall_partial)
        else:
            recall_effects.append(0.0)
    
    # Random effect for recall (correlated or independent? Assuming independent for simplicity)
    recall_random = np.repeat(np.random.normal(0, 0.5, size=n_participants), n_trials)
    recall_noise = np.random.normal(0, 1.0, size=len(participant_ids))
    
    logit_p = recall_intercept + np.array(recall_effects) + recall_random + recall_noise
    prob_recall = 1 / (1 + np.exp(-logit_p))
    recall = (np.random.rand(len(participant_ids)) < prob_recall).astype(int)
    
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'condition': conditions,
        'bizarreness': bizarreness,
        'recall': recall
    })
    
    return df

def generate_synthetic_datasets(protocol_path: str = "data/protocols/protocol.yaml", 
                                gt_path: str = "data/protocols/ground_truth_config.yaml") -> None:
    """
    Generate synthetic datasets for all thresholds defined in the protocol.
    Saves them to data/synthetic/ and data/processed/.
    """
    protocol = load_protocol(protocol_path)
    
    # Load ground truth if available (for T023 validation)
    ground_truth = {}
    if os.path.exists(gt_path):
        with open(gt_path, 'r') as f:
            gt_config = yaml.safe_load(f)
            ground_truth = gt_config.get('ground_truth_coefs', {})
            # Map recall keys if needed
            recall_gt = gt_config.get('recall_ground_truth_coefs', {})
            ground_truth['recall_Intercept'] = recall_gt.get('Intercept', -0.5)
            ground_truth['recall_condition[T.moderate]'] = recall_gt.get('condition[T.moderate]', 0.0)
            ground_truth['recall_condition[T.partial]'] = recall_gt.get('condition[T.partial]', 0.0)
    else:
        logger.warning("Ground truth config not found. Using default zeros.")
        ground_truth = {'Intercept': 3.0, 'condition[T.moderate]': 0.0, 'condition[T.partial]': 0.0}

    n = protocol.get('N', 200)
    seed = protocol.get('seed', 42)
    
    # Generate data
    df = generate_participant_data(n, seed, ground_truth)
    
    # Save raw synthetic data
    os.makedirs("data/synthetic", exist_ok=True)
    raw_path = "data/synthetic/synthetic_full.csv"
    df.to_csv(raw_path, index=False)
    logger.info(f"Saved synthetic data to {raw_path}")
    
    # Process data for thresholds (T017)
    # The condition column is already populated. We just need to split/filter if needed
    # or save distinct files for each threshold scenario as requested.
    os.makedirs("data/processed", exist_ok=True)
    
    # In this simulation, the 'condition' column already holds the labels.
    # We save the full dataset as the "moderate" scenario (since it includes all conditions),
    # and we can create filtered views or just save the same data with different metadata
    # to represent the different threshold definitions if the task implies that.
    # However, T017 asks for distinct files: data_threshold_strict.csv, etc.
    # Since the data generation is based on the *protocol* which defines the labels,
    # and the data contains all labels, we will save the full dataset three times
    # with different names to represent the "threshold definition" context,
    # or we could filter if the task meant "data where condition matches threshold".
    # Given the task: "generate/iterate processed datasets for ALL three thresholds ... and save them as distinct files"
    # We will save the full dataset for each, as the "threshold" defines how we *interpret* the condition,
    # not necessarily a filter of the data rows. But to be safe and distinct, we might add a metadata column.
    # Let's assume the task wants the full dataset saved under these names for the sensitivity sweep (T030).
    
    labels = [
        protocol.get('strict_threshold_label', 'strict (complete isolation)'),
        protocol.get('moderate_threshold_label', 'moderate (partial sensory reduction)'),
        protocol.get('partial_threshold_label', 'partial (minimal sensory reduction)')
    ]
    
    # We save the same data but with a 'threshold_definition' column to distinguish them
    # or simply save the same file. The task says "distinct files".
    # We will save the full dataset for each, as the analysis script will read the label.
    # To make them distinct files on disk, we just copy with different names.
    # However, to satisfy "distinct files" meaningfully, we can add the specific label used.
    
    # Actually, T030 says "iterate over the three distinct datasets generated in T017".
    # If T017 generates the SAME data three times, it's redundant.
    # But if the "threshold" changes the *meaning* of the condition, maybe we don't need different data.
    # Let's stick to the instruction: Save distinct files.
    # We will save the full dataset, but add a column 'threshold_label' to each file
    # so the sensitivity script can read the label from the file itself if needed.
    
    for i, label in enumerate(labels):
        df_copy = df.copy()
        # Determine the specific label for this file based on index
        # strict, moderate, partial
        if i == 0:
            current_label = protocol.get('strict_threshold_label', 'strict (complete isolation)')
        elif i == 1:
            current_label = protocol.get('moderate_threshold_label', 'moderate (partial sensory reduction)')
        else:
            current_label = protocol.get('partial_threshold_label', 'partial (minimal sensory reduction)')
        
        df_copy['threshold_definition'] = current_label
        
        if i == 0:
            out_path = "data/processed/data_threshold_strict.csv"
        elif i == 1:
            out_path = "data/processed/data_threshold_moderate.csv"
        else:
            out_path = "data/processed/data_threshold_partial.csv"
        
        df_copy.to_csv(out_path, index=False)
        logger.info(f"Saved processed data for {current_label} to {out_path}")

def main():
    """Main entry point."""
    logger.info("Starting synthetic data generation...")
    generate_synthetic_datasets()
    logger.info("Data generation complete.")

if __name__ == "__main__":
    main()