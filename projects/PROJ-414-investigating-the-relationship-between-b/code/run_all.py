"""CLI orchestrator for the brain-network-dynamics / improvisation pipeline.

Usage (documented in specs/001-investigating-the-relationship-between-b/quickstart.md):

    python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000

Stages are executed in the pinned order from config.STAGE_ORDER. Run a
subset with repeated ``--stage`` flags, e.g.:

    python code/run_all.py --stage download --stage extract --stage metrics

Each stage maps to a sibling module; modules for later tasks
(extract_rois, connectivity, graph_metrics, dimensionality, analysis,
sensitivity, visualization) are introduced by their own tasks. If a
stage's module is not yet present, the orchestrator fails loudly with a
clear message naming the missing module — it never silently skips or
fabricates output.
"""
import argparse
import importlib
import sys
from pathlib import Path

# Allow running both as `python code/run_all.py` and as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402  (pinned parameters; sibling module)
from llmxive_toolkit import get_logger, paths  # noqa: E402

log = get_logger(__name__)

# stage name -> (module name, entry function)
STAGE_MODULES = {
    "download": ("download_openneuro", "main"),
    "extract": ("extract_rois", "main"),
    "metrics": ("connectivity", "main"),
    "pca": ("dimensionality", "main"),
    "analysis": ("analysis", "main"),
    "sensitivity": ("sensitivity", "main"),
    "visualization": ("visualization", "main"),
    "manifest": ("manifest", "main"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_all.py",
        description=(
            "Orchestrate the vertex-block connectivity-descriptor pipeline "
            "on the verified clane9/openneuro-fslr64k parquet shard. "
            "Descriptors are vertex-block connectivity descriptors, not "
            "brain-network properties."
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=config.DEFAULT_SEED,
        help=f"Global random seed (default {config.DEFAULT_SEED}).",
    )
    parser.add_argument(
        "--window", type=float, default=config.DEFAULT_WINDOW_SECONDS,
        help=f"Sliding-window length in seconds (default {config.DEFAULT_WINDOW_SECONDS}).",
    )
    parser.add_argument(
        "--step", type=float, default=config.DEFAULT_STEP_SECONDS,
        help=f"Sliding-window step in seconds (default {config.DEFAULT_STEP_SECONDS}).",
    )
    parser.add_argument(
        "--permutations", type=int, default=config.N_PERMUTATIONS,
        help=f"Freedman-Lane permutation count (default {config.N_PERMUTATIONS}).",
    )
    parser.add_argument(
        "--tr", type=float, default=config.TR_SECONDS,
        help=f"Repetition time in seconds (default {config.TR_SECONDS}).",
    )
    parser.add_argument(
        "--output_dir", type=str, default=None,
        help=(
            "Optional output directory for results (default: the project's "
            "results/ folder)."
        ),
    )
    parser.add_argument(
        "--stage", action="append", choices=config.STAGE_ORDER, default=None,
        help=(
            "Run only the named stage (repeatable). Default: all stages in "
            f"order {config.STAGE_ORDER}."
        ),
    )
    return parser


def run_stage(stage: str, args: argparse.Namespace) -> None:
    """Execute one stage, failing loudly if its module is missing."""
    module_name, entry_name = STAGE_MODULES[stage]
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"[run_all] Stage '{stage}' requires module "
            f"'{module_name}.py', which is not present in code/. "
            f"This stage is implemented by a later task; the orchestrator "
            f"refuses to run it silently. (missing: {e})"
        )
    entry = getattr(module, entry_name, None)
    if entry is None:
        raise SystemExit(
            f"[run_all] Module '{module_name}' has no entry point "
            f"'{entry_name}()' for stage '{stage}'."
        )
    log.info(f"=== stage: {stage} ({module_name}.{entry_name}) ===")
    entry(args)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output_dir is not None:
        log.info(f"Output directory override: {args.output_dir}")

    stages = args.stage if args.stage else config.STAGE_ORDER
    # Preserve pinned order regardless of --stage flag order.
    stages = [s for s in config.STAGE_ORDER if s in stages]

    log.info(
        f"Pipeline run: seed={args.seed} window={args.window}s "
        f"step={args.step}s permutations={args.permutations} "
        f"tr={args.tr}s stages={stages}"
    )
    for stage in stages:
        run_stage(stage, args)
    log.info("Pipeline run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
