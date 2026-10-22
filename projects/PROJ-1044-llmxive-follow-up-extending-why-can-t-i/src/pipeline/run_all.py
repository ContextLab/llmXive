"""
End-to-end pipeline driver.

Usage (see quickstart.md):

    python -m src.pipeline.run_all --config configs/run.yaml

The driver accepts a YAML config file (``--config``) plus the historic
CLI flags (``--num_videos``, ``--lambda_values``, ``--seeds``,
``--flow_divergence_thresh``, ``--feature_sim_thresh``,
``--output_dir``, ``--subset_size``).  Config-file values are used as
defaults; explicit CLI flags override them.

Steps performed:
1. Parse CLI arguments and merge the YAML config.
2. Ensure the output directory and the source-video directory exist.
3. Invoke the optical-flow pre-compute step for original videos.
4. Write a checksum manifest for all ``.npy`` files under ``data/flow``.
5. Print a concise summary of produced artefacts and exit 0.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List

import yaml

from llmxive_toolkit import get_logger, paths

# Import the pre-compute script (T004).
from src.data.optical_flow_precompute import main as precompute_flow

log = get_logger(__name__)

PROJECT_ROOT = paths.root


def _sha256_of_file(file_path: Path) -> str:
    """Return the SHA-256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _gather_npy_files(root: Path) -> List[Path]:
    """Return a list of all ``.npy`` files under *root* (recursively)."""
    if not root.is_dir():
        return []
    return list(root.rglob("*.npy"))


def _write_manifest(manifest_path: Path, root: Path) -> None:
    """Write ``relative_path,sha256`` lines for every ``.npy`` under *root*."""
    npy_files = _gather_npy_files(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for npy_path in sorted(npy_files):
            rel = npy_path.relative_to(PROJECT_ROOT)
            sha = _sha256_of_file(npy_path)
            f.write(f"{rel.as_posix()},{sha}\n")
    log.info("Manifest written with %d entries to %s", len(npy_files), manifest_path)


def _load_config(config_path: Path) -> dict:
    """Load a YAML config file; returns an empty dict if unreadable."""
    if config_path is None or not Path(config_path).is_file():
        return {}
    with Path(config_path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Accepts both the modern ``--config`` style and the historic flags
    used by earlier quickstart versions.
    """
    parser = argparse.ArgumentParser(
        description="Run the full counterfactual consistency pipeline."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a YAML config file (options from the config are merged).",
    )
    parser.add_argument(
        "--num_videos", type=int, default=None, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--lambda_values", nargs="*", type=float, default=None, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--seeds", nargs="*", type=int, default=None, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--flow_divergence_thresh", type=float, default=None, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--feature_sim_thresh", type=float, default=None, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=None,
        help="Root output directory for generated artifacts.",
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=None,
        help="Optional subset size for downstream stages.",
    )
    args = parser.parse_args(argv)

    # Merge config-file values as defaults for anything not given on CLI.
    config = _load_config(args.config) if args.config else {}
    if args.subset_size is None and "subset_size" in config:
        args.subset_size = int(config["subset_size"])
    if args.num_videos is None:
        args.num_videos = args.subset_size
    if args.lambda_values is None:
        args.lambda_values = list(config.get("lambda_values", []))
    if args.seeds is None:
        args.seeds = list(config.get("seeds", []))
    if args.flow_divergence_thresh is None:
        args.flow_divergence_thresh = config.get(
            "optical_flow_divergence_threshold", 0.15
        )
    if args.feature_sim_thresh is None:
        args.feature_sim_thresh = config.get("feature_similarity_threshold", 0.9)
    if args.output_dir is None:
        args.output_dir = Path(config.get("output_dir", "./output"))
    return args


def main(argv: List[str] | None = None) -> int:
    """Run the pipeline driver; returns 0 on success."""
    args = parse_cli_args(argv)

    # Ensure the output directory exists (used by downstream stages).
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure the source-video directory exists so the pre-compute step
    # always finds a directory (it writes an empty manifest when no
    # MP4 files are present yet, e.g. on a fresh checkout).
    videos_dir = PROJECT_ROOT / "data" / "videos" / "orig"
    videos_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Step 3 – pre-compute optical flow for original videos.
    # ------------------------------------------------------------------
    log.info("Running optical-flow pre-compute for original videos …")
    flow_ret = precompute_flow(
        [
            "--input_dir", str(videos_dir),
            "--output_dir", str(PROJECT_ROOT / "data" / "flow" / "orig"),
            "--manifest_path", str(PROJECT_ROOT / "data" / "checksums" / "manifest.csv"),
        ]
    )
    if flow_ret != 0:
        log.error("Optical-flow pre-compute failed with exit code %d", flow_ret)
        return flow_ret

    # ------------------------------------------------------------------
    # Step 4 – write manifest for all flow files.
    # ------------------------------------------------------------------
    manifest_path = PROJECT_ROOT / "data" / "checksums" / "manifest.csv"
    flow_root = PROJECT_ROOT / "data" / "flow"
    _write_manifest(manifest_path, flow_root)

    # ------------------------------------------------------------------
    # Step 5 – print a short summary.
    # ------------------------------------------------------------------
    npy_files = _gather_npy_files(flow_root)
    summary_lines = [
        "=== Pipeline Summary ===",
        f"Config: {args.config}",
        f"Output directory: {output_dir}",
        f"Number of .npy flow files: {len(npy_files)}",
        f"Manifest path: {manifest_path}",
        "========================",
    ]
    for line in summary_lines:
        log.info("%s", line)
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())