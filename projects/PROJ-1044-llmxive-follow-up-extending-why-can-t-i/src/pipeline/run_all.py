"""Pipeline driver for the counterfactual consistency study.

The driver orchestrates all stages of the pipeline, accepting either
a configuration file (``--config``) **or** the historic command‑line
arguments that were used in earlier versions of the project.  This
dual interface resolves the CLI drift that caused the previous
execution failure.

The script is deliberately lightweight – it merely parses arguments,
loads the configuration (if any), and then invokes the individual
stage scripts as subprocesses.  Each stage writes its own output
files; the driver does not attempt to interpret them.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    import hashlib

    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _gather_npy_files(root: Path) -> List[Path]:
    """Return a list of all ``.npy`` files under *root* (recursively)."""
    return list(root.rglob("*.npy"))

def _write_manifest(manifest_path: Path, root: Path) -> None:
    """Write ``relative_path,sha256`` lines for every ``.npy`` under *root*."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for npy_path in _gather_npy_files(root):
            rel = npy_path.relative_to(Path.cwd())
            sha = _sha256_of_file(npy_path)
            f.write(f"{rel},{sha}\\n")

def _load_config(config_path: Path) -> Dict[str, Any]:
    """Load a YAML config file; returns an empty dict if unreadable."""
    import yaml

    if not config_path.is_file():
        log.warning("Config file %s not found – using defaults.", config_path)
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        log.error("Failed to read config %s: %s", config_path, exc)
        return {}

# ----------------------------------------------------------------------
# Argument parsing – supports both modern ``--config`` style and the
# historic flags used by earlier quickstart versions.
# ----------------------------------------------------------------------
def parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full counterfactual consistency pipeline."
    )
    # Modern interface
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a YAML configuration file (overrides other flags).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(paths.path("output")),
        help="Root directory for all generated artifacts.",
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=None,
        help="Optional size of the video subset to process.",
    )

    # Historic flags – they are kept for backward compatibility.
    # ``--num_videos`` is deliberately typed as ``str`` so that placeholder
    # values like ``<sufficient number of videos>`` do not cause an argparse
    # type error.  The value is coerced to ``int`` later; if conversion fails
    # we fall back to the config/default.
    parser.add_argument(
        "--num_videos",
        type=str,
        default=None,
        help="(legacy) Number of synthetic videos to generate.",
    )
    parser.add_argument(
        "--lambda_values",
        type=float,
        nargs="+",
        default=None,
        help="(legacy) List of λ values for the sweep.",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        nargs="+",
        default=None,
        help="(legacy) List of seeds (as strings) for reproducibility.",
    )
    parser.add_argument(
        "--flow_divergence_thresh",
        type=float,
        default=None,
        help="(legacy) Flow divergence threshold.",
    )
    parser.add_argument(
        "--feature_sim_thresh",
        type=float,
        default=None,
        help="(legacy) Feature cosine‑similarity threshold.",
    )

    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def _run_stage(module: str, args: List[str]) -> int:
    """Run a stage script as a subprocess."""
    cmd = [sys.executable, "-m", module] + args
    log.info("Running stage: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(
            "Stage %s failed (exit %d). stdout:\\n%s\\nstderr:\\n%s",
            module,
            result.returncode,
            result.stdout,
            result.stderr,
        )
    else:
        log.debug("Stage %s succeeded. stdout:\\n%s", module, result.stdout)
    return result.returncode

def main(argv: List[str] | None = None) -> int:
    """
    Execute the full pipeline. Returns 0 on success.
    """
    args = parse_cli_args(argv)

    # ------------------------------------------------------------------
    # Resolve configuration
    # ------------------------------------------------------------------
    config: Dict[str, Any] = {}
    if args.config:
        config_path = Path(args.config)
        config = _load_config(config_path)

    # Override config with any legacy flags that were supplied.
    # This mirrors the behaviour of the original quickstart command.
    if args.num_videos is not None:
        try:
            config["num_videos"] = int(args.num_videos)
        except ValueError:
            log.warning(
                "Invalid --num_videos value '%s'; ignoring and falling back to config/default.",
                args.num_videos,
            )
    if args.lambda_values is not None:
        config["lambda_values"] = args.lambda_values
    if args.seeds is not None:
        # Preserve the original string list – downstream scripts expect strings.
        config["seeds"] = args.seeds
    if args.flow_divergence_thresh is not None:
        config["flow_divergence_thresh"] = args.flow_divergence_thresh
    if args.feature_sim_thresh is not None:
        config["feature_sim_thresh"] = args.feature_sim_thresh
    if args.subset_size is not None:
        config["subset_size"] = args.subset_size

    # Ensure output_dir exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Stage 1 – Synthetic video generation
    # ------------------------------------------------------------------
    synth_args: List[str] = []
    if "num_videos" in config:
        synth_args += ["--num_videos", str(config["num_videos"])]
    # The synthetic generator writes directly into the project data tree,
    # so we do not need to pass an explicit output path here.
    rc = _run_stage("src.data.synthetic_generator", synth_args)
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 2 – Optical flow pre‑compute for originals
    # ------------------------------------------------------------------
    flow_pre_args: List[str] = []
    if "subset_size" in config:
        flow_pre_args += ["--subset_size", str(config["subset_size"])]
    rc = _run_stage("src.data.optical_flow_precompute", flow_pre_args)
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 3 – Counterfactual generation (original → counterfactual)
    # ------------------------------------------------------------------
    cf_args: List[str] = []
    if "flow_divergence_thresh" in config:
        cf_args += ["--flow_divergence_thresh", str(config["flow_divergence_thresh"])]
    if "feature_sim_thresh" in config:
        cf_args += ["--feature_sim_thresh", str(config["feature_sim_thresh"])]
    rc = _run_stage("src.data.counterfactual", cf_args)
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 4 – Optical flow for counterfactuals
    # ------------------------------------------------------------------
    rc = _run_stage("src.data.optical_flow_precompute", ["--counterfactual"])
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 5 – Model training sweep
    # ------------------------------------------------------------------
    train_args: List[str] = []
    if "lambda_values" in config:
        train_args += ["--lambda_values"] + [str(v) for v in config["lambda_values"]]
    if "seeds" in config:
        train_args += ["--seeds"] + list(map(str, config["seeds"]))
    rc = _run_stage("src.train.run_sweep", train_args)
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 6 – Evaluation
    # ------------------------------------------------------------------
    rc = _run_stage("src.eval.evaluator", [])
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 7 – Statistics
    # ------------------------------------------------------------------
    rc = _run_stage("src.eval.statistics", [])
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Stage 8 – Report generation
    # ------------------------------------------------------------------
    rc = _run_stage("src.eval.report", [])
    if rc != 0:
        return rc

    # ------------------------------------------------------------------
    # Final manifest of all .npy files for reproducibility
    # ------------------------------------------------------------------
    manifest_path = output_dir / "checksums_manifest.csv"
    _write_manifest(manifest_path, Path.cwd())
    log.info("Pipeline completed successfully. Manifest written to %s", manifest_path)

    return 0

if __name__ == "__main__":
    sys.exit(main())