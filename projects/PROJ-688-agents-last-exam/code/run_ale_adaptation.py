import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

# Ensure we can run as a standalone script
if __name__ == "__main__":
    # Create output directories
    data_dir = Path("data")
    figures_dir = Path("figures")
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    # --- Configuration (Scaled Down) ---
    # Original paper tasks often use 1M+ paths. We use 5,000 for CPU speed.
    NUM_PATHS = 5000
    TIME_STEPS = 50
    MATURITY = 1.0  # 1 year
    RISK_FREE_RATE = 0.05
    VOLATILITY = 0.20
    STRIKE = 100.0
    SPOT = 100.0
    
    # Tolerance for "Passing" (simulating the paper's "verifiable outcome" check)
    # A real agent might fail if it's > 2% off.
    TOLERANCE_RATIO = 0.02 

    print(f"Starting ALE Adaptation: American Option Pricing (Longstaff-Schwartz)")
    print(f"Parameters: S0={SPOT}, K={STRIKE}, T={MATURITY}, r={RISK_FREE_RATE}, sigma={VOLATILITY}")
    print(f"Scale: {NUM_PATHS} paths, {TIME_STEPS} steps (Scaled for CPU)")

    # --- 1. Generate Real Financial Data (Monte Carlo Simulation) ---
    # We use real stochastic processes (Geometric Brownian Motion)
    dt = MATURITY / TIME_STEPS
    drift = (RISK_FREE_RATE - 0.5 * VOLATILITY**2) * dt
    diffusion = VOLATILITY * math.sqrt(dt)
    
    # Generate paths
    # Shape: (NUM_PATHS, TIME_STEPS + 1)
    z = np.random.standard_normal((NUM_PATHS, TIME_STEPS))
    paths = np.zeros((NUM_PATHS, TIME_STEPS + 1))
    paths[:, 0] = SPOT
    
    for t in range(1, TIME_STEPS + 1):
        paths[:, t] = paths[:, t-1] * np.exp(drift + diffusion * z[:, t-1])

    # --- 2. Implement Longstaff-Schwartz Algorithm ---
    # This is the "Core Logic" of the task the paper benchmarks.
    # We implement it directly to get a "Real Result" without an LLM.
    
    # Payoff at maturity (American Put)
    payoffs = np.maximum(STRIKE - paths[:, -1], 0.0)
    
    # Discount factor per step
    df = np.exp(-RISK_FREE_RATE * dt)
    
    # Backward induction
    # We only need to consider exercise at time steps where it might be optimal
    # For simplicity, we check every step from T-1 down to 1
    cash_flows = np.zeros(NUM_PATHS)
    cash_flows[payoffs > 0] = payoffs[payoffs > 0] # Initialize with maturity payoff
    
    # Store continuation values for analysis
    exercise_times = np.full(NUM_PATHS, TIME_STEPS, dtype=int)

    # Lagrange polynomial basis functions (simplified: 1, S, S^2)
    def get_basis(S):
        return np.vstack([np.ones_like(S), S, S**2]).T

    for t in range(TIME_STEPS - 1, 0, -1):
        # Only consider paths that are in-the-money (ITM)
        in_the_money = (STRIKE - paths[:, t]) > 0
        if not np.any(in_the_money):
            continue
            
        S = paths[in_the_money, t]
        Y = cash_flows[in_the_money] * df # Discounted future cash flows
        
        # Regression: Y = f(S)
        X = get_basis(S)
        try:
            # Least squares regression
            beta = np.linalg.lstsq(X, Y, rcond=None)[0]
            continuation_value = X @ beta
            
            # Exercise decision
            immediate_exercise = STRIKE - S
            exercise_now = immediate_exercise > continuation_value
            
            # Update cash flows for paths that exercise now
            if np.any(exercise_now):
                indices = np.where(in_the_money)[0][exercise_now]
                cash_flows[indices] = immediate_exercise[exercise_now]
                exercise_times[indices] = t
        except np.linalg.LinAlgError:
            # Fallback if singular matrix (rare with 5k paths)
            continue

    # --- 3. Calculate Result ---
    # Discount all cash flows to present value
    discount_factors = np.exp(-RISK_FREE_RATE * (np.array(exercise_times) * dt))
    option_price = np.mean(cash_flows * discount_factors)
    
    # --- 4. Reference Calculation (Approximation) ---
    # For American Puts, there is no closed form, but we can use a high-precision 
    # binomial tree or a known approximation to verify the LS result.
    # Here we use a very high-step binomial tree as the "Ground Truth" for the benchmark.
    N_binomial = 500
    dt_b = MATURITY / N_binomial
    u = np.exp(VOLATILITY * np.sqrt(dt_b))
    d = 1/u
    p = (np.exp(RISK_FREE_RATE * dt_b) - d) / (u - d)
    
    # Binomial Tree
    tree = np.zeros((N_binomial + 1, N_binomial + 1))
    # Terminal nodes
    for i in range(N_binomial + 1):
        tree[i, N_binomial] = max(STRIKE - SPOT * (u**i) * (d**(N_binomial-i)), 0)
    
    # Backward induction
    for j in range(N_binomial - 1, -1, -1):
        for i in range(j + 1):
            continuation = np.exp(-RISK_FREE_RATE * dt_b) * (p * tree[i+1, j+1] + (1-p) * tree[i, j+1])
            exercise = max(STRIKE - SPOT * (u**i) * (d**(j-i)), 0)
            tree[i, j] = max(continuation, exercise)
            
    reference_price = tree[0, 0]
    
    # --- 5. Compute Metrics ---
    absolute_error = abs(option_price - reference_price)
    relative_error = absolute_error / reference_price
    passed = relative_error < TOLERANCE_RATIO
    
    # --- 6. Generate Artifacts ---
    
    # A. JSON Result
    result_data = {
        "task": "american_option_pricing_ls",
        "paper_context": "Agents' Last Exam (ALE) - Scaled Adaptation",
        "parameters": {
            "spot": SPOT,
            "strike": STRIKE,
            "maturity": MATURITY,
            "rate": RISK_FREE_RATE,
            "volatility": VOLATILITY,
            "paths": NUM_PATHS,
            "steps": TIME_STEPS
        },
        "results": {
            "ls_price": float(option_price),
            "reference_price": float(reference_price),
            "absolute_error": float(absolute_error),
            "relative_error_percent": float(relative_error * 100),
            "tolerance_percent": float(TOLERANCE_RATIO * 100),
            "passed": passed
        },
        "status": "PASS" if passed else "FAIL",
        "notes": "Scaled Monte Carlo (5k paths) vs High-Step Binomial (500 steps). "
                 "This demonstrates the quantitative result of the task logic."
    }
    
    with open(data_dir / "ale_result.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\n--- Results ---")
    print(f"LS Price: ${option_price:.4f}")
    print(f"Reference Price: ${reference_price:.4f}")
    print(f"Relative Error: {relative_error*100:.4f}%")
    print(f"Status: {'PASS' if passed else 'FAIL'} (Tolerance: {TOLERANCE_RATIO*100}%)")
    
    # B. Plotting (Matplotlib)
    try:
        import matplotlib
        matplotlib.use('Agg') # Non-interactive backend
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 6))
        
        # Plot the distribution of simulated payoffs
        # We only plot the final cash flows for visualization
        plt.hist(cash_flows, bins=50, alpha=0.6, label='Simulated Cash Flows', color='skyblue')
        plt.axvline(x=option_price, color='red', linestyle='--', linewidth=2, label=f'LS Price ({option_price:.2f})')
        plt.axvline(x=reference_price, color='green', linestyle='--', linewidth=2, label=f'Reference ({reference_price:.2f})')
        
        plt.title(f'ALE Adaptation: American Option Pricing Distribution\n(Paths: {NUM_PATHS}, Steps: {TIME_STEPS})')
        plt.xlabel('Cash Flow Value')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(figures_dir / "pricing_distribution.png", dpi=150)
        print(f"Plot saved to {figures_dir / 'pricing_distribution.png'}")
        
    except ImportError:
        print("Warning: Matplotlib not found. Skipping plot generation.")

    print("\nAdaptation complete. Real artifacts written to data/ and figures/.")
