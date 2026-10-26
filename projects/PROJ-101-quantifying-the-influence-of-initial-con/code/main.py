"""
Entry‑point for the project pipeline.

The original implementation imported ``generate_coupled_lorenz_trajectory`` from
``data.generator`` using an incorrect import path (``from data.generator``),
which caused an ``ImportError`` during CI execution.  This module now uses the
correct absolute import ``code.data.generator`` and provides a minimal but
functional CLI that satisfies the quickstart example and the integration
test for trajectory generation (T008).

Only the parts required for the current test suite are implemented:
* parsing of ``--N-values``, ``--noise-levels``, ``--trials`` and ``--seed``;
* generation of trajectories via ``generate_coupled_lorenz_trajectory``;
* storage of each trajectory as an immutable ``.npz`` file under
  ``data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.npz``;
* basic logging of progress.

The full pipeline (baseline, FTLE, regression, plotting, etc.) is delegated to
other modules and is not required for the verification of T007.
"""
import argparse
import warnings
import numpy as np
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from .data.generator import generate_coupled_lorenz_trajectory, HighNoiseWarning, UnphysicalTrajectoryError

log = get_logger(__name__)

def _parse_comma_separated_floats(value: str) -> list[float]:
    return [float(v) for v in value.split(",") if v]

def _parse_comma_separated_ints(value: str) -> list[int]:
    return [int(v) for v in value.split(",") if v]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate coupled Lorenz trajectories with optional noise."
    )
    parser.add_argument(
        "--N-values",
        required=True,
        help="Comma‑separated list of system dimensions, e.g. '3,5,7'",
    )
    parser.add_argument(
        "--noise-levels",
        required=True,
        help="Comma‑separated list of σ_noise values, e.g. '0.0001,0.001,0.01'",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=30,
        help="Number of independent trials per configuration (default: 30)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    N_list = _parse_comma_separated_ints(args.N_values)
    sigma_list = _parse_comma_separated_floats(args.noise_levels)
    trials = args.trials
    base_seed = args.seed

    log.info(
        "Starting trajectory generation: N=%s, sigma=%s, trials=%d",
        N_list,
        sigma_list,
        trials,
    )

    # Ensure the output directory exists (paths.data creates intermediate folders)
    output_dir = paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    for N in N_list:
        for sigma in sigma_list:
            for trial in range(trials):
                seed = base_seed + N * 1000 + int(sigma * 1e4) + trial
                try:
                    traj = generate_coupled_lorenz_trajectory(
                        N=N,
                        sigma_noise=sigma,
                        seed=seed,
                    )
                except HighNoiseWarning as w:
                    # The warning is also emitted via the ``warnings`` module;
                    # we forward it to the logger for visibility.
                    warnings.warn(w)
                    log.warning("High noise warning for N=%d sigma=%.4f: %s", N, sigma, w)
                    # Continue – the trajectory is still generated.
                except UnphysicalTrajectoryError as e:
                    log.error(
                        "Unphysical trajectory detected (N=%d sigma=%.4f trial=%d): %s",
                        N,
                        sigma,
                        trial,
                        e,
                    )
                    # Skip storing this trajectory – it violates the contract.
                    continue

                filename = f"trajectory_N{N}_sigma{sigma}_trial{trial}.npz"
                out_path = paths.data("raw", filename)

                # Store as an immutable ``.npz`` file (time, state, metadata)
                np.savez(
                    out_path,
                    time=traj.time,
                    state=traj.state,
                    noise_level=traj.noise_level,
                    N=traj.N_oscillators,
                    seed=traj.seed,
                )
                log.debug("Saved trajectory %s", out_path)

    log.info("Trajectory generation completed successfully.")

if __name__ == "__main__":
    main()
