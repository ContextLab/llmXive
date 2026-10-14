"""
generate_clips.py
-----------------

Generates a reproducible set of interaction clips using the CartPole
environment. Each clip is saved as a ``.npz`` file containing three arrays:
``states``, ``actions`` and ``observations``.

The script is deterministic (fixed random seeds) and always produces
exactly ``num_clips`` files named ``clip_000.npz`` … ``clip_{num_clips‑1}.npz``.
"""

import argparse
import sys
import numpy as np
import gymnasium as gym
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _clean_output_dir(out_dir: Path) -> None:
    """
    Remove any existing ``clip_*.npz`` files in ``out_dir``.
    Guarantees that after a run exactly ``num_clips`` files exist.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("clip_*.npz"):
        f.unlink()
    log.debug(f"Cleaned output directory {out_dir}")


def generate_one_clip(clip_id: int, out_dir: Path, seed: int = 42) -> None:
    """
    Generate a single interaction clip using CartPole.

    Parameters
    ----------
    clip_id : int
        Identifier for the clip; used to name the output file.
    out_dir : Path
        Directory where the ``clip_{clip_id}.npz`` file will be written.
    seed : int, optional
        Random seed for reproducibility (default: 42).
    """
    np.random.seed(seed + clip_id)  # deterministic per clip
    env = gym.make("CartPole-v1", render_mode=None)
    env.action_space.seed(seed + clip_id)
    obs, _ = env.reset(seed=seed + clip_id)

    states = []
    actions = []
    observations = []

    max_steps = 200  # fixed horizon
    for _ in range(max_steps):
        state = np.array(obs, dtype=np.float32)
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)

        states.append(state)
        actions.append(np.array([action], dtype=np.float32))
        observations.append(np.array(next_obs, dtype=np.float32))

        if terminated or truncated:
            break
        obs = next_obs

    # Convert lists to arrays.
    states_arr = np.stack(states)          # shape (T, state_dim)
    actions_arr = np.stack(actions)        # shape (T, 1)
    observations_arr = np.stack(observations)  # shape (T, obs_dim)

    clip_path = out_dir / f"clip_{clip_id:03d}.npz"
    np.savez_compressed(
        clip_path,
        states=states_arr,
        actions=actions_arr,
        observations=observations_arr,
    )
    log.debug(f"Saved clip {clip_path}")


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
    _clean_output_dir(out_dir)

    log.info(f"Generating {num_clips} clips in {out_dir}")
    for clip_id in range(num_clips):
        generate_one_clip(clip_id, out_dir)
    log.info(f"Finished generating {num_clips} clips.")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate CartPole interaction clips.")
    parser.add_argument(
        "--num-clips",
        type=int,
        default=50,
        help="Number of clips to generate (default: 50).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for clips (default: data/raw).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    generate_clips(num_clips=args.num_clips, out_dir=args.out_dir)


if __name__ == "__main__":
    main()