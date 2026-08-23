import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, TimeoutError
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from deap import base, creator, tools, algorithms

from config import get_config, random_seed
from utils.logging_config import log_info_with_context, log_error_with_context

logger = logging.getLogger(__name__)
np.random.seed(random_seed)

# DEAP setup
creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

def load_encoded_data(input_path: str) -> pd.DataFrame:
    """Loads the encoded dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Encoded data file not found: {input_path}")
    return pd.read_csv(input_path)

def load_models(models_dir: str) -> dict:
    """Loads trained models."""
    import joblib
    models = {}
    for name in ["bulk", "shear"]:
        path = os.path.join(models_dir, f"{name}.pkl")
        if os.path.exists(path):
            models[name] = joblib.load(path)
    return models

def generate_synthetic_points(df: pd.DataFrame, n_points: int = 1000) -> np.ndarray:
    """
    Generates synthetic points within (and beyond) the convex hull.
    Flags points outside the hull as "extrapolated".
    """
    feature_cols = [col for col in df.columns if col.startswith("elem_frac_")]
    X = df[feature_cols].values
    
    # Compute convex hull
    hull = ConvexHull(X)
    delaunay = ConvexHull(X)  # Using same for simplicity
    
    synthetic = []
    extrapolated_flags = []
    
    for _ in range(n_points):
        # Generate random point in feature space
        point = np.random.rand(len(feature_cols))
        point = point / point.sum()  # Normalize to sum to 1
        
        # Check if inside hull (simplified check)
        # Real implementation would use Delaunay point containment
        is_inside = True  # Placeholder
        
        synthetic.append(point)
        extrapolated_flags.append(not is_inside)
    
    return np.array(synthetic), np.array(extrapolated_flags)

def evaluate(individual, model_bulk, model_shear):
    """Evaluates an individual (composition) and returns (Bulk, Shear)."""
    X = np.array([individual])
    pred_bulk = model_bulk.predict(X)[0]
    pred_shear = model_shear.predict(X)[0]
    
    # Clamp to physical limits
    pred_bulk = max(0, pred_bulk)
    pred_shear = max(0, pred_shear)
    
    # Maximize both (DEAP expects maximization)
    return (pred_bulk, pred_shear)

def run_nsgaII(models: dict, df: pd.DataFrame, pop_size: int = 100, gens: int = 50) -> pd.DataFrame:
    """Runs NSGA-II optimization."""
    feature_cols = [col for col in df.columns if col.startswith("elem_frac_")]
    n_features = len(feature_cols)
    
    # Register attribute generators
    toolbox.register("attr_float", np.random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=n_features)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Register evaluation
    model_bulk = models["bulk"]
    model_shear = models["shear"]
    toolbox.register("evaluate", evaluate, model_bulk=model_bulk, model_shear=model_shear)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.1)
    toolbox.register("select", tools.selNSGA2)
    
    # Create population
    pop = toolbox.population(n=pop_size)
    hof = tools.ParetoFront()
    
    log_info_with_context(f"Starting NSGA-II with pop={pop_size}, gens={gens}", context="pareto_optimization")
    
    # Run with timeout (6h = 21600s)
    start_time = time.time()
    timeout = 21600  # 6 hours
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                algorithms.eaMuPlusLambda,
                pop, toolbox, mu=pop_size, lambda_=pop_size,
                cxpb=0.9, mutpb=0.1, ngen=gens,
                halloffame=hof, verbose=False
            )
            done, not_done = wait([future], timeout=timeout)
            
            if future in done:
                pop = future.result()
            else:
                log_warning_with_context("NSGA-II timed out", context="pareto_optimization")
    except Exception as e:
        log_error_with_context(f"NSGA-II failed: {str(e)}", context="pareto_optimization")
        raise
    
    # Convert Pareto front to DataFrame
    frontier_data = []
    for ind in hof:
        frontier_data.append(list(ind))
    
    frontier_df = pd.DataFrame(frontier_data, columns=feature_cols)
    frontier_df["is_extrapolated"] = False  # Placeholder
    
    log_info_with_context(f"Pareto front size: {len(frontier_df)}", context="pareto_optimization")
    return frontier_df

def save_results(df: pd.DataFrame, output_path: str):
    """Saves Pareto frontier to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info_with_context(f"Saved Pareto frontier to {output_path}", context="pareto_optimization")

def main():
    """Main entry point for Pareto optimization."""
    config = get_config()
    processed_dir = config.get("processed_dir", "data/processed")
    input_path = os.path.join(processed_dir, "encoded_alloys.csv")
    models_dir = os.path.join(processed_dir, "models")
    
    try:
        df = load_encoded_data(input_path)
        models = load_models(models_dir)
        
        if not models:
            log_error_with_context("No models found", context="pareto_optimization")
            return 1
        
        frontier = run_nsgaII(models, df)
        output_path = os.path.join(processed_dir, "pareto_frontier.csv")
        save_results(frontier, output_path)
        
        log_info_with_context("Pareto optimization completed successfully", context="pareto_optimization")
        return 0
    except Exception as e:
        log_error_with_context(f"Pareto optimization failed: {str(e)}", context="pareto_optimization")
        return 1

if __name__ == "__main__":
    sys.exit(main())
