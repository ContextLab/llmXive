"""
CLI Entry Point for Entanglement Entropy Pipeline.

Orchestrates the workflow, handles delta_grid.csv input, and manages
output artifacts including metadata logging for unresolved realizations.
"""
import argparse
import csv
import os
import sys
import time
import json
from pathlib import Path

from config import validate_config, get_default_config, ConfigError
from hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats
from ground_state import compute_ground_state, is_numerically_unresolved, get_ground_state_statistics
from entropy import compute_entanglement_entropy_batch, get_entropy_statistics
from analysis import select_model_aic, bootstrap_resample, compute_bootstrap_statistics
from state_manager import log_unresolved_realization

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantify entanglement entropy in randomly perturbed quantum spin chains."
    )
    parser.add_argument(
        "--delta-grid",
        type=str,
        default="data/raw/delta_grid.csv",
        help="Path to CSV file containing disorder strengths (default: data/raw/delta_grid.csv)"
    )
    parser.add_argument(
        "--L",
        type=int,
        default=30,
        help="System size (default: 30)"
    )
    parser.add_argument(
        "--N-real",
        type=int,
        default=100,
        help="Number of realizations (default: 100)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Enable development mode (bypasses some validation checks)"
    )
    return parser.parse_args()

def load_delta_grid(filepath: str) -> list:
    """
    Load disorder strengths from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        List of float values for delta.
    """
    deltas = []
    if not os.path.exists(filepath):
        # Create a default grid if file doesn't exist for demonstration
        print(f"Warning: {filepath} not found. Using default grid [0.0, 0.1, 0.2].")
        return [0.0, 0.1, 0.2]

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume column name is 'delta'
            if 'delta' in row:
                deltas.append(float(row['delta']))
            elif len(row) > 0:
                # Fallback: first column
                deltas.append(float(list(row.values())[0]))

    if not deltas:
        raise ValueError("No delta values found in grid file.")

    return deltas

def run_single_delta(
    delta: float,
    L: int,
    N_real: int,
    seed: int,
    dev_mode: bool = False
) -> dict:
    """
    Run the workflow for a single disorder strength.

    Args:
        delta: Disorder strength.
        L: System size.
        N_real: Number of realizations.
        seed: Random seed.
        dev_mode: If True, bypass certain validation checks.

    Returns:
        Dictionary containing results and metadata.
    """
    np = __import__('numpy')
    np.random.seed(seed)

    results = {
        "delta": delta,
        "L": L,
        "N_real": N_real,
        "entropy_data": [],
        "unresolved_count": 0,
        "unresolved_reasons": [],
        "scaling_result": None
    }

    # Generate couplings for each realization
    for i in range(N_real):
        # Generate random couplings J_i ~ U[-delta, 1+delta]
        couplings = np.random.uniform(-delta, 1 + delta, size=L - 1)

        # Compute ground state
        try:
            mps, gs_metadata = compute_ground_state(L, couplings)

            if is_numerically_unresolved(gs_metadata):
                results["unresolved_count"] += 1
                reason = gs_metadata.get("reason", "Convergence failure")
                results["unresolved_reasons"].append(reason)

                # Log to metadata
                log_unresolved_realization(
                    realization_id=i,
                    delta=delta,
                    L=L,
                    reason=reason
                )
                continue

            # Compute entanglement entropy for all bipartitions
            entropies = compute_entanglement_entropy_batch(mps, L)
            results["entropy_data"].append({
                "realization_id": i,
                "entropies": entropies.tolist()
            })

        except Exception as e:
            # Log unresolved realization
            reason = str(e)
            results["unresolved_count"] += 1
            results["unresolved_reasons"].append(reason)
            log_unresolved_realization(
                realization_id=i,
                delta=delta,
                L=L,
                reason=reason
            )
            continue

    # Perform model selection and bootstrap if we have enough data
    if len(results["entropy_data"]) > 0:
        # Aggregate entropies
        all_entropies = np.array([d["entropies"] for d in results["entropy_data"]])
        mean_entropies = np.mean(all_entropies, axis=0)
        positions = np.arange(1, L)

        # Model selection
        try:
            model_result = select_model_aic(positions, mean_entropies)
            results["scaling_result"] = {
                "model": model_result.model,
                "alpha": model_result.alpha,
                "aic": model_result.aic,
                "r_squared": model_result.r_squared
            }

            # Bootstrap
            bootstrap_data = bootstrap_resample(all_entropies, n_resamples=100)
            bootstrap_stats = compute_bootstrap_statistics(bootstrap_data)
            results["bootstrap_stats"] = bootstrap_stats

        except Exception as e:
            results["model_selection_error"] = str(e)

    return results

def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Validate configuration
    try:
        config = get_default_config()
        config["L"] = args.L
        config["N_real"] = args.N_real
        config["dev_mode"] = args.dev_mode
        validate_config(config)
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Load delta grid
    try:
        deltas = load_delta_grid(args.delta_grid)
    except Exception as e:
        print(f"Error loading delta grid: {e}")
        sys.exit(1)

    print(f"Starting workflow for {len(deltas)} disorder strengths...")
    print(f"System size L={args.L}, Realizations N={args.N_real}")

    start_time = time.time()

    all_results = []
    for delta in deltas:
        print(f"Processing delta={delta}...")
        result = run_single_delta(
            delta=delta,
            L=args.L,
            N_real=args.N_real,
            seed=args.seed + int(delta * 1000),
            dev_mode=args.dev_mode
        )
        all_results.append(result)

        # Check timeout (6 hours = 21600 seconds)
        elapsed = time.time() - start_time
        if elapsed > 21600:
            print("WARNING: Wall-clock timeout (6h) approaching. Stopping run.")
            break

    # Save outputs
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save entropy data
    entropy_file = output_dir / "entropy_data.csv"
    with open(entropy_file, 'w') as f:
        # Simplified CSV output
        f.write("delta,realization_id,position,entropy\n")
        for res in all_results:
            for entry in res.get("entropy_data", []):
                for pos, ent in enumerate(entry["entropies"]):
                    f.write(f"{res['delta']},{entry['realization_id']},{pos+1},{ent}\n")

    # Save scaling fit results
    fit_file = output_dir / "scaling_fit.txt"
    with open(fit_file, 'w') as f:
        f.write("Scaling Fit Results\n")
        f.write("=" * 40 + "\n")
        for res in all_results:
            f.write(f"Delta: {res['delta']}\n")
            if res.get("scaling_result"):
                sr = res["scaling_result"]
                f.write(f"  Model: {sr['model']}\n")
                f.write(f"  Alpha: {sr['alpha']:.4f}\n")
                f.write(f"  AIC: {sr['aic']:.4f}\n")
                f.write(f"  R^2: {sr['r_squared']:.4f}\n")
            else:
                f.write("  No scaling result (insufficient data or error)\n")
            f.write(f"  Unresolved: {res['unresolved_count']}/{res['N_real']}\n")
            f.write("-" * 40 + "\n")

    # Save bootstrap summary
    boot_file = output_dir / "bootstrap_summary.txt"
    with open(boot_file, 'w') as f:
        f.write("Bootstrap Summary\n")
        f.write("=" * 40 + "\n")
        for res in all_results:
            f.write(f"Delta: {res['delta']}\n")
            if res.get("bootstrap_stats"):
                bs = res["bootstrap_stats"]
                f.write(f"  Resamples: {bs.get('n_resamples', 0)}\n")
                f.write(f"  SE: {bs.get('se', 0.0):.4f}\n")
                f.write(f"  P-value: {bs.get('p_value', 0.0):.4f}\n")
            else:
                f.write("  No bootstrap stats available\n")
            f.write("-" * 40 + "\n")

    print(f"Workflow completed in {time.time() - start_time:.2f} seconds.")
    print(f"Outputs saved to {output_dir}")

if __name__ == "__main__":
    main()