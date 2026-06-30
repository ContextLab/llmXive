"""
Bidirectional Evolutionary Search (BES) CPU Adapter

This script implements a CPU-tractable, scaled-down version of the core BES logic
described in "Self-Improving Language Models with Bidirectional Evolutionary Search".

Approximations made for CPU/CI constraints:
1.  **Task**: Replaced complex geometry optimization (Circle Packing/Heilbronn) with 
    a "Synthetic Subgoal Optimization" task. The goal is to find a set of 5 numbers 
    that sum to 10.0 and have a minimal variance.
2.  **Forward Search**: Replaced LLM-based expansion with a Gaussian mutation operator.
    Replaced LLM-based recombination with a simple arithmetic crossover (avg of parents).
3.  **Backward Search**: Replaced recursive LLM decomposition with a deterministic 
    "Split-and-Verify" heuristic. The goal (sum=10) is split into sub-goals for 
    subsets of numbers, providing dense feedback.
4.  **Scale**: Population size = 20, Generations = 10. Runs in < 10 seconds.

Outputs:
- data/bes_results.json: Final population, best score, and backward satisfaction metrics.
- figures/evolution_plot.png: Convergence plot of the best score over generations.
"""

import json
import os
import random
import math
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for CI
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple, Optional

# Configuration
POP_SIZE = 20
GENERATIONS = 10
MUTATION_RATE = 0.3
MUTATION_STD = 0.1
CROSSOVER_RATE = 0.6
NUM_VARIABLES = 5
TARGET_SUM = 10.0
ATOL = 0.1 # Tolerance for sum check

# Output paths
DATA_DIR = "data"
FIGURES_DIR = "figures"

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

def generate_initial_population(pop_size: int, n_vars: int) -> List[np.ndarray]:
    """Generates random initial candidates."""
    population = []
    for _ in range(pop_size):
        # Random values between 0 and 2 (sum roughly 10)
        candidate = np.random.uniform(0, 2, n_vars)
        population.append(candidate)
    return population

def calculate_fitness(candidate: np.ndarray) -> Tuple[float, bool]:
    """
    Calculates fitness based on:
    1. Sum constraint (must be close to TARGET_SUM)
    2. Variance (minimize variance for 'optimal' packing)
    
    Returns: (score, is_valid)
    Score is lower is better.
    """
    current_sum = np.sum(candidate)
    variance = np.var(candidate)
    
    sum_error = abs(current_sum - TARGET_SUM)
    
    # Penalty for invalid sum
    penalty = 0.0
    if sum_error > ATOL:
        penalty = sum_error * 10.0 # Heavy penalty
    
    score = variance + penalty
    is_valid = sum_error <= ATOL
    
    return score, is_valid

def backward_decomposition(candidate: np.ndarray) -> Dict[str, Any]:
    """
    Simulates the 'Backward Search' / Goal Decomposition.
    Instead of LLM recursion, we split the problem into sub-goals:
    1. Sum of first half
    2. Sum of second half
    3. Individual bounds
    
    Returns satisfaction scores for these sub-goals.
    """
    n = len(candidate)
    mid = n // 2
    
    sum_half1 = np.sum(candidate[:mid])
    sum_half2 = np.sum(candidate[mid:])
    
    # Sub-goal targets (half of total target)
    target_half = TARGET_SUM / 2.0
    
    sat_1 = max(0, 1.0 - abs(sum_half1 - target_half))
    sat_2 = max(0, 1.0 - abs(sum_half2 - target_half))
    
    # Check bounds (0 to 2)
    bounds_sat = 1.0 if np.all((candidate >= 0) & (candidate <= 2)) else 0.5
    
    return {
        "subgoal_sum_half1": float(sat_1),
        "subgoal_sum_half2": float(sat_2),
        "subgoal_bounds": float(bounds_sat),
        "total_satisfaction": float((sat_1 + sat_2 + bounds_sat) / 3.0)
    }

def evolve_population(population: List[np.ndarray], generation: int) -> Tuple[List[np.ndarray], List[float], List[Dict[str, Any]]]:
    """
    Performs one generation of evolution:
    1. Evaluate fitness
    2. Select parents (tournament)
    3. Crossover (arithmetic)
    4. Mutation
    5. Backward decomposition for dense feedback
    """
    new_population = []
    scores = []
    backward_metrics = []
    
    # Evaluate current
    current_scores = [calculate_fitness(ind)[0] for ind in population]
    
    for _ in range(len(population)):
        # Tournament Selection
        tournament = random.sample(list(range(len(population))), 3)
        best_idx = min(tournament, key=lambda i: current_scores[i])
        parent1 = population[best_idx].copy()
        
        # Crossover
        if random.random() < CROSSOVER_RATE and len(population) > 1:
            other_idx = random.choice([i for i in range(len(population)) if i != best_idx])
            parent2 = population[other_idx].copy()
            alpha = random.random()
            child = alpha * parent1 + (1 - alpha) * parent2
        else:
            child = parent1
            
        # Mutation
        if random.random() < MUTATION_RATE:
            child += np.random.normal(0, MUTATION_STD, child.shape)
            # Clip to reasonable bounds
            child = np.clip(child, -1, 3)
            
        new_population.append(child)
        
        # Evaluate new child immediately for feedback
        score, is_valid = calculate_fitness(child)
        scores.append(score)
        
        # Run backward decomposition
        b_metrics = backward_decomposition(child)
        backward_metrics.append(b_metrics)
        
    return new_population, scores, backward_metrics

def run_bes_simulation():
    """Main execution flow."""
    print("Starting BES CPU Adapter Simulation...")
    ensure_dirs()
    
    population = generate_initial_population(POP_SIZE, NUM_VARIABLES)
    best_score_over_time = []
    best_candidate_history = []
    
    print(f"Initial Population Size: {POP_SIZE}, Variables: {NUM_VARIABLES}")
    
    for gen in range(GENERATIONS):
        population, scores, b_metrics = evolve_population(population, gen)
        
        # Track best
        current_best_idx = np.argmin(scores)
        current_best_score = scores[current_best_idx]
        current_best_candidate = population[current_best_idx]
        
        best_score_over_time.append(current_best_score)
        best_candidate_history.append(current_best_candidate.tolist())
        
        print(f"Gen {gen+1}/{GENERATIONS}: Best Score = {current_best_score:.4f}, "
              f"Sum = {np.sum(current_best_candidate):.2f}, "
              f"Backward Sat = {b_metrics[current_best_idx]['total_satisfaction']:.2f}")

    # Final Analysis
    final_best_idx = np.argmin(best_score_over_time)
    final_candidate = np.array(best_candidate_history[final_best_idx])
    final_score = best_score_over_time[final_best_idx]
    final_sum = np.sum(final_candidate)
    final_variance = np.var(final_candidate)
    
    # Prepare Output Data
    result_data = {
        "metadata": {
            "task": "Synthetic Sum Optimization (BES Proxy)",
            "population_size": POP_SIZE,
            "generations": GENERATIONS,
            "target_sum": TARGET_SUM,
            "num_variables": NUM_VARIABLES
        },
        "best_result": {
            "candidate": final_candidate.tolist(),
            "sum": float(final_sum),
            "variance": float(final_variance),
            "score": float(final_score),
            "is_valid": abs(final_sum - TARGET_SUM) <= ATOL
        },
        "backward_search_metrics": {
            "final_satisfaction": float(backward_decomposition(final_candidate)['total_satisfaction']),
            "subgoals": {
                "sum_half1": float(backward_decomposition(final_candidate)['subgoal_sum_half1']),
                "sum_half2": float(backward_decomposition(final_candidate)['subgoal_sum_half2']),
                "bounds": float(backward_decomposition(final_candidate)['subgoal_bounds'])
            }
        },
        "convergence": {
            "generations": list(range(1, GENERATIONS + 1)),
            "best_scores": best_score_over_time
        }
    }
    
    # Write JSON
    json_path = os.path.join(DATA_DIR, "bes_results.json")
    with open(json_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    print(f"Results written to {json_path}")
    
    # Plot Convergence
    plt.figure(figsize=(8, 5))
    plt.plot(result_data['convergence']['generations'], 
             result_data['convergence']['best_scores'], 
             marker='o', label='Best Score (Lower is Better)')
    plt.xlabel('Generation')
    plt.ylabel('Fitness Score')
    plt.title('BES Evolutionary Search Convergence (CPU Adapter)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    fig_path = os.path.join(FIGURES_DIR, "evolution_plot.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Plot written to {fig_path}")
    
    return result_data

if __name__ == "__main__":
    try:
        result = run_bes_simulation()
        print("Simulation completed successfully.")
    except Exception as e:
        print(f"Simulation failed with error: {e}")
        # Write a failure artifact to ensure the pipeline doesn't crash
        error_data = {
            "status": "failed",
            "error": str(e),
            "metadata": {"task": "Synthetic Sum Optimization"}
        }
        with open(os.path.join(DATA_DIR, "bes_results.json"), 'w') as f:
            json.dump(error_data, f)
        raise
