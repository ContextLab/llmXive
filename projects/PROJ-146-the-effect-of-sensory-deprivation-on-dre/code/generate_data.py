import os
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Import setup_logging from sibling module
from logging_config import setup_logging

def load_protocol(protocol_path: str = "data/protocols/protocol.yaml") -> dict:
    """Load simulation parameters from the protocol YAML file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading protocol from {protocol_path}")
    try:
        with open(protocol_path, 'r') as f:
            protocol = yaml.safe_load(f)
        logger.info(f"Protocol loaded successfully: N={protocol.get('N', 'N/A')}")
        return protocol
    except FileNotFoundError:
        logger.error(f"Protocol file not found at {protocol_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing protocol YAML: {e}")
        raise

def generate_participant_data(protocol: dict, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic participant data based on protocol parameters.
    
    Args:
        protocol: Dictionary containing simulation parameters.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with simulated dream recall and bizarreness data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating synthetic data with seed={seed}, N={protocol['N']}")
    
    np.random.seed(seed)
    n = protocol['N']
    effect_sizes = protocol.get('effect_sizes', [0.5, 0.0, -0.2])
    icc = protocol.get('ICC', 0.3)
    
    # Generate participant IDs
    participant_ids = np.repeat(np.arange(n // 3), 3) # 3 measurements per participant
    
    # Generate conditions (stratified by effect size scenarios)
    conditions = np.array(['strict', 'moderate', 'partial'] * (n // 3))
    
    # Simulate random intercepts (participant-level variation)
    random_intercepts = np.random.normal(0, np.sqrt(icc), size=n // 3)
    random_intercepts_expanded = np.repeat(random_intercepts, 3)
    
    # Base probabilities for dream recall
    base_recall_prob = 0.5
    
    # Apply effect sizes to recall probability
    recall_probs = []
    for i, cond in enumerate(conditions):
        idx = i % 3
        effect = effect_sizes[idx]
        # Logistic transformation
        logit = np.log(base_recall_prob / (1 - base_recall_prob)) + effect + random_intercepts_expanded[i]
        prob = 1 / (1 + np.exp(-logit))
        recall_probs.append(prob)
    
    recall_probs = np.array(recall_probs)
    recall = np.random.binomial(1, recall_probs)
    
    # Simulate bizarreness scores (1-7 scale)
    # Base mean shifted by condition
    condition_means = {'strict': 5.0, 'moderate': 4.0, 'partial': 3.0}
    bizarreness_base = np.array([condition_means[c] for c in conditions])
    bizarreness_noise = np.random.normal(0, 1.0, size=n)
    bizarreness = np.clip(bizarreness_base + bizarreness_noise + random_intercepts_expanded, 1, 7).astype(int)
    
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'condition': conditions,
        'recall': recall,
        'bizarreness': bizarreness,
        'timestamp': datetime.now().isoformat()
    })
    
    logger.info(f"Generated data shape: {df.shape}")
    logger.info(f"Recall distribution: {df['recall'].value_counts().to_dict()}")
    logger.info(f"Bizarreness distribution: {df['bizarreness'].value_counts().to_dict()}")
    
    return df

def generate_synthetic_datasets(protocol: dict, output_dir: str = "data/synthetic/", seed: int = 42) -> list:
    """
    Generate synthetic datasets for all scenarios defined in the protocol.
    
    Args:
        protocol: Protocol dictionary.
        output_dir: Directory to save generated datasets.
        seed: Base random seed.
        
    Returns:
        List of paths to generated files.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting synthetic data generation to {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    effect_sizes = protocol.get('effect_sizes', [0.5, 0.0, -0.2])
    scenario_labels = ['positive_effect', 'null_effect', 'negative_effect']
    
    for i, (effect, label) in enumerate(zip(effect_sizes, scenario_labels)):
        # Create a temporary protocol override for this scenario
        scenario_protocol = protocol.copy()
        scenario_protocol['effect_sizes'] = [effect]
        
        # Generate data with a specific seed for this scenario
        scenario_seed = seed + i
        df = generate_participant_data(scenario_protocol, seed=scenario_seed)
        
        # Add scenario metadata
        df['scenario'] = label
        df['effect_size'] = effect
        df['simulation_seed'] = scenario_seed
        df['is_synthetic'] = True
        
        # Save file
        filename = f"synthetic_{label}_seed{scenario_seed}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        
        logger.info(f"Saved synthetic dataset: {filepath}")
        generated_files.append(filepath)
    
    logger.info(f"Completed generation of {len(generated_files)} synthetic datasets")
    return generated_files

def main():
    """Main entry point for data generation."""
    logger = setup_logging(log_level=logging.INFO, log_file="logs/generate_data.log")
    logger.info("=== Starting Synthetic Data Generation ===")
    
    try:
        # Load protocol
        protocol = load_protocol("data/protocols/protocol.yaml")
        
        # Log generation parameters
        logger.info(f"Generation Parameters:")
        logger.info(f"  - Sample Size (N): {protocol['N']}")
        logger.info(f"  - Effect Sizes: {protocol['effect_sizes']}")
        logger.info(f"  - ICC: {protocol['ICC']}")
        logger.info(f"  - Strict Threshold Label: {protocol['strict_threshold_label']}")
        logger.info(f"  - Moderate Threshold Label: {protocol['moderate_threshold_label']}")
        logger.info(f"  - Partial Threshold Label: {protocol['partial_threshold_label']}")
        
        # Generate datasets
        files = generate_synthetic_datasets(protocol, seed=42)
        
        logger.info("=== Data Generation Complete ===")
        logger.info(f"Generated files: {files}")
        
    except Exception as e:
        logger.error(f"Data generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
