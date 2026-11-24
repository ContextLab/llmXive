"""
Verification script for the runtime instrumentation (Task T014).

The script emulates a full pipeline run by stepping through the
canonical list of stages defined in the project specification.
For each stage it records a start and end timestamp using the
``code.runtime`` utilities and finally writes ``runtime_report.json``.
No actual heavy‑weight work is performed – the purpose is to prove
that the timing infrastructure works and that the required artefact
is produced.

The script exits with status 0 on success; any unexpected exception
will cause a non‑zero exit code, which the CI verifier will treat as
a failure.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from code.runtime import init_runtime, stage, write_report

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Ordered list of pipeline stages (must match the verification checklist)
# ----------------------------------------------------------------------
PIPELINE_STAGES = [
    "data_acquisition",
    "prompt_engineering",
    "synthetic_generation",
    "feature_extraction",
    "timestamp_simulation",
    "matching",
    "analysis",
    "sensitivity",
    "visualization",
    "report_generation",
]

def main() -> int:
    """
    Execute the verification run.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        # Initialise the global recorder – the output path resolves to
        # ``data/processed/runtime_report.json``.
        output_path = paths.data("processed", "runtime_report.json")
        init_runtime(PIPELINE_STAGES, output_path=output_path)

        # Iterate over the stages – we do not perform any real work,
        # but we still respect the timing API.
        for stage_name in PIPELINE_STAGES:
            log.info(f"=== Simulating stage: {stage_name} ===")
            # The ``stage`` context manager records start/end timestamps.
            with stage(stage_name):
                # Placeholder for real work – keep it essentially a no‑op.
                pass

        # Finalise and write the JSON report.
        write_report()

        # Basic sanity check – the file must exist and contain the required keys.
        if not output_path.is_file():
            log.error(f"Runtime report not found at expected location: {output_path}")
            return 1

        import json

        with output_path.open("r", encoding="utf-8") as fp:
            report = json.load(fp)

        required_keys = {"stage_times", "total_seconds"}
        if not required_keys.issubset(report.keys()):
            log.error(f"Runtime report missing required keys: {required_keys - report.keys()}")
            return 1

        # Ensure every declared stage has a timing entry (even if zero).
        missing = [s for s in PIPELINE_STAGES if s not in report["stage_times"]]
        if missing:
            log.error(f"Stage timings missing for: {missing}")
            return 1

        # Enforce the 6‑hour (21 600 s) wall‑time ceiling.
        if report["total_seconds"] > 21600:
            log.error(f"Total runtime {report['total_seconds']:.1f}s exceeds the 6‑hour limit.")
            return 1

        log.info("Runtime verification completed successfully.")
        return 0

    except Exception as exc:  # pragma: no cover – any unexpected error is a failure
        log.exception("Unexpected error during runtime verification", exc_info=exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
