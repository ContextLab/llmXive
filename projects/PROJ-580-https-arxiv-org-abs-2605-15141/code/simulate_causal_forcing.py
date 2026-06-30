import os
import math
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict

# Ensure output directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def create_synthetic_video_data(batch_size: int = 4, seq_len: int = 32) -> torch.Tensor:
    """
    Creates a simple synthetic 'video' (batch, seq_len) representing a moving sine wave.
    This replaces the massive Wan2.1 latent space with a tractable 1D proxy.
    """
    t = torch.linspace(0, 2 * math.pi, seq_len).unsqueeze(0)
    # Create a pattern that moves slightly over time (simulating motion)
    # We generate a single 'clean' frame and add noise to simulate diffusion states
    clean_frame = torch.sin(t + 0.5) 
    return clean_frame.unsqueeze(0).expand(batch_size, -1).unsqueeze(-1) # Shape: (B, T, 1) -> simplified to (B, T)

def flow_field(x: torch.Tensor, t: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Implements the Flow-Matching vector field.
    In Flow Matching, the optimal vector field is often v = x1 - x0 (linear path).
    Here, we approximate the conditional flow: v = target - x.
    """
    return target - x

def integrate_ode(x0: torch.Tensor, target: torch.Tensor, num_steps: int) -> List[torch.Tensor]:
    """
    Simulates the Teacher (48-step) ODE integration.
    Uses Euler integration for simplicity.
    """
    trajectory = [x0.clone()]
    dt = 1.0 / num_steps
    
    current_x = x0.clone()
    for i in range(num_steps):
        t = (i + 1) * dt
        # Vector field at current state
        v = flow_field(current_x, torch.tensor([t]), target)
        current_x = current_x + dt * v
        trajectory.append(current_x.clone())
    
    return trajectory

def integrate_student_ode(x0: torch.Tensor, target: torch.Tensor, num_steps: int, 
                          use_causal_init: bool = False) -> List[torch.Tensor]:
    """
    Simulates the Student (2-step) ODE integration.
    If use_causal_init is True, we initialize x0 closer to the target (mimicking Causal Forcing).
    If False, we start from pure noise (Naive initialization).
    """
    trajectory = [x0.clone()]
    dt = 1.0 / num_steps
    
    current_x = x0.clone()
    
    # Causal Forcing Approximation:
    # The paper argues that initializing the student closer to the teacher's early steps
    # reduces the error in few-step generation.
    if use_causal_init:
        # Instead of starting at pure noise (0), we start at a point that is
        # partially denoised (e.g., 20% of the way to the target).
        # This simulates the "causal consistency distillation" initialization.
        current_x = x0 * 0.8 + target * 0.2
    
    for i in range(num_steps):
        v = flow_field(current_x, torch.tensor([(i + 1) * dt]), target)
        current_x = current_x + dt * v
        trajectory.append(current_x.clone())
        
    return trajectory

def compute_trajectory_error(teacher_traj: List[torch.Tensor], student_traj: List[torch.Tensor]) -> float:
    """
    Computes the Mean Squared Error between the Teacher and Student trajectories.
    Since steps differ (48 vs 2), we compare the final frame and a few intermediate checkpoints.
    """
    # Teacher has 49 points (0 to 48), Student has 3 points (0 to 2)
    # We align by time: compare Student[0], Student[1], Student[2] to Teacher[0], Teacher[24], Teacher[48]
    indices = [0, 24, 48]
    errors = []
    
    for i, idx in enumerate(indices):
        if idx < len(teacher_traj):
            err = torch.mean((teacher_traj[idx] - student_traj[i]) ** 2).item()
            errors.append(err)
            
    return sum(errors) / len(errors)

def main():
    print("Starting Causal Forcing++ CPU Adaptation...")
    
    # 1. Setup Synthetic Data
    batch_size = 4
    seq_len = 32
    target_video = create_synthetic_video_data(batch_size, seq_len)
    
    # Initial noise (x0)
    x0 = torch.randn(batch_size, seq_len, 1) * 0.5
    
    # 2. Run Teacher (48 steps) - The "Ground Truth" Trajectory
    print("Generating Teacher Trajectory (48 steps)...")
    teacher_trajectory = integrate_ode(x0, target_video, num_steps=48)
    
    # 3. Run Student (2 steps) - Naive Initialization
    print("Generating Student Trajectory (Naive Init)...")
    student_naive = integrate_student_ode(x0, target_video, num_steps=2, use_causal_init=False)
    error_naive = compute_trajectory_error(teacher_trajectory, student_naive)
    
    # 4. Run Student (2 steps) - Causal Initialization (Our Approximation of the Paper's Method)
    print("Generating Student Trajectory (Causal Init)...")
    student_causal = integrate_student_ode(x0, target_video, num_steps=2, use_causal_init=True)
    error_causal = compute_trajectory_error(teacher_trajectory, student_causal)
    
    # 5. Save Results
    # Save Teacher Trajectory (subset of frames for brevity)
    teacher_df = pd.DataFrame()
    for i, frame in enumerate(teacher_trajectory):
        if i % 12 == 0: # Save every 12th step
            frame_flat = frame.flatten().numpy()
            for j, val in enumerate(frame_flat):
                teacher_df[f'frame_{i}_pixel_{j}'] = [val]
    teacher_df.to_csv("data/teacher_trajectory.csv", index=False)
    
    # Save Student Trajectories
    student_df = pd.DataFrame()
    for i, frame in enumerate(student_naive):
        frame_flat = frame.flatten().numpy()
        for j, val in enumerate(frame_flat):
            student_df[f'naive_frame_{i}_pixel_{j}'] = [val]
    for i, frame in enumerate(student_causal):
        frame_flat = frame.flatten().numpy()
        for j, val in enumerate(frame_flat):
            student_df[f'causal_frame_{i}_pixel_{j}'] = [val]
    student_df.to_csv("data/student_trajectory.csv", index=False)
    
    # Save Quantitative Results
    results = {
        "method": ["Naive Initialization", "Causal Forcing Initialization"],
        "trajectory_mse": [error_naive, error_causal],
        "description": [
            "Student initialized at pure noise (standard diffusion)",
            "Student initialized with partial denoising (Causal Forcing approximation)"
        ]
    }
    results_df = pd.DataFrame(results)
    results_df.to_csv("data/results.csv", index=False)
    
    print(f"Results saved to data/results.csv")
    print(f"Naive MSE: {error_naive:.6f}")
    print(f"Causal MSE: {error_causal:.6f}")
    print(f"Improvement: {((error_naive - error_causal) / error_naive * 100):.2f}%")
    
    # 6. Plot Results
    plt.figure(figsize=(12, 6))
    
    # Plot a single sample path for visualization
    sample_idx = 0
    sample_seq_len = seq_len
    
    # Extract a single pixel's evolution over time for visualization
    # We pick the center pixel
    center_pixel = sample_seq_len // 2
    
    t_teacher = np.linspace(0, 1, len(teacher_trajectory))
    y_teacher = [t[sample_idx, center_pixel, 0].item() for t in teacher_trajectory]
    
    t_student = [0.0, 0.5, 1.0] # Approximate time steps for 2-step
    y_naive = [t[sample_idx, center_pixel, 0].item() for t in student_naive]
    y_causal = [t[sample_idx, center_pixel, 0].item() for t in student_causal]
    
    plt.plot(t_teacher, y_teacher, 'k-', label='Teacher (48 steps)', linewidth=2)
    plt.plot(t_student, y_naive, 'r--o', label='Student (Naive, 2 steps)', markersize=10)
    plt.plot(t_student, y_causal, 'b-s', label='Student (Causal, 2 steps)', markersize=10)
    
    plt.title("Trajectory Comparison: Naive vs. Causal Forcing Initialization")
    plt.xlabel("Time (t)")
    plt.ylabel("Pixel Value (Center)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/flow_comparison.png", dpi=150)
    print("Plot saved to figures/flow_comparison.png")
    
    print("Adaptation complete. All artifacts generated.")

if __name__ == "__main__":
    main()
