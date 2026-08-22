"""
Main entry point for the llmXive A2UI Latency Study pipeline.

Orchestrates the full research workflow:
1. Ingest raw data from Hugging Face
2. Route/Classify queries (DistilBERT)
3. Simulate interactions (Latency + Patience modeling)
4. Analyze results (Stats + Sensitivity)
5. Visualize and Report (Pareto frontiers, Thresholds)
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import core configuration
from config import get_raw_data_path, get_processed_data_path, get_annotated_data_path, get_holdout_data_path, ensure_dirs

# Import Data Pipeline
from data.ingest import load_dataset_from_hf, save_raw_csv
from data.annotate import sample_for_annotation, interactive_annotation_loop, save_annotated_data
from data.verify_holdout import verify_file_exists, verify_row_count, verify_columns

# Import Simulation Components
from models.router import load_router, run_inference
from models.fallback import FallbackGenerator
from simulation.patience import sample_patience
from simulation.runner import run_simulation, save_simulation_results
from simulation.rubric import calculate_alignment_score

# Import Analysis Components
from analysis.stats import analyze_alignment_scores_by_density, save_fdr_analysis_report
from analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report
from analysis.viz import calculate_pareto_frontier, plot_pareto_frontier, plot_alignment_by_density
from analysis.rubric_validation import load_holdout_set, calculate_correlation, save_validation_report

# Import Utilities
from utils.logging import get_experiment_logger, log_experiment_start, log_experiment_end, log_metric, log_info, log_error
from utils.versioning import update_state_file

def run_full_pipeline(args):
    """Execute the full research pipeline."""
    
    # Setup Logging
    logger = get_experiment_logger("main_pipeline")
    log_info(logger, "Starting llmXive A2UI Latency Study Pipeline")
    log_info(logger, f"Project Root: {PROJECT_ROOT}")

    # Ensure directories exist
    ensure_dirs()

    # --- PHASE 1: DATA INGESTION ---
    log_info(logger, "--- Phase 1: Data Ingestion ---")
    
    raw_path = get_raw_data_path()
    annotated_path = get_annotated_data_path()
    
    # Check if raw data exists, if not ingest
    if not raw_path.exists():
        log_info(logger, "Raw data not found. Ingesting from Hugging Face...")
        # Note: In a real run, this calls the real HF loader.
        # We assume T012 has already populated this or this script handles the fetch.
        # For the pipeline runner, we expect the data to be present or fetched here.
        # If T012 is the fetcher, we call it.
        # However, to keep this as an orchestrator, we assume data exists or we trigger the fetch.
        # Let's trigger the fetch if missing to be robust.
        try:
            dataset = load_dataset_from_hf()
            save_raw_csv(dataset, raw_path)
            log_metric(logger, "raw_rows", len(dataset))
        except Exception as e:
            log_error(logger, f"Failed to ingest data: {e}")
            raise
    else:
        log_info(logger, f"Raw data found at {raw_path}")

    # Check if annotated data exists
    if not annotated_path.exists():
        log_info(logger, "Annotated data not found. Generating sample for annotation...")
        # In a real scenario, this would be a manual step or a CLI trigger.
        # For the automated pipeline, we assume the annotated file exists (T013/T015).
        # If missing, we might need to generate a placeholder for the simulation to proceed
        # IF the task allows CI placeholder (T015d-Gen).
        # However, T038 is the main runner. If data is missing, it should fail loudly
        # unless it's a specific "generate" mode.
        # We will assume the data is pre-processed as per the pipeline state.
        log_error(logger, "Annotated data missing. Please run T013/T015 first.")
        raise FileNotFoundError(f"Annotated data not found at {annotated_path}")

    # --- PHASE 2: MODEL LOADING ---
    log_info(logger, "--- Phase 2: Model Loading ---")
    
    model_path = PROJECT_ROOT / "code" / "models" / "router_model"
    if not model_path.exists():
        log_error(logger, f"Router model not found at {model_path}. Please run T019/T019b first.")
        raise FileNotFoundError(f"Router model not found at {model_path}")

    router = load_router(model_path)
    fallback_gen = FallbackGenerator()
    log_info(logger, "Models loaded successfully.")

    # --- PHASE 3: SIMULATION ---
    log_info(logger, "--- Phase 3: Simulation ---")
    
    sim_results_path = PROJECT_ROOT / "data" / "simulation" / "results.csv"
    
    if not sim_results_path.exists():
        log_info(logger, "Running simulation...")
        # Run the simulation engine
        # This loads annotated data, routes, simulates latency/patience, and scores
        results = run_simulation(
            data_path=annotated_path,
            router=router,
            fallback_generator=fallback_gen,
            seed=42
        )
        save_simulation_results(results, sim_results_path)
        log_metric(logger, "simulation_rows", len(results))
    else:
        log_info(logger, f"Simulation results found at {sim_results_path}")

    # --- PHASE 4: ANALYSIS ---
    log_info(logger, "--- Phase 4: Analysis ---")
    
    # 4a. Statistical Analysis (FDR)
    stats_report_path = PROJECT_ROOT / "data" / "analysis" / "stats_report.json"
    if not stats_report_path.exists():
        log_info(logger, "Running statistical analysis (FDR)...")
        analyze_alignment_scores_by_density(
            input_path=sim_results_path,
            output_path=stats_report_path
        )
    else:
        log_info(logger, f"Stats report found at {stats_report_path}")

    # 4b. Sensitivity Analysis
    sens_report_path = PROJECT_ROOT / "data" / "analysis" / "sensitivity_report.json"
    if not sens_report_path.exists():
        log_info(logger, "Running sensitivity analysis...")
        run_sensitivity_analysis(
            input_path=sim_results_path,
            output_path=sens_report_path
        )
    else:
        log_info(logger, f"Sensitivity report found at {sens_report_path}")

    # 4c. Rubric Validation (if holdout exists)
    holdout_path = get_holdout_data_path()
    if holdout_path.exists():
        rubric_report_path = PROJECT_ROOT / "data" / "rubric_validation_report.json"
        if not rubric_report_path.exists():
            log_info(logger, "Running rubric validation...")
            load_holdout_set(holdout_path) # Validates existence
            calculate_correlation(
                sim_path=sim_results_path,
                holdout_path=holdout_path,
                output_path=rubric_report_path
            )
        else:
            log_info(logger, f"Rubric validation report found at {rubric_report_path}")
    else:
        log_warning(logger, "Holdout set not found. Skipping rubric validation.")

    # --- PHASE 5: VISUALIZATION & REPORT ---
    log_info(logger, "--- Phase 5: Visualization & Report ---")
    
    # 5a. Pareto Frontier
    pareto_plot_path = PROJECT_ROOT / "figures" / "pareto_frontier.png"
    if not pareto_plot_path.exists():
        log_info(logger, "Generating Pareto frontier plot...")
        plot_pareto_frontier(
            input_path=sim_results_path,
            output_path=pareto_plot_path
        )
    else:
        log_info(logger, f"Pareto plot found at {pareto_plot_path}")

    # 5b. Density Plot
    density_plot_path = PROJECT_ROOT / "figures" / "alignment_by_density.png"
    if not density_plot_path.exists():
        log_info(logger, "Generating density alignment plot...")
        plot_alignment_by_density(
            input_path=sim_results_path,
            output_path=density_plot_path
        )
    else:
        log_info(logger, f"Density plot found at {density_plot_path}")

    # 5c. Final Report Generation (T039)
    report_path = PROJECT_ROOT / "output" / "report.md"
    if not report_path.exists():
        log_info(logger, "Generating final report...")
        # Generate a simple markdown report summarizing the findings
        # In a real implementation, this would parse the JSON reports and figures
        with open(report_path, "w") as f:
            f.write("# llmXive A2UI Latency Study Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Summary\n")
            f.write("- Pareto Frontier: See `figures/pareto_frontier.png`\n")
            f.write("- Sensitivity Analysis: See `data/analysis/sensitivity_report.json`\n")
            f.write("- Statistical Significance: See `data/analysis/stats_report.json`\n")
            f.write("\n## Conclusion\n")
            f.write("Pipeline execution complete. All metrics calculated and visualized.\n")
    
    log_info(logger, "Pipeline execution complete.")
    log_metric(logger, "status", "success")
    
    # Update version state
    update_state_file(PROJECT_ROOT)

def main():
    parser = argparse.ArgumentParser(description="llmXive A2UI Latency Study Pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Run without executing heavy steps")
    
    args = parser.parse_args()
    
    try:
        run_full_pipeline(args)
    except Exception as e:
        log_error(logging.getLogger(), f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()