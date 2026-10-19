"""Command‑line orchestrator for the brain‑network dynamics pipeline.

The orchestrator parses global arguments (seed, window, step,
permutations, etc.) and then runs the requested stages in order.
Each stage is implemented as a module with a ``main()`` function that
takes **no positional arguments**. The orchestrator therefore imports
the module and calls ``module.main()`` without forwarding the parsed
``argparse.Namespace``. This fixes the earlier ``TypeError`` where
``run_stage`` attempted to call ``main(args)``.
"""
import argparse
import importlib
import sys
from pathlib import Path

import config
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Mapping from stage name (as used on the CLI) to the module that
# implements it. All modules expose a ``main()`` entry point that
# takes no arguments.
STAGE_MODULES = {
    "download": "download_openneuro",
    "extract": "extract_rois",
    "metrics": "connectivity",
    "pca": "dimensionality",
    "analysis": "analysis",
    "sensitivity": "sensitivity",
    "visualization": "visualization",
    "manifest": "manifest",  # placeholder – may be added later
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full brain‑network dynamics pipeline."
    )
    parser.add_argument("--seed", type=int, default=config.DEFAULT_SEED,
                        help="Global random seed")
    parser.add_argument("--window", type=float, default=config.DEFAULT_WINDOW_SECONDS,
                        help="Sliding‑window length in seconds")
    parser.add_argument("--step", type=float, default=config.DEFAULT_STEP_SECONDS,
                        help="Sliding‑window step in seconds")
    parser.add_argument("--permutations", type=int, default=config.N_PERMUTATIONS,
                        help="Number of Freedman–Lane permutations")
    parser.add_argument("--output_dir", type=Path, default=None,
                        help="Override the default results directory")
    parser.add_argument("--stage", action="append", dest="stages",
                        choices=config.STAGE_ORDER,
                        help="Run only the specified stage(s) in order")
    return parser


def run_stage(stage: str, args: argparse.Namespace) -> None:
    """Import the module for *stage* and execute its ``main()``."""
    if stage not in STAGE_MODULES:
        raise ValueError(f"unknown stage: {stage}")
    module_name = STAGE_MODULES[stage]
    try:
        module = importlib.import_module(f"code.{module_name}")
    except ImportError as exc:
        log.error("failed to import module for stage %s: %s", stage, exc)
        raise
    # All stage modules define ``main()`` that takes no arguments.
    if not hasattr(module, "main"):
        raise AttributeError(f"module {module_name} has no main()")
    log.info("=== stage: %s (%s) ===", stage, module_name)
    exit_code = module.main()
    if exit_code not in (0, None):
        raise SystemExit(exit_code)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Determine which stages to run.
    if args.stages:
        stages_to_run = [s for s in config.STAGE_ORDER if s in args.stages]
    else:
        stages_to_run = config.STAGE_ORDER

    # Override results directory if requested.
    if args.output_dir:
        # The ``paths`` helper creates the directory hierarchy.
        paths.results = lambda *parts: Path(args.output_dir, *parts)
        log.info("Output directory overridden: %s", args.output_dir)

    log.info(
        "Pipeline run: seed=%s window=%s step=%s permutations=%s stages=%s",
        args.seed, args.window, args.step, args.permutations, stages_to_run,
    )

    for stage in stages_to_run:
        run_stage(stage, args)

    log.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())