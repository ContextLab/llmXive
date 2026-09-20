"""
Main entry point for the llmXive A2UI Latency Study pipeline.

Orchestrates the full research workflow:
1. Ingest raw data
2. Route/Classify intent
3. Simulate interactions with latency injection
4. Analyze results (stats, sensitivity, thresholds)
5. Generate visualizations and final report
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs, get_processed_data_path, get_annotated_data_path, get_figures_path
from data.ingest import load_dataset_from_hf, save_raw_csv, main as ingest_main
from data.annotate import interactive_annotation_loop, save_annotated_data, main as annotate_main
from models.router import load_router, run_inference, main as router_main
from simulation.runner import run_simulation, save_simulation_results, main as simulation_main
from analysis.stats import analyze_alignment_scores_by_density, save_fdr_analysis_report, main as stats_main
from analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report, main as sensitivity_main
from analysis.viz import plot_pareto_frontier, plot_alignment_by_density, main as viz_main
from analysis.threshold_finder import find_latency_threshold, main as threshold_main
from utils.logging import get_experiment_logger, log_experiment_start, log_experiment_end, log_metric, log_error
from utils.versioning import update_state_file

def run_full_pipeline(args):
    """
    Execute the full research pipeline end-to-end.
    """
    logger = get_experiment_logger("pipeline_main")
    log_experiment_start(logger, "Full A2UI Latency Study Pipeline")

    try:
        # 1. Setup & Directories
        ensure_dirs()
        logger.info("Directories initialized.")

        # 2. Ingest Data
        # Note: In a real run, we assume data/ingest.py has been run to create raw CSV.
        # If --reingest is passed, we force reload.
        if args.reingest:
            logger.info("Re-ingesting raw dataset...")
            # We call the internal function directly to avoid CLI parsing conflicts
            raw_df = load_dataset_from_hf(args.dataset_id, streaming=True)
            raw_path = get_processed_data_path("raw_a2ui.csv")
            save_raw_csv(raw_df, raw_path)
            logger.info(f"Raw data saved to {raw_path}")
        else:
            raw_path = get_processed_data_path("raw_a2ui.csv")
            if not raw_path.exists():
                raise FileNotFoundError(f"Raw data not found at {raw_path}. Run with --reingest or run code/data/ingest.py first.")
            logger.info(f"Using existing raw data: {raw_path}")

        # 3. Annotate (Simulated/CLI Step)
        # In CI or automated runs, we assume annotation is done or we use the placeholder logic if available.
        # For the purpose of this orchestration, we check for annotated data.
        annotated_path = get_annotated_data_path("annotated_turns.csv")
        if not annotated_path.exists():
            logger.warning(f"Annotated data not found at {annotated_path}.")
            logger.warning("Skipping annotation step. Ensure code/data/annotate_cli.py has been run or data is pre-labeled.")
            # In a real scenario, we might trigger the CLI here, but for script orchestration
            # we expect the file to exist or fail loudly.
            # To allow the pipeline to proceed for testing (if T015d-Gen was run), we proceed if it exists.
            if not annotated_path.exists():
                raise FileNotFoundError(f"Annotated data missing. Please run the annotation step first.")

        # 4. Train/Load Router
        # Check if model exists, if not, train it (or fail if training data missing)
        model_path = PROJECT_ROOT / "models" / "router_model"
        if not model_path.exists() or not any(model_path.glob("*.bin")):
            logger.info("Router model not found. Training required.")
            # We assume the training script (T019) is run separately or we call it here.
            # For strict orchestration, we expect the model to be present.
            # If we must train:
            # router_main(['--input', str(annotated_path), '--output', str(model_path)])
            # For now, we raise if missing to enforce the dependency order.
            raise FileNotFoundError(f"Router model not found at {model_path}. Run code/models/train_router.py first.")

        logger.info("Loading router model...")
        router = load_router(model_path)
        logger.info("Router loaded successfully.")

        # 5. Simulation
        logger.info("Starting simulation...")
        sim_results_path = PROJECT_ROOT / "data" / "simulation" / "results.csv"
        # Ensure parent dir exists
        sim_results_path.parent.mkdir(parents=True, exist_ok=True)

        # Run simulation
        # We pass the annotated path and the loaded router
        # Note: The runner expects to load data internally or we pass the dataframe.
        # Adjusting to the runner's expected interface based on the API surface.
        # Assuming runner takes a data path.
        run_simulation(
            input_path=str(annotated_path),
            output_path=str(sim_results_path),
            router=router,
            density_levels=[1, 3, 5, 10],
            latency_levels=[0, 500, 1000, 2000]
        )
        logger.info(f"Simulation results saved to {sim_results_path}")
        log_metric(logger, "simulation_rows", "count", "N/A", "Simulation completed")

        # 6. Analysis
        logger.info("Running statistical analysis...")
        stats_report_path = PROJECT_ROOT / "data" / "analysis" / "stats_report.json"
        stats_report_path.parent.mkdir(parents=True, exist_ok=True)

        # Run FDR analysis
        analyze_alignment_scores_by_density(str(sim_results_path), str(stats_report_path))
        logger.info(f"Stats report saved to {stats_report_path}")

        # 7. Sensitivity Analysis
        logger.info("Running sensitivity analysis...")
        sensitivity_report_path = PROJECT_ROOT / "data" / "analysis" / "sensitivity_report.json"
        run_sensitivity_analysis(str(sim_results_path), str(sensitivity_report_path), thresholds=[0.6, 0.7, 0.8])
        logger.info(f"Sensitivity report saved to {sensitivity_report_path}")

        # 8. Threshold Finding
        logger.info("Identifying latency threshold...")
        threshold_report_path = PROJECT_ROOT / "data" / "analysis" / "threshold_report.json"
        find_latency_threshold(str(stats_report_path), str(threshold_report_path))
        logger.info(f"Threshold report saved to {threshold_report_path}")

        # 9. Visualization
        logger.info("Generating visualizations...")
        figures_dir = get_figures_path()
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Pareto Frontier
        pareto_path = figures_dir / "pareto_frontier.png"
        plot_pareto_frontier(str(sim_results_path), str(pareto_path))
        logger.info(f"Pareto plot saved to {pareto_path}")

        # Alignment by Density
        density_path = figures_dir / "alignment_by_density.png"
        plot_alignment_by_density(str(sim_results_path), str(density_path))
        logger.info(f"Alignment plot saved to {density_path}")

        # 10. Final Report Generation (T039)
        logger.info("Generating final report...")
        report_path = PROJECT_ROOT / "output" / "report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate a markdown report summarizing the findings
        with open(report_path, "w") as f:
            f.write("# A2UI Latency Study Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Summary\n")
            f.write("The pipeline successfully processed the dataset, simulated interactions, and analyzed results.\n\n")
            f.write("## Key Findings\n")
            f.write(f"- Threshold Report: {threshold_report_path}\n")
            f.write(f"- Sensitivity Report: {sensitivity_report_path}\n")
            f.write(f"- Pareto Frontier: {pareto_path}\n")
            f.write(f"- Alignment by Density: {density_path}\n")
            f.write("\n## Conclusion\n")
            f.write("See individual reports for detailed statistical significance and threshold identification.\n")

        logger.info(f"Final report saved to {report_path}")
        log_experiment_end(logger, "Pipeline completed successfully")

        return True

    except Exception as e:
        log_error(logger, f"Pipeline failed: {str(e)}")
        logger.exception("Traceback:")
        return False

def main():
    parser = argparse.ArgumentParser(description="Orchestrate the full A2UI Latency Study pipeline.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--reingest", action="store_true", help="Force re-ingestion of raw dataset")
    parser.add_argument("--dataset-id", type=str, default="macaron-data/a2ui-bench", help="HuggingFace dataset ID")

    args = parser.parse_args()

    success = run_full_pipeline(args)

    if not success:
        sys.exit(1)
    else:
        print("Pipeline completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()