import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import analysis modules
from analysis.study_counter import run_study_counter, main as run_study_counter_main
from analysis.tract_counting import run_tract_counting, main as run_tract_counting_main
from analysis.meta_analysis import run_meta_analysis, main as run_meta_analysis_main
from analysis.narrative import generate_narrative_summary, main as run_narrative_main
from analysis.narrative_logic import run_narrative_logic, main as run_narrative_logic_main
from analysis.bias import run_bias_assessment, main as run_bias_main
from analysis.heterogeneity import run_heterogeneity_analysis, main as run_heterogeneity_main
from analysis.correction import run_correction_analysis, main as run_correction_main

# Import extraction modules
from extraction.parser import parse_input, main as run_parser_main

# Import visualization modules (T028: Integration)
from visualization.plots_forest import run_forest_plot_generation
from visualization.plots_funnel import run_funnel_plot_generation
from visualization.plots_correlation import run_correlation_plot_generation
from visualization.regenerator import run_regeneration
from visualization.memory_monitor import check_memory_usage

# Import utilities
from utils.config import get_project_root, load_config, resolve_path
from utils.logger import get_logger, log_error_context
from utils.validator import validate_file_size, validate_generated_plots

logger = get_logger(__name__)

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents, or None if it doesn't exist."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
        return None

def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def run_pipeline(args: argparse.Namespace) -> int:
    """
    Main pipeline orchestrator.
    Executes tasks in dependency order, handles gate logic, and integrates visualization.
    """
    root = get_project_root()
    config = load_config()
    
    # Define paths
    data_raw_dir = root / "data" / "raw"
    data_processed_dir = root / "data" / "processed"
    data_derived_dir = root / "data" / "derived"
    data_logs_dir = root / "data" / "logs"
    
    # Ensure directories exist
    for d in [data_raw_dir, data_processed_dir, data_derived_dir, data_logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Extraction (T013)
    # Input: data/raw/studies.csv (or similar), Output: data/processed/extracted_studies.csv
    input_file = data_raw_dir / "studies.csv"
    if not input_file.exists():
        # Check for alternative names or error
        logger.error(f"Input file {input_file} not found. Pipeline cannot proceed.")
        return 1

    logger.info("Step 1: Parsing and extracting study data...")
    try:
        parse_input(str(input_file), str(data_processed_dir / "extracted_studies.csv"))
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1

    # 2. Count Studies (T014a)
    logger.info("Step 2: Counting studies...")
    run_study_counter_main()
    study_count_data = load_json_file(data_processed_dir / "study_count.json")
    if not study_count_data:
        logger.error("Failed to load study count.")
        return 1
    N = study_count_data.get("N", 0)
    logger.info(f"Study count N = {N}")

    # 3. Count Tracts (T008c)
    logger.info("Step 3: Counting unique tracts...")
    run_tract_counting_main()
    tract_count_data = load_json_file(data_processed_dir / "tract_count.json")
    k = tract_count_data.get("k", 0) if tract_count_data else 0
    logger.info(f"Tract count k = {k}")

    # 4. Meta-Analysis Gate (T014)
    meta_status = {"status": "unknown", "N": N}
    if N < 10:
        logger.warning(f"Insufficient studies (N={N}) for quantitative meta-analysis. Skipping.")
        meta_status["status"] = "skipped"
        meta_status["reason"] = "Insufficient studies"
        save_json_file(data_processed_dir / "meta_status.json", meta_status)
    else:
        logger.info("Running random-effects meta-analysis...")
        try:
            run_meta_analysis_main()
            meta_status_data = load_json_file(data_processed_dir / "meta_status.json")
            if meta_status_data:
                meta_status = meta_status_data
        except Exception as e:
            logger.error(f"Meta-analysis failed: {e}")
            meta_status["status"] = "error"
            meta_status["error"] = str(e)
            save_json_file(data_processed_dir / "meta_status.json", meta_status)

    # 5. Narrative Fallback Logic (T015)
    synthesis_mode = "quantitative"
    if N < 10 or meta_status.get("status") == "skipped":
        logger.info("Generating narrative summary (Fallback)...")
        try:
            # Run narrative logic aggregation
            run_narrative_logic_main()
            # Generate the markdown summary
            generate_narrative_summary()
            synthesis_mode = "narrative"
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            # Continue with partial results if possible

    # 6. Heterogeneity & Bias (T021, T021b) - Only if N >= 10
    if N >= 10 and meta_status.get("status") != "error":
        logger.info("Running heterogeneity and bias analysis...")
        try:
            run_heterogeneity_main()
            run_bias_main()
        except Exception as e:
            logger.error(f"Heterogeneity/Bias analysis failed: {e}")

    # 7. Correction (T022)
    if N >= 10 and k >= 2:
        logger.info("Running multiple comparison correction...")
        try:
            run_correction_main()
        except Exception as e:
            logger.error(f"Correction analysis failed: {e}")

    # 8. Visualization Integration (T028)
    # Only run if quantitative results are available and synthesis_mode is quantitative
    # If synthesis_mode is narrative, we might still want to plot what we have, 
    # but the spec implies plots are for quantitative synthesis.
    if synthesis_mode == "quantitative" and N >= 10:
        logger.info("Generating visualization plots...")
        try:
            # Check memory before plotting
            check_memory_usage()
            
            # Generate Forest Plot (T027a)
            run_forest_plot_generation()
            # Generate Funnel Plot (T027b)
            run_funnel_plot_generation()
            # Generate Correlation Summary Plot (T027c)
            run_correlation_plot_generation()
            
            # 9. Validation (T031)
            logger.info("Validating generated plots...")
            validation_passed = True
            failed_plots = []
            
            plot_files = [
                data_derived_dir / "forest_plot.png",
                data_derived_dir / "funnel_plot.png",
                data_derived_dir / "correlation_summary.png"
            ]
            
            for p in plot_files:
                if not p.exists():
                    validation_passed = False
                    failed_plots.append(p.name)
                    logger.error(f"Plot missing: {p.name}")
                elif not validate_file_size(p, max_size_mb=5):
                    validation_passed = False
                    failed_plots.append(p.name)
                    logger.warning(f"Plot too large: {p.name}")
            
            validation_report = {
                "overall_status": "pass" if validation_passed else "fail",
                "timestamp": datetime.now().isoformat(),
                "failed_plots": failed_plots
            }
            save_json_file(data_derived_dir / "validation_report.json", validation_report)
            
            if not validation_passed:
                logger.warning("Validation failed. Attempting regeneration (T027d)...")
                run_regeneration()
                # Re-validate after regeneration
                # (Simplified: in a real loop, we'd check again, but T027d handles the retry logic internally)

        except Exception as e:
            logger.error(f"Visualization pipeline failed: {e}")
            save_json_file(data_derived_dir / "validation_report.json", {
                "overall_status": "fail",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # 10. Final Results Aggregation
    logger.info("Aggregating final results...")
    final_results = {
        "synthesis_mode": synthesis_mode,
        "study_count": N,
        "tract_count": k,
        "timestamp": datetime.now().isoformat(),
        "meta_analysis": load_json_file(data_processed_dir / "meta_status.json"),
        "heterogeneity": load_json_file(data_derived_dir / "heterogeneity_results.json"),
        "bias": load_json_file(data_derived_dir / "bias_results.json"),
        "correction": load_json_file(data_derived_dir / "correction_results.json"),
        "narrative_summary_path": "data/derived/narrative_summary.md" if synthesis_mode == "narrative" else None
    }
    
    save_json_file(data_derived_dir / "results.json", final_results)
    logger.info("Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Meta-Analysis Pipeline")
    parser.add_argument("--input", type=str, help="Path to input CSV")
    parser.add_argument("--config", type=str, default="code/config/config.yaml", help="Path to config file")
    args = parser.parse_args()
    
    sys.exit(run_pipeline(args))

if __name__ == "__main__":
    main()