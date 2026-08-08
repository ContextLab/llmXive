"""
Power Analysis Module for LMM Simulation.

This module provides functions to simulate data for a Linear Mixed Model (LMM),
fit the model, estimate statistical power, and determine the required sample size.
"""
import json
import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Ensure imports work when run as a script or imported
if __name__ == "__main__" and "code" not in str(Path.cwd()):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

def simulate_data(
    n_participants: int,
    n_stimuli_per_participant: int = 4,
    effect_size_interaction: float = 0.35,
    effect_size_main_relationship: float = 0.50,
    effect_size_main_cue: float = 0.40,
    random_effect_variance: float = 0.2,
    residual_variance: float = 1.0,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic data for LMM power analysis.
    
    Simulates a factorial design where each participant rates multiple stimuli.
    The model structure is: rating ~ relationship * cue_intensity + (1|participant)
    
    Args:
        n_participants: Number of unique participants.
        n_stimuli_per_participant: Number of stimuli each participant rates.
        effect_size_interaction: True effect size for the interaction term.
        effect_size_main_relationship: True effect size for relationship main effect.
        effect_size_main_cue: True effect size for cue intensity main effect.
        random_effect_variance: Variance of the random intercept for participants.
        residual_variance: Residual error variance.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with columns: participant_id, stimulus_id, relationship, cue_intensity, rating
    """
    if seed is not None:
        np.random.seed(seed)
    
    data_rows = []
    
    # Encode categorical variables numerically for simulation
    # Relationship: 0, 1, 2 (e.g., Stranger, Acquaintance, Friend)
    # Cue Intensity: 0, 1, 2 (Low, Medium, High)
    
    for pid in range(n_participants):
        # Random intercept for this participant
        u_0 = np.random.normal(0, np.sqrt(random_effect_variance))
        
        for _ in range(n_stimuli_per_participant):
            # Randomly assign relationship and cue intensity
            relationship = np.random.choice([0, 1, 2])
            cue_intensity = np.random.choice([0, 1, 2])
            
            # Linear predictor
            # Intercept (base) + Main Effects + Interaction + Random Effect
            intercept = 3.0 # Base rating
            beta_rel = effect_size_main_relationship
            beta_cue = effect_size_main_cue
            beta_int = effect_size_interaction
            
            eta = intercept + (beta_rel * relationship) + (beta_cue * cue_intensity) + (beta_int * relationship * cue_intensity) + u_0
            
            # Add residual noise
            y = eta + np.random.normal(0, np.sqrt(residual_variance))
            
            data_rows.append({
                "participant_id": pid,
                "stimulus_id": f"stim_{pid}_{_}",
                "relationship": relationship,
                "cue_intensity": cue_intensity,
                "rating": y
            })
    
    return pd.DataFrame(data_rows)

def run_lmm(df: pd.DataFrame) -> Tuple[Optional[float], bool]:
    """
    Fit the LMM: rating ~ relationship * cue_intensity + (1|participant_id)
    
    Returns:
        Tuple of (interaction_p_value, success_flag)
        Returns (None, False) if the model fails to converge.
    """
    try:
        # Prepare data
        # We use statsmodels MixedLM
        # Formula: rating ~ relationship * cue_intensity
        # Random effects: (1 | participant_id)
        
        # statsmodels MixedLM requires endog (y) and exog (X)
        # We need to handle the interaction manually or use a formula interface if available
        # statsmodels does not have a native formula interface for MixedLM in the same way as R's lmer
        # So we construct the design matrix manually.
        
        y = df['rating'].values
        
        # Create design matrix for fixed effects
        # Intercept, relationship, cue_intensity, interaction
        X = np.column_stack([
            np.ones(len(df)),
            df['relationship'].values.astype(float),
            df['cue_intensity'].values.astype(float),
            (df['relationship'].values.astype(float) * df['cue_intensity'].values.astype(float))
        ])
        
        # Random effects: Group variable
        groups = df['participant_id'].values
        
        # Fit model
        # method='REML' is standard, but for hypothesis testing on fixed effects, 'ML' is sometimes preferred
        # We'll use REML as it's the default and robust for variance components
        model = MixedLM(y, X, groups=groups, exog_re=np.ones((len(df), 1)))
        
        # Suppress convergence warnings for the power analysis loop
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.fit(maxiter=1000)
        
        if not result.converged:
            return None, False
        
        # Extract p-value for the interaction term (index 3)
        # statsmodels result.pvalues returns a dictionary or array-like
        # We need the p-value corresponding to the 4th column (interaction)
        p_values = result.pvalues
        interaction_p = p_values.iloc[3] if hasattr(p_values, 'iloc') else list(p_values.values)[3]
        
        return float(interaction_p), True
        
    except Exception as e:
        # Log error if needed, but return failure
        return None, False

def estimate_power(
    n_simulations: int,
    n_participants: int,
    alpha: float = 0.05,
    effect_size_interaction: float = 0.35,
    **kwargs
) -> float:
    """
    Estimate statistical power for a given sample size.
    
    Args:
        n_simulations: Number of simulated datasets.
        n_participants: Sample size (N) to test.
        alpha: Significance level.
        effect_size_interaction: True effect size for simulation.
        **kwargs: Additional parameters for simulate_data.
        
    Returns:
        Proportion of simulations where the interaction effect was significant.
    """
    significant_count = 0
    valid_simulations = 0
    
    for i in range(n_simulations):
        df = simulate_data(
            n_participants=n_participants,
            effect_size_interaction=effect_size_interaction,
            seed=42 + i, # Vary seed for each simulation
            **kwargs
        )
        
        p_val, success = run_lmm(df)
        
        if success and p_val is not None:
            valid_simulations += 1
            if p_val < alpha:
                significant_count += 1
    
    if valid_simulations == 0:
        return 0.0
        
    return significant_count / valid_simulations

def find_required_n(
    n_min: int,
    n_max: int,
    n_step: int,
    n_simulations: int,
    alpha: float = 0.05,
    target_power: float = 0.80,
    effect_size_interaction: float = 0.35,
    effect_size_main_relationship: float = 0.50,
    effect_size_main_cue: float = 0.40,
    random_effect_variance: float = 0.2,
    residual_variance: float = 1.0,
    logger: Optional[logging.Logger] = None
) -> Optional[Dict[str, Any]]:
    """
    Find the minimum N required to achieve target_power.
    
    Iterates through sample sizes from n_min to n_max.
    Returns the first N where estimated_power >= target_power.
    
    Args:
        n_min, n_max, n_step: Range and step for N.
        n_simulations: Simulations per N.
        alpha, target_power: Target metrics.
        effect sizes and variances: Simulation parameters.
        logger: Logger instance.
        
    Returns:
        Dict with 'required_n' and 'power_at_required_n', or None if not found.
    """
    power_curve = []
    
    for n in range(n_min, n_max + 1, n_step):
        if logger:
            logger.info(f"Testing N={n}...")
        
        power = estimate_power(
            n_simulations=n_simulations,
            n_participants=n,
            alpha=alpha,
            effect_size_interaction=effect_size_interaction,
            effect_size_main_relationship=effect_size_main_relationship,
            effect_size_main_cue=effect_size_main_cue,
            random_effect_variance=random_effect_variance,
            residual_variance=residual_variance
        )
        
        power_curve.append({"n": n, "power": power})
        
        if logger:
            logger.info(f"N={n}: Power={power:.3f}")
        
        if power >= target_power:
            return {
                "required_n": n,
                "power_at_required_n": power,
                "power_curve": power_curve
            }
    
    # If loop finishes without reaching target
    return None

def save_power_analysis_results(results: Dict[str, Any], output_path: Path):
    """
    Save power analysis results to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def load_power_analysis_results(input_path: Path) -> Dict[str, Any]:
    """
    Load power analysis results from a JSON file.
    """
    with open(input_path, 'r') as f:
        return json.load(f)

def generate_power_curve(results: Dict[str, Any], output_path: Path):
    """
    Generate a plot of the power curve (optional visualization).
    """
    try:
        import matplotlib.pyplot as plt
        curve = results.get("power_curve", [])
        if not curve:
            return
        
        ns = [c["n"] for c in curve]
        powers = [c["power"] for c in curve]
        
        plt.figure(figsize=(10, 6))
        plt.plot(ns, powers, marker='o', label='Estimated Power')
        plt.axhline(y=0.80, color='r', linestyle='--', label='Target Power (0.80)')
        plt.xlabel('Sample Size (N)')
        plt.ylabel('Statistical Power')
        plt.title('Power Analysis Curve for LMM Interaction Effect')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()
    except ImportError:
        pass # Matplotlib not available, skip plot

def main():
    """
    CLI entry point for running the power analysis directly.
    """
    # Default parameters
    n_min, n_max, n_step = 20, 200, 20
    n_sims = 500
    output_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "power_analysis_results.json"
    
    print(f"Running power analysis. Saving to {output_file}")
    
    results = find_required_n(
        n_min=n_min,
        n_max=n_max,
        n_step=n_step,
        n_simulations=n_sims,
        target_power=0.80,
        effect_size_interaction=0.35
    )
    
    if results:
        print(f"Required N: {results['required_n']}")
        print(f"Power at N: {results['power_at_required_n']:.3f}")
        save_power_analysis_results(results, output_file)
    else:
        print("Could not find required N within range.")

if __name__ == "__main__":
    main()
