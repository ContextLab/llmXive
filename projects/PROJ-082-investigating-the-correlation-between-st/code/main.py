import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Local imports from project structure
from utils.config import get_project_root, load_config, ensure_directory
from utils.logger import get_logger, log_error_context
from analysis.study_counter import run_study_counter
from analysis.tract_counting import run_tract_counting
from analysis.meta_analysis import run_meta_analysis
from analysis.bias import run_bias_assessment
from analysis.heterogeneity import run_heterogeneity_analysis
from analysis.correction import run_correction_analysis
from analysis.narrative import generate_narrative_summary
from extraction.parser import parse_input, save_extracted_studies
from visualization.plots import run_visualization_analysis
from utils.validator import validate_generated_plots
from quickstart_validator import run_pipeline_execution

# Setup logging
logger = get_logger(__name__)

def run_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main orchestration function for the meta-analysis pipeline.
    Executes the full workflow: Extraction -> Analysis -> Visualization -> Reporting.
    """
    root = get_project_root()
    if config is None:
        config = load_config()
    
    seed = config.get('seed', 42)
    # Set seed for reproducibility if needed by downstream modules
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

    results = {
        "pipeline_start": datetime.now().isoformat(),
        "status": "running",
        "synthesis_mode": None,
        "metrics": {}
    }

    try:
        # 1. Data Extraction (T013)
        logger.info("Phase 1: Data Extraction")
        input_path = root / "data" / "raw" / "studies.csv"
        if not input_path.exists():
            # Fallback to mock data if real data not found for testing
            mock_path = root / "data" / "raw" / "mock_studies_quant.csv"
            if mock_path.exists():
                input_path = mock_path
            else:
                raise FileNotFoundError(f"Input data not found at {input_path} or {mock_path}")

        extracted_data = parse_input(input_path)
        extracted_csv_path = root / "data" / "processed" / "extracted_studies.csv"
        save_extracted_studies(extracted_data, extracted_csv_path)
        logger.info(f"Extracted {len(extracted_data)} studies to {extracted_csv_path}")

        # 2. Count Studies (T014a)
        logger.info("Phase 2: Study Counting")
        study_count_result = run_study_counter(extracted_csv_path)
        N = study_count_result.get('N', 0)
        logger.info(f"Total studies (N): {N}")

        # 3. Count Tracts (T008c)
        logger.info("Phase 2b: Tract Counting")
        tract_count_result = run_tract_counting(extracted_csv_path)
        k = tract_count_result.get('k', 0)
        logger.info(f"Unique tracts (k): {k}")

        # 4. Meta-Analysis (T014) & Gate Logic (T016a)
        logger.info("Phase 3: Meta-Analysis")
        meta_status_path = root / "data" / "processed" / "meta_status.json"
        meta_results_path = root / "data" / "derived" / "results_quant.json"
        
        # Run meta-analysis (handles N < 10 skipping internally)
        meta_analysis_output = run_meta_analysis(extracted_csv_path, meta_status_path, meta_results_path)
        
        # Determine synthesis mode based on N and meta_status
        with open(meta_status_path, 'r') as f:
            meta_status = json.load(f)
        
        synthesis_mode = "quantitative"
        if meta_status.get('status') == 'skipped' or N < 10:
            synthesis_mode = "narrative"
            logger.warning(f"Insufficient studies (N={N}) for quantitative meta-analysis. Switching to narrative mode.")
            
            # Run Narrative Logic (T015a)
            from analysis.narrative_logic import run_narrative_logic
            themes_path = root / "data" / "derived" / "narrative_themes.json"
            run_narrative_logic(extracted_csv_path, themes_path)
            
            # Generate Narrative Summary (T015)
            narrative_path = root / "data" / "derived" / "narrative_summary.md"
            generate_narrative_summary(
                study_count=N,
                themes_path=themes_path,
                output_path=narrative_path
            )
            
            # Update results for narrative mode
            results["synthesis_mode"] = "narrative"
            results["metrics"]["narrative_summary"] = str(narrative_path)
        else:
            # Quantitative path
            synthesis_mode = "quantitative"
            results["synthesis_mode"] = "quantitative"
            results["metrics"]["meta_analysis"] = meta_results_path

            # 5. Heterogeneity (T021b)
            logger.info("Phase 4a: Heterogeneity Analysis")
            hetero_path = root / "data" / "derived" / "heterogeneity.json"
            run_heterogeneity_analysis(extracted_csv_path, meta_results_path, hetero_path)

            # 6. Bias Assessment (T021) - INTEGRATION POINT FOR T023
            logger.info("Phase 4b: Bias Assessment")
            bias_path = root / "data" / "derived" / "bias_analysis.json"
            bias_output = run_bias_assessment(extracted_csv_path, meta_results_path, bias_path)
            
            # Update results with bias metrics
            if bias_output:
                results["metrics"]["bias_analysis"] = bias_path
                # Merge Egger's result into main results if present
                if 'egger_p' in bias_output:
                    results["metrics"]["egger_p"] = bias_output['egger_p']

            # 7. Correction (T022)
            logger.info("Phase 4c: Multiple Comparison Correction")
            correction_path = root / "data" / "derived" / "correction.json"
            correction_output = run_correction_analysis(k, N, bias_path, correction_path)
            if correction_output:
                results["metrics"]["correction"] = correction_path

        # 8. Visualization (T027a/b/c) - Only if quantitative or if narrative has plots
        if synthesis_mode == "quantitative":
            logger.info("Phase 5: Visualization")
            viz_dir = root / "data" / "derived"
            plots = {
                "forest": viz_dir / "forest_plot.png",
                "funnel": viz_dir / "funnel_plot.png",
                "correlation": viz_dir / "correlation_summary.png"
            }
            
            run_visualization_analysis(meta_results_path, plots)
            
            # Validate plots (T031)
            validation_report = validate_generated_plots(plots)
            if validation_report.get("overall_status") == "fail":
                logger.error("Plot validation failed. Triggering regeneration (T027d).")
                # Regeneration logic would be called here (T027d)
                # For now, we raise to stop pipeline if validation fails
                raise RuntimeError("Plot validation failed after generation.")
            
            results["metrics"]["visualizations"] = {k: str(v) for k, v in plots.items()}

        # 9. Final Output
        final_results_path = root / "data" / "derived" / "results.json"
        results["pipeline_end"] = datetime.now().isoformat()
        results["status"] = "completed"
        
        with open(final_results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Pipeline completed successfully. Final results saved to {final_results_path}")
        return results

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        results["status"] = "failed"
        results["error"] = str(e)
        results["pipeline_end"] = datetime.now().isoformat()
        raise

def main():
    parser = argparse.ArgumentParser(description="Run the Meta-Analysis Pipeline")
    parser.add_argument("--config", type=str, default="code/config/config.yaml", help="Path to config file")
    parser.add_argument("--mode", type=str, default="full", choices=["full", "validation"], help="Execution mode")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else None

    if args.mode == "validation":
        # Run quickstart validation
        run_pipeline_execution()
    else:
        run_pipeline(config)

if __name__ == "__main__":
    main()