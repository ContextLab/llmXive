import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import Solvent, SimulationConfig, AnalysisConfig
from utils.logging import setup_logging, get_logger
from utils.data_fetcher import validate_nist_refs_exists
from simulation.topology import generate_topology
from simulation.runner import run_simulation
from analysis.msd import analyze_msd, batch_analyze_msd
from analysis.sensitivity import run_sensitivity_sweep, save_sensitivity_report
from reporting.plots import generate_timescale_accuracy_plot, generate_multi_solvent_comparison
import json
from datetime import datetime
import os

# Ensure we are running from the project root or code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

def load_nist_references() -> Dict[str, Dict[str, float]]:
    """Load the curated NIST references from data/raw/nist_refs.json."""
    validate_nist_refs_exists()
    nist_path = DATA_RAW_DIR / "nist_refs.json"
    with open(nist_path, 'r') as f:
        return json.load(f)

def calculate_mae(results: List[Dict[str, Any]], nist_refs: Dict[str, Dict[str, float]]) -> float:
    """Calculate Mean Absolute Error between calculated diffusion and NIST references."""
    errors = []
    for res in results:
        solvent = res.get('solvent')
        calculated_d = res.get('diffusion_coefficient')
        if solvent in nist_refs and 'D_exp' in nist_refs[solvent]:
            expected_d = nist_refs[solvent]['D_exp']
            errors.append(abs(calculated_d - expected_d))
    
    if not errors:
        return 0.0
    return sum(errors) / len(errors)

def run_pipeline(
    solvents: List[Solvent],
    timescales: List[float],
    config: SimulationConfig,
    analysis_config: AnalysisConfig
) -> Dict[str, Any]:
    """
    Run the full MD diffusion analysis pipeline.
    1. Generate topology
    2. Run simulation
    3. Analyze MSD -> Diffusion Coefficient
    4. Run Sensitivity Analysis (US2)
    5. Calculate MAE against NIST
    6. Generate Plots
    """
    logger = get_logger("main")
    results = []
    sensitivity_reports = []
    
    # Ensure output directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting pipeline for {len(solvents)} solvents and {len(timescales)} timescales.")

    for solvent in solvents:
        for ts_ns in timescales:
            ts_name = f"{int(ts_ns)}ns"
            logger.info(f"Processing {solvent.name} at {ts_name}.")
            
            # 1. Topology
            topo_config = config.topology_config
            topo_result = generate_topology(solvent, topo_config, ts_ns)
            if not topo_result.success:
                logger.error(f"Topology generation failed for {solvent.name}: {topo_result.message}")
                continue

            # 2. Simulation
            sim_result = run_simulation(topo_result, ts_ns, config)
            if not sim_result.success:
                logger.warning(f"Simulation failed or timed out for {solvent.name} at {ts_name}. Skipping MSD analysis.")
                continue

            # 3. MSD Analysis (Primary Analysis)
            msd_result = analyze_msd(
                trajectory_path=sim_result.trajectory_path,
                solvent=solvent,
                duration_ns=ts_ns,
                analysis_config=analysis_config
            )
            
            if not msd_result.is_valid:
                logger.warning(f"MSD analysis failed linearity check for {solvent.name} at {ts_name}.")
                # Still proceed to sensitivity if we have data, or skip if no valid MSD
                if msd_result.diffusion_coefficient is None:
                    continue

            # 4. Sensitivity Analysis (US2 Integration)
            # Runs after primary analysis for this solvent-timescale
            logger.info(f"Running sensitivity analysis for {solvent.name} at {ts_name}.")
            sens_report = run_sensitivity_sweep(
                trajectory_path=sim_result.trajectory_path,
                solvent=solvent,
                duration_ns=ts_ns,
                analysis_config=analysis_config,
                start_times=analysis_config.sensitivity_start_times
            )
            
            if sens_report:
                # Save individual sensitivity report
                report_path = DATA_PROCESSED_DIR / f"sensitivity_{solvent.name}_{ts_name}.json"
                save_sensitivity_report(sens_report, report_path)
                sensitivity_reports.append({
                    "solvent": solvent.name,
                    "timescale": ts_name,
                    "variance_percent": sens_report.variance_percent,
                    "stable": sens_report.variance_percent < 5.0
                })
                logger.info(f"Sensitivity variance for {solvent.name} {ts_name}: {sens_report.variance_percent:.2f}%")

            # Store primary result
            results.append({
                "solvent": solvent.name,
                "timescale": ts_name,
                "diffusion_coefficient": msd_result.diffusion_coefficient,
                "r_squared": msd_result.r_squared,
                "mae": None # Calculated later
            })

    # 5. Calculate MAE
    nist_refs = load_nist_references()
    for res in results:
        solvent = res["solvent"]
        if solvent in nist_refs:
            exp_d = nist_refs[solvent].get("D_exp")
            if exp_d:
                res["mae"] = abs(res["diffusion_coefficient"] - exp_d)
            else:
                res["mae"] = 0.0 # Or handle missing ref
        else:
            res["mae"] = 0.0

    # 6. Generate Plots
    logger.info("Generating timescale-accuracy plots.")
    plot_path = FIGURES_DIR / "timescale_accuracy_curves.png"
    generate_timescale_accuracy_plot(results, plot_path)
    
    multi_plot_path = FIGURES_DIR / "multi_solvent_comparison.png"
    generate_multi_solvent_comparison(results, multi_plot_path)

    # Save final results summary
    summary_path = DATA_PROCESSED_DIR / "pipeline_results_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "sensitivity_summary": sensitivity_reports
        }, f, indent=2)

    return {
        "results": results,
        "sensitivity_summary": sensitivity_reports,
        "summary_path": str(summary_path)
    }

def main():
    parser = argparse.ArgumentParser(description="MD Diffusion Predictive Power Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    # Setup Logging
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_file=log_dir / "main.log")
    logger = get_logger("main")

    logger.info("Pipeline initialization started.")

    # Load Configs (simplified for this implementation, assuming defaults if not fully parsed)
    # In a real scenario, we would parse args.config
    try:
        from config import SimulationConfig, AnalysisConfig, Solvent
        # Assuming defaults or loaded from a file not shown here, but structure is defined in config.py
        # We instantiate with typical values for the task
        solvents = [Solvent.WATER, Solvent.ETHANOL, Solvent.ACETONE]
        timescales = [1.0, 5.0, 10.0] # 1ns, 5ns, 10ns
        
        sim_cfg = SimulationConfig(
            force_field="MARTINI",
            timeout_seconds=3600,
            density_threshold=0.01,
            topology_config=None # Passed in generate_topology
        )
        
        # Sensitivity start times as defined in T021 (0.1, 0.2, 0.3)
        analysis_cfg = AnalysisConfig(
            r_squared_threshold=0.95,
            sensitivity_start_times=[0.1, 0.2, 0.3]
        )

        result = run_pipeline(solvents, timescales, sim_cfg, analysis_cfg)
        
        logger.info(f"Pipeline completed successfully. Results saved to {result['summary_path']}")
        
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()