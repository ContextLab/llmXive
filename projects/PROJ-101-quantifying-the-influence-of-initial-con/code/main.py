"""
code/main.py
-------------
CLI entry point for trajectory generation.

The original version expected the function
``code.data.generator.generate_coupled_lorenz_trajectory`` but the
module path and the accepted arguments were mismatched with the
quick‑start documentation.  This rewrite:

* Imports the correct wrapper from ``code.data.generator``.
* Adds the ``--window-sizes`` flag (optional) so that the quick‑start
  command ``python -m code.main … --window-sizes …`` is accepted.
* Persists each generated trajectory as an immutable ``.npz`` file
  under ``data/raw/`` using the ``llmxive_toolkit.paths`` helper.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from llmxive_toolkit import paths, get_logger

# The wrapper provides the public API expected by the tests and the CLI.
from code.data.generator import (
    generate_coupled_lorenz_trajectory,
    HighNoiseWarning,
    UnphysicalTrajectoryError,
)

log = get_logger(__name__)

def parse_list(arg: str, cast_type):
    """Parse a comma‑separated list into a list of ``cast_type`` values."""
    return [cast_type(item) for item in arg.split(",") if item]

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trajectory generation for coupled Lorenz system"
    )
    parser.add_argument(
        "--N-values",
        required=True,
        help="Comma‑separated list of system dimensions (e.g. 3,5,7)",
    )
    parser.add_argument(
        "--noise-levels",
        required=True,
        help="Comma‑separated list of sigma_noise values (e.g. 0.001,0.01)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=30,
        help="Number of independent trials per configuration",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global random seed for reproducibility",
    )
    parser.add_argument(
        "--mode",
        choices=["generate", "run-all"],
        default="generate",
        help="Pipeline mode (only 'generate' is implemented for now)",
    )
    # Accept the flag required by the quick‑start; it is ignored here
    # because the generation step does not need window sizes.
    parser.add_argument(
        "--window-sizes",
        default="",
        help="Sliding‑window lengths for FTLE (ignored in generate mode)",
    )

    args = parser.parse_args(argv)

    # Convert CLI strings to proper Python types.
    N_list = parse_list(args.N_values, int)
    sigma_list = parse_list(args.noise_levels, float)
    trials = args.trials
    global_seed = args.seed

    rng = np.random.default_rng(global_seed)

    for N in N_list:
        for sigma in sigma_list:
            for trial in range(trials):
                # Each trial gets its own deterministic seed.
                seed = int(rng.integers(0, 2**31 - 1))
                try:
                    traj = generate_coupled_lorenz_trajectory(
                        N=N,
                        sigma_noise=sigma,
                        seed=seed,
                    )
                except UnphysicalTrajectoryError as e:
                    log.warning(
                        f"Trial {trial} for N={N}, sigma={sigma} aborted: {e}"
                    )
                    continue
                except Exception as exc:
                    log.error(f"Unexpected error: {exc}")
                    raise

                out_path = paths.data(
                    "raw",
                    f"trajectory_N{N}_sigma{sigma:.4f}_trial{trial}.npz",
                )
                # ``np.savez_compressed`` creates the file; the folder is
                # created automatically by ``paths.data``.
                np.savez_compressed(
                    out_path,
                    time=traj.time,
                    state=traj.state,
                    noise_level=traj.noise_level,
                    N_oscillators=traj.N_oscillators,
                    coupling_strength=traj.coupling_strength,
                    seed=traj.seed,
                )
                log.info(f"Saved trajectory to {out_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
