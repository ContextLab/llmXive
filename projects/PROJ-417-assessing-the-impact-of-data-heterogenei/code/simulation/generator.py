import json
import math
import random
import csv
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import from project API
from utils.logging import get_logger, log_simulation_progress

logger = get_logger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for the simulation run."""
    tau2_levels: List[float]
    num_replicates: int
    base_data_path: str
    seed: Optional[int] = None

@dataclass
class StudyResult:
    """Represents a single study within a simulated meta-analysis."""
    study_id: str
    effect_size: float
    variance: float
    n_studies: int
    injected_true_effect: float
    injected_tau2: float
    reliability_flag: bool  # True if N < 5 (unreliable)

@dataclass
class SimulationResult:
    """Container for a single replicate's simulation data."""
    replicate_id: int
    tau2_level: float
    studies: List[StudyResult]
    num_studies: int
    is_valid: bool  # False if N < 5
    metadata: Dict[str, Any] = field(default_factory=dict)

def load_base_data_structure(base_path: str) -> List[Dict[str, Any]]:
    """
    Loads the base dataset (Cochrane or Synthetic) to determine
    the distribution of study sizes and variances.
    """
    path = Path(base_path)
    if not path.exists():
        raise FileNotFoundError(f"Base data file not found at {base_path}. "
                                "Please ensure T040 or T040b has been completed.")
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'effect_size': float(row.get('effect_size', 0.0)),
                'variance': float(row.get('variance', 1.0)),
                'n_studies': int(row.get('n_studies', 10))
            })
    logger.info(f"Loaded {len(data)} study records from {base_path}")
    return data

def calculate_effect_and_variance(
    base_effect: float, 
    base_var: float, 
    true_effect: float, 
    true_tau2: float,
    seed: int
) -> tuple[float, float]:
    """
    Calculates the simulated effect size and variance for a study.
    Applies the injected heterogeneity (tau2) to the base variance.
    """
    random.seed(seed)
    np.random.seed(seed)
    import numpy as np

    # The observed effect is the true effect + sampling error + between-study error
    # Sampling error ~ N(0, base_var)
    # Between-study error ~ N(0, true_tau2)
    
    sampling_error = np.random.normal(0, math.sqrt(base_var))
    between_study_error = np.random.normal(0, math.sqrt(true_tau2)) if true_tau2 > 0 else 0.0
    
    simulated_effect = true_effect + sampling_error + between_study_error
    
    # The observed variance is the base variance + tau2 (if we assume variance includes heterogeneity)
    # However, typically in meta-analysis simulation, the reported variance is the within-study variance.
    # The total variance of the effect estimator is V_i + tau^2.
    # For the purpose of the generator output, we store the within-study variance (base_var)
    # and the true parameters separately. The estimator will use base_var + tau2.
    simulated_variance = base_var 
    
    return float(simulated_effect), float(simulated_variance)

def create_replicate(
    base_data: List[Dict[str, Any]],
    tau2_level: float,
    replicate_id: int,
    true_effect: float,
    seed: int
) -> SimulationResult:
    """
    Creates a single replicate of a meta-analysis.
    Handles edge cases: N < 5 (flagged), tau2 = 0 (stable).
    """
    # Determine number of studies (sampling from base data distribution or fixed)
    # For this implementation, we use the size of the base dataset or a subset
    # to simulate a meta-analysis.
    num_studies = len(base_data)
    
    # Edge Case: Small Study Effects (N < 5)
    is_valid = num_studies >= 5
    
    studies = []
    for i, base_row in enumerate(base_data):
        # Generate a unique seed for this study within the replicate
        study_seed = seed + replicate_id * 10000 + i
        
        eff, var = calculate_effect_and_variance(
            base_row['effect_size'],
            base_row['variance'],
            true_effect,
            tau2_level,
            study_seed
        )
        
        reliability_flag = not is_valid
        
        study = StudyResult(
            study_id=f"R{replicate_id}_S{i}",
            effect_size=eff,
            variance=var,
            n_studies=num_studies,
            injected_true_effect=true_effect,
            injected_tau2=tau2_level,
            reliability_flag=reliability_flag
        )
        studies.append(study)
    
    return SimulationResult(
        replicate_id=replicate_id,
        tau2_level=tau2_level,
        studies=studies,
        num_studies=num_studies,
        is_valid=is_valid,
        metadata={
            'seed': seed,
            'true_effect': true_effect,
            'tau2': tau2_level
        }
    )

def generate_synthetic_meta_analysis(config: SimulationConfig) -> List[SimulationResult]:
    """
    Generates the full set of synthetic meta-analysis replicates.
    Implements the loop for >= 500 replicates per level.
    """
    base_data = load_base_data_structure(config.base_data_path)
    results = []
    
    # Determine true effect based on base data mean or a fixed value
    # Using the mean of the base data as a proxy for the "true" underlying effect
    # in the absence of a specific ground truth for the synthetic generation.
    true_effect = sum(d['effect_size'] for d in base_data) / len(base_data)
    
    logger.info(f"Starting simulation with {len(config.tau2_levels)} levels, "
                f"{config.num_replicates} replicates each.")
    
    total_replicates = 0
    for tau2 in config.tau2_levels:
        for rep_idx in range(config.num_replicates):
            # Use a deterministic seed based on level and index
            rep_seed = (config.seed or 42) + int(tau2 * 1000) + rep_idx
            
            result = create_replicate(
                base_data=base_data,
                tau2_level=tau2,
                replicate_id=total_replicates,
                true_effect=true_effect,
                seed=rep_seed
            )
            
            results.append(result)
            total_replicates += 1
            
            if total_replicates % 100 == 0:
                log_simulation_progress(total_replicates, config.num_replicates * len(config.tau2_levels))
    
    logger.info(f"Simulation complete. Generated {total_replicates} replicates.")
    return results

def validate_simulation_output(results: List[SimulationResult]) -> bool:
    """
    Validates that the output conforms to the expected structure.
    Checks for required fields and data types.
    """
    if not results:
        logger.error("No results to validate.")
        return False
    
    required_fields = ['replicate_id', 'tau2_level', 'studies', 'num_studies', 'is_valid']
    study_fields = ['study_id', 'effect_size', 'variance', 'n_studies', 'injected_true_effect', 'injected_tau2', 'reliability_flag']
    
    for i, res in enumerate(results):
        for field in required_fields:
            if not hasattr(res, field):
                logger.error(f"Result {i} missing field: {field}")
                return False
        
        if not isinstance(res.studies, list):
            logger.error(f"Result {i} studies is not a list")
            return False
        
        for j, study in enumerate(res.studies):
            for field in study_fields:
                if not hasattr(study, field):
                    logger.error(f"Result {i}, Study {j} missing field: {field}")
                    return False
    
    logger.info("Validation passed.")
    return True

def save_results_to_json(results: List[SimulationResult], output_path: str):
    """
    Saves the simulation results to a JSON file conforming to the schema.
    Converts dataclasses to dictionaries.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to serializable format
    serializable_results = []
    for res in results:
        serializable_res = {
            'replicate_id': res.replicate_id,
            'tau2_level': res.tau2_level,
            'num_studies': res.num_studies,
            'is_valid': res.is_valid,
            'metadata': res.metadata,
            'studies': [asdict(s) for s in res.studies]
        }
        serializable_results.append(serializable_res)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Entry point for the simulation generator.
    Reads configuration from arguments or defaults.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic meta-analysis datasets")
    parser.add_argument('--levels', nargs='+', type=float, default=[0.0, 0.1, 0.5, 1.0, 2.0],
                        help='Heterogeneity levels (tau2)')
    parser.add_argument('--replicates', type=int, default=500, help='Number of replicates per level')
    parser.add_argument('--base-data', type=str, default='data/raw/cochrane_base.csv',
                        help='Path to base data file (Cochrane or Synthetic)')
    parser.add_argument('--output', type=str, default='data/results/simulation_raw.json',
                        help='Output JSON file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Fallback to synthetic if real data not found (handled by load_base_data_structure raising error)
    # However, per spec, if T040 failed, T040b should have run.
    # We rely on the file existence check in load_base_data_structure.
    
    config = SimulationConfig(
        tau2_levels=args.levels,
        num_replicates=args.replicates,
        base_data_path=args.base_data,
        seed=args.seed
    )
    
    results = generate_synthetic_meta_analysis(config)
    
    if not validate_simulation_output(results):
        raise RuntimeError("Simulation output validation failed.")
    
    save_results_to_json(results, args.output)
    logger.info("Simulation pipeline completed successfully.")

if __name__ == "__main__":
    main()