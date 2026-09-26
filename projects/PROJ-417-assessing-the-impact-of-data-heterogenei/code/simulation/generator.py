import json
import math
import random
import csv
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path

# Import from project API surface
from utils.logging import get_logger
from config_loader import load_config, get_simulation_params, get_base_data_path, get_replicate_count, get_tau2_levels, get_random_seed

logger = get_logger(__name__)

@dataclass
class SimulationConfig:
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    base_data_path: str
    seed: int

@dataclass
class StudyResult:
    study_id: int
    effect_size: float
    standard_error: float
    variance: float
    # For homogeneity check
    is_homogeneous: bool = False

@dataclass
class SimulationResult:
    replicate_id: int
    injected_true_effect: float
    injected_tau2: float
    N_studies: int
    studies: List[Dict[str, Any]]
    # Aggregated stats for quick validation
    observed_between_study_variance: float = 0.0
    mean_effect: float = 0.0

def load_base_data_structure(base_data_path: str) -> Tuple[List[float], List[float]]:
    """
    Loads the base data (effect sizes and standard errors) from the CSV file.
    Returns: (effects, ses)
    """
    effects = []
    ses = []
    
    if not os.path.exists(base_data_path):
        logger.error(f"Base data file not found: {base_data_path}")
        raise FileNotFoundError(f"Base data file not found: {base_data_path}")

    with open(base_data_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential keys from different generators
            eff_key = 'effect_size' if 'effect_size' in row else 'effect'
            se_key = 'standard_error' if 'standard_error' in row else 'se'
            
            try:
                effects.append(float(row[eff_key]))
                ses.append(float(row[se_key]))
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row in base data: {row}, error: {e}")
                continue
    
    if len(effects) == 0:
        raise ValueError("Base data file is empty or contains no valid rows.")
    
    logger.info(f"Loaded {len(effects)} studies from base data.")
    return effects, ses

def calculate_effect_and_variance(
    base_effect: float, 
    base_se: float, 
    true_effect: float, 
    tau2: float, 
    rng: np.random.Generator
) -> Tuple[float, float]:
    """
    Calculates the simulated effect size and variance for a single study.
    
    Model: y_i ~ N(mu + u_i, v_i) where u_i ~ N(0, tau2)
    Simulated Effect = base_effect + random_normal(0, sqrt(tau2))
    Simulated Variance = base_se^2 (assumed fixed for this simulation design)
    
    Special handling for tau2=0 to ensure numerical stability (homogeneity).
    """
    # Numerical stability for zero variance
    if tau2 == 0.0:
        # Explicitly set between-study variance to 0 to avoid any floating point noise
        heterogeneity_component = 0.0
    else:
        # Draw heterogeneity component
        heterogeneity_component = rng.normal(0.0, math.sqrt(tau2))
    
    # Calculate the simulated effect size
    # We assume the base data represents the observed effect y_i
    # and we shift it by the true effect difference if needed, or just add heterogeneity
    # Standard meta-analysis simulation: y_i = mu + u_i + e_i
    # Here we use the base data as the 'e_i' component (sampling error) centered around 0?
    # Or we assume base data is the 'observed' and we inject true_effect as the mean.
    # Interpretation: We want to simulate a dataset where the true mean is `true_effect`
    # and between-study variance is `tau2`.
    # We use the base SEs as the sampling variances.
    # Simulated Effect = true_effect + heterogeneity_component + sampling_error
    # But we don't have the original sampling errors, we have the base effects.
    # Assumption: The base effects are from a study with mean 0 and variance se^2?
    # Or we simply add the heterogeneity to the base effect and shift the mean.
    # Common approach: y_sim = true_effect + u_i + e_i.
    # If we use base_se as e_i's std dev, we need e_i.
    # Let's assume the base data is a distribution of effects we are perturbing.
    # To strictly control the mean, we should probably generate e_i from N(0, se^2).
    # But the task says "load base data ... and implement a loop".
    # Let's assume the base data provides the SEs (precision) and we generate the effects.
    # However, if we generate entirely new effects, we lose the specific SE distribution shape.
    # Strategy: Use base_se as the sampling error std dev. Generate e_i ~ N(0, base_se^2).
    # Then y_i = true_effect + u_i + e_i.
    
    # Sampling error component
    sampling_error = rng.normal(0.0, base_se)
    
    simulated_effect = true_effect + heterogeneity_component + sampling_error
    simulated_variance = base_se ** 2
    
    return simulated_effect, simulated_variance

def create_replicate(
    config: SimulationConfig, 
    base_effects: List[float], 
    base_ses: List[float], 
    rng: np.random.Generator
) -> SimulationResult:
    """
    Generates a single replicate of a meta-analysis dataset.
    """
    studies = []
    N = config.N_studies
    
    # If base data has fewer studies than requested, cycle or pad?
    # Usually we assume base data is representative of the SE distribution.
    # We will sample N studies from the base SE distribution.
    # If N > len(base_ses), we repeat.
    
    # Determine which SEs to use
    if len(base_ses) >= N:
        selected_ses = base_ses[:N]
    else:
        # Repeat to fill
        selected_ses = (base_ses * (math.ceil(N / len(base_ses))))[:N]
    
    for i in range(N):
        se = selected_ses[i]
        effect, var = calculate_effect_and_variance(
            0.0, # base_effect placeholder (not used in new logic)
            se,
            config.injected_true_effect,
            config.injected_tau2,
            rng
        )
        
        # Determine if homogeneous for this study (only relevant if tau2=0)
        is_homogeneous = (config.injected_tau2 == 0.0)
        
        study = StudyResult(
            study_id=i,
            effect_size=effect,
            standard_error=se,
            variance=var,
            is_homogeneous=is_homogeneous
        )
        studies.append(asdict(study))
    
    # Calculate observed stats for validation
    if N > 1:
        effects_arr = np.array([s['effect_size'] for s in studies])
        # Observed variance of effects
        total_var = np.var(effects_arr, ddof=1)
        # Expected sampling variance (average of variances)
        avg_var = np.mean([s['variance'] for s in studies])
        # Observed between-study variance estimate (Method of Moments approx)
        # tau2_obs = max(0, total_var - avg_var)
        tau2_obs = max(0.0, total_var - avg_var)
        mean_eff = float(np.mean(effects_arr))
    else:
        tau2_obs = 0.0
        mean_eff = studies[0]['effect_size'] if studies else 0.0

    return SimulationResult(
        replicate_id=0, # Will be set by caller
        injected_true_effect=config.injected_true_effect,
        injected_tau2=config.injected_tau2,
        N_studies=N,
        studies=studies,
        observed_between_study_variance=tau2_obs,
        mean_effect=mean_eff
    )

def generate_synthetic_meta_analysis(config: SimulationConfig) -> List[SimulationResult]:
    """
    Generates multiple replicates for a given configuration.
    """
    base_effects, base_ses = load_base_data_structure(config.base_data_path)
    
    rng = np.random.default_rng(config.seed)
    results = []
    
    # T010 requirement: >= 500 replicates per level. 
    # This function is called per level, so we generate the requested count.
    # The caller (main) handles the loop over levels.
    # We assume the config passed here implies the number of replicates needed 
    # or we use a default from config_loader if not in this specific object.
    # For T012, we focus on the generation logic itself.
    
    # We'll assume 1 replicate per call for modularity, 
    # but the loop is usually in the main script. 
    # However, to satisfy T010's "loop generating >= 500", 
    # we should probably generate them here if this is the main entry for a level.
    # Let's assume the caller passes the count.
    # If not, we default to 1 for this function's scope and let the outer loop handle it.
    # Actually, looking at T010, the loop is part of the task.
    # We will implement the loop here to ensure T010 is satisfied if this is the main entry.
    # But T012 is about the logic. Let's just generate one here and assume the outer loop exists.
    # Wait, T010 says "Implement generator.py to ... implement a loop".
    # So the loop MUST be in this file.
    
    # We need the replicate count. Let's fetch it from config_loader if not in config.
    # But config is a dataclass. Let's add a field or fetch it.
    # Fetching from global config for the count.
    from config_loader import get_replicate_count
    n_replicates = get_replicate_count()
    
    logger.info(f"Generating {n_replicates} replicates for tau2={config.injected_tau2}")
    
    for i in range(n_replicates):
        # Update seed for this replicate to ensure reproducibility
        # We can increment the seed or use a sub-rng
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, base_effects, base_ses, sub_rng)
        result.replicate_id = i
        results.append(result)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{n_replicates} replicates")
    
    return results

def validate_simulation_output(results: List[SimulationResult]) -> bool:
    """
    Validates that the output conforms to the schema requirements.
    Checks for injected_true_effect, injected_tau2, N_studies.
    """
    if not results:
        logger.error("Validation failed: No results to validate.")
        return False
    
    # Check first result structure
    r = results[0]
    required_fields = ['injected_true_effect', 'injected_tau2', 'N_studies', 'studies']
    for field in required_fields:
        if not hasattr(r, field):
            logger.error(f"Validation failed: Missing field {field} in result.")
            return False
    
    # Check studies structure
    if r.studies:
        study = r.studies[0]
        study_fields = ['study_id', 'effect_size', 'standard_error', 'variance']
        for field in study_fields:
            if field not in study:
                logger.error(f"Validation failed: Missing field {field} in study.")
                return False
    
    logger.info("Simulation output validation passed.")
    return True

def save_results_to_json(results: List[SimulationResult], output_path: str):
    """
    Saves the simulation results to a JSON file.
    """
    # Convert dataclasses to dicts
    data = []
    for r in results:
        # Flatten the structure slightly for the JSON record as per schema
        # Schema: injected_true_effect, injected_tau2, N_studies, studies (list)
        record = asdict(r)
        # Ensure types are JSON serializable (numpy types might need casting)
        record['injected_true_effect'] = float(record['injected_true_effect'])
        record['injected_tau2'] = float(record['injected_tau2'])
        record['N_studies'] = int(record['N_studies'])
        record['replicate_id'] = int(record['replicate_id'])
        record['observed_between_study_variance'] = float(record['observed_between_study_variance'])
        record['mean_effect'] = float(record['mean_effect'])
        data.append(record)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """
    Main entry point for the simulation generator.
    Handles the loop over tau2 levels and replicates.
    """
    config = load_config()
    params = get_simulation_params(config)
    tau2_levels = get_tau2_levels(config)
    base_path = get_base_data_path(config)
    seed = get_random_seed(config)
    n_replicates = get_replicate_count(config)
    
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "simulation_raw.json"
    
    all_results = []
    
    for tau2 in tau2_levels:
        logger.info(f"Starting simulation for tau2={tau2}")
        
        # T012: Handle tau2=0 specifically to avoid numerical instability
        # The logic in calculate_effect_and_variance handles this,
        # but we ensure the config is set correctly.
        if tau2 == 0.0:
            logger.info("Detected tau2=0. Ensuring numerical stability (homogeneity).")
            # Force exact zero to prevent any float artifacts
            effective_tau2 = 0.0
        else:
            effective_tau2 = tau2
        
        current_config = SimulationConfig(
            injected_true_effect=params.get('injected_true_effect', 0.5),
            injected_tau2=effective_tau2,
            N_studies=params.get('N_studies', 20),
            base_data_path=base_path,
            seed=seed
        )
        
        results = generate_synthetic_meta_analysis(current_config)
        all_results.extend(results)
        logger.info(f"Completed simulation for tau2={tau2}. Generated {len(results)} replicates.")
    
    # Validate and Save
    if validate_simulation_output(all_results):
        save_results_to_json(all_results, str(output_file))
        logger.info("Simulation pipeline completed successfully.")
    else:
        logger.error("Simulation pipeline failed validation.")
        raise ValueError("Simulation output validation failed.")

if __name__ == "__main__":
    main()