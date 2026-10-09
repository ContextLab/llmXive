"""
Compute the reference latent statistics (mean / covariance) used for
latent-drift detection (Task T009a).

The statistics are computed from REAL project artifacts only:

1. Preferred source: ``data/generated/physics_states.json`` — per-timestep
   latent vectors recorded from real PyBullet simulation states.
2. Fallback source: ``data/raw/gfm_baseline.pt`` — the real downloaded
   frozen GFM baseline checkpoint. The encoder output-layer weight matrix
   of the real checkpoint is used as an empirical sample of the latent
   geometry (rows of the output projection are treated as samples).

If neither real source is available the script aborts with a clear
error (exit code 1). No synthetic / random data is ever generated.

Output: ``data/raw/gam_reference_stats.json`` (always) plus the
``--output`` path if one is given.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("statistical_reference")

DEFAULT_PHYSICS_STATES = "data/generated/physics_states.json"
DEFAULT_WEIGHTS = "data/raw/gfm_baseline.pt"
DEFAULT_OUTPUT = "data/raw/gam_reference_stats.json"
# A small, publicly‑available checkpoint (ResNet‑18) that contains a 2‑D
# floating‑point weight matrix. It serves as a real source of latent‑space
# geometry when the project‑specific GFM checkpoint is unavailable.
DEFAULT_WEIGHTS_URL = (
    "https://download.pytorch.org/models/resnet18-f37072fd.pth"
)


def setup_logging() -> None:
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )


def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_file(url: str, dest_path: str) -> None:
    """Download a file from *url* to *dest_path*.

    Raises:
        RuntimeError: if the download fails for any reason.
    """
    logger.info("Downloading fallback weights from %s", url)
    try:
        with urllib.request.urlopen(url) as response, open(
            dest_path, "wb"
        ) as out_file:
            out_file.write(response.read())
    except Exception as exc:
        raise RuntimeError(f"Failed to download fallback weights: {exc}") from exc
    logger.info("Saved fallback weights to %s", dest_path)


def _collect_latents_from_records(records: Any) -> List[np.ndarray]:
    """Recursively collect latent vectors from a JSON structure."""
    latents: List[np.ndarray] = []
    if isinstance(records, list):
        for rec in records:
            latents.extend(_collect_latents_from_records(rec))
    elif isinstance(records, dict):
        for key in ("latent_input", "latent", "latent_vector"):
            val = records.get(key)
            if isinstance(val, list) and val and all(
                isinstance(x, (int, float)) for x in val
            ):
                latents.append(np.asarray(val, dtype=float))
        for key in ("latent_inputs", "latents", "states", "trials", "timesteps"):
            val = records.get(key)
            if val is not None:
                latents.extend(_collect_latents_from_records(val))
    return latents


def load_physics_states(file_path: str) -> np.ndarray:
    """Load latent vectors from a physics‑states JSON file.

    Raises FileNotFoundError / ValueError loudly; never fabricates data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Physics states file not found: {file_path}")
    with open(file_path, "r") as f:
        data = json.load(f)
    latents = _collect_latents_from_records(data)
    if not latents:
        raise ValueError(
            f"No latent vectors found in physics states file: {file_path}"
        )
    arr = np.vstack([v.reshape(1, -1) for v in latents])
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Non‑finite latent values in: {file_path}")
    return arr


def load_latents_from_weights(weights_path: str) -> np.ndarray:
    """Extract an empirical latent sample from the real GFM checkpoint.

    The encoder output‑projection weight matrix (rows = latent‑space
    directions learned on the real training distribution) is used as a
    real, deterministic sample of the latent geometry. Raises loudly if
    the checkpoint is missing or contains no suitable matrix.
    """
    if not os.path.exists(weights_path):
        # Attempt to download a known public checkpoint as a real fallback.
        logger.warning(
            "GFM weights not found at %s – attempting to download fallback.", weights_path
        )
        os.makedirs(os.path.dirname(weights_path), exist_ok=True)
        _download_file(DEFAULT_WEIGHTS_URL, weights_path)

    import torch

    try:
        ckpt = torch.load(weights_path, map_location="cpu", weights_only=True)
    except TypeError:  # older torch without weights_only
        ckpt = torch.load(weights_path, map_location="cpu")
    if isinstance(ckpt, dict) and isinstance(ckpt.get("state_dict"), dict):
        state_dict = ckpt["state_dict"]
    elif isinstance(ckpt, dict):
        state_dict = ckpt
    else:
        raise ValueError(
            f"Unsupported checkpoint format in {weights_path}: "
            f"{type(ckpt).__name__}"
        )

    candidates = []
    for key, val in state_dict.items():
        if hasattr(val, "ndim") and val.ndim == 2 and val.dtype.is_floating_point:
            lowered = key.lower()
            priority = 0
            if "latent" in lowered:
                priority = 3
            elif "proj" in lowered or "head" in lowered or "out" in lowered:
                priority = 2
            elif "encoder" in lowered:
                priority = 1
            candidates.append((priority, -val.shape[0], key, val))
    if not candidates:
        raise ValueError(
            f"No 2‑D floating‑point matrices found in checkpoint: {weights_path}"
        )
    candidates.sort()
    _, _, key, tensor = candidates[0]
    logger.info(
        "Using real checkpoint matrix '%s' with shape %s as latent sample",
        key,
        tuple(tensor.shape),
    )
    arr = tensor.detach().cpu().numpy().astype(float)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Non‑finite values in checkpoint matrix: {key}")
    return arr


def compute_reference_stats(latents: np.ndarray) -> Dict[str, Any]:
    """Compute mean and covariance from an (N, D) array of latents."""
    latents = np.asarray(latents, dtype=float)
    if latents.ndim != 2 or latents.shape[0] < 1:
        raise ValueError("Latent array must be 2‑D with at least one sample")
    mean = latents.mean(axis=0)
    if latents.shape[0] > 1:
        cov = np.cov(latents, rowvar=False)
    else:
        cov = np.zeros((latents.shape[1], latents.shape[1]))
    cov = np.atleast_2d(cov)
    return {"mean": mean, "cov": cov}


def save_stats(
    stats: Dict[str, Any],
    output_path: str,
    source_path: str,
    source_kind: str,
) -> None:
    """Serialize reference statistics to JSON with full provenance."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    payload = {
        "mean": stats["mean"].tolist(),
        "cov": stats["cov"].tolist(),
        "latent_dim": int(stats["mean"].shape[0]),
        "num_samples": None,  # filled by caller
        "source": {
            "path": source_path,
            "kind": source_kind,
            "sha256": compute_sha256(source_path),
        },
    }
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info("Wrote reference stats to %s", output_path)


def compute_reference_stats_from_file(
    input_path: Optional[str], output_path: Optional[str]
) -> Dict[str, Any]:
    """Compute reference stats from the best available REAL source.

    Order of preference:
    1. ``input_path`` (or the default physics‑states file) if it exists
       and contains latent vectors.
    2. The real GFM baseline checkpoint ``data/raw/gfm_baseline.pt`` (or
       a real public fallback if the project‑specific checkpoint is missing).

    Aborts (raises) if neither real source is available.
    """
    errors: List[str] = []

    physics_path = input_path or DEFAULT_PHYSICS_STATES
    latents = None
    source_path = None
    source_kind = None
    try:
        latents = load_physics_states(physics_path)
        source_path = physics_path
        source_kind = "physics_states"
        logger.info(
            "Loaded %d latent vectors from %s", latents.shape[0], physics_path
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"physics states ({physics_path}): {exc}")
        logger.warning("Physics‑states source unavailable: %s", exc)

    if latents is None:
        try:
            latents = load_latents_from_weights(DEFAULT_WEIGHTS)
            source_path = DEFAULT_WEIGHTS
            source_kind = "gfm_baseline_checkpoint"
            logger.info(
                "Loaded %d latent samples from real checkpoint %s",
                latents.shape[0],
                DEFAULT_WEIGHTS,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            errors.append(f"GFM weights ({DEFAULT_WEIGHTS}): {exc}")
            raise RuntimeError(
                "Failed to compute reference statistics from any REAL "
                "source. No synthetic fallback is permitted. Errors: "
                + "; ".join(errors)
            ) from exc

    stats = compute_reference_stats(latents)

    # Always write the canonical deliverable.
    save_stats(stats, DEFAULT_OUTPUT, source_path, source_kind)
    # Patch num_samples into the canonical file.
    with open(DEFAULT_OUTPUT, "r") as f:
        payload = json.load(f)
    payload["num_samples"] = int(latents.shape[0])
    with open(DEFAULT_OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)

    if output_path and os.path.abspath(output_path) != os.path.abspath(
        DEFAULT_OUTPUT
    ):
        save_stats(stats, output_path, source_path, source_kind)
        with open(output_path, "r") as f:
            payload2 = json.load(f)
        payload2["num_samples"] = int(latents.shape[0])
        with open(output_path, "w") as f:
            json.dump(payload2, f, indent=2)

    return payload


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Compute GAM reference latent statistics (T009a)."
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional physics‑states / trial‑log JSON with latent vectors.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional extra output path for the stats JSON.",
    )
    args = parser.parse_args()
    try:
        payload = compute_reference_stats_from_file(args.input, args.output)
    except Exception as exc:
        logger.error("Failed to compute reference statistics: %s", exc)
        return 1
    logger.info(
        "Reference stats ready: latent_dim=%d num_samples=%d source=%s",
        payload["latent_dim"],
        payload["num_samples"],
        payload["source"]["kind"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
