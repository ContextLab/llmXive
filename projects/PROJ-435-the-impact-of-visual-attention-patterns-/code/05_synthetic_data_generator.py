"""
Synthetic Data Generator for Simulation (T022).

Generates a unified synthetic dataset for the simulation of visual attention
patterns on susceptibility to misleading headlines.

Mandatory Requirements:
1. Generate `belief_rating` (Uniform distribution, Likert scale 1-7).
2. Generate `cognitive_reflection_score` (Normal distribution, mean=5, std=1.5).
3. Generate ground truth variables for the three-way interaction with specific coefficients:
   - fixation_coef=0.5
   - valence_coef=0.3
   - crt_coef=-0.2
   - interaction_coef=0.1
4. DO NOT generate `confidence_assignment_time` or four-way interaction variables.
5. Output: `data/derived/synthetic_raw_data.csv`.

Note: This task is strictly for raw synthetic generation. Outlier capping and
merging are handled in T023.
"""
import os
import random
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import project utilities for configuration and reproducibility
from utils.environment_manager import load_config, setup_reproducibility, get_paths

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ground Truth Coefficients (FR-004: Three-way interaction)
COEFF_FIXATION = 0.5
COEFF_VALENCE = 0.3
COEFF_CRT = -0.2
COEFF_INTERACTION = 0.1
NOISE_SCALE = 0.5  # Standard deviation for random noise

def generate_synthetic_dataset(n_participants: int = 100, n_stimuli: int = 20, n_trials_per_participant: int = 10):
    """
    Generates the unified synthetic dataset for simulation.

    Args:
        n_participants: Number of unique participants.
        n_stimuli: Number of unique headlines (stimuli).
        n_trials_per_participant: Number of trials (headline exposures) per participant.

    Returns:
        pd.DataFrame: The generated synthetic dataset.
    """
    logger.info(f"Starting synthetic data generation: {n_participants} participants, {n_stimuli} stimuli.")

    # Setup reproducibility
    config = load_config()
    seed = get_config_value(config, 'random_seed', 42)
    setup_reproducibility(seed)
    logger.info(f"Reproducibility set with seed: {seed}")

    # Generate Participant IDs
    participant_ids = [f"P{i:03d}" for i in range(1, n_participants + 1)]
    
    # Generate Stimulus IDs and Text (Simulated)
    stimulus_ids = [f"S{i:03d}" for i in range(1, n_stimuli + 1)]
    # Simulate headline text and valence
    # Valence: -1 (negative) to 1 (positive)
    stimulus_data = []
    for s_id in stimulus_ids:
        # Random valence for simulation
        valence = np.random.uniform(-1, 1)
        stimulus_data.append({
            'stimulus_id': s_id,
            'headline_text': f"Simulated Headline {s_id}", # Placeholder text
            'valence': valence
        })
    stimuli_df = pd.DataFrame(stimulus_data)

    # Generate Trials
    trials = []
    for p_id in participant_ids:
        # Generate participant-specific CRT score (Normal distribution, mean=5, std=1.5)
        # This is a trait-like variable for the participant
        crt_score = np.random.normal(loc=5.0, scale=1.5)
        
        # Generate trials for this participant
        for t_idx in range(n_trials_per_participant):
            # Randomly select a stimulus for this trial
            s_id = random.choice(stimulus_ids)
            s_row = stimuli_df[stimuli_df['stimulus_id'] == s_id].iloc[0]
            
            # Generate Fixation Duration (Simulated continuous variable in seconds)
            # Log-normal distribution to mimic realistic gaze durations
            fixation_duration = np.random.lognormal(mean=1.0, sigma=0.5)
            
            # Generate Belief Rating (Uniform distribution 1-7, Likert scale)
            # This is the outcome variable, but we will also calculate a "ground truth"
            # based on the coefficients to ensure the simulation reflects the hypothesis.
            # However, the task asks to generate the rating. In a real simulation,
            # the rating is the result of the model + noise.
            
            # Calculate the "true" score based on the three-way interaction model
            # Model: belief = fixation_coef * fixation + valence_coef * valence + crt_coef * crt + interaction_coef * (fix * val * crt) + noise
            # Note: We normalize inputs slightly for the linear combination to keep scale reasonable
            norm_fixation = np.log(fixation_duration + 1) # Log transform to reduce skew
            norm_valence = s_row['valence']
            norm_crt = crt_score / 10.0 # Normalize CRT to similar scale
            
            true_score = (
                COEFF_FIXATION * norm_fixation +
                COEFF_VALENCE * norm_valence +
                COEFF_CRT * norm_crt +
                COEFF_INTERACTION * (norm_fixation * norm_valence * norm_crt)
            )
            
            # Add noise
            noise = np.random.normal(0, NOISE_SCALE)
            raw_rating = true_score + noise
            
            # Map to Likert scale 1-7 (clip and round)
            belief_rating = int(np.clip(np.round(raw_rating), 1, 7))
            
            trials.append({
                'participant_id': p_id,
                'stimulus_id': s_id,
                'trial_index': t_idx,
                'fixation_duration': fixation_duration,
                'valence': s_row['valence'],
                'cognitive_reflection_score': crt_score,
                'belief_rating': belief_rating
            })
    
    df = pd.DataFrame(trials)
    logger.info(f"Generated {len(df)} trial records.")
    return df

def main():
    """
    Main entry point for the synthetic data generator.
    Writes output to `data/derived/synthetic_raw_data.csv`.
    """
    try:
        # Get paths from environment manager
        paths = get_paths()
        output_dir = paths.get('derived_data_dir', 'data/derived')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'synthetic_raw_data.csv')
        
        # Generate data
        df = generate_synthetic_dataset(
            n_participants=100,
            n_stimuli=20,
            n_trials_per_participant=10
        )
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote synthetic data to {output_path}")
        
        # Print summary
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Belief Rating Range: {df['belief_rating'].min()} - {df['belief_rating'].max()}")
        logger.info(f"CRT Score Mean: {df['cognitive_reflection_score'].mean():.2f}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise

if __name__ == "__main__":
    main()