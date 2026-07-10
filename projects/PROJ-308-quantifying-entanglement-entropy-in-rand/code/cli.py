"""
CLI Entry Point for Entanglement Entropy Research Pipeline

Orchestrates the workflow, handles delta_grid.csv input, and manages output artifacts.
Integrates metadata logging for unresolved realizations.
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from config import validate_config, get_default_config, ConfigError
from hamiltonian import generate_xxz_hamiltonian
from ground_state import compute_ground_state_batch, is_numerically_unresolved
from entropy import compute_entanglement_entropy_batch
from analysis import (
    select_model_aic, 
    filter_unresolved_realizations,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    generate_entropy_vs_l_plot
)
from state_manager import log_unresolved_batch, get_unresolved_summary

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantify entanglement entropy in randomly perturbed quantum spin chains"
    )
    parser.add_argument(
        "--delta-grid",
        type=str,
        default="data/raw/delta_grid.csv",
        help="Path to CSV file with disorder strengths to scan"
    )
    parser.add_argument(
        "--L",
        type=int,
        default=30,
        help="Chain length (default: 30)"
    )
    parser.add_argument(
        "--N-real",
        type=int,
        default=100,
        help="Number of realizations per delta (default: 100)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def load_delta_grid(filepath: str) -> List[float]:
    """Load delta values from CSV file."""
    deltas = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            deltas.append(float(row['delta']))
    return deltas

def run_single_delta(
    delta: float,
    L: int,
    N_real: int,
    seed: int
) -> Dict[str, Any]:
    """
    Run the full workflow for a single delta value.

    Returns:
        Dict with results including alpha, CI, p-value, and unresolved count
    """
    # Validate configuration
    config = get_default_config()
    config['L'] = L
    config['delta'] = delta
    config['N_real'] = N_real
    config['random_seed'] = seed

    try:
        validate_config(config)
    except ConfigError as e:
        print(f"Configuration error for delta={delta}: {e}")
        return {"error": str(e)}

    # Generate ground states for all realizations
    print(f"Computing ground states for delta={delta}, N={N_real}...")
    ground_states, coupling_matrices = compute_ground_state_batch(
        L=L,
        delta=delta,
        N_real=N_real,
        seed=seed
    )

    # Identify unresolved realizations
    unresolved_indices = []
    unresolved_details = []
    for i, gs in enumerate(ground_states):
        if is_numerically_unresolved(gs):
            unresolved_indices.append(i)
            unresolved_details.append({
                "realization_id": i,
                "reason": "Ground state not converged"
            })

    # Log unresolved realizations
    if unresolved_details:
        log_unresolved_batch(unresolved_details, delta=delta)
        print(f"Logged {len(unresolved_details)} unresolved realizations for delta={delta}")

    # Filter out unresolved realizations
    valid_ground_states = [gs for i, gs in enumerate(ground_states) if i not in unresolved_indices]
    valid_couplings = [c for i, c in enumerate(coupling_matrices) if i not in unresolved_indices]

    if not valid_ground_states:
        print(f"Warning: No valid realizations for delta={delta}")
        return {"delta": delta, "valid_count": 0}

    # Compute entanglement entropy for valid realizations
    print(f"Computing entanglement entropy for {len(valid_ground_states)} valid realizations...")
    entropy_data = compute_entanglement_entropy_batch(
        ground_states=valid_ground_states,
        L=L
    )

    # Aggregate entropy data across realizations
    avg_entropy = []
    l_values = list(range(1, L))
    
    for l in l_values:
        entropies_at_l = [edata[l-1] for edata in entropy_data if l-1 < len(edata)]
        if entropies_at_l:
            avg_entropy.append(sum(entropies_at_l) / len(entropies_at_l))
        else:
            avg_entropy.append(0.0)

    # Model selection using AIC
    model_result = select_model_aic(l_values, avg_entropy)
    
    # Compute scaling exponent
    alpha = model_result.slope
    ci_lower, ci_upper = model_result.ci_lower, model_result.ci_upper
    p_value = model_result.p_value

    # Bootstrap analysis
    bootstrap_samples = bootstrap_resample(l_values, avg_entropy, n_resamples=1000)
    bootstrap_stats = compute_bootstrap_statistics(bootstrap_samples)

    # Generate plot
    plot_path = generate_entropy_vs_l_plot(
        l_values, 
        avg_entropy, 
        model_result,
        output_path=f"data/processed/entropy_vs_l_delta_{delta:.2f}.png"
    )

    return {
        "delta": delta,
        "valid_count": len(valid_ground_states),
        "unresolved_count": len(unresolved_indices),
        "alpha": alpha,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_upper - ci_lower,
        "p_value": p_value,
        "model": model_result.model_type,
        "r_squared": model_result.r_squared,
        "plot_path": plot_path,
        "bootstrap_stats": bootstrap_stats
    }

def main():
    """Main entry point."""
    args = parse_args()
    
    print("Starting entanglement entropy analysis pipeline...")
    
    # Load delta grid
    if not os.path.exists(args.delta_grid):
        print(f"Error: Delta grid file not found: {args.delta_grid}")
        sys.exit(1)
    
    deltas = load_delta_grid(args.delta_grid)
    print(f"Loaded {len(deltas)} delta values: {deltas}")

    # Process each delta
    results = []
    for delta in deltas:
        print(f"\n--- Processing delta={delta} ---")
        result = run_single_delta(
            delta=delta,
            L=args.L,
            N_real=args.N_real,
            seed=args.seed
        )
        results.append(result)

    # Generate summary outputs
    print("\n--- Generating summary outputs ---")
    
    # Write delta_vs_exponent.csv
    output_csv = "data/processed/delta_vs_exponent.csv"
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['delta', 'alpha', 'ci_lower', 'ci_upper', 'ci_width', 'p_value'])
        
        for res in results:
            if "error" not in res and res.get("valid_count", 0) > 0:
                writer.writerow([
                    res["delta"],
                    res["alpha"],
                    res["ci_lower"],
                    res["ci_upper"],
                    res["ci_width"],
                    res["p_value"]
                ])

    # Write bootstrap_summary.txt
    summary_path = "data/processed/bootstrap_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("Bootstrap Analysis Summary\n")
        f.write("=" * 40 + "\n\n")
        for res in results:
            if "bootstrap_stats" in res:
                stats = res["bootstrap_stats"]
                f.write(f"Delta: {res['delta']}\n")
                f.write(f"  Resample count: {stats['n_resamples']}\n")
                f.write(f"  Standard error: {stats['std_error']:.6f}\n")
                f.write(f"  P-value: {stats['p_value']:.6f}\n")
                f.write(f"  95% CI: [{stats['ci_lower']:.6f}, {stats['ci_upper']:.6f}]\n\n")

    # Print unresolved summary
    unresolved_summary = get_unresolved_summary()
    print(f"\nTotal unresolved realizations logged: {unresolved_summary['unresolved_count']}")

    print("\nPipeline completed successfully!")
    print(f"Results saved to: {output_csv}")
    print(f"Bootstrap summary: {summary_path}")

if __name__ == "__main__":
    main()
