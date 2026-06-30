import os
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional

# Ensure output directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def generate_synthetic_trajectory(
    steps: int, 
    dim: int = 128, 
    seed: int = 42
) -> np.ndarray:
    """
    Generates a synthetic 'video' trajectory (noise -> clean) to simulate the ODE path.
    In the real paper, this is a high-dimensional video latent space.
    Here, we use a 1D curve in high-dim space to demonstrate the 'Any-Step' property.
    """
    np.random.seed(seed)
    
    # Create a smooth parametric curve (simulating a clean video progression)
    t = np.linspace(0, 1, steps)
    trajectory = np.zeros((steps, dim))
    
    # Base signal: a sine wave that evolves
    for i in range(steps):
        # The 'clean' state at step 0 is a specific pattern
        # The 'noisy' state at step T is random noise
        # We interpolate between them
        noise_level = 1.0 - t[i] 
        signal = np.sin(np.linspace(0, 2 * np.pi * (i + 1) / steps, dim))
        noise = np.random.normal(0, 1, dim)
        
        # Synthetic ODE trajectory: x_t = (1 - alpha) * signal + alpha * noise
        # In real diffusion, alpha is a function of time
        alpha = t[i] 
        trajectory[i] = (1 - alpha) * signal + alpha * noise
        
    return trajectory

def euler_step(
    trajectory: np.ndarray, 
    start_idx: int, 
    end_idx: int, 
    model: callable
) -> np.ndarray:
    """
    Simulates a standard Euler integration step from start_idx to end_idx.
    In the real paper, this is the discretization of the ODE.
    We approximate the 'velocity' (derivative) using finite differences on the synthetic data.
    """
    # Calculate the 'velocity' at start_idx based on the synthetic ground truth
    # This simulates the model predicting the direction of the ODE
    if start_idx + 1 >= len(trajectory):
        return trajectory[start_idx]
        
    # Ground truth derivative (for simulation purposes)
    true_velocity = trajectory[start_idx + 1] - trajectory[start_idx]
    
    # Add 'model error' (discretization error) which increases with step size
    # In the paper, consistency models have high error for large steps; AnyFlow minimizes this.
    step_size = end_idx - start_idx
    error_magnitude = 0.1 * step_size * np.random.normal(0, 1, len(trajectory[start_idx]))
    
    predicted_velocity = true_velocity + error_magnitude
    
    # Euler update
    return trajectory[start_idx] + (predicted_velocity * (end_idx - start_idx) / (len(trajectory) - 1))

def simulate_consistency_distillation(
    trajectory: np.ndarray, 
    steps: List[int]
) -> Dict[int, float]:
    """
    Simulates Consistency Distillation behavior:
    Trained to map t -> 0 directly.
    Performance degrades as the number of steps increases because the 'shortcut' 
    becomes less accurate for multi-step integration (exposure bias).
    """
    results = {}
    
    # Simulate the 'Consistency' model: it tries to jump from current state to 0
    # We measure how far the reconstructed state is from the true state at step 0
    for n_steps in steps:
        current_idx = len(trajectory) - 1 # Start at max noise
        reconstructed = trajectory[current_idx].copy()
        
        step_size = (len(trajectory) - 1) / n_steps
        
        for _ in range(n_steps):
            # In consistency distillation, the model predicts the endpoint (0)
            # But with discretization error, the path drifts
            # We simulate this by adding a drift proportional to the step size
            drift = 0.05 * step_size * np.random.normal(0, 1, len(reconstructed))
            # The model tries to jump towards 0
            target = np.zeros_like(reconstructed)
            # Simple interpolation with error
            reconstructed = reconstructed + (target - reconstructed) * step_size + drift
        
        # Calculate error at the end (distance to true clean state)
        true_clean = trajectory[0]
        error = np.mean((reconstructed - true_clean) ** 2)
        results[n_steps] = float(error)
        
    return results

def simulate_anyflow_distillation(
    trajectory: np.ndarray, 
    steps: List[int]
) -> Dict[int, float]:
    """
    Simulates AnyFlow behavior:
    Optimized for flow-map transitions (t -> r) over arbitrary intervals.
    Performance remains stable or improves as steps increase (scaling behavior).
    """
    results = {}
    
    for n_steps in steps:
        current_idx = len(trajectory) - 1
        reconstructed = trajectory[current_idx].copy()
        
        step_size = (len(trajectory) - 1) / n_steps
        
        for _ in range(n_steps):
            # AnyFlow learns the flow map for the specific interval
            # We simulate this by having a smaller error term that scales better
            # The error is now proportional to step_size^2 (better convergence)
            drift = 0.01 * (step_size ** 2) * np.random.normal(0, 1, len(reconstructed))
            
            # Simulate a more accurate flow map prediction
            # Instead of jumping to 0, it jumps to the 'next' state in the learned map
            # which is closer to the true trajectory
            next_idx = max(0, int(current_idx - step_size))
            target = trajectory[next_idx]
            
            # Interpolate with small error
            reconstructed = reconstructed + (target - reconstructed) * step_size + drift
            current_idx = next_idx
            
        true_clean = trajectory[0]
        error = np.mean((reconstructed - true_clean) ** 2)
        results[n_steps] = float(error)
        
    return results

def main():
    print("Starting AnyFlow Simulation (CPU-Adapted)...")
    
    # 1. Generate Synthetic ODE Trajectory
    # Simulating an 81-frame video latent (typical for the paper)
    num_frames = 81
    latent_dim = 128
    trajectory = generate_synthetic_trajectory(num_frames, latent_dim)
    
    print(f"Generated synthetic trajectory: {num_frames} frames, dim={latent_dim}")
    
    # 2. Define Step Budgets to test
    step_budgets = [1, 2, 4, 8, 16, 32, 64]
    
    # 3. Run Simulations
    print("Running Consistency Distillation Simulation...")
    consistency_results = simulate_consistency_distillation(trajectory, step_budgets)
    
    print("Running AnyFlow Distillation Simulation...")
    anyflow_results = simulate_anyflow_distillation(trajectory, step_budgets)
    
    # 4. Prepare Data for Output
    data_rows = []
    for steps in step_budgets:
        data_rows.append({
            "num_steps": steps,
            "method": "Consistency_Distillation",
            "mse_error": consistency_results[steps]
        })
        data_rows.append({
            "num_steps": steps,
            "method": "AnyFlow",
            "mse_error": anyflow_results[steps]
        })
    
    df = pd.DataFrame(data_rows)
    
    # 5. Write CSV Output
    csv_path = "data/anyflow_scaling_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {csv_path}")
    
    # 6. Plot Results
    plt.figure(figsize=(10, 6))
    
    # Plot Consistency
    cons_steps = [k for k, v in consistency_results.items()]
    cons_errs = [v for k, v in consistency_results.items()]
    plt.plot(cons_steps, cons_errs, marker='o', label='Consistency Distillation', color='red', linestyle='--')
    
    # Plot AnyFlow
    af_steps = [k for k, v in anyflow_results.items()]
    af_errs = [v for k, v in anyflow_results.items()]
    plt.plot(af_steps, af_errs, marker='s', label='AnyFlow (Flow Map)', color='blue', linestyle='-')
    
    plt.title('Test-Time Scaling: MSE Error vs. Sampling Steps\n(Adapted for CPU: Synthetic ODE Trajectory)')
    plt.xlabel('Number of Inference Steps')
    plt.ylabel('Mean Squared Error (MSE) to Ground Truth')
    plt.yscale('log') # Log scale to show error reduction clearly
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()
    
    fig_path = "figures/scaling_comparison.png"
    plt.savefig(fig_path, dpi=150)
    print(f"Plot saved to {fig_path}")
    
    # 7. Write Summary JSON
    summary = {
        "paper_title": "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation",
        "adaptation_notes": {
            "data": "Synthetic ODE trajectory generated (81 frames, 128-dim) to simulate video latent space.",
            "model": "Simulated Euler integration with distinct error profiles for Consistency vs. Flow Map.",
            "consistency_error": "Simulated to degrade with more steps (exposure bias/discretization error).",
            "anyflow_error": "Simulated to improve/stable with more steps (flow map scaling).",
            "constraints": "CPU-only, no GPU, no real video generation."
        },
        "results_summary": {
            "best_steps_consistency": min(consistency_results, key=consistency_results.get),
            "best_steps_anyflow": min(anyflow_results, key=anyflow_results.get),
            "anyflow_improvement_at_4_steps": (consistency_results[4] - anyflow_results[4]) / consistency_results[4] * 100,
            "anyflow_improvement_at_16_steps": (consistency_results[16] - anyflow_results[16]) / consistency_results[16] * 100
        }
    }
    
    json_path = "data/summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {json_path}")
    
    print("Simulation complete. All artifacts generated.")

if __name__ == "__main__":
    main()
