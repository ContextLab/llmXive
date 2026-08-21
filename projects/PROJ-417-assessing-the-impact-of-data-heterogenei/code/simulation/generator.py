import json
import math
import random
import csv
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
import numpy as np

from utils.logging import get_logger
from config_loader import get_base_data_path, get_simulation_params

logger = get_logger(__name__)

@dataclass
class SimulationConfig:
    tau2_level: float
    replicate_count: int
    true_effect: float
    seed: int
    base_data_path: str

@dataclass
class StudyResult:
    study_id: int
    effect_size: float
    variance: float
    se: float
    n_studies: int
    reliability_flag: bool
    injected_true_effect: float
    injected_tau2: float

@dataclass
class SimulationResult:
    config: SimulationConfig
    studies: List[StudyResult]
    timestamp: str

def load_base_data_structure(base_path: str) -> List[Dict[str, Any]]:
    """
    Loads the base data (either real Cochrane or synthetic) from CSV.
    Returns a list of dictionaries with 'effect_size' and 'se' (or 'variance').
    """
    data = []
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Base data file not found: {base_path}")
    
    with open(base_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys if necessary
            entry = {
                'effect_size': float(row.get('effect_size', row.get('effect', 0.0))),
                'se': float(row.get('se', row.get('standard_error', 1.0))),
                'variance': float(row.get('variance', float(row.get('se', 1.0))**2))
            }
            data.append(entry)
    
    if not data:
        raise ValueError("Base data file is empty or invalid.")
    
    return data

def calculate_effect_and_variance(base_entry: Dict[str, Any], tau2: float, true_effect: float, rng: np.random.Generator) -> tuple:
    """
    Calculates the simulated effect size and variance for a study.
    
    Handles the edge case where tau2 == 0 to avoid numerical instability 
    (e.g., sqrt(0) is fine, but ensuring no division by zero or negative variance).
    
    Model: y_i = theta_i + e_i
    theta_i ~ N(true_effect, tau2)
    e_i ~ N(0, v_i) where v_i is the base variance (se^2)
    
    Total Variance = tau2 + v_i
    Simulated Effect = true_effect + Z1 * sqrt(tau2) + Z2 * sqrt(v_i)
    """
    v_i = base_entry['variance']
    se_i = math.sqrt(v_i) if v_i > 0 else 1e-6 # Guard against zero base variance
    
    # Between-study variance component
    if tau2 < 0:
        raise ValueError(f"Invalid tau2 level: {tau2}. Must be non-negative.")
    
    # Numerical stability for tau2=0
    # If tau2 is extremely small but positive, we treat it as 0 to avoid floating point noise
    # or if it is exactly 0.
    effective_tau2 = max(tau2, 0.0)
    
    if effective_tau2 == 0.0:
        # Homogeneous case: No between-study variance
        # theta_i = true_effect exactly
        # y_i = true_effect + e_i
        # Variance = v_i
        between_study_component = 0.0
    else:
        between_study_component = math.sqrt(effective_tau2)
    
    # Generate random components
    z_between = rng.standard_normal()
    z_within = rng.standard_normal()
    
    # Simulate true effect for this study (theta_i)
    theta_i = true_effect + (between_study_component * z_between)
    
    # Simulate observed effect (y_i)
    observed_effect = theta_i + (se_i * z_within)
    
    # Total variance for this replicate
    total_variance = effective_tau2 + v_i
    
    return observed_effect, total_variance, math.sqrt(total_variance)

def create_replicate(
    base_data: List[Dict[str, Any]],
    config: SimulationConfig,
    rng: np.random.Generator
) -> List[StudyResult]:
    """
    Generates a single replicate of the simulation based on the base data structure
    and the specified tau2 level.
    """
    studies = []
    n_base = len(base_data)
    
    # Ensure we have enough base studies or replicate the base structure if needed
    # The task implies using the structure of the base data (N_studies)
    # We assume base_data represents the 'shape' (N, SE distribution) of one study set.
    # We iterate through the base data entries to generate one study per entry.
    
    for i, base_entry in enumerate(base_data):
        effect, var, se = calculate_effect_and_variance(
            base_entry, 
            config.tau2_level, 
            config.true_effect, 
            rng
        )
        
        # Reliability flag logic (T011b): N_studies < 5
        # Here N_studies refers to the total count in the meta-analysis (length of base_data)
        n_studies = n_base
        reliability_flag = n_studies >= 5
        
        study = StudyResult(
            study_id=i,
            effect_size=effect,
            variance=var,
            se=se,
            n_studies=n_studies,
            reliability_flag=reliability_flag,
            injected_true_effect=config.true_effect,
            injected_tau2=config.tau2_level
        )
        studies.append(study)
    
    return studies

def generate_synthetic_meta_analysis(config: SimulationConfig) -> SimulationResult:
    """
    Runs the simulation for a specific tau2 level and replicate count.
    Returns a list of all study results across all replicates.
    """
    logger.info(f"Starting simulation for tau2={config.tau2_level}, replicates={config.replicate_count}")
    
    base_data = load_base_data_structure(config.base_data_path)
    logger.info(f"Loaded {len(base_data)} base studies from {config.base_data_path}")
    
    # Initialize RNG with seed
    rng = np.random.default_rng(config.seed)
    
    all_studies = []
    
    for r in range(config.replicate_count):
        # Increment seed for each replicate to ensure independence if needed, 
        # though the RNG state handles this. 
        # We can use the main RNG directly.
        replicate_studies = create_replicate(base_data, config, rng)
        all_studies.extend(replicate_studies)
        
        if (r + 1) % 100 == 0:
            logger.info(f"Completed {r + 1}/{config.replicate_count} replicates")
    
    return SimulationResult(
        config=config,
        studies=all_studies,
        timestamp="generated" # Placeholder, usually datetime.now().isoformat()
    )

def validate_simulation_output(result: SimulationResult) -> bool:
    """
    Validates that the output conforms to the expected schema requirements:
    - injected_true_effect exists
    - injected_tau2 exists
    - values are numeric
    """
    if not result.studies:
        logger.error("No studies generated.")
        return False
    
    for s in result.studies:
        if s.injected_true_effect is None or s.injected_tau2 is None:
            logger.error("Missing injected parameters.")
            return False
        if not isinstance(s.effect_size, (int, float)):
            return False
        if not isinstance(s.variance, (int, float)):
            return False
        # Check for numerical instability (NaN or Inf)
        if math.isnan(s.effect_size) or math.isinf(s.effect_size):
            logger.error(f"Numerical instability detected in effect size: {s.effect_size}")
            return False
        if math.isnan(s.variance) or math.isinf(s.variance):
            logger.error(f"Numerical instability detected in variance: {s.variance}")
            return False
        
    return True

def save_results_to_json(result: SimulationResult, output_path: str):
    """
    Saves the simulation results to a JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert dataclass to dict recursively
    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(i) for i in obj]
        else:
            return obj
    
    data = to_dict(result)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Entry point for the simulation generator.
    Reads config from config_loader and runs the simulation.
    """
    try:
        params = get_simulation_params()
        base_path = get_base_data_path()
        
        # Default values if not in config
        tau2_levels = params.get('tau2_levels', [0.0, 0.1, 0.5, 1.0, 2.0])
        replicate_count = params.get('replicate_count', 500)
        true_effect = params.get('true_effect', 0.5)
        seed = params.get('seed', 42)
        
        all_results = []
        
        for tau2 in tau2_levels:
            config = SimulationConfig(
                tau2_level=tau2,
                replicate_count=replicate_count,
                true_effect=true_effect,
                seed=seed,
                base_data_path=base_path
            )
            
            result = generate_synthetic_meta_analysis(config)
            
            if not validate_simulation_output(result):
                raise RuntimeError(f"Validation failed for tau2={tau2}")
            
            all_results.extend(result.studies)
        
        output_file = "data/results/simulation_raw.json"
        save_results_to_json(SimulationResult(
            config=SimulationConfig(0, 0, 0, 0, ""), # Dummy config for aggregation
            studies=all_results,
            timestamp=""
        ), output_file)
        
        logger.info("Simulation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise

if __name__ == "__main__":
    main()