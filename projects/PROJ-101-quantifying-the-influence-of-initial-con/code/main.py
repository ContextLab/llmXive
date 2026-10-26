"""
code/main.py
-------------
Minimal CLI entry point that drives the trajectory‑generation step required
for task T006/T007.  The full pipeline (baseline, FTLE, regression, etc.) is
implemented in other modules; this script focuses on the generation loop so
that the unit‑ and integration‑tests can succeed.

The CLI accepts the same flags described in ``quickstart.md`` but only
implements the ``generate`` mode needed for the current verification stage.
"""

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

from code.data.generator import generate_coupled_lorenz_trajectory, HighNoiseWarning, UnphysicalTrajectoryError

log = get_logger(__name__)


def parse_list(arg: str, cast_type):
    return [cast_type(item) for item in arg.split(",") if item]


def main(argv=None):
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

    args = parser.parse_args(argv)

    N_list = parse_list(args.N_values, int)
    sigma_list = parse_list(args.noise_levels, float)
    trials = args.trials
    global_seed = args.seed

    rng = np.random.default_rng(global_seed)

    for N in N_list:
        for sigma in sigma_list:
            for trial in range(trials):
                seed = int(rng.integers(0, 2**31 - 1))
                try:
                    traj = generate_coupled_lorenz_trajectory(
                        N=N,
                        sigma_noise=sigma,
                        seed=seed,
                    )
                except UnphysicalTrajectoryError as e:
                    log.warning(f"Trial {trial} for N={N}, sigma={sigma} aborted: {e}")
                    continue
                except Exception as exc:
                    log.error(f"Unexpected error: {exc}")
                    raise
                
                # Save trajectory as immutable .npz
                out_path = paths.data(
                    "raw",
                    f"trajectory_N{N}_sigma{sigma:.4f}_trial{trial}.npz",
                )
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
