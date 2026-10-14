"""Grid-search optimal ICWM inference hyper-parameters (tau, k) per training clip.

For every training clip in ``data/raw`` the discrete grid
``tau in {0.5, 1.0, 1.5, 2.0}`` x ``k in {16, 32, 64}`` is evaluated on
the CPU-only ICWM policy.  The pair with the highest success rate is
selected; ties are broken deterministically with ``np.random.seed(123)``.
The result is written to ``data/labels.csv``.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

from src.utils.icwm_encoder import encode

log = get_logger(__name__)

# Discrete hyper-parameter grid (FR-002).
TAUS = [0.5, 1.0, 1.5, 2.0]
KS = [16, 32, 64]

# Policy-evaluation protocol constants.
N_EPISODES = 10          # stochastic rollouts per grid point
NOISE_SCALE = 0.05       # exploration noise scale (relative to tau)
TOLERANCE = 1.0          # mean‑squared error below which a timestep counts as a success
MASTER_SEED = 123        # deterministic tie‑breaking seed

CLIP_PATTERN = re.compile(r"^clip_(\d{3})\.npz$")


def _normalize_actions(actions: np.ndarray) -> np.ndarray:
    """Map discrete 0/1 actions to the {-1, +1} range used by the policy."""
    a = np.asarray(actions, dtype=float)
    if a.ndim == 1:
        a = a[:, None]
    uniq = set(np.unique(a).tolist())
    if uniq <= {0.0, 1.0}:
        return 2.0 * a - 1.0
    return a


def evaluate_policy(
    latents: np.ndarray,
    actions: np.ndarray,
    tau: float,
    k: int,
    rng: np.random.Generator,
) -> float:
    """Run the ICWM policy for ``N_EPISODES`` episodes and return a *fractional* success rate.

    The policy predicts the next action from the mean of the last ``k``
    latent tokens, scaled by the sampling temperature ``tau``.  For each
    timestep we compute the mean‑squared error against the recorded (normalized)
    actions; a timestep is a success when that error is below ``TOLERANCE``.
    The episode success rate is the fraction of successful timesteps, and the
    final return value is the average over ``N_EPISODES`` episodes.
    """
    target = _normalize_actions(actions)
    T, L = latents.shape
    A = target.shape[1]
    k_eff = min(k, T)

    # Static projection from latent space to the action space.
    if L >= A:
        proj = latents[:, :A]
    else:
        proj = np.tile(latents, (1, int(np.ceil(A / L))))[:, :A]

    episode_rates = []
    for _ in range(N_EPISODES):
        successes = 0
        for t in range(T):
            context = proj[max(0, t - k_eff + 1) : t + 1].mean(axis=0)
            pred = tau * np.tanh(context)
            noise = rng.normal(0.0, NOISE_SCALE * tau, size=A)
            sq_err = np.mean((pred + noise - target[t]) ** 2)
            if sq_err < TOLERANCE:
                successes += 1
        episode_rates.append(successes / T)  # fraction of successful timesteps
    return float(np.mean(episode_rates))


def grid_search_clip(
    latents: np.ndarray,
    actions: np.ndarray,
    clip_index: int,
) -> dict:
    """Evaluate the full (tau, k) grid for one clip and pick the best pair."""
    rates = np.zeros((len(TAUS), len(KS)))
    for i, tau in enumerate(TAUS):
        for j, k in enumerate(KS):
            rng = np.random.default_rng(
                MASTER_SEED + clip_index * 10000 + i * 100 + j
            )
            rates[i, j] = evaluate_policy(latents, actions, tau, k, rng)

    best = rates.max()
    tied = np.argwhere(rates == best)  # array of (i, j) pairs
    # Deterministic tie‑breaking (spec edge case / plan note).
    np.random.seed(123)
    choice = tied[np.random.choice(len(tied))]
    i, j = int(choice[0]), int(choice[1])
    return {
        "tau": TAUS[i],
        "k": KS[j],
        "success_rate": float(rates[i, j]),
    }


def list_clip_files(input_dir: Path) -> list:
    """Return the canonical 3‑digit clip files, sorted by clip id."""
    files = []
    for p in input_dir.glob("clip_*.npz"):
        m = CLIP_PATTERN.match(p.name)
        if m:
            files.append((int(m.group(1)), p))
    files.sort(key=lambda x: x[0])
    if not files:
        raise FileNotFoundError(
            f"No clip_*.npz files matching {CLIP_PATTERN.pattern} found in {input_dir}. "
            "Run `python -m src.pipeline.generate_clips` first."
        )
    return [p for _, p in files]


def run_grid_search(input_dir: Path = None, output_path: Path = None) -> Path:
    """Grid‑search every training clip and write ``data/labels.csv``."""
    if input_dir is None:
        input_dir = paths.data("raw")
    if output_path is None:
        output_path = paths.data("labels.csv")

    clip_files = list_clip_files(Path(input_dir))
    log.info(
        "Grid‑searching %d clips over %d hyper‑parameter combinations",
        len(clip_files),
        len(TAUS) * len(KS),
    )

    rows = []
    for idx, clip_path in enumerate(clip_files):
        data = np.load(clip_path)
        latents = encode(
            data["states"], data["actions"], data["observations"]
        )
        result = grid_search_clip(latents, data["actions"], idx)
        rows.append(
            {
                "clip_id": clip_path.stem,
                "tau": result["tau"],
                "k": result["k"],
                "success_rate": result["success_rate"],
            }
        )
        log.info(
            "%s -> tau=%.1f k=%d success_rate=%.3f",
            clip_path.stem,
            result["tau"],
            result["k"],
            result["success_rate"],
        )

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log.info("Wrote %d labels to %s", len(df), output_path)
    return output_path


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing clip_*.npz files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: data/labels.csv)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)
    run_grid_search(args.input_dir, args.output)


if __name__ == "__main__":
    main()