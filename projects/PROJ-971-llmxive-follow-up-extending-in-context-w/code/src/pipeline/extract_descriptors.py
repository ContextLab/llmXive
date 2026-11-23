import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import welch
from jsonschema import Draft7Validator
import yaml

from llmxive_toolkit import paths, get_logger
from src.utils.icwm_encoder import encode

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for descriptor computation
# ----------------------------------------------------------------------
def _load_schema() -> dict:
    """
    Load the JSON‑Schema for a descriptor record.
    """
    # The schema lives under the spec directory for this feature branch.
    schema_path = (
        paths.root / "specs" / "001-llmxive-follow-up-extending-in-context-w" / "contracts" / "descriptor.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _variance(tokens: np.ndarray) -> float:
    """Return the sample variance of the token matrix."""
    return float(np.var(tokens, ddof=0))

def _lag1_autocorrelation(tokens: np.ndarray) -> float:
    """
    Compute the average lag‑1 autocorrelation across token dimensions.
    If a dimension has length < 2 or zero variance, its contribution is 0.
    """
    if tokens.shape[0] < 2:
        return 0.0
    corrs = []
    for dim in range(tokens.shape[1]):
        x = tokens[:-1, dim]
        y = tokens[1:, dim]
        if np.std(x) == 0 or np.std(y) == 0:
            corrs.append(0.0)
        else:
            # np.corrcoef returns a 2x2 matrix [[1, r], [r, 1]]
            corr = np.corrcoef(x, y)[0, 1]
            corrs.append(corr)
    return float(np.mean(corrs))

def _mean_spectral_density(tokens: np.ndarray) -> float:
    """
    Compute the mean power spectral density using Welch's method.
    The PSD is computed per dimension and then averaged over frequencies
    and dimensions.
    """
    psd_means = []
    # nperseg must be <= length of signal
    nperseg = min(256, tokens.shape[0])
    for dim in range(tokens.shape[1]):
        freqs, psd = welch(tokens[:, dim], nperseg=nperseg)
        psd_means.append(np.mean(psd))
    return float(np.mean(psd_means))

# ----------------------------------------------------------------------
# Core processing of a single clip
# ----------------------------------------------------------------------
def process_clip(clip_path: Path) -> dict:
    """
    Load a ``.npz`` interaction clip, encode it with the ICWM encoder,
    and compute the three statistical descriptors.

    Parameters
    ----------
    clip_path: Path
        Path to the ``clip_*.npz`` file.

    Returns
    -------
    dict
        Mapping with keys ``clip_id``, ``variance``, ``autocorr_lag1``,
        ``spectral_density``.
    """
    data = np.load(clip_path)
    states = data["states"]
    actions = data["actions"]
    observations = data["observations"]

    # Encode the raw trajectory into a latent token sequence.
    # Ensure tokens is a numpy array for subsequent computations.
    tokens = np.asarray(encode(states, actions, observations))

    var = _variance(tokens)
    if var < 1e-12:  # near‑zero variance edge case
        autocorr = 0.0
        spectral = 0.0
    else:
        autocorr = _lag1_autocorrelation(tokens)
        spectral = _mean_spectral_density(tokens)

    clip_id = clip_path.stem  # e.g. "clip_000"
    return {
        "clip_id": clip_id,
        "variance": var,
        "autocorr_lag1": autocorr,
        "spectral_density": spectral,
    }

# ----------------------------------------------------------------------
# Batch extraction and validation
# ----------------------------------------------------------------------
def extract_all_descriptors(input_dir: Path, output_path: Path) -> None:
    """
    Iterate over all ``clip_*.npz`` files in ``input_dir``,
    compute descriptors, validate against the JSON schema,
    enforce the variance‑ratio acceptance scenario, and write a CSV.

    Parameters
    ----------
    input_dir: Path
        Directory containing raw ``.npz`` clips.
    output_path: Path
        Destination CSV file (will be created, parent dirs are made
        automatically).
    """
    input_dir = Path(input_dir)
    records = []
    clip_files = sorted(input_dir.glob("clip_*.npz"))
    
    if not clip_files:
        raise FileNotFoundError(f"No clip_*.npz files found in {input_dir}")

    for clip_file in clip_files:
        records.append(process_clip(clip_file))

    df = pd.DataFrame.from_records(records)

    # ------------------------------------------------------------------
    # Schema validation (no nulls, correct types)
    # ------------------------------------------------------------------
    schema = _load_schema()
    validator = Draft7Validator(schema)

    for _, row in df.iterrows():
        # Convert numpy scalar types to native Python types for jsonschema
        record = {
            k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
            for k, v in row.to_dict().items()
        }
        validator.validate(record)

    if df.isnull().any().any():
        raise AssertionError("Null values detected in descriptor CSV")

    # ------------------------------------------------------------------
    # Acceptance scenario: high‑variance vs low‑variance clip
    # ------------------------------------------------------------------
    var_max = df["variance"].max()
    var_min = df["variance"].min()
    if var_min == 0:
        # If min is exactly 0, we check if max is > 0 to avoid trivial failure
        if var_max == 0:
            raise AssertionError("All clips have zero variance")
        # Mathematically, any var_max > 0 is > 2 * 0, but let's be explicit
    
    if not (var_max > 2 * var_min):
        raise AssertionError(
            f"Variance ratio check failed: max={var_max:.6f} not > 2*min={var_min:.6f}"
        )

    # Write CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(f"Descriptor CSV written to %s", output_path)

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract latent statistical descriptors from ICWM clips"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory containing *.npz interaction clips (default: data/raw)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=str(paths.data("processed", "descriptors.csv")),
        help="Path to write the descriptor CSV (default: data/processed/descriptors.csv)",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_args()
    extract_all_descriptors(Path(args.input_dir), Path(args.output_csv))

if __name__ == "__main__":
    main()