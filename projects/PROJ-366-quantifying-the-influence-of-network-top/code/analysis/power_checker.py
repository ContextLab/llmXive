import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_config, get_paths

logger = logging.getLogger(__name__)

def count_valid_samples(conductivities_dir: Path, excluded_file: Optional[Path] = None) -> int:
    """
    Count the number of valid thermal samples in the conductivities directory.
    If an excluded_samples.json file exists, exclude those IDs from the count.
    
    Args:
        conductivities_dir: Path to data/processed/conductivities/
        excluded_file: Optional path to data/processed/graphs/excluded_samples.json
        
    Returns:
        Integer count of valid samples
    """
    if not conductivities_dir.exists():
        logger.error(f"Conductivities directory does not exist: {conductivities_dir}")
        return 0
        
    valid_ids = set()
    excluded_ids = set()
    
    # Load excluded IDs if the file exists
    if excluded_file and excluded_file.exists():
        try:
            with open(excluded_file, 'r') as f:
                excluded_data = json.load(f)
                excluded_ids = set(excluded_data.get('excluded_sample_ids', []))
            logger.info(f"Loaded {len(excluded_ids)} excluded sample IDs from {excluded_file}")
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse excluded_samples.json: {e}. Proceeding without exclusions.")
        except Exception as e:
            logger.warning(f"Error reading excluded file {excluded_file}: {e}. Proceeding without exclusions.")
    
    # Count all valid sample files (pickle format)
    sample_count = 0
    for file_path in conductivities_dir.glob("*.pkl"):
        sample_id = file_path.stem
        if sample_id not in excluded_ids:
            valid_ids.add(sample_id)
            sample_count += 1
        else:
            logger.debug(f"Skipping excluded sample: {sample_id}")
            
    logger.info(f"Counted {sample_count} valid samples from {len(list(conductivities_dir.glob('*.pkl')))} total files.")
    return sample_count

def write_power_analysis_report(
    n_samples: int,
    output_path: Path,
    min_required: int = 10,
    min_runnable: int = 2
) -> Dict[str, Any]:
    """
    Write the power analysis report to the specified output path.
    
    Logic:
    - If N < 2: Exit with code 1 (fatal error)
    - If 2 <= N < 10: Write status "INSUFFICIENT_POWER", log WARNING, allow proceeding
    - If N >= 10: Write status "SUFFICIENT_POWER", log INFO
    
    Args:
        n_samples: The count of valid samples
        output_path: Path to write the JSON report
        min_required: The target sample size for full statistical power (default 10)
        min_runnable: The minimum sample size to proceed with the pipeline (default 2)
        
    Returns:
        The report dictionary
    """
    report = {
        "sample_count": n_samples,
        "min_required_for_power": min_required,
        "min_runnable": min_runnable,
        "status": "",
        "message": ""
    }
    
    if n_samples < min_runnable:
        report["status"] = "FATAL_INSUFFICIENT_DATA"
        report["message"] = (
            f"Sample count (N={n_samples}) is below the minimum runnable threshold ({min_runnable}). "
            "The pipeline cannot proceed. Exiting with code 1."
        )
        logger.critical(report["message"])
        # We write the report first so the failure is documented, then exit
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
        
    elif n_samples < min_required:
        report["status"] = "INSUFFICIENT_POWER"
        report["message"] = (
            f"Sample count (N={n_samples}) is below the recommended statistical power threshold ({min_required}). "
            "Proceeding in proof-of-concept mode (Plan N=2) but results may lack statistical significance. "
            "See Spec SC-004 vs Plan conflict resolution."
        )
        logger.warning(report["message"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Power analysis report written to {output_path}")
        
    else:
        report["status"] = "SUFFICIENT_POWER"
        report["message"] = (
            f"Sample count (N={n_samples}) meets or exceeds the statistical power requirement ({min_required}). "
            "Proceeding with full analysis."
        )
        logger.info(report["message"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
            
    return report

def main():
    """
    Entry point for the statistical power check.
    Reads configuration, counts samples, and writes the power analysis report.
    """
    # Setup logging if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = get_config()
        paths = get_paths()
        
        conductivities_dir = paths.get("conductivities_dir", paths["data_processed"] / "conductivities")
        excluded_file = paths.get("excluded_samples_file", paths["data_processed_graphs"] / "excluded_samples.json")
        output_file = paths.get("power_analysis_file", paths["data_processed_model_outputs"] / "power_analysis.json")
        
        # Ensure directories exist
        Path(conductivities_dir).mkdir(parents=True, exist_ok=True)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Scanning directory: {conductivities_dir}")
        n_samples = count_valid_samples(Path(conductivities_dir), Path(excluded_file) if excluded_file else None)
        
        logger.info(f"Calculating power analysis for N={n_samples}...")
        report = write_power_analysis_report(
            n_samples=n_samples,
            output_path=Path(output_file),
            min_required=config.get("statistical_power", {}).get("min_samples", 10),
            min_runnable=config.get("statistical_power", {}).get("min_runnable", 2)
        )
        
        logger.info(f"Power check completed. Status: {report['status']}")
        
    except Exception as e:
        logger.error(f"Power check failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
