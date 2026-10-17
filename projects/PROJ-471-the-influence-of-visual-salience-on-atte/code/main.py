"""
Main orchestrator for the Visual Salience pipeline.
Provides a unified entry point for running different stages of the research.
"""
import argparse
import sys
import logging
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def run_smoke_test():
    """
    Perform a basic smoke test to verify project layout and environment.
    """
    log.info("Running smoke test stage...")
    
    # Verify essential directories exist
    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.docs(),
    ]
    
    for d in required_dirs:
        if not d.is_dir():
            raise RuntimeError(f"Smoke test failed: Required directory {d} missing.")
    
    # Verify requirements.txt exists
    req_file = paths.root / "requirements.txt"
    if not req_file.is_file():
        raise RuntimeError("Smoke test failed: requirements.txt not found.")
    
    log.info("Smoke test passed: Project layout and basic environment verified.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Visual Salience Pipeline Orchestrator")
    parser.add_argument(
        "--stage", 
        type=str, 
        required=True, 
        choices=["smoke", "full"], 
        help="Stage of the pipeline to execute"
    )
    
    args = parser.parse_args()
    
    try:
        if args.stage == "smoke":
            run_smoke_test()
        elif args.stage == "full":
            # In a full run, this would call the sequence of scripts defined in plan.md
            # For T001, we only need to ensure the entry point is runnable.
            log.info("Full pipeline execution requested. (Implementation follows in subsequent tasks)")
            # For now, we just run the smoke test as a baseline
            run_smoke_test()
        
        log.info(f"Stage '{args.stage}' completed successfully.")
    except Exception as e:
        log.exception(f"Pipeline failed during stage '{args.stage}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()