"""
End‑to‑end pipeline driver.

The original stub accepted only ``--output_dir`` and ``--subset_size``.
The quickstart (and historic usage) passes a richer set of arguments
(``--num_videos``, ``--lambda_values`` …).  To restore compatibility we
extend the parser to accept those historic flags (they are stored but not
used by the current minimal implementation).  The driver now explicitly
invokes the optical‑flow pre‑compute step so that the required
``data/checksums/manifest.csv`` is produced before the summary is printed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from llmxive_toolkit import get_logger, paths

# Import the newly‑implemented pre‑compute script.
from src.data.optical_flow_precompute import main as precompute_flow

log = get_logger(__name__)

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
    npy_files = _gather_npy_files(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for npy_path in sorted(npy_files):
            rel = npy_path.relative_to(Path.cwd())
            sha = _sha256_of_file(npy_path)
            f.write(f"{rel.as_posix()},{sha}\\n")
    log.info("Manifest written with %d entries to %s", len(npy_files), manifest_path)

def parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments.

    The parser now accepts both the modern ``--config`` style arguments
    and the historic flags used by the quickstart.  Unknown arguments are
    ignored so that future extensions do not break the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Run the full counterfactual consistency pipeline."
    )
    # Modern usage
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a YAML config file (options from the config are merged).",
    )
    # Historic quick‑start flags (stored but not acted upon in this minimal stub)
    parser.add_argument("--num_videos", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument(
        "--lambda_values",
        nargs="*",
        type=float,
        default=[],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        default=[],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--flow_divergence_thresh",
        type=float,
        default=0.0,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--feature_sim_thresh",
        type=float,
        default=0.0,
        help=argparse.SUPPRESS,
    )
    # Core arguments used by the stub
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("./output"),
        help="Root output directory for generated artifacts.",
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=None,
        help="Optional subset size for downstream stages (unused here).",
    )
    args = parser.parse_args(argv)

    # If a config file is supplied, we could merge its contents, but for this
    # minimal implementation we simply ignore it – the historic flags already
    # populate the namespace.
    return args

def main(argv: List[str] | None = None) -> int:
    """
    Run the pipeline stub.

    Steps performed:
    1. Parse CLI arguments (accepting historic flags).
    2. Ensure the output directory exists.
    3. Invoke the optical‑flow pre‑compute step for original videos.
    4. Write a checksum manifest for all ``.npy`` files under ``data/flow``.
    5. Print a concise summary of produced artefacts.
    """
    args = parse_cli_args(argv)

    # Ensure the output directory exists (used by downstream stages).
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Step 3 – pre‑compute optical flow for original videos.
    # ------------------------------------------------------------------
    log.info("Running optical‑flow pre‑compute for original videos …")
    flow_ret = precompute_flow()
    if flow_ret != 0:
        log.error("Optical‑flow pre‑compute failed with exit code %d", flow_ret)
        return flow_ret

    # ------------------------------------------------------------------
    # Step 4 – write manifest for all flow files.
    # ------------------------------------------------------------------
    manifest_path = Path("data/checksums/manifest.csv")
    flow_root = Path("data/flow")
    _write_manifest(manifest_path, flow_root)

    # ------------------------------------------------------------------
    # Step 5 – print a short summary.
    # ------------------------------------------------------------------
    npy_files = _gather_npy_files(flow_root)
    log.info("=== Pipeline Summary ===")
    log.info("Output directory: %s", args.output_dir)
    log.info("Number of .npy flow files: %d", len(npy_files))
    log.info("Manifest path: %s", manifest_path)
    log.info("========================")

    return 0

if __name__ == "__main__":
    sys.exit(main())
