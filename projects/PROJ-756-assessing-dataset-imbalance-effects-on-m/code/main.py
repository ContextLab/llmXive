"""
Entry-point CLI for the Assessing Dataset Imbalance Effects on Materials
Property Predictions project.

Supported flags:
  --full-pipeline   Run the complete end-to-end pipeline (ingestion -> SHAP).
  --include-mp      Attempt to download Materials Project data (requires MP_API_KEY).
  --fallback-mode   Force fallback mode (skip MP even if API key is present).
  --streaming       Use streaming mode for dataset downloads where supported.

The pipeline steps are delegated to the sibling modules, invoked as
subprocesses so each stage runs with its own CLI and isolated imports:
ingestion -> descriptors -> imbalance -> baseline training -> resampling ->
balanced training -> evaluation -> SHAP analysis.
"""
import argparse
import subprocess
import sys

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

PROJECT_ROOT = paths.root


def parse_args(argv=None):
    """Parse CLI arguments. Uses sys.argv when argv is None."""
    parser = argparse.ArgumentParser(
        prog="python -m code.main",
        description=(
            "Project CLI for assessing dataset imbalance effects on "
            "materials property predictions."
        ),
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Execute the full pipeline (ingestion, descriptors, training, "
             "evaluation, SHAP).",
    )
    parser.add_argument(
        "--include-mp",
        action="store_true",
        help="Attempt to download Materials Project data (requires MP_API_KEY).",
    )
    parser.add_argument(
        "--fallback-mode",
        action="store_true",
        help="Force fallback mode - skip Materials Project even if an API "
             "key is available. Overrides --include-mp.",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming mode for large dataset downloads.",
    )
    return parser.parse_args(argv)


def _pipeline_steps(args):
    """Build the ordered list of pipeline commands (module, argv) to run."""
    ingestion_flags = []
    if args.streaming:
        ingestion_flags.append("--streaming")

    steps = [
        ("code.ingestion",
         ingestion_flags + ["--output-dir", "data/raw"]),
        ("code.descriptors", []),
        ("code.imbalance", []),
        # training.py takes positional <data_path> <output_dir>
        ("code.training",
         ["data/processed/descriptors.parquet", "artifacts/models/baseline"]),
        ("code.resampling", []),
        ("code.training",
         ["data/processed/balanced_dataset.parquet", "artifacts/models/balanced"]),
        ("code.evaluation", []),
        ("code.shap_analysis", []),
    ]
    return steps


def run_pipeline(args):
    """
    Execute the pipeline stages described by the parsed arguments.

    Returns 0 on success. Raises RuntimeError (fail loudly) if any stage
    exits with a non-zero status code. When --full-pipeline is not set,
    no stages are executed.
    """
    if not args.full_pipeline:
        log.info(
            "No pipeline execution requested "
            "(use --full-pipeline to run all stages)."
        )
        return 0

    if args.fallback_mode:
        log.info(
            "Fallback mode active: Materials Project data will be skipped "
            "even if MP_API_KEY is set (FR-008)."
        )
    elif args.include_mp:
        log.info(
            "Materials Project inclusion requested; ingestion will probe "
            "availability via MP_API_KEY."
        )
    if args.streaming:
        log.info("Streaming mode enabled for dataset downloads.")

    for module, module_args in _pipeline_steps(args):
        cmd = [sys.executable, "-m", module] + list(module_args)
        log.info("Running stage: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            raise RuntimeError(
                f"Pipeline stage '{module}' failed with exit code "
                 f"{result.returncode}."
            )

    log.info("Full pipeline executed successfully.")
    return 0


def main(argv=None):
    """Parse arguments, validate flag combinations, and run the pipeline."""
    args = parse_args(argv)

    # --fallback-mode overrides --include-mp (FR-008 fallback semantics)
    if args.fallback_mode and args.include_mp:
        log.warning(
            "--fallback-mode overrides --include-mp; "
            "Materials Project will be skipped."
        )
        args.include_mp = False

    log.info("CLI arguments parsed:")
    log.info("  full_pipeline = %s", args.full_pipeline)
    log.info("  include_mp    = %s", args.include_mp)
    log.info("  fallback_mode = %s", args.fallback_mode)
    log.info("  streaming     = %s", args.streaming)

    return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
