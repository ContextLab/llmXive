"""
CLI orchestrator for the LLM impact evaluation pipeline.

This script wires together the pipeline phases (extraction, detection,
inference, analysis, reporting). For the purpose of the smoke test it
executes a minimal end‑to‑end run that writes a valid metrics JSON file
(`data/results/smoke_report.json`) conforming to
`contracts/analysis_metrics_schema.schema.yaml` and logs a `"cli_start"`
event to `logs/pipeline.jsonl`.

The implementation is deliberately lightweight: real heavy‑weight steps
(GitHub fetching, model inference, alignment, statistical testing) are
delegated to their respective modules when the `--run all` mode is used.
The smoke mode skips those steps and produces a deterministic placeholder
report that satisfies the schema validation requirements.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Project utilities
from code.src.config.settings import get_paths, ensure_directories, get_seed
from llmxive_toolkit import paths

# Logging utilities
try:
    from code.src.pipeline.logging_utils import log_event
except ImportError:
    def log_event(event: Dict[str, Any]) -> None:
        """Fallback logger that writes a JSON line to logs/pipeline.jsonl."""
        log_path = Path("logs/pipeline.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

# Phase runners – import the real implementations if they exist.
def _run_phase(module_path: str, func_name: str, config: Dict[str, Any]) -> bool:
    """Dynamically import and execute a phase function."""
    try:
        module = __import__(module_path, fromlist=[func_name])
        phase_func = getattr(module, func_name)
        return bool(phase_func(config))
    except Exception as exc:
        logging.error(f"Failed to run phase {module_path}.{func_name}: {exc}")
        return False

def run_extraction_phase(config: Dict[str, Any]) -> bool:
    return _run_phase("code.src.extraction.fetch_prs", "main", config)

def run_detection_phase(config: Dict[str, Any]) -> bool:
    return _run_phase("code.src.detection.detect_llm_code", "main", config)

def run_inference_phase(config: Dict[str, Any]) -> bool:
    return _run_phase("code.src.inference.run_inference", "main", config)

def run_analysis_phase(config: Dict[str, Any]) -> bool:
    return _run_phase("code.src.analysis.align", "main", config)

def run_reporting_phase(config: Dict[str, Any]) -> bool:
    return _run_phase("code.src.reporting.generate_report", "main", config)

def parse_args():
    parser = argparse.ArgumentParser(
        description="LLM Code Impact Analysis Pipeline"
    )
    parser.add_argument(
        "--run",
        choices=["smoke", "all"],
        default="smoke",
        help="Execution mode: 'smoke' runs a minimal end‑to‑end pipeline "
             "producing a placeholder report; 'all' runs the full pipeline.",
    )
    parser.add_argument(
        "--timeout-hours",
        type=float,
        default=6.0,
        help="Global timeout limit in hours (default: 6.0)",
    )
    parser.add_argument(
        "--phases",
        type=str,
        nargs="+",
        default=["all"],
        choices=["extraction", "detection", "inference", "analysis", "reporting", "all"],
        help="Specific phases to execute (default: all).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()

def _write_smoke_report(output_path: Path, runtime_seconds: int) -> None:
    """Write a minimal but schema‑valid metrics JSON for the smoke test."""
    smoke_metrics = {
        "threshold": 0.85,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "llm_only_recall": 0.0,
        "mcnemar_p_value": 1.0,
        "chi_square_p_value": 1.0,
        "chi_square_statistic": 0.0,
        "effect_size": 0.0,
        "total_runtime_seconds": runtime_seconds,
        "sensitivity_to_noise": {
            "high_confidence_p_value": 1.0,
            "full_set_p_value": 1.0,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(smoke_metrics, f, indent=2, ensure_ascii=False)

def main():
    args = parse_args()

    # Initialise logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Log CLI start event (Requirement for T005)
    log_event({"event": "cli_start", "timestamp": time.time()})

    # Resolve project paths and ensure directories exist
    paths_map = get_paths()
    ensure_directories()

    # Record the effective random seed (FR‑019)
    seed = get_seed()
    log_event({"event": "seed_used", "seed": seed, "timestamp": time.time()})

    # Build a simple config dictionary passed to phase runners
    config = {
        "paths": paths_map,
        "timeout_hours": args.timeout_hours,
        "seed": seed,
        "verbose": args.verbose,
    }

    start_time = time.time()

    if args.run == "smoke":
        logger.info("Running smoke test – generating placeholder report.")
        # Write to data/results/smoke_report.json as required by T005
        # Use paths.data("results", ...) to ensure it lands in data/results/
        report_path = paths.data("results", "smoke_report.json")
        elapsed = int(time.time() - start_time)
        _write_smoke_report(report_path, elapsed)
        logger.info(f"Smoke report written to {report_path}")
        # Emit a final log entry and exit cleanly.
        log_event({"event": "cli_complete", "status": "success", "timestamp": time.time()})
        return 0

    # Full pipeline execution
    logger.info("Running full pipeline.")
    phases_to_run = (
        ["extraction", "detection", "inference", "analysis", "reporting"]
        if "all" in args.phases
        else args.phases
    )

    phase_functions = {
        "extraction": run_extraction_phase,
        "detection": run_detection_phase,
        "inference": run_inference_phase,
        "analysis": run_analysis_phase,
        "reporting": run_reporting_phase,
    }

    for phase in phases_to_run:
        logger.info(f"--- Starting phase: {phase} ---")
        success = phase_functions[phase](config)
        if not success:
            logger.error(f"Phase '{phase}' failed – aborting pipeline.")
            log_event(
                {
                    "event": "cli_complete",
                    "status": "failed",
                    "failed_phase": phase,
                    "timestamp": time.time(),
                }
            )
            sys.exit(1)

    total_runtime = int(time.time() - start_time)
    logger.info(f"Pipeline completed in {total_runtime} seconds.")
    log_event(
        {
            "event": "cli_complete",
            "status": "success",
            "total_runtime_seconds": total_runtime,
            "timestamp": time.time(),
        }
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())