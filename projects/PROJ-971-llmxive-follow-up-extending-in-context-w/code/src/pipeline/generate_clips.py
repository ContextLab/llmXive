"""
generate_clips.py

Generate a reproducible set of interaction clips for the minimal pipeline.

Each clip is stored as a ``.npz`` file containing three arrays:
  - ``states``: the raw environment observations (numpy array of shape (T, obs_dim))
  - ``actions``: the actions taken by the agent (numpy array of shape (T, action_dim))
  - ``observations``: a duplicate of ``states`` for compatibility with downstream code.

The script uses the classic control environment ``CartPole-v1`` from ``gymnasium``.
This provides real, physics‑based data without requiring heavyweight simulation
dependencies (e.g., MuJoCo). The generation is deterministic via fixed random
seeds, ensuring reproducibility across CI runs.
"""

import argparse
import numpy as np
import gymnasium as gym
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def generate_one_clip(clip_id: int, out_dir: Path, seed: int = 42) -> None:
    """
    Generate a single interaction clip using the CartPole environment.

    Parameters
    ----------
    clip_id : int
        Identifier for the clip; used to name the output file.
    out_dir : Path
        Directory where the ``clip_{clip_id}.npz`` file will be written.
    seed : int, optional
        Random seed for reproducibility (default: 42).

    The function runs the environment for a fixed number of steps
    (or until termination) and records observations and actions.
    """
    env = gym.make("CartPole-v1")
    # ``reset`` returns (observation, info) in gymnasium ≥0.26
    obs, _ = env.reset(seed=seed + clip_id)

    states = []
    actions = []
    observations = []

    max_steps = 200  # CartPole episodes terminate before this on average
    for step in range(max_steps):
        # Sample a random action; this yields a realistic trajectory.
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)

        states.append(obs)
        actions.append(action)
        observations.append(obs)  # duplicate for downstream compatibility

        # Prepare for next iteration
        obs = next_obs

        if terminated or truncated:
            # Episode finished; stop early.
            break

    # Convert lists to numpy arrays
    states_arr = np.stack(states, axis=0)          # shape (T, obs_dim)
    actions_arr = np.stack(actions, axis=0)        # shape (T, action_dim)
    observations_arr = np.stack(observations, axis=0)

    clip_path = out_dir / f"clip_{clip_id:03d}.npz"
    np.savez(
        clip_path,
        states=states_arr,
        actions=actions_arr,
        observations=observations_arr,
    )
    log.info(f"Generated clip {clip_id:03d} with {states_arr.shape[0]} steps → {clip_path}")

def generate_clips(num_clips: int = 50, out_dir: Path = None) -> None:
    """
    Generate ``num_clips`` reproducible interaction clips.

    Parameters
    ----------
    num_clips : int
        Number of clips to create (default: 50).
    out_dir : Path, optional
        Destination directory. If ``None``, uses ``paths.data('raw')``.
    """
    if out_dir is None:
        out_dir = paths.data("raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Generating {num_clips} clips in {out_dir}")

    for i in range(num_clips):
        generate_one_clip(i, out_dir)

    log.info(f"Finished generating {num_clips} clips.")

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a small dataset of interaction clips for the minimal pipeline."
    )
    parser.add_argument(
        "--num-clips",
        type=int,
        default=50,
        help="Number of clips to generate (default: 50).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to store the generated .npz files. Defaults to data/raw.",
    )
    return parser.parse_args()

def main():
    args = _parse_args()
    out_dir = Path(args.output_dir) if args.output_dir else None
    generate_clips(num_clips=args.num_clips, out_dir=out_dir)

if __name__ == "__main__":
    main()
