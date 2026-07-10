"""
Main ingestion pipeline script for High-Entropy Alloy data.
Orchestrates: Fetch -> Filter -> Normalize -> Feature Engineering -> Output.
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

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, setup_logging
from utils.seeds import set_seed, get_seed
from src.data.fetch_oqmd import OQMDFetcher
from src.data.fetch_mp import MaterialsProjectFetcher
from src.data.filter import filter_hea_samples, count_principal_elements
from src.data.normalize import normalize_dataframe
from src.features.descriptors import compute_descriptors, apply_ilr_transformation
from src.features.targets import compute_residual_target, calculate_miedema_bulk_modulus
from src.report.power_report import calculate_power_deficit, generate_power_report
from src.pipeline.output_writer import write_processed_features, write_source_metadata

logger = get_logger(__name__)

# Configuration
MIN_SAMPLES_THRESHOLD = 500
OUTPUT_CSV = "data/processed/hea_features.csv"
OUTPUT_METADATA = "data/source_metadata.yaml"
OUTPUT_POWER_REPORT = "results/power_analysis_report.yaml"


def run_pipeline(
    fetch_oqmd: bool = True,
    fetch_mp: bool = True,
    oqmd_api_key: Optional[str] = None,
    mp_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the full data ingestion and feature engineering pipeline.
    
    Args:
        fetch_oqmd: Whether to fetch from OQMD.
        fetch_mp: Whether to fetch from Materials Project.
        oqmd_api_key: Optional API key for OQMD.
        mp_api_key: Optional API key for Materials Project.
    
    Returns:
        Dictionary containing pipeline statistics and paths.
    """
    start_time = time.time()
    set_seed(42)  # Default seed for reproducibility
    run_seed = get_seed()

    # Initialize run metadata
    run_metadata = {
        "run_id": f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "start_time": datetime.utcnow().isoformat(),
        "seed": run_seed,
        "sources": [],
        "parameters": {
            "min_samples_threshold": MIN_SAMPLES_THRESHOLD,
            "fetch_oqmd": fetch_oqmd,
            "fetch_mp": fetch_mp
        },
        "stats": {}
    }

    all_dataframes = []

    # --- Step 1: Fetch Data ---
    logger.info("=== Step 1: Data Fetching ===")
    
    if fetch_oqmd:
        logger.info("Fetching from OQMD...")
        try:
            oqmd_fetcher = OQMDFetcher(api_key=oqmd_api_key)
            # The fetcher handles the >=5 elements filter internally or post-fetch
            df_oqmd = oqmd_fetcher.fetch()
            if df_oqmd is not None and not df_oqmd.empty:
                df_oqmd['source'] = 'oqmd'
                all_dataframes.append(df_oqmd)
                run_metadata["sources"].append({
                    "name": "oqmd",
                    "count": len(df_oqmd),
                    "status": "success"
                })
                logger.info(f"Fetched {len(df_oqmd)} samples from OQMD.")
            else:
                logger.warning("OQMD fetch returned empty data.")
                run_metadata["sources"].append({"name": "oqmd", "count": 0, "status": "empty"})
        except Exception as e:
            logger.error(f"Failed to fetch from OQMD: {e}")
            run_metadata["sources"].append({"name": "oqmd", "count": 0, "status": "error", "error": str(e)})

    if fetch_mp:
        logger.info("Fetching from Materials Project...")
        try:
            mp_fetcher = MaterialsProjectFetcher(api_key=mp_api_key)
            df_mp = mp_fetcher.fetch()
            if df_mp is not None and not df_mp.empty:
                df_mp['source'] = 'materials_project'
                all_dataframes.append(df_mp)
                run_metadata["sources"].append({
                    "name": "materials_project",
                    "count": len(df_mp),
                    "status": "success"
                })
                logger.info(f"Fetched {len(df_mp)} samples from Materials Project.")
            else:
                logger.warning("Materials Project fetch returned empty data.")
                run_metadata["sources"].append({"name": "materials_project", "count": 0, "status": "empty"})
        except Exception as e:
            logger.error(f"Failed to fetch from Materials Project: {e}")
            run_metadata["sources"].append({"name": "materials_project", "count": 0, "status": "error", "error": str(e)})

    if not all_dataframes:
        logger.error("No data fetched from any source. Aborting pipeline.")
        raise RuntimeError("Pipeline aborted: No data available.")

    # Merge data
    df = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"Total samples after merge: {len(df)}")
    run_metadata["stats"]["total_samples_fetched"] = len(df)

    # --- Step 2: Filter (>=5 elements) ---
    logger.info("=== Step 2: Filtering (>=5 principal elements) ===")
    # Assuming filter_hea_samples handles the logic based on composition columns
    # If the fetchers already filtered, this is a safety check
    df_filtered = filter_hea_samples(df, min_elements=5)
    logger.info(f"Samples after filtering: {len(df_filtered)}")
    run_metadata["stats"]["samples_after_filter"] = len(df_filtered)

    # --- Step 3: Normalize ---
    logger.info("=== Step 3: Normalization ===")
    df_normalized = normalize_dataframe(df_filtered)
    logger.info("Normalization complete.")

    # --- Step 4: Feature Engineering ---
    logger.info("=== Step 4: Feature Engineering ===")
    
    # Calculate Miedema Bulk Modulus for target residual
    logger.info("Calculating Miedema Bulk Modulus for residual target...")
    df_normalized = calculate_miedema_bulk_modulus(df_normalized)
    
    # Compute descriptors (including Miedema-derived ones)
    logger.info("Computing descriptors...")
    df_features = compute_descriptors(df_normalized)
    
    # Apply ILR transformation for compositional data
    logger.info("Applying ILR transformation...")
    df_features = apply_ilr_transformation(df_features)
    
    # Compute Residual Target
    logger.info("Computing residual target (Observed - Miedema)...")
    df_features = compute_residual_target(df_features)
    
    logger.info(f"Feature engineering complete. Final columns: {len(df_features.columns)}")
    run_metadata["stats"]["feature_count"] = len(df_features.columns)

    # --- Step 5: Power Analysis ---
    logger.info("=== Step 5: Power Analysis ===")
    if len(df_features) < MIN_SAMPLES_THRESHOLD:
        logger.warning(f"Sample count ({len(df_features)}) is below threshold ({MIN_SAMPLES_THRESHOLD}).")
        power_deficit = calculate_power_deficit(len(df_features), MIN_SAMPLES_THRESHOLD)
        power_report = generate_power_report(power_deficit, len(df_features))
        
        # Write power report
        power_report_path = str(project_root / OUTPUT_POWER_REPORT)
        with open(power_report_path, 'w') as f:
            yaml.dump(power_report, f, default_flow_style=False)
        logger.info(f"Power analysis report written to {power_report_path}")
        
        run_metadata["power_analysis"] = {
            "underpowered": True,
            "sample_count": len(df_features),
            "threshold": MIN_SAMPLES_THRESHOLD,
            "report_path": OUTPUT_POWER_REPORT
        }
    else:
        logger.info(f"Sample count ({len(df_features)}) meets threshold.")
        run_metadata["power_analysis"] = {
            "underpowered": False,
            "sample_count": len(df_features),
            "threshold": MIN_SAMPLES_THRESHOLD
        }

    # --- Step 6: Output ---
    logger.info("=== Step 6: Writing Outputs ===")
    
    output_csv_path = str(project_root / OUTPUT_CSV)
    write_processed_features(df_features, output_csv_path)
    
    run_metadata["outputs"] = {
        "features_csv": OUTPUT_CSV,
        "metadata_yaml": OUTPUT_METADATA
    }
    run_metadata["end_time"] = datetime.utcnow().isoformat()
    run_metadata["duration_seconds"] = time.time() - start_time

    metadata_path = str(project_root / OUTPUT_METADATA)
    write_source_metadata(run_metadata, metadata_path)

    logger.info("=== Pipeline Complete ===")
    logger.info(f"Total duration: {run_metadata['duration_seconds']:.2f}s")
    logger.info(f"Output CSV: {output_csv_path}")
    logger.info(f"Metadata YAML: {metadata_path}")

    return run_metadata


def main():
    """Entry point for script execution."""
    setup_logging(level=logging.INFO)
    try:
        run_pipeline()
        return 0
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())