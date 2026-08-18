import os
import sys
import logging
import argparse
import json
import time
import signal
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, Delaunay
from deap import base, creator, tools, algorithms
from sklearn.ensemble import GradientBoostingRegressor

# Project imports
from config import get_config
from utils.convex_hull import ConvexHullWrapper, compute_convex_hull, test_points_in_hull
from utils.logging_config import log_info_with_context, log_warning_with_context, log_error_with_context, configure_root_logger
from model_utils import clamp_predictions, test_extrapolation, process_model_predictions

# Constants
POPULATION_SIZE = 100
N_GENERATIONS = 50
CX_PROB = 0.9
MUT_PROB = 0.1
TIMEOUT_SECONDS = 6 * 3600  # 6 hours
RANDOM_SEED = 42

# Setup logger
configure_root_logger()
logger = logging.getLogger(__name__)

# DEAP setup
creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))  # Maximize Bulk and Shear
creator.create("Individual", np.ndarray, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

def load_encoded_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the encoded alloy data from the processed CSV."""
    data_path = Path(config.get("data_processed_path", "data/processed/encoded_alloys.csv"))
    if not data_path.exists():
        raise FileNotFoundError(f"Encoded data file not found: {data_path}")
    
    log_info_with_context(logger, f"Loading encoded data from {data_path}", context={"file": str(data_path)})
    df = pd.read_csv(data_path)
    
    # Validate columns
    required_cols = ["composition_string", "bulk_modulus", "shear_modulus"]
    feature_cols = [col for col in df.columns if col.startswith("feature_")]
    if not feature_cols:
        raise ValueError("No feature columns found in encoded data. Ensure feature_encoder.py was run.")
    
    log_info_with_context(logger, f"Loaded {len(df)} entries with {len(feature_cols)} features", context={"rows": len(df), "features": len(feature_cols)})
    return df, feature_cols

def load_models(config: Dict[str, Any]) -> Tuple[GradientBoostingRegressor, GradientBoostingRegressor]:
    """Load the trained models from the saved artifacts."""
    bulk_model_path = Path(config.get("bulk_model_path", "data/processed/model_bulk.pkl"))
    shear_model_path = Path(config.get("shear_model_path", "data/processed/model_shear.pkl"))
    
    if not bulk_model_path.exists() or not shear_model_path.exists():
        raise FileNotFoundError("Trained models not found. Ensure model_training.py has been run.")
    
    import joblib
    bulk_model = joblib.load(bulk_model_path)
    shear_model = joblib.load(shear_model_path)
    
    log_info_with_context(logger, "Models loaded successfully", context={"bulk": str(bulk_model_path), "shear": str(shear_model_path)})
    return bulk_model, shear_model

def generate_synthetic_points(
    feature_df: pd.DataFrame,
    feature_cols: List[str],
    n_points: int = 1000,
    random_seed: int = RANDOM_SEED
) -> Tuple[np.ndarray, List[bool]]:
    """
    Generate synthetic composition points within the convex hull of the training data.
    Returns: (points_array, is_extrapolated_flags)
    """
    log_info_with_context(logger, f"Generating {n_points} synthetic points within convex hull", context={"n": n_points})
    
    features = feature_df[feature_cols].values
    hull = ConvexHull(features)
    tri = Delaunay(features)
    
    # Generate random points in the bounding box first
    min_vals = features.min(axis=0)
    max_vals = features.max(axis=0)
    
    synthetic_points = []
    extrapolated_flags = []
    
    # We need to generate points strictly inside the hull
    # Strategy: Generate random barycentric coordinates for random simplices
    # Or use rejection sampling if n_points is small relative to volume
    
    # Rejection sampling approach for robustness
    attempts = 0
    max_attempts = n_points * 100
    while len(synthetic_points) < n_points and attempts < max_attempts:
        # Sample a random simplex (triangle in 3D, tetrahedron in 4D, etc.)
        # Actually, simpler: sample random convex combination of hull vertices
        # But Delaunay is better for "inside"
        
        # Pick a random point in the bounding box
        point = np.random.uniform(min_vals, max_vals)
        
        # Check if inside hull
        if tri.find_simplex(point) != -1:
            synthetic_points.append(point)
            extrapolated_flags.append(False) # Inside hull
        else:
            extrapolated_flags.append(True) # Outside (will be filtered)
        
        attempts += 1
    
    if len(synthetic_points) < n_points:
        log_warning_with_context(logger, f"Could only generate {len(synthetic_points)} points inside hull (target: {n_points})", context={"generated": len(synthetic_points), "target": n_points})
    
    return np.array(synthetic_points), extrapolated_flags

def evaluate(
    individual: np.ndarray,
    bulk_model: GradientBoostingRegressor,
    shear_model: GradientBoostingRegressor,
    feature_cols: List[str],
    config: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Evaluate the individual (synthetic composition) using the trained models.
    Returns: (bulk_modulus, shear_modulus) - both to be maximized
    """
    # Ensure input is 2D for sklearn
    x = individual.reshape(1, -1)
    
    # Predict
    try:
        bulk_pred = bulk_model.predict(x)[0]
        shear_pred = shear_model.predict(x)[0]
    except Exception as e:
        log_error_with_context(logger, f"Prediction failed for individual: {e}", context={"error": str(e)})
        return 0.0, 0.0  # Worst case for maximization
    
    # Clamp predictions to physical limits (moduli > 0)
    bulk_clamped = clamp_predictions(np.array([bulk_pred]), lower_bound=0.0)[0]
    shear_clamped = clamp_predictions(np.array([shear_pred]), lower_bound=0.0)[0]
    
    # Flag extrapolation if outside convex hull (handled in generation, but double check)
    # If we passed a point from generate_synthetic_points, we know its status, 
    # but here we just return the values. The flagging is done during generation.
    
    return float(bulk_clamped), float(shear_clamped)

def run_nsgaII(
    feature_df: pd.DataFrame,
    feature_cols: List[str],
    bulk_model: GradientBoostingRegressor,
    shear_model: GradientGBRegressor,
    config: Dict[str, Any]
) -> List[Tuple[float, float]]:
    """
    Run NSGA-II algorithm to find Pareto optimal compositions.
    """
    log_info_with_context(logger, "Starting NSGA-II optimization", context={"pop": POPULATION_SIZE, "gen": N_GENERATIONS})
    
    # Generate initial population
    # We generate more points than population to ensure diversity
    synth_points, _ = generate_synthetic_points(feature_df, feature_cols, n_points=POPULATION_SIZE * 10)
    
    # Create initial population
    population = [creator.Individual(p) for p in synth_points[:POPULATION_SIZE]]
    
    # Setup toolbox
    toolbox.register("evaluate", evaluate, 
                    bulk_model=bulk_model, 
                    shear_model=shear_model, 
                    feature_cols=feature_cols,
                    config=config)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=MUT_PROB)
    toolbox.register("select", tools.selNSGA2)
    
    # Run algorithm
    log_info_with_context(logger, "Evaluating initial population")
    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)
    
    # Main loop
    for gen in range(N_GENERATIONS):
        # Select offspring
        offspring = algorithms.varAnd(population, toolbox, cxpb=CX_PROB, mutpb=MUT_PROB)
        
        # Evaluate offspring
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        log_info_with_context(logger, f"Generation {gen}: Evaluating {len(invalid_ind)} individuals")
        
        for ind in invalid_ind:
            ind.fitness.values = toolbox.evaluate(ind)
        
        # Select next generation
        population = toolbox.select(offspring + population, POPULATION_SIZE)
        
        # Log progress
        if gen % 10 == 0:
            fits = [ind.fitness.values for ind in population if ind.fitness.valid]
            if fits:
                avg_bulk = np.mean([f[0] for f in fits])
                avg_shear = np.mean([f[1] for f in fits])
                log_info_with_context(logger, f"Generation {gen}: Avg Bulk={avg_bulk:.2f}, Avg Shear={avg_shear:.2f}", 
                                    context={"gen": gen, "avg_bulk": avg_bulk, "avg_shear": avg_shear})
    
    # Extract Pareto frontier
    pareto_front = tools.selNSGA2(population, len(population))
    results = [tuple(ind.fitness.values) for ind in pareto_front]
    
    log_info_with_context(logger, f"NSGA-II completed. Found {len(results)} Pareto optimal points")
    return results

def save_results(
    pareto_front: List[Tuple[float, float]],
    config: Dict[str, Any]
):
    """Save the Pareto frontier results to a JSON file."""
    output_path = Path(config.get("pareto_output_path", "data/processed/pareto_frontier.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of dicts for JSON serialization
    results_data = [
        {"bulk_modulus": float(b), "shear_modulus": float(s)} 
        for b, s in pareto_front
    ]
    
    with open(output_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    log_info_with_context(logger, f"Pareto frontier saved to {output_path}", context={"points": len(pareto_front)})
    return output_path

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"NSGA-II optimization exceeded the {TIMEOUT_SECONDS} second limit.")

def main():
    """Main entry point for Pareto optimization."""
    parser = argparse.ArgumentParser(description="Run NSGA-II for multi-property alloy optimization")
    parser.add_argument("--config", type=str, default="config_default.yaml", help="Path to config file")
    args = parser.parse_args()
    
    # Load config
    config = get_config(args.config)
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    
    try:
        log_info_with_context(logger, "Starting Pareto Optimization Pipeline")
        
        # Load data
        df, feature_cols = load_encoded_data(config)
        
        # Load models
        bulk_model, shear_model = load_models(config)
        
        # Run NSGA-II
        pareto_front = run_nsgaII(
            feature_df=df,
            feature_cols=feature_cols,
            bulk_model=bulk_model,
            shear_model=shear_model,
            config=config
        )
        
        # Save results
        save_results(pareto_front, config)
        
        log_info_with_context(logger, "Pareto Optimization completed successfully")
        
    except TimeoutError as e:
        log_error_with_context(logger, str(e), context={"timeout": TIMEOUT_SECONDS})
        raise
    except Exception as e:
        log_error_with_context(logger, f"Optimization failed: {e}", context={"error": str(e)})
        raise
    finally:
        signal.alarm(0)  # Cancel the alarm

if __name__ == "__main__":
    main()
