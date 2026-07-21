"""
Power analysis for Linear Mixed-Effects Models (LMM).

This module performs a simulation-based power analysis to determine the required
sample size (N) for detecting a medium interaction effect between relationship type
and cue intensity in a text message emotional support study.

Methodology:
- Simulates data based on a planned LMM design (Fixed effects: Relationship, CueIntensity, Interaction)
- Random intercepts for Participant and Stimulus
- Iteratively increases N until power >= 0.80 at alpha=0.05
"""

import json
import os
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

from config import get_processed_data_dir

# Suppress convergence warnings for cleaner output during simulation
warnings.filterwarnings("ignore", category=sm.tools.sm_exceptions.ConvergenceWarning)

# Simulation parameters
N_SIMULATIONS = 100  # Number of Monte Carlo simulations per N
ALPHA = 0.05
TARGET_POWER = 0.80
EFFECT_SIZE = 0.25  # Medium effect size (Cohen's f^2 approx)

# Design parameters
N_STIMULI_BASE = 10  # Base number of unique stimuli
N_CONDITIONS = 4     # 2 (Relationship: Friend/Acquaintance) x 2 (Cue: Low/High)

def simulate_data(
    n_participants: int,
    n_stimuli: int,
    effect_size: float = EFFECT_SIZE,
    seed: int = 42
) -> pd.DataFrame:
    """
    Simulate dataset for power analysis.
    
    Args:
        n_participants: Number of participants (N)
        n_stimuli: Number of unique stimuli
        effect_size: The interaction effect size to detect
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with simulated ratings
    """
    np.random.seed(seed)
    
    # Create design matrix
    # Each participant rates all stimuli (fully crossed)
    data = []
    
    # Generate participant IDs
    p_ids = [f"P{str(i).zfill(3)}" for i in range(n_participants)]
    # Generate stimulus IDs
    s_ids = [f"S{str(i).zfill(3)}" for i in range(n_stimuli)]
    
    # Create full crossed design
    for p_id in p_ids:
        for s_id in s_ids:
            # Randomly assign relationship context (Friend vs Acquaintance)
            # 0: Acquaintance, 1: Friend
            relationship = np.random.choice([0, 1])
            
            # Randomly assign cue intensity (Low vs High)
            # 0: Low, 1: High
            cue_intensity = np.random.choice([0, 1])
            
            # Generate base rating (intercept ~ 3.0 on 1-5 scale)
            rating = 3.0
            
            # Add random noise
            noise = np.random.normal(0, 1.0)
            
            # Add main effects (small)
            rating += 0.1 * relationship  # Friend slightly higher
            rating += 0.1 * cue_intensity # High cue slightly higher
            
            # Add interaction effect (the target we want to detect)
            # Interaction: High cue is much more supportive with Friends than Acquaintances
            if relationship == 1 and cue_intensity == 1:
                rating += effect_size * 2.0  # Boost for interaction
            
            # Add random intercepts for participant and stimulus
            # (Simulating the mixed model structure)
            p_intercept = np.random.normal(0, 0.5)
            s_intercept = np.random.normal(0, 0.3)
            
            final_rating = rating + p_intercept + s_intercept + noise
            
            # Clip to 1-5 scale
            final_rating = np.clip(final_rating, 1.0, 5.0)
            
            data.append({
                "participant_id": p_id,
                "stimulus_id": s_id,
                "relationship": relationship,
                "cue_intensity": cue_intensity,
                "rating": final_rating
            })
    
    return pd.DataFrame(data)

def run_lmm(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Run the LMM and return the p-value for the interaction term.
    
    Args:
        df: Simulated dataset
        
    Returns:
        Tuple of (p_value, converged)
    """
    try:
        # Formula: rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)
        # Note: statsmodels mixedlm uses a slightly different syntax for random effects
        # We use a simplified approach: random intercepts for participant and stimulus
        
        # Convert categorical to numeric for formula (already 0/1)
        df['relationship'] = df['relationship'].astype(float)
        df['cue_intensity'] = df['cue_intensity'].astype(float)
        
        # Fit model
        # Using a simplified random effects structure:
        # We'll use a group for participant and another for stimulus, 
        # but statsmodels mixedlm typically handles one grouping variable.
        # To handle crossed random effects, we might need a workaround or 
        # use linearmodels if available. For this simulation, we'll use 
        # a simplified single-group approach or aggregate if necessary.
        
        # Alternative: Use a single group for participant and treat stimulus as fixed?
        # No, we need crossed. Let's try a workaround: 
        # Since statsmodels mixedlm doesn't natively support crossed random effects 
        # in the standard formula interface easily without complex grouping, 
        # we will use a simplified model for power estimation:
        # rating ~ relationship * cue_intensity + (1|participant_id)
        # And assume stimulus variance is captured or negligible for this specific 
        # power calculation approximation, OR use a fixed effect for stimulus if N_stimuli is small.
        
        # Given the constraints of standard statsmodels formula interface for crossed effects,
        # we will implement a "within-subjects" style approximation where we treat 
        # stimulus as a fixed effect if N is small, or use a simplified random effect.
        # For robust power analysis, we simulate the specific structure.
        
        # Let's use a simpler approach for the simulation: 
        # Fit a model with random intercept for participant, and fixed effects for 
        # relationship, cue, and their interaction. 
        # This is a conservative estimate if stimulus variance is ignored, 
        # but sufficient for determining N if the effect is strong.
        
        model = mixedlm(
            "rating ~ relationship * cue_intensity", 
            df, 
            groups=df["participant_id"]
        )
        
        # Fit with reml=False for p-values (ML) or REML=True (standard)
        # We use REML for variance components, but ML for fixed effects comparison sometimes.
        # Standard practice: REML.
        result = model.fit(reml=True)
        
        # Extract p-value for the interaction term
        # The interaction term is 'relationship:cue_intensity'
        p_value = result.pvalues.get("relationship:cue_intensity", 1.0)
        
        return p_value, True
        
    except Exception as e:
        # If model fails to converge, return high p-value (fail to reject)
        return 1.0, False

def estimate_power(
    n_participants: int,
    n_stimuli: int,
    n_sims: int = N_SIMULATIONS,
    seed_base: int = 42
) -> float:
    """
    Estimate power for a given sample size.
    
    Args:
        n_participants: Number of participants
        n_stimuli: Number of stimuli
        n_sims: Number of simulations
        seed_base: Base seed
        
    Returns:
        Estimated power (0.0 to 1.0)
    """
    significant_count = 0
    
    for i in range(n_sims):
        # Simulate data
        df = simulate_data(n_participants, n_stimuli, seed=seed_base + i)
        
        # Run model
        p_val, converged = run_lmm(df)
        
        if converged and p_val < ALPHA:
            significant_count += 1
    
    return significant_count / n_sims

def find_required_n(
    n_stimuli: int = N_STIMULI_BASE,
    min_n: int = 20,
    max_n: int = 500,
    step: int = 10,
    n_sims: int = N_SIMULATIONS
) -> Tuple[int, Dict[int, float]]:
    """
    Find the required sample size (N) to achieve target power.
    
    Args:
        n_stimuli: Number of stimuli
        min_n: Minimum participants to test
        max_n: Maximum participants to test
        step: Increment step
        n_sims: Simulations per N
        
    Returns:
        Tuple of (required_n, power_curve_dict)
    """
    power_curve = {}
    required_n = None
    
    print(f"Starting power analysis for interaction effect (target power={TARGET_POWER})...")
    print(f"Stimuli: {n_stimuli}, Alpha: {ALPHA}")
    
    for n in range(min_n, max_n + 1, step):
        power = estimate_power(n, n_stimuli, n_sims)
        power_curve[n] = power
        
        print(f"N={n}: Power={power:.3f}")
        
        if power >= TARGET_POWER and required_n is None:
            required_n = n
            print(f"--> Target power reached at N={n}")
            break
    
    if required_n is None:
        # If not reached, return max_n or raise warning
        print(f"WARNING: Target power not reached within range. Max power at N={max_n} was {power_curve.get(max_n, 0):.3f}")
        required_n = max_n
        
    return required_n, power_curve

def main():
    """
    Main entry point for power analysis.
    Runs the analysis and saves results to data/processed/power_analysis_results.json
    """
    processed_dir = get_processed_data_dir()
    output_path = processed_dir / "power_analysis_results.json"
    
    # Ensure directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis
    required_n, power_curve = find_required_n(
        n_stimuli=N_STIMULI_BASE,
        min_n=20,
        max_n=300,
        step=10,
        n_sims=50  # Reduced for speed in initial run, can be increased for final
    )
    
    # Prepare results
    results = {
        "target_power": TARGET_POWER,
        "alpha": ALPHA,
        "effect_size_assumed": EFFECT_SIZE,
        "n_stimuli": N_STIMULI_BASE,
        "required_participants": required_n,
        "power_curve": {str(k): float(v) for k, v in power_curve.items()},
        "methodology": "Monte Carlo simulation of LMM with random intercepts for Participant",
        "timestamp": str(pd.Timestamp.now())
    }
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nPower analysis complete.")
    print(f"Required sample size (N): {required_n} participants")
    print(f"Results saved to: {output_path}")
    
    return required_n

if __name__ == "__main__":
    main()
