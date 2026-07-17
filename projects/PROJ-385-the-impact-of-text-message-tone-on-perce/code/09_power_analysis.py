"""
Power analysis for Linear Mixed-Effects Model (LMM) interaction effect.

This script performs a simulation-based power analysis to determine the
required sample size (number of participants) to detect a medium interaction
effect between relationship type and cue intensity with alpha=0.05 and power=0.80.

It uses the `statsmodels` library to fit LMMs and simulation to estimate power.
The result is saved to `data/processed/power_analysis_results.json`.
"""

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.formula.api import mixedlm
from scipy import stats

# Suppress convergence warnings for cleaner output during simulation
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Configuration
RANDOM_SEED = 42
N_SIMULATIONS = 1000  # Number of simulation iterations
ALPHA = 0.05
TARGET_POWER = 0.80
EFFECT_SIZE = 0.5  # Medium effect size (Cohen's f or similar standard)

# Output path
OUTPUT_PATH = Path("data/processed/power_analysis_results.json")

def simulate_data(n_participants, n_stimuli_per_participant=24, effect_size=EFFECT_SIZE, seed=None):
    """
    Simulate data for the LMM power analysis.

    Model structure:
    Rating ~ Relationship * CueIntensity + (1 | Participant) + (1 | Stimulus)

    We simulate a specific interaction effect and check if the model detects it.
    """
    if seed is not None:
        np.random.seed(seed)

    # Define factors
    relationships = ["friend", "acquaintance"]
    # Cue intensity is a composite of emoji, punctuation, length (simplified for simulation)
    # We'll simulate it as a continuous or ordinal factor for the power analysis
    cue_levels = np.linspace(-1, 1, n_stimuli_per_participant // 2) # Approximate levels
    # Actually, let's stick to the factorial design: 3 emoji x 2 punct x 2 length x 2 context = 24
    # For power analysis, we need to simulate the specific interaction.
    # Let's assume the interaction effect is the difference in slopes between relationships.

    data = []
    for p_id in range(n_participants):
        rel = relationships[p_id % 2] # Alternate or randomize
        # Generate 24 stimuli per participant
        for s_id in range(n_stimuli_per_participant):
            # Simulate Cue Intensity (0 to 1)
            cue_intensity = np.random.beta(2, 2) # Random distribution
            # Simulate Relationship Effect (main effect)
            rel_effect = 0.5 if rel == "friend" else 0.0
            # Simulate Interaction Effect
            # If interaction exists, the slope of cue on rating differs by relationship
            interaction_term = effect_size * cue_intensity if rel == "friend" else 0.0
            
            # Random effects
            p_random = np.random.normal(0, 0.5) # Participant random intercept
            s_random = np.random.normal(0, 0.3) # Stimulus random intercept
            
            # Residual error
            error = np.random.normal(0, 1.0)
            
            # Base rating
            base_rating = 3.0
            
            rating = base_rating + rel_effect + interaction_term + p_random + s_random + error
            rating = np.clip(rating, 1, 7) # Likert scale 1-7

            data.append({
                "participant_id": f"P-{p_id:04d}",
                "stimulus_id": f"S-{s_id:04d}",
                "relationship": rel,
                "cue_intensity": cue_intensity,
                "rating": rating
            })

    return pd.DataFrame(data)

def run_lmm(df):
    """
    Fit the LMM and return the p-value for the interaction term.
    Formula: rating ~ relationship * cue_intensity + (1 | participant_id) + (1 | stimulus_id)
    """
    try:
        # Convert categorical variables
        df["relationship"] = df["relationship"].astype("category")
        
        # Fit model
        # Note: statsmodels mixedlm syntax
        model = mixedlm(
            "rating ~ relationship + cue_intensity + relationship:cue_intensity",
            df,
            groups=df["participant_id"]
        )
        # Note: Random intercept for stimulus is harder to fit directly with mixedlm in one go
        # without expanding the formula syntax or using linearmodels.
        # For power analysis simulation, we often simplify to random intercept for participant
        # and assume stimulus variance is captured in error or a second grouping if possible.
        # However, to be rigorous, let's try to include stimulus random effect if possible.
        # statsmodels mixedlm supports only one grouping variable in the standard formula.
        # We will use a simplified model for the power analysis simulation that captures
        # the main source of non-independence (participant) and treats stimulus as fixed or
        # aggregated, OR we assume the stimulus random effect is small compared to participant.
        # Given the constraints of statsmodels mixedlm, we will fit:
        # rating ~ relationship * cue_intensity + (1 | participant_id)
        # This is a standard approximation for power analysis in LMMs when stimulus random effects
        # are secondary or when we are focusing on participant power.
        
        result = model.fit(reml=False)
        
        # Extract p-value for the interaction term
        # The parameter name will be "relationship[T.friend]:cue_intensity" or similar
        p_values = result.pvalues
        interaction_p = None
        
        for param, p_val in p_values.items():
            if "relationship" in param and "cue_intensity" in param:
                interaction_p = p_val
                break
        
        return interaction_p
    except Exception as e:
        # If model fails to converge, return None (treat as non-significant for power calc)
        return None

def estimate_power(n_participants, n_simulations=N_SIMULATIONS, seed=RANDOM_SEED):
    """
    Estimate statistical power for a given number of participants.
    """
    significant_count = 0
    
    for i in range(n_simulations):
        sim_seed = seed + i
        df = simulate_data(n_participants, seed=sim_seed)
        p_val = run_lmm(df)
        
        if p_val is not None and p_val < ALPHA:
            significant_count += 1
    
    power = significant_count / n_simulations
    return power

def find_required_n(target_power=TARGET_POWER, start_n=10, step=5, max_n=500):
    """
    Perform a binary search or linear scan to find the minimum N required.
    """
    current_n = start_n
    current_power = 0.0
    
    print(f"Starting power analysis search. Target power: {target_power}")
    
    while current_n <= max_n:
        power = estimate_power(current_n)
        print(f"N={current_n}: Power={power:.3f}")
        
        if power >= target_power:
            return current_n, power
        
        current_n += step
    
    return max_n, estimate_power(max_n)

def main():
    """
    Main entry point for power analysis.
    """
    print("Running Power Analysis for LMM Interaction Effect...")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Find required N
    # We start with a small N and increase until power >= 0.80
    # Using a step of 10 for efficiency, then refining if needed
    required_n, final_power = find_required_n(
        target_power=TARGET_POWER, 
        start_n=20, 
        step=10, 
        max_n=300
    )
    
    # Refine if the step was too large (optional, but good practice)
    # If final_power is just above target, we might want to check N-10
    if required_n > 20:
        prev_n = required_n - 10
        prev_power = estimate_power(prev_n)
        if prev_power >= TARGET_POWER:
            required_n = prev_n
            final_power = prev_power
    
    result = {
        "analysis_type": "LMM Interaction Power Analysis",
        "method": "Simulation-based (Monte Carlo)",
        "parameters": {
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "effect_size": EFFECT_SIZE,
            "n_simulations": N_SIMULATIONS,
            "random_seed": RANDOM_SEED,
            "model_formula": "rating ~ relationship + cue_intensity + relationship:cue_intensity + (1 | participant_id)"
        },
        "result": {
            "target_sample_size_n": required_n,
            "achieved_power_at_n": final_power,
            "description": f"Minimum number of participants required to detect a medium interaction effect (f={EFFECT_SIZE}) with {TARGET_POWER} power and alpha={ALPHA} is {required_n}."
        }
    }
    
    # Write results to JSON
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Power analysis complete. Required N: {required_n}")
    print(f"Results saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
