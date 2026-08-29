import os
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Configure logging to use the project's standard setup
try:
    from logging_config import setup_logging
    logger = setup_logging(__name__)
except ImportError:
    # Fallback if logging_config is not yet available or imported differently
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def load_protocol(protocol_path: str = "data/protocols/protocol.yaml") -> dict:
    """
    Loads the simulation protocol from the YAML file.
    
    Args:
        protocol_path: Path to the protocol.yaml file.
        
    Returns:
        Dictionary containing protocol parameters.
        
    Raises:
        FileNotFoundError: If the protocol file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found at {protocol_path}")
    
    with open(protocol_path, 'r') as f:
        protocol = yaml.safe_load(f)
    
    logger.info(f"Loaded protocol from {protocol_path}")
    return protocol

def generate_participant_data(
    n_participants: int,
    effect_size: float,
    seed: int,
    icc: float = 0.3
) -> pd.DataFrame:
    """
    Generates synthetic data for a single participant group based on effect size.
    
    This function simulates dream recall (binary) and bizarreness (1-7) scores
    under a specific sensory deprivation condition defined by the effect size.
    
    Args:
        n_participants: Number of participants to generate.
        effect_size: Cohen's d value for the simulated effect.
        seed: Random seed for reproducibility.
        icc: Intraclass correlation coefficient for random effects.
        
    Returns:
        DataFrame with columns: participant_id, condition_label, recall, bizarreness, 
                                random_effect_recall, random_effect_bizarreness
    """
    np.random.seed(seed)
    
    # Generate random effects for participants (simulating repeated measures or 
    # individual baselines if we were doing longitudinal, here treated as individual 
    # variation in baseline)
    # For a cross-sectional simulation with N participants, we treat each row as 
    # a participant's aggregate or single observation, but we add a random effect 
    # component to simulate the ICC structure if we were grouping. 
    # Since this is a simulation of N=200 participants total across conditions,
    # we will assign participants to conditions.
    
    # However, the task implies generating datasets for 3 scenarios. 
    # We will generate N participants for EACH scenario (3 datasets).
    # Each dataset will have the effect_size applied to the condition.
    
    # Generate IDs
    participant_ids = [f"P{str(i).zfill(3)}" for i in range(1, n_participants + 1)]
    
    # Random intercepts for recall and bizarreness
    # Variance decomposition: Total variance = 1 (for simplicity in binary probit) or 1 for linear
    # ICC = Var_random / (Var_random + Var_residual)
    # We assume Var_residual = 1 for standardization
    var_random = icc / (1 - icc) if icc < 1 else 1.0
    std_random = np.sqrt(var_random)
    
    random_effect_recall = np.random.normal(0, std_random, n_participants)
    random_effect_bizarreness = np.random.normal(0, std_random, n_participants)
    
    # Baseline parameters (intercepts)
    # For recall (binary): Logit model. Baseline probability ~ 0.5 -> intercept ~ 0
    baseline_recall_logit = 0.0
    # For bizarreness (1-7): Linear. Baseline ~ 4 (midpoint)
    baseline_bizarreness = 4.0
    
    # Apply effect size
    # For recall: effect_size is in log-odds units (approx) or we convert to probability shift
    # For simplicity in simulation, we add effect_size to the logit
    recall_logit = baseline_recall_logit + random_effect_recall + effect_size
    # Convert to probability
    recall_prob = 1 / (1 + np.exp(-recall_logit))
    # Generate binary recall
    recall = np.random.binomial(1, recall_prob, n_participants)
    
    # For bizarreness: Linear model
    # effect_size is in standard deviation units. We scale by the residual std (1)
    bizarreness_score = baseline_bizarreness + random_effect_bizarreness + effect_size * 1.0
    # Add residual noise
    bizarreness_score += np.random.normal(0, 1, n_participants)
    # Clip to 1-7 and round
    bizarreness = np.clip(np.round(bizarreness_score), 1, 7).astype(int)
    
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'recall': recall,
        'bizarreness': bizarreness
    })
    
    return df

def generate_synthetic_datasets(
    protocol: dict,
    output_dir: str = "data/synthetic/"
) -> list:
    """
    Generates synthetic datasets for all effect size scenarios defined in the protocol.
    
    Args:
        protocol: Dictionary containing study parameters.
        output_dir: Directory to save the generated CSV files.
        
    Returns:
        List of paths to the generated files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    n_participants = protocol['study']['n_participants']
    seed = protocol['study']['seed']
    icc = protocol['statistical']['intraclass_correlation']
    effect_sizes = protocol['effect_sizes']
    
    generated_files = []
    
    # Define the mapping from effect size name to a condition label for the dataset
    # The task asks for 3 scenarios. We will create one file per scenario.
    scenario_mapping = {
        'moderate_positive': 'positive_effect',
        'null': 'null_effect',
        'moderate_negative': 'negative_effect'
    }
    
    for scenario in effect_sizes:
        name = scenario['name']
        value = scenario['value']
        
        logger.info(f"Generating dataset for scenario: {name} (d={value})")
        
        # Generate data
        df = generate_participant_data(
            n_participants=n_participants,
            effect_size=value,
            seed=seed,
            icc=icc
        )
        
        # Add metadata columns
        df['scenario'] = name
        df['effect_size'] = value
        df['data_source'] = "Simulation-based"
        df['generation_timestamp'] = datetime.now().isoformat()
        
        # Save to CSV
        filename = f"synthetic_{name}_n{n_participants}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        
        generated_files.append(filepath)
        logger.info(f"Saved synthetic data to {filepath}")
        
    return generated_files

def main():
    """
    Main entry point for the data generation script.
    """
    protocol_path = "data/protocols/protocol.yaml"
    output_dir = "data/synthetic/"
    
    try:
        protocol = load_protocol(protocol_path)
        files = generate_synthetic_datasets(protocol, output_dir)
        logger.info(f"Successfully generated {len(files)} synthetic datasets.")
        for f in files:
            print(f"Generated: {f}")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise

if __name__ == "__main__":
    main()
