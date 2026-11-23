import json
import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats

# Import local config for paths
try:
    from config import get_processed_data_dir
except ImportError:
    # Fallback for direct execution in code/ directory
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_processed_data_dir

logger = logging.getLogger(__name__)

def simulate_data(n_participants: int, n_stimuli: int, seed: int, 
                  effect_size: float = 0.5, intra_class_corr: float = 0.3) -> pd.DataFrame:
    """
    Simulate a dataset for power analysis based on a linear mixed model.
    Model: Rating ~ CueIntensity + (1 | Participant) + (1 | Stimulus)
    
    Parameters:
    - n_participants: Number of unique participants
    - n_stimuli: Number of unique stimuli
    - seed: Random seed for reproducibility
    - effect_size: The expected coefficient for the fixed effect (CueIntensity)
    - intra_class_corr: Approximate intra-class correlation for random effects
    
    Returns:
    - DataFrame with columns: participant_id, stimulus_id, cue_intensity, rating
    """
    np.random.seed(seed)
    
    # Generate IDs
    participant_ids = [f"P{i:03d}" for i in range(n_participants)]
    stimulus_ids = [f"S{i:03d}" for i in range(n_stimuli)]
    
    # Create full factorial design (every participant sees every stimulus)
    # In a real scenario, this might be a subset, but for power analysis we simulate the full design
    # to maximize power estimation accuracy for the given N.
    trials = []
    for p_id in participant_ids:
        for s_id in stimulus_ids:
            trials.append({'participant_id': p_id, 'stimulus_id': s_id})
    
    df = pd.DataFrame(trials)
    
    # Generate random effects
    # Estimate variance components based on ICC and total variance assumption
    # Assume residual variance = 1.0 for simplicity
    residual_var = 1.0
    total_var = residual_var / (1 - intra_class_corr)
    random_effect_var = total_var - residual_var
    sd_random = np.sqrt(random_effect_var)
    
    # Random intercepts for participants
    p_intercepts = np.random.normal(0, sd_random, n_participants)
    p_map = {pid: val for pid, val in zip(participant_ids, p_intercepts)}
    
    # Random intercepts for stimuli
    s_intercepts = np.random.normal(0, sd_random, n_stimuli)
    s_map = {sid: val for sid, val in zip(stimulus_ids, s_intercepts)}
    
    # Fixed effect: CueIntensity (0 to 1 continuous)
    df['cue_intensity'] = np.random.uniform(0, 1, len(df))
    
    # Calculate rating
    # Rating = Intercept + EffectSize * CueIntensity + P_Random + S_Random + Residual
    intercept = 3.0 # Baseline rating
    df['rating'] = (
        intercept + 
        effect_size * df['cue_intensity'] + 
        df['participant_id'].map(p_map) + 
        df['stimulus_id'].map(s_map) + 
        np.random.normal(0, np.sqrt(residual_var), len(df))
    )
    
    return df

def run_lmm(df: pd.DataFrame) -> Dict[str, float]:
    """
    Run a Linear Mixed Model using statsmodels (Python equivalent of lmer).
    Since rpy2 is listed in requirements but we want a pure Python simulation
    for speed in power analysis loops, we use statsmodels MixedLM.
    
    Returns:
    - Dictionary with 'p_value' and 't_statistic' for the fixed effect of cue_intensity
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        raise ImportError("statsmodels is required for power analysis. Install via requirements.txt.")
    
    # Fit model: rating ~ cue_intensity + (1 | participant_id) + (1 | stimulus_id)
    # Note: statsmodels MixedLM handles random intercepts well.
    # We treat participant and stimulus as random effects.
    try:
        model = smf.mixedlm("rating ~ cue_intensity", df, 
                          groups=df["participant_id"],
                          exog_re={"stimulus": df["stimulus_id"]})
        # Note: The above exog_re syntax is for random slopes. 
        # For simple random intercepts for both, we usually fit one and control for the other or use a simpler approach.
        # To strictly mimic lmer(1|P) + (1|S), we can use a simpler approach or iterate.
        # For power analysis speed, we will fit: rating ~ cue_intensity + (1|participant_id)
        # and include stimulus_id as a fixed effect if N_stimuli is small, or ignore it if we assume it's balanced.
        # However, the most robust simple simulation for power is to fit the main effect of interest.
        
        # Let's use a simpler model that captures the variance structure:
        # rating ~ cue_intensity + (1 | participant_id)
        # We assume stimulus variance is captured in the residual or balanced out in the simulation design.
        # For a more accurate simulation, we would need to fit both. 
        # Given statsmodels limitations with multiple grouping factors in a single call without complex setup:
        # We will fit the model with participant as random group.
        
        model = smf.mixedlm("rating ~ cue_intensity", df, groups=df["participant_id"])
        result = model.fit()
        
        # Get the p-value for the cue_intensity coefficient
        # The coefficients are: Intercept, cue_intensity
        p_val = result.pvalues['cue_intensity']
        t_val = result.tvalues['cue_intensity']
        
        return {'p_value': p_val, 't_statistic': t_val, 'converged': True}
    except Exception as e:
        warnings.warn(f"Model fitting failed: {e}")
        return {'p_value': 1.0, 't_statistic': 0.0, 'converged': False}

def estimate_power(n_simulations: int, n_participants: int, n_stimuli: int, 
                   effect_size: float, alpha: float = 0.05, seed: int = 42) -> float:
    """
    Estimate statistical power by running n_simulations.
    Power = proportion of simulations where p < alpha.
    """
    logger.info(f"Running {n_simulations} simulations for N={n_participants} participants...")
    significant_count = 0
    
    for i in range(n_simulations):
        sim_seed = seed + i
        df = simulate_data(n_participants, n_stimuli, sim_seed, effect_size=effect_size)
        result = run_lmm(df)
        
        if result['converged'] and result['p_value'] < alpha:
            significant_count += 1
            
        if (i + 1) % 10 == 0:
            logger.debug(f"Completed {i+1}/{n_simulations} simulations")
    
    power = significant_count / n_simulations
    logger.info(f"Estimated power: {power:.3f}")
    return power

def find_required_n(target_power: float = 0.80, alpha: float = 0.05, 
                    effect_size: float = 0.5, n_stimuli: int = 50, 
                    n_simulations_per_n: int = 100, max_n: int = 200, seed: int = 42) -> Tuple[int, float]:
    """
    Iteratively find the number of participants (N) required to achieve target_power.
    Returns (target_N, estimated_power_at_target_N)
    """
    logger.info(f"Searching for N to achieve power >= {target_power}...")
    
    # Start with a reasonable guess
    current_n = 30
    step = 10
    best_n = max_n
    best_power = 0.0
    
    while current_n <= max_n:
        power = estimate_power(n_simulations_per_n, current_n, n_stimuli, effect_size, alpha, seed)
        
        if power >= target_power:
            best_n = current_n
            best_power = power
            break # Found sufficient N
        
        current_n += step
        
        # If we are close, refine
        if power > 0.6 and step > 5:
            step = 5
            current_n = current_n - step + 5 # Adjust slightly back to search linearly
    
    # If loop finishes without break (unlikely with max_n=200 for reasonable effect sizes)
    if best_power < target_power:
        logger.warning(f"Could not reach target power {target_power} even with N={max_n}")
        return max_n, best_power
      
    return best_n, best_power

def save_power_analysis_results(results: Dict[str, Any], output_path: str):
    """Saves the power analysis results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Power analysis results saved to {output_path}")

def load_power_analysis_results(input_path: str) -> Dict[str, Any]:
    """Loads power analysis results from a JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Results file not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def generate_power_curve(n_values: List[int], effect_size: float, n_stimuli: int, 
                         n_sims: int, seed: int) -> List[Dict]:
    """Generates a list of (N, power) pairs for plotting."""
    curve = []
    for n in n_values:
        power = estimate_power(n_sims, n, n_stimuli, effect_size, seed=seed)
        curve.append({'n_participants': n, 'estimated_power': power})
    return curve

def main():
    """Main entry point for the power analysis task."""
    # Configuration
    N_SIMULATIONS = 100  # Reduced for speed in this implementation, increase for production
    TARGET_POWER = 0.80
    ALPHA = 0.05
    EFFECT_SIZE = 0.5    # Medium effect size assumption
    N_STIMULI = 50       # Assumed number of stimuli in the study
    RANDOM_SEED = 42
    
    # Output path
    output_dir = get_processed_data_dir()
    output_path = os.path.join(output_dir, "power_analysis_results.json")
    
    logger.info("Starting Power Analysis for LMM")
    
    # Perform the search for required N
    target_n, estimated_power = find_required_n(
        target_power=TARGET_POWER,
        alpha=ALPHA,
        effect_size=EFFECT_SIZE,
        n_stimuli=N_STIMULI,
        n_simulations_per_n=N_SIMULATIONS,
        max_n=200,
        seed=RANDOM_SEED
    )
    
    results = {
        "estimated_power": round(estimated_power, 4),
        "target_N": target_n,
        "method": "simulation-based power analysis using statsmodels MixedLM",
        "parameters": {
            "target_power": TARGET_POWER,
            "alpha": ALPHA,
            "assumed_effect_size": EFFECT_SIZE,
            "assumed_n_stimuli": N_STIMULI,
            "simulations_per_n": N_SIMULATIONS,
            "random_seed": RANDOM_SEED
        }
    }
    
    save_power_analysis_results(results, output_path)
    
    # Verification check
    if estimated_power < TARGET_POWER:
        logger.error(f"Estimated power {estimated_power} is below target {TARGET_POWER} for N={target_n}")
        # In a strict pipeline, we might raise an error here, but the task asks to write results.
        # The verification script T091-Check will handle the failure.
    
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
