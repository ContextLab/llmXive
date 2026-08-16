import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from analysis.bias import run_bias_assessment
from analysis.correction import run_correction_analysis
from analysis.meta_analysis import run_meta_analysis
from analysis.narrative_engine import run_narrative_engine
from analysis.study_counter import run_study_counter
from analysis.tract_counting import run_tract_counting
from extraction.parser import parse_input, save_extracted_studies
from utils.config import get_project_root, get_output_path, get_figure_path, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: dict) -> None:
    """Save a dictionary to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the full research pipeline.
    
    This function orchestrates the execution of all major stages:
    1. Data Extraction (T013)
    2. Study Counting (T014a)
    3. Tract Counting (T008c)
    4. Meta-Analysis (T014)
    5. Bias Assessment (T021/T021b) - INTEGRATED HERE (T023)
    6. Correction Analysis (T022)
    7. Narrative Synthesis or Visualization (Conditional)
    """
    project_root = get_project_root()
    config = load_config()
    
    # Paths
    raw_data_path = project_root / "data" / "raw" / "studies.csv"
    extracted_path = project_root / "data" / "processed" / "extracted_studies.csv"
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    tract_count_path = project_root / "data" / "processed" / "tract_count.json"
    meta_status_path = project_root / "data" / "processed" / "meta_status.json"
    bonferroni_status_path = project_root / "data" / "derived" / "bonferroni_status.json"
    results_path = project_root / "data" / "derived" / "results.json"
    narrative_content_path = project_root / "data" / "derived" / "narrative_content.md"
    narrative_summary_path = project_root / "data" / "derived" / "narrative_summary.md"

    try:
        # 1. Data Extraction (T013)
        logger.info("Starting Data Extraction (T013)...")
        parse_input(raw_data_path, extracted_path)
        save_extracted_studies(extracted_path)
        logger.info(f"Extraction complete. Output: {extracted_path}")

        # 2. Study Counting (T014a)
        logger.info("Starting Study Counting (T014a)...")
        run_study_counter(extracted_path, study_count_path)
        study_count_data = load_json_file(study_count_path)
        N = study_count_data.get("N", 0)
        logger.info(f"Study count: {N}")

        # 3. Tract Counting (T008c)
        logger.info("Starting Tract Counting (T008c)...")
        run_tract_counting(extracted_path, tract_count_path)
        tract_count_data = load_json_file(tract_count_path)
        k = tract_count_data.get("k", 0)
        logger.info(f"Tract count: {k}")

        # 4. Meta-Analysis (T014)
        logger.info("Starting Meta-Analysis (T014)...")
        run_meta_analysis(study_count_path, meta_status_path)
        meta_status = load_json_file(meta_status_path)
        meta_status_code = meta_status.get("status", "unknown")
        logger.info(f"Meta-analysis status: {meta_status_code}")

        # 5. BIAS ASSESSMENT INTEGRATION (T023)
        # Run bias assessment (Egger's + Heterogeneity) AFTER meta-analysis
        # This task (T023) specifically integrates this step into the main flow
        logger.info("Starting Bias Assessment Integration (T023)...")
        bias_results = run_bias_assessment(study_count_path, meta_status_path)
        
        # Update MetaAnalysisResult JSON with bias metrics
        # We load the meta_status (which acts as the base results object for now)
        # and update it with bias metrics, then save to results.json later
        if bias_results:
            logger.info(f"Bias assessment complete. I²: {bias_results.get('i_squared')}, Egger p: {bias_results.get('egger_p')}")
            # Merge bias results into the meta_status for the final output
            meta_status.update(bias_results)
        else:
            logger.warning("Bias assessment returned no results.")

        # 6. Correction Analysis (T022)
        logger.info("Starting Correction Analysis (T022)...")
        correction_results = run_correction_analysis(tract_count_path, study_count_path, bonferroni_status_path)
        
        # 7. Gate Logic & Final Output
        synthesis_mode = "quantitative"
        final_results = {}

        if N < 10 or meta_status_code == "skipped":
            logger.info(f"Insufficient studies (N={N}). Triggering Narrative Synthesis.")
            synthesis_mode = "narrative"
            
            # Run Narrative Engine (T015b)
            run_narrative_engine(study_count_path, narrative_content_path)
            
            # Generate Summary (T015c) - Assuming narrative.py handles the file generation
            # Note: T015c logic is often embedded in narrative.py or called via narrative_engine
            # For this integration, we assume narrative_engine generates the content,
            # and we might need to call a summary generator if separate.
            # Based on T015c spec, it generates narrative_summary.md.
            # We assume narrative.py (T015c) is the generator.
            from analysis.narrative import generate_narrative_summary
            generate_narrative_summary(narrative_content_path, narrative_summary_path)

            final_results = {
                "synthesis_mode": "narrative",
                "study_count": N,
                "limitations": "Data insufficient for quantitative meta-analysis (N < 10).",
                "narrative_summary_path": str(narrative_summary_path)
            }
            if "narrative_content_path" in locals():
                final_results["narrative_content_path"] = str(narrative_content_path)
        else:
            logger.info("Sufficient studies. Proceeding with Quantitative Results.")
            synthesis_mode = "quantitative"
            final_results = {
                "synthesis_mode": "quantitative",
                "study_count": N,
                "tract_count": k,
                "meta_analysis": meta_status,
                "bias_assessment": {
                    "i_squared": meta_status.get("i_squared"),
                    "egger_p": meta_status.get("egger_p"),
                    "egger_intercept": meta_status.get("egger_intercept"),
                    "bias_status": "completed" if meta_status.get("status") == "completed" else "skipped"
                },
                "correction": correction_results
            }

        # Save Final Results
        save_json_file(results_path, final_results)
        logger.info(f"Pipeline complete. Final results saved to {results_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        return 1

def main():
    parser = argparse.ArgumentParser(description="Run the Meta-Analysis Pipeline")
    parser.add_argument('--config', type=str, default='code/config/config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    sys.exit(run_pipeline(args))

if __name__ == "__main__":
    main()