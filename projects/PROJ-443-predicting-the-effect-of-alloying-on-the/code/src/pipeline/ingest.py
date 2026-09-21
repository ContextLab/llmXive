"""
Main pipeline script for User Story 1: Data Ingestion and Feature Engineering.

Orchestrates:
1. Fetch data from OQMD and Materials Project
2. Filter for >=5 principal elements
3. Normalize compositions
4. Calculate descriptors and targets
5. Apply ILR transformation
6. Save processed CSV and source_metadata.yaml

Implements FR-009: Dynamic generation of source_metadata.yaml
"""
import os
import sys
import logging
import time
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_logger, setup_logging, is_logging_initialized
from src.utils.seeds import set_seed, get_seed
from src.data.fetch_oqmd import OQMDFetcher, main as fetch_oqmd_main
from src.data.fetch_mp import MaterialsProjectFetcher, main as fetch_mp_main
from src.data.filter import filter_hea_samples, count_principal_elements, main as filter_main
from src.data.normalize import normalize_dataframe, main as normalize_main
from src.features.descriptors import compute_descriptors, apply_ilr_transformation, main as descriptors_main
from src.features.targets import compute_residual_target, compute_miedema_column, main as targets_main
from src.pipeline.output_writer import write_processed_features, write_source_metadata, main as writer_main
from src.report.power_report import calculate_power_deficit, generate_power_report, main as power_report_main

# Constants
MIN_PRINCIPAL_ELEMENTS = 5
MIN_SAMPLE_COUNT = 500
OUTPUT_CSV_PATH = "data/processed/hea_features.csv"
OUTPUT_METADATA_PATH = "data/source_metadata.yaml"
OUTPUT_POWER_REPORT_PATH = "results/power_analysis_report.yaml"

def run_pipeline(
    oqmd_data_path: Optional[str] = None,
    mp_data_path: Optional[str] = None,
    output_csv: str = OUTPUT_CSV_PATH,
    output_metadata: str = OUTPUT_METADATA_PATH,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute the full ingestion pipeline.

    Args:
        oqmd_data_path: Optional path to pre-fetched OQMD data (for testing)
        mp_data_path: Optional path to pre-fetched MP data (for testing)
        output_csv: Path to write the processed features CSV
        output_metadata: Path to write the source metadata YAML
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing pipeline execution results and statistics
    """
    # Initialize logging
    if not is_logging_initialized():
        setup_logging(level=logging.INFO)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Starting HEA Data Ingestion Pipeline (US1)")
    logger.info(f"Seed: {seed}")
    logger.info("=" * 60)

    # Set seeds for reproducibility
    set_seed(seed)
    logger.info(f"Random seed set to {get_seed()}")

    # Track pipeline metrics
    pipeline_metrics = {
        "start_time": datetime.now().isoformat(),
        "seed": seed,
        "steps": {},
        "total_samples": 0,
        "filtered_samples": 0,
        "final_samples": 0,
        "sources": [],
        "warnings": [],
        "power_analysis": None
    }

    # Step 1: Fetch Data
    logger.info("Step 1: Fetching data from OQMD and Materials Project")
    start_fetch = time.time()

    fetched_data = []
    oqmd_count = 0
    mp_count = 0

    try:
        if oqmd_data_path or not mp_data_path:
            logger.info("Fetching OQMD data...")
            oqmd_fetcher = OQMDFetcher()
            oqmd_df = oqmd_fetcher.fetch()
            if oqmd_df is not None and not oqmd_df.empty:
                fetched_data.append({
                    "source": "OQMD",
                    "data": oqmd_df,
                    "count": len(oqmd_df)
                })
                oqmd_count = len(oqmd_df)
                pipeline_metrics["sources"].append({
                    "name": "OQMD",
                    "count": oqmd_count,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"OQMD fetched {oqmd_count} samples")
            else:
                logger.warning("OQMD returned no data")
        else:
            logger.info("Skipping OQMD fetch (using pre-fetched data)")
            # In a real scenario, we'd load from oqmd_data_path
    except Exception as e:
        logger.error(f"Failed to fetch OQMD data: {e}")
        pipeline_metrics["warnings"].append(f"OQMD fetch failed: {str(e)}")

    try:
        if mp_data_path:
            logger.info("Fetching Materials Project data...")
            mp_fetcher = MaterialsProjectFetcher()
            mp_df = mp_fetcher.fetch()
            if mp_df is not None and not mp_df.empty:
                fetched_data.append({
                    "source": "Materials Project",
                    "data": mp_df,
                    "count": len(mp_df)
                })
                mp_count = len(mp_df)
                pipeline_metrics["sources"].append({
                    "name": "Materials Project",
                    "count": mp_count,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Materials Project fetched {mp_count} samples")
            else:
                logger.warning("Materials Project returned no data")
        else:
            logger.info("Skipping Materials Project fetch (using pre-fetched data)")
    except Exception as e:
        logger.error(f"Failed to fetch Materials Project data: {e}")
        pipeline_metrics["warnings"].append(f"MP fetch failed: {str(e)}")

    fetch_duration = time.time() - start_fetch
    pipeline_metrics["steps"]["fetch"] = {
        "duration_seconds": fetch_duration,
        "oqmd_samples": oqmd_count,
        "mp_samples": mp_count
    }

    if not fetched_data:
        logger.error("No data fetched from any source. Aborting pipeline.")
        return pipeline_metrics

    # Merge all fetched data
    import pandas as pd
    combined_df = pd.concat([item["data"] for item in fetched_data], ignore_index=True)
    pipeline_metrics["total_samples"] = len(combined_df)
    logger.info(f"Combined dataset has {len(combined_df)} samples")

    # Step 2: Filter for >=5 principal elements
    logger.info("Step 2: Filtering for >=5 principal elements")
    start_filter = time.time()

    try:
        filtered_df = filter_hea_samples(
            combined_df,
            min_elements=MIN_PRINCIPAL_ELEMENTS,
            logger=logger
        )
        pipeline_metrics["filtered_samples"] = len(filtered_df)
        logger.info(f"Filtered dataset: {len(filtered_df)} samples (removed {len(combined_df) - len(filtered_df)})")
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        # Fall back to original if filter fails, but log warning
        filtered_df = combined_df
        pipeline_metrics["warnings"].append(f"Filter failed, using unfiltered data: {str(e)}")

    filter_duration = time.time() - start_filter
    pipeline_metrics["steps"]["filter"] = {
        "duration_seconds": filter_duration,
        "samples_before": len(combined_df),
        "samples_after": len(filtered_df)
    }

    # Step 3: Normalize compositions
    logger.info("Step 3: Normalizing compositions")
    start_normalize = time.time()

    try:
        normalized_df = normalize_dataframe(filtered_df, logger=logger)
        logger.info("Compositions normalized successfully")
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        normalized_df = filtered_df
        pipeline_metrics["warnings"].append(f"Normalization failed, using unnormalized data: {str(e)}")

    normalize_duration = time.time() - start_normalize
    pipeline_metrics["steps"]["normalize"] = {
        "duration_seconds": normalize_duration
    }

    # Step 4: Calculate descriptors (including Miedema features)
    logger.info("Step 4: Calculating descriptors")
    start_descriptors = time.time()

    try:
        descriptor_df = compute_descriptors(normalized_df, logger=logger)
        logger.info(f"Descriptors calculated: {len(descriptor_df.columns)} columns")
    except Exception as e:
        logger.error(f"Descriptor calculation failed: {e}")
        descriptor_df = normalized_df
        pipeline_metrics["warnings"].append(f"Descriptor calculation failed: {str(e)}")

    descriptor_duration = time.time() - start_descriptors
    pipeline_metrics["steps"]["descriptors"] = {
        "duration_seconds": descriptor_duration,
        "descriptor_count": len(descriptor_df.columns) if not descriptor_df.empty else 0
    }

    # Step 5: Calculate targets (Residual Bulk Modulus)
    logger.info("Step 5: Calculating target variables")
    start_targets = time.time()

    try:
        target_df = compute_residual_target(descriptor_df, logger=logger)
        logger.info("Target variables calculated (Residual Bulk Modulus)")
    except Exception as e:
        logger.error(f"Target calculation failed: {e}")
        target_df = descriptor_df
        pipeline_metrics["warnings"].append(f"Target calculation failed: {str(e)}")

    target_duration = time.time() - start_targets
    pipeline_metrics["steps"]["targets"] = {
        "duration_seconds": target_duration
    }

    # Step 6: Apply ILR transformation
    logger.info("Step 6: Applying ILR transformation")
    start_ilr = time.time()

    try:
        ilr_df = apply_ilr_transformation(target_df, logger=logger)
        logger.info("ILR transformation applied successfully")
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        ilr_df = target_df
        pipeline_metrics["warnings"].append(f"ILR transformation failed: {str(e)}")

    ilr_duration = time.time() - start_ilr
    pipeline_metrics["steps"]["ilr"] = {
        "duration_seconds": ilr_duration
    }

    pipeline_metrics["final_samples"] = len(ilr_df)
    logger.info(f"Final dataset size: {len(ilr_df)} samples")

    # Step 7: Power Analysis (Reduced Power Analysis if < 500 samples)
    logger.info("Step 7: Running power analysis")
    if len(ilr_df) < MIN_SAMPLE_COUNT:
        logger.warning(f"Sample count ({len(ilr_df)}) is below threshold ({MIN_SAMPLE_COUNT}). Running Reduced Power Analysis.")
        try:
            power_report = generate_power_report(
                sample_count=len(ilr_df),
                threshold=MIN_SAMPLE_COUNT,
                logger=logger
            )
            pipeline_metrics["power_analysis"] = power_report
            
            # Write power report to file
            power_report_path = Path(project_root) / OUTPUT_POWER_REPORT_PATH
            power_report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(power_report_path, 'w') as f:
                yaml.dump(power_report, f, default_flow_style=False)
            logger.info(f"Power report written to {power_report_path}")
        except Exception as e:
            logger.error(f"Power report generation failed: {e}")
            pipeline_metrics["warnings"].append(f"Power report failed: {str(e)}")
    else:
        logger.info(f"Sample count ({len(ilr_df)}) meets threshold ({MIN_SAMPLE_COUNT}). No power analysis needed.")

    # Step 8: Write outputs
    logger.info("Step 8: Writing output files")
    start_write = time.time()

    # Create output directories
    output_csv_path = Path(project_root) / output_csv
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Write processed features CSV
    try:
        write_processed_features(ilr_df, str(output_csv_path), logger=logger)
        logger.info(f"Processed features written to {output_csv_path}")
    except Exception as e:
        logger.error(f"Failed to write processed features: {e}")
        pipeline_metrics["warnings"].append(f"CSV write failed: {str(e)}")

    # Step 9: Generate and write source_metadata.yaml (FR-009)
    logger.info("Step 9: Generating source metadata (FR-009)")
    
    metadata = {
        "pipeline_version": "1.0.0",
        "execution_timestamp": datetime.now().isoformat(),
        "seed": seed,
        "sources": pipeline_metrics["sources"],
        "parameters": {
            "min_principal_elements": MIN_PRINCIPAL_ELEMENTS,
            "min_sample_count": MIN_SAMPLE_COUNT,
            "output_csv": output_csv,
            "output_metadata": output_metadata
        },
        "statistics": {
            "total_samples_fetched": pipeline_metrics["total_samples"],
            "samples_after_filter": pipeline_metrics["filtered_samples"],
            "final_samples": pipeline_metrics["final_samples"],
            "samples_dropped": pipeline_metrics["total_samples"] - pipeline_metrics["final_samples"]
        },
        "duration_seconds": time.time() - pipeline_metrics["start_time"],
        "warnings": pipeline_metrics["warnings"],
        "power_analysis_applied": pipeline_metrics["power_analysis"] is not None
    }

    if pipeline_metrics["power_analysis"]:
        metadata["power_analysis_summary"] = {
            "sample_count": pipeline_metrics["power_analysis"].get("sample_count"),
            "threshold": pipeline_metrics["power_analysis"].get("threshold"),
            "deficit": pipeline_metrics["power_analysis"].get("deficit"),
            "message": pipeline_metrics["power_analysis"].get("message")
        }

    output_metadata_path = Path(project_root) / output_metadata
    try:
        write_source_metadata(metadata, str(output_metadata_path), logger=logger)
        logger.info(f"Source metadata written to {output_metadata_path}")
    except Exception as e:
        logger.error(f"Failed to write source metadata: {e}")
        pipeline_metrics["warnings"].append(f"Metadata write failed: {str(e)}")

    write_duration = time.time() - start_write
    pipeline_metrics["steps"]["write"] = {
        "duration_seconds": write_duration
    }

    # Final summary
    pipeline_metrics["end_time"] = datetime.now().isoformat()
    total_duration = time.time() - start_fetch
    pipeline_metrics["total_duration_seconds"] = total_duration

    logger.info("=" * 60)
    logger.info("Pipeline Execution Complete")
    logger.info(f"Total duration: {total_duration:.2f}s")
    logger.info(f"Final samples: {pipeline_metrics['final_samples']}")
    logger.info(f"Output CSV: {output_csv_path}")
    logger.info(f"Output Metadata: {output_metadata_path}")
    if pipeline_metrics["warnings"]:
        logger.warning(f"Warnings encountered: {len(pipeline_metrics['warnings'])}")
        for w in pipeline_metrics["warnings"]:
            logger.warning(f"  - {w}")
    logger.info("=" * 60)

    return pipeline_metrics

def main():
    """Main entry point for the pipeline script."""
    import argparse

    parser = argparse.ArgumentParser(description="HEA Data Ingestion Pipeline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--oqmd-data", type=str, default=None, help="Path to pre-fetched OQMD data")
    parser.add_argument("--mp-data", type=str, default=None, help="Path to pre-fetched MP data")
    parser.add_argument("--output-csv", type=str, default=OUTPUT_CSV_PATH, help="Output CSV path")
    parser.add_argument("--output-metadata", type=str, default=OUTPUT_METADATA_PATH, help="Output metadata path")

    args = parser.parse_args()

    results = run_pipeline(
        oqmd_data_path=args.oqmd_data,
        mp_data_path=args.mp_data,
        output_csv=args.output_csv,
        output_metadata=args.output_metadata,
        seed=args.seed
    )

    # Exit with error if critical warnings occurred
    if results.get("final_samples", 0) == 0:
        print("ERROR: Pipeline produced no samples.")
        sys.exit(1)

    print(f"Pipeline completed successfully. Final samples: {results['final_samples']}")
    sys.exit(0)

if __name__ == "__main__":
    main()