"""
Main orchestrator for the DFT-D3 Transferability pipeline.
Coordinates data acquisition, calculations, analysis, and reporting.
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def run_stage(stage_name, func):
    """Helper to execute a pipeline stage with logging."""
    log.info(f"=== Starting stage: {stage_name} ===")
    try:
        func()
        log.info(f"=== Finished stage: {stage_name} ===")
    except Exception as e:
        log.error(f"Stage {stage_name} failed: {e}")
        # Critical stages that must succeed for the pipeline to continue
        if stage_name in ["download_il_benchmark", "load_data"]:
            raise e

def main():
    parser = argparse.ArgumentParser(description="DFT-D3 Transferability Pipeline Orchestrator")
    parser.add_argument("--subset", type=int, help="Limit the number of ion pairs processed")
    args = parser.parse_args()

    # Dynamic imports to prevent failure if specific modules are not yet fully implemented
    try:
        from code import (
            download_il_benchmark,
            load_data,
            analyze_energies,
            derive_scaling,
            correlate_bulk,
            generate_reports
        )
    except ImportError as e:
        log.error(f"Pipeline import failure: {e}")
        sys.exit(1)

    # Pipeline sequence
    stages = [
        ("download_il_benchmark", download_il_benchmark.main),
        ("load_data", load_data.main),
        ("analyze_energies", analyze_energies.main),
        ("derive_scaling", derive_scaling.main),
        ("correlate_bulk", correlate_bulk.main),
        ("generate_reports", generate_reports.main),
    ]

    for name, func in stages:
        run_stage(name, func)

    # Handle subsetting for verification (T001)
    if args.subset:
        csv_path = paths.data("derived", "raw_energies.csv")
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                if len(df) > args.subset:
                    df_subset = df.head(args.subset)
                    df_subset.to_csv(csv_path, index=False)
                    log.info(f"Subset applied: {len(df_subset)} rows written to {csv_path}")
                else:
                    log.info(f"Dataset size ({len(df)}) already within subset limit ({args.subset})")
            except Exception as e:
                log.error(f"Failed to apply subset to {csv_path}: {e}")
        else:
            log.warning(f"Subset requested but {csv_path} was not produced by the pipeline.")

    log.info("Pipeline execution completed.")

if __name__ == "__main__":
    main()