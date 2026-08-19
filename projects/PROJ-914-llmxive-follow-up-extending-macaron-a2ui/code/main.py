"""
Main entry point for the llmXive A2UI Latency Study pipeline.

Orchestrates the full workflow:
1. Ingest: Fetch raw A2UI-Bench data
2. Route: Train and load the DistilBERT router
3. Simulate: Run latency-injected simulations with patience modeling
4. Analyze: Compute alignment scores, FDR correction, Pareto frontiers
5. Report: Generate final plots and validation reports
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_raw_data_path, get_processed_data_path, get_annotated_data_path, get_holdout_data_path, get_figures_path, ensure_dirs
from utils.logging import get_experiment_logger, log_experiment_start, log_experiment_end, log_metric, log_error, log_info, log_warning, log_debug
from utils.versioning import compute_version_state, update_state_file
from data.ingest import load_dataset_from_hf, validate_dataframe, save_raw_csv
from data.annotate import load_raw_data, sample_for_annotation, interactive_annotation_loop, save_annotated_data
from data.annotate_holdout import sample_holdout_set, save_holdout_set
from models.train_router import load_annotated_data, tokenize_data, train_model
from simulation.runner import run_simulation
from simulation.metrics import load_simulation_results, aggregate_metrics_by_density, save_metrics_report
from simulation.rubric import calculate_alignment_score
from analysis.stats import benjamini_hochberg_fdr, analyze_alignment_scores_by_density, find_latency_threshold, save_fdr_analysis_report
from analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report
from analysis.viz import calculate_pareto_frontier, plot_pareto_frontier, plot_alignment_by_density
from analysis.rubric_validation import load_holdout_set, simulate_rubric_scoring, calculate_correlation, validate_correlation, save_validation_report

def run_full_pipeline(args):
    """Execute the full research pipeline."""
    logger = get_experiment_logger("pipeline_run")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log_info(logger, f"Starting pipeline run: {run_id}")
    log_info(logger, f"Arguments: {vars(args)}")

    # Ensure directories exist
    ensure_dirs()
    log_debug(logger, "Ensured all required directories exist")

    # --- PHASE 1: INGEST ---
    log_info(logger, "--- PHASE 1: DATA INGESTION ---")
    raw_path = get_raw_data_path()
    
    if not args.skip_ingest:
        try:
            dataset = load_dataset_from_hf(args.dataset_id)
            if validate_dataframe(dataset):
                save_raw_csv(dataset, raw_path)
                log_metric(logger, "ingest_rows", len(dataset))
                log_info(logger, f"Successfully ingested data to {raw_path}")
            else:
                log_error(logger, "Data validation failed. Aborting.")
                return False
        except Exception as e:
            log_error(logger, f"Failed to ingest data: {str(e)}")
            raise
    else:
        log_info(logger, "Skipping ingestion (assumes raw data exists)")

    # --- PHASE 2: ANNOTATION (Simulated for automation) ---
    log_info(logger, "--- PHASE 2: DATA PREPARATION ---")
    annotated_path = get_annotated_data_path()
    holdout_path = get_holdout_data_path()

    if not args.skip_annotation:
        # In a real scenario, this would be manual. For the pipeline, we assume
        # T012b has produced the file, or we simulate the sampling step if raw exists.
        if os.path.exists(raw_path) and not os.path.exists(annotated_path):
            log_warning(logger, "Raw data exists but annotated data missing. Running sampling step (simulating annotation).")
            raw_df = load_raw_data(raw_path)
            sampled_df = sample_for_annotation(raw_df, args.sample_size)
            save_annotated_data(sampled_df, annotated_path)
            log_info(logger, f"Created annotated dataset at {annotated_path}")
        elif os.path.exists(annotated_path):
            log_info(logger, "Using existing annotated data")
        else:
            log_error(logger, "No annotated data found and raw data missing or skipped.")
            return False

        if not os.path.exists(holdout_path) and os.path.exists(raw_path):
            log_info(logger, "Creating hold-out set...")
            sample_holdout_set(raw_path, holdout_path, args.holdout_size)
            log_info(logger, f"Created hold-out set at {holdout_path}")
        elif os.path.exists(holdout_path):
            log_info(logger, "Using existing hold-out set")
    else:
        log_info(logger, "Skipping annotation steps")

    # --- PHASE 3: ROUTER TRAINING ---
    log_info(logger, "--- PHASE 3: ROUTER TRAINING ---")
    model_path = project_root / "code" / "models" / "router_model"
    
    if not args.skip_train:
        if os.path.exists(annotated_path):
            log_info(logger, f"Training router on {annotated_path}...")
            train_model(annotated_path, str(model_path))
            log_metric(logger, "router_trained", 1)
            log_info(logger, "Router training complete")
        else:
            log_error(logger, "Cannot train router: annotated data missing.")
            return False
    else:
        log_info(logger, "Skipping training (assumes model exists)")

    # --- PHASE 4: SIMULATION ---
    log_info(logger, "--- PHASE 4: SIMULATION ---")
    if not args.skip_simulate:
        log_info(logger, "Running simulation...")
        # Density levels from T025: {1, 3, 5, 10}
        density_levels = [1, 3, 5, 10]
        run_simulation(
            data_path=annotated_path,
            model_path=str(model_path),
            densities=density_levels,
            patience_mean=2.0
        )
        log_metric(logger, "simulation_complete", 1)
        log_info(logger, "Simulation complete")
    else:
        log_info(logger, "Skipping simulation")

    # --- PHASE 5: ANALYSIS ---
    log_info(logger, "--- PHASE 5: ANALYSIS ---")
    
    # 5.1 Metrics Aggregation
    metrics_report_path = project_root / "data" / "metrics_report.json"
    if os.path.exists(project_root / "data" / "simulation_results.jsonl"):
        log_info(logger, "Aggregating metrics...")
        aggregate_metrics_by_density(
            input_path=str(project_root / "data" / "simulation_results.jsonl"),
            output_path=str(metrics_report_path)
        )
        log_info(logger, f"Metrics report saved to {metrics_report_path}")
    else:
        log_warning(logger, "No simulation results found. Skipping metrics aggregation.")

    # 5.2 Statistical Analysis (FDR)
    fdr_report_path = project_root / "data" / "fdr_analysis.json"
    if os.path.exists(metrics_report_path):
        log_info(logger, "Running FDR analysis...")
        save_fdr_analysis_report(
            metrics_path=str(metrics_report_path),
            output_path=str(fdr_report_path)
        )
        log_info(logger, f"FDR report saved to {fdr_report_path}")
    else:
        log_warning(logger, "No metrics report found. Skipping FDR analysis.")

    # 5.3 Sensitivity Analysis
    sensitivity_report_path = project_root / "data" / "sensitivity_analysis.json"
    if os.path.exists(metrics_report_path):
        log_info(logger, "Running sensitivity analysis...")
        save_sensitivity_report(
            metrics_path=str(metrics_report_path),
            output_path=str(sensitivity_report_path)
        )
        log_info(logger, f"Sensitivity report saved to {sensitivity_report_path}")
    else:
        log_warning(logger, "No metrics report found. Skipping sensitivity analysis.")

    # 5.4 Rubric Validation
    validation_report_path = project_root / "data" / "rubric_validation.json"
    if os.path.exists(holdout_path) and os.path.exists(metrics_report_path):
        log_info(logger, "Validating rubric against hold-out set...")
        save_validation_report(
            holdout_path=str(holdout_path),
            metrics_path=str(metrics_report_path),
            output_path=str(validation_report_path)
        )
        log_info(logger, f"Validation report saved to {validation_report_path}")
    else:
        log_warning(logger, "Missing hold-out or metrics data. Skipping rubric validation.")

    # --- PHASE 6: VISUALIZATION & REPORTING ---
    log_info(logger, "--- PHASE 6: VISUALIZATION & REPORTING ---")
    figures_path = get_figures_path()
    
    if os.path.exists(metrics_report_path):
        # Pareto Frontier
        pareto_fig = figures_path / "pareto_frontier.png"
        log_info(logger, f"Generating Pareto frontier plot: {pareto_fig}")
        plot_pareto_frontier(
            metrics_path=str(metrics_report_path),
            output_path=str(pareto_fig)
        )
        
        # Alignment by Density
        density_fig = figures_path / "alignment_by_density.png"
        log_info(logger, f"Generating alignment by density plot: {density_fig}")
        plot_alignment_by_density(
            metrics_path=str(metrics_report_path),
            output_path=str(density_fig)
        )
        
        log_metric(logger, "figures_generated", 2)
        log_info(logger, "Visualization complete")
    else:
        log_warning(logger, "No metrics report found. Skipping visualization.")

    # --- FINALIZE ---
    log_info(logger, "--- PIPELINE COMPLETE ---")
    log_experiment_end(logger, status="success")
    
    # Update version state
    compute_version_state()
    update_state_file()
    
    return True

def main():
    parser = argparse.ArgumentParser(description="llmXive A2UI Latency Study Pipeline")
    parser.add_argument("--dataset-id", type=str, default="macaron-data/a2ui-bench", help="HuggingFace dataset ID")
    parser.add_argument("--sample-size", type=int, default=500, help="Number of samples to annotate")
    parser.add_argument("--holdout-size", type=int, default=50, help="Number of samples for hold-out set")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip data ingestion")
    parser.add_argument("--skip-annotation", action="store_true", help="Skip annotation steps")
    parser.add_argument("--skip-train", action="store_true", help="Skip router training")
    parser.add_argument("--skip-simulate", action="store_true", help="Skip simulation")
    
    args = parser.parse_args()
    
    success = run_full_pipeline(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()