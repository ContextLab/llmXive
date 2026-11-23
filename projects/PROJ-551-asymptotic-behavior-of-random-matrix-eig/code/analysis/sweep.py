"""
Sweep engine for random matrix eigenvalue experiments.

This script generates a set of simulation runs over a grid of parameters
(matrix size ``N``, perturbation norm ``theta``, rank ``k`` and sparsity
pattern). For each run it records a ``SimulationRun`` entry and the
associated top-10 eigenvalues (``EigenvalueResult``). The combined data is
written to ``data/processed/sweep_runs.parquet``.

Validation is performed both per-record (via JSON-Schema) and column-wise
on the final DataFrame before writing to ensure structural fidelity.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.sparse.linalg import eigsh
import jsonschema
import yaml

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------
def _load_schema(schema_name: str) -> dict:
    """Load a JSON-Schema from ``contracts/<schema_name>.schema.yaml``."""
    schema_path = paths.root / "contracts" / f"{schema_name}.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_record(record: dict, schema_name: str) -> None:
    """Validate ``record`` against the named contract."""
    schema = _load_schema(schema_name)
    jsonschema.validate(instance=record, schema=schema)

def _wigner_matrix(N: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a symmetric Wigner matrix with scaling 1/sqrt(N)."""
    A = rng.normal(loc=0.0, scale=1.0, size=(N, N))
    A = (A + A.T) / 2.0
    return A / np.sqrt(N)

def _perturbation_matrix(N: int, theta: float, k: int, pattern: str,
                         rng: np.random.Generator) -> np.ndarray:
    """
    Construct a deterministic sparse perturbation of rank ``k``.
    """
    P = np.zeros((N, N))
    if pattern == "diagonal":
        np.fill_diagonal(P[:k, :k], theta)
    elif pattern == "block-sparse":
        # Rank k perturbation: theta * I_k block
        P[:k, :k] = theta * np.eye(k)
    elif pattern == "random-sparse":
        indices = rng.choice(N, size=k, replace=False)
        for i in indices:
            P[i, i] = theta
    else:
        raise ValueError(f"Unsupported pattern: {pattern}")
    return P

def _outlier_rule(eigenvalue: float, N: int) -> bool:
    """
    Apply the outlier detection rule: λ > 2 + τ(N)
    where τ(N) = max(0.05, 2·N^{-2/3}).
    """
    tau = max(0.05, 2 * N ** (-2.0 / 3.0))
    return eigenvalue > 2.0 + tau

# -----------------------------------------------------------------
# Main sweep logic
# -----------------------------------------------------------------
def run_sweep(args: argparse.Namespace) -> None:
    """
    Execute the parameter sweep and write the resulting Parquet file.
    """
    output_path = paths.data("processed", "sweep_runs.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sim_rows = []
    eig_rows = []

    thetas = np.arange(args.theta_min, args.theta_max + args.theta_step / 2,
                       args.theta_step)
    
    # We respect the user iterations, but keep a reasonable limit for CI
    # The task asks for 1,152 records, which is approx 26 thetas * 3 k * 3 patterns * 5 iters
    iters = args.iterations

    run_counter = 0
    for theta in thetas:
        for k in args.k:
            for pattern in args.patterns:
                for i in range(iters):
                    seed = args.seed_start + i
                    rng = np.random.default_rng(seed)

                    # 1. Generate matrices
                    W = _wigner_matrix(args.N, rng)
                    P = _perturbation_matrix(args.N, theta, k, pattern, rng)
                    M = W + P

                    # 2. Compute top 10 eigenvalues
                    try:
                        eigenvalues = eigsh(M, k=10, which='LA', tol=1e-10, maxiter=1000,
                                           return_eigenvectors=False)
                        eigenvalues = np.sort(eigenvalues)[::-1]
                    except Exception as e:
                        logger.error(f"ARPACK failed for run {run_counter} (theta={theta}): {e}")
                        continue

                    # 3. Record SimulationRun
                    run_id = run_counter
                    timestamp = datetime.now(timezone.utc).isoformat()
                    sim_record = {
                        "run_id": int(run_id),
                        "N": int(args.N),
                        "seed": int(seed),
                        "theta": float(theta),
                        "k": int(k),
                        "pattern_type": str(pattern),
                        "timestamp": str(timestamp)
                    }
                    _validate_record(sim_record, "simulation_run")
                    sim_rows.append(sim_record)

                    # 4. Record EigenvalueResult rows
                    for idx, val in enumerate(eigenvalues):
                        eig_record = {
                            "run_id": int(run_id),
                            "index": int(idx),
                            "value": float(val),
                            "outlier": bool(_outlier_rule(val, args.N))
                        }
                        _validate_record(eig_record, "eigenvalue_result")
                        eig_rows.append(eig_record)

                    run_counter += 1

    if not sim_rows:
        raise RuntimeError("Sweep produced no results. Check input parameters or solver stability.")

    # -----------------------------------------------------------------
    # Assemble and Column-wise Validation
    # -----------------------------------------------------------------
    sim_df = pd.DataFrame(sim_rows)
    eig_df = pd.DataFrame(eig_rows)

    # Merge all SimulationRun fields into the EigenvalueResult records
    # This ensures the Parquet contains both entities' data per eigenvalue
    merged_df = eig_df.merge(sim_df, on="run_id")
    merged_df = merged_df.rename(columns={"outlier": "outlier_flag"})

    # Column-wise validation against entity field definitions
    # SimulationRun required fields
    sim_fields = {"run_id", "N", "seed", "theta", "k", "pattern_type", "timestamp"}
    # EigenvalueResult required fields
    eig_fields = {"run_id", "index", "value", "outlier_flag"}
    
    all_required = sim_fields.union(eig_fields)
    missing_cols = all_required - set(merged_df.columns)
    if missing_cols:
        raise ValueError(f"Final DataFrame missing required columns: {missing_cols}")

    # Write Parquet
    merged_df.to_parquet(output_path, engine="pyarrow", index=False)

    logger.info(f"Sweep completed: {len(sim_rows)} runs, {len(eig_rows)} eigenvalue records")
    logger.info(f"Parquet written to: {output_path}")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a sweep of random-matrix simulations and write results to Parquet."
    )
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--theta-min", type=float, required=True)
    parser.add_argument("--theta-max", type=float, required=True)
    parser.add_argument("--theta-step", type=float, required=True)
    parser.add_argument("--k", type=int, nargs="+", required=True)
    parser.add_argument("--patterns", type=str, nargs="+", required=True)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=0)
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        run_sweep(args)
        return 0
    except Exception as exc:
        logger.exception(f"Sweep failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())