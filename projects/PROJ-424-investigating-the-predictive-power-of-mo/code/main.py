"""
Main pipeline entry point for the MD Diffusion Predictive Power investigation.

Orchestrates the full workflow:
1. Topology generation (T014)
2. Simulation execution (T015)
3. MSD extraction & Diffusion calculation (T016)
4. MAE calculation against NIST refs
5. Plotting (T017)

Implements T018: Orchestration of the full pipeline.
"""
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import configuration and data models
from config import Solvent, SimulationConfig, AnalysisConfig
from utils.logging import setup_logger, get_logger, log_event
from utils.data_fetcher import validate_nist_refs
from utils.checksums import calculate_sha256
from simulation.topology import generate_topology, TopologyConfig
from simulation.runner import run_simulation, load_topology_files
from analysis.msd import analyze_msd, load_trajectory_timeseries, perform_linear_regression, calculate_diffusion_coefficient, validate_linearity
from reporting.plots import generate_timescale_accuracy_plot, load_diffusion_results, PlotConfig

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_nist_references() -> Dict[str, float]:
    """
    Load experimental diffusion coefficients from the curated NIST references file.
    
    Returns:
        Dict mapping solvent names to diffusion coefficients (m²/s)
        
    Raises:
        FileNotFoundError: If nist_refs.json is missing
        ValueError: If file format is invalid
    """
    nist_file = DATA_RAW_DIR / "nist_refs.json"
    
    # Validate existence and checksum before loading
    try:
        validate_nist_refs()
    except Exception as e:
        logger = get_logger()
        logger.error(f"NIST references validation failed: {e}")
        raise
    
    logger = get_logger()
    logger.info(f"Loading NIST references from {nist_file}")
    
    import json
    with open(nist_file, 'r') as f:
        data = json.load(f)
    
    # Extract diffusion coefficients
    refs = {}
    for solvent_name, solvent_data in data.items():
        if 'diffusion_coefficient' in solvent_data:
            refs[solvent_name] = solvent_data['diffusion_coefficient']
        else:
            logger.warning(f"Missing diffusion_coefficient for {solvent_name}, skipping")
    
    if not refs:
        raise ValueError("No valid diffusion coefficients found in NIST references")
        
    return refs

def calculate_mae(predicted: Dict[str, float], actual: Dict[str, float]) -> float:
    """
    Calculate Mean Absolute Error between predicted and actual diffusion coefficients.
    
    Args:
        predicted: Dict of solvent -> predicted D (m²/s)
        actual: Dict of solvent -> actual D (m²/s)
        
    Returns:
        MAE value (m²/s)
    """
    errors = []
    for solvent in actual:
        if solvent in predicted:
            error = abs(predicted[solvent] - actual[solvent])
            errors.append(error)
        else:
            logger = get_logger()
            logger.warning(f"Missing prediction for {solvent}, skipping in MAE calculation")
    
    if not errors:
        return float('nan')
        
    return sum(errors) / len(errors)

def run_single_solvent_pipeline(
    solvent: Solvent,
    timescale: str,
    simulation_config: SimulationConfig,
    analysis_config: AnalysisConfig,
    nist_refs: Dict[str, float]
) -> Optional[Dict[str, Any]]:
    """
    Run the full pipeline for a single solvent and timescale.
    
    Args:
        solvent: Solvent to simulate
        timescale: Simulation duration (e.g., "1ns", "5ns")
        simulation_config: Configuration for simulation
        analysis_config: Configuration for analysis
        nist_refs: Reference diffusion coefficients
        
    Returns:
        Dictionary with results or None if pipeline fails
    """
    logger = get_logger()
    logger.info(f"Starting pipeline for {solvent.value} at {timescale}")
    
    try:
        # Step 1: Generate Topology
        logger.info(f"Generating topology for {solvent.value}")
        topology_config = TopologyConfig(
            solvent=solvent,
            timescale=timescale,
            force_field=simulation_config.force_field
        )
        topology_files = generate_topology(topology_config)
        
        if not topology_files or not all(f.exists() for f in topology_files.values()):
            logger.error(f"Topology generation failed for {solvent.value}")
            return None
        
        # Step 2: Run Simulation
        logger.info(f"Running simulation for {solvent.value} at {timescale}")
        sim_result = run_simulation(
            topology_files=topology_files,
            config=simulation_config,
            timescale=timescale
        )
        
        if not sim_result.success:
            logger.error(f"Simulation failed for {solvent.value}: {sim_result.error_message}")
            return None
        
        # Step 3: MSD Extraction and Diffusion Calculation
        logger.info(f"Analyzing MSD for {solvent.value}")
        msd_result = analyze_msd(
            trajectory_path=sim_result.trajectory_path,
            config=analysis_config
        )
        
        if not msd_result.is_valid:
            logger.error(f"MSD analysis failed for {solvent.value}: {msd_result.error_message}")
            return None
        
        # Step 4: Compare to NIST and calculate MAE
        predicted_d = msd_result.diffusion_coefficient
        solvent_name = solvent.value.lower()
        
        if solvent_name not in nist_refs:
            logger.warning(f"No NIST reference for {solvent_name}, skipping MAE calculation")
            return {
                "solvent": solvent_name,
                "timescale": timescale,
                "predicted_d": predicted_d,
                "actual_d": None,
                "mae": None,
                "r_squared": msd_result.r_squared
            }
        
        actual_d = nist_refs[solvent_name]
        mae = abs(predicted_d - actual_d)
        
        logger.info(
            f"{solvent.value} ({timescale}): Predicted D={predicted_d:.2e}, "
            f"Actual D={actual_d:.2e}, MAE={mae:.2e}, R²={msd_result.r_squared:.3f}"
        )
        
        return {
            "solvent": solvent_name,
            "timescale": timescale,
            "predicted_d": predicted_d,
            "actual_d": actual_d,
            "mae": mae,
            "r_squared": msd_result.r_squared,
            "simulation_time": sim_result.simulation_time
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed for {solvent.value} at {timescale}: {str(e)}", exc_info=True)
        return None

def run_pipeline(
    solvents: List[Solvent],
    timescales: List[str],
    simulation_config: SimulationConfig,
    analysis_config: AnalysisConfig
) -> List[Dict[str, Any]]:
    """
    Run the full pipeline for all solvent-timescale combinations.
    
    Args:
        solvents: List of solvents to simulate
        timescales: List of simulation durations
        simulation_config: Simulation configuration
        analysis_config: Analysis configuration
        
    Returns:
        List of result dictionaries
    """
    logger = get_logger()
    logger.info("Starting full pipeline execution")
    
    # Validate NIST references
    nist_refs = load_nist_references()
    logger.info(f"Loaded {len(nist_refs)} NIST references")
    
    results = []
    total_combinations = len(solvents) * len(timescales)
    completed = 0
    
    for solvent in solvents:
        for timescale in timescales:
            result = run_single_solvent_pipeline(
                solvent=solvent,
                timescale=timescale,
                simulation_config=simulation_config,
                analysis_config=analysis_config,
                nist_refs=nist_refs
            )
            
            if result:
                results.append(result)
                completed += 1
            
            logger.info(f"Progress: {completed}/{total_combinations} combinations completed")
    
    # Save results
    results_file = DATA_PROCESSED_DIR / "pipeline_results.json"
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved pipeline results to {results_file}")
    
    # Calculate overall MAE
    valid_results = [r for r in results if r['mae'] is not None]
    if valid_results:
        overall_mae = calculate_mae(
            {r['solvent']: r['predicted_d'] for r in valid_results},
            {r['solvent']: r['actual_d'] for r in valid_results}
        )
        logger.info(f"Overall MAE across all solvents: {overall_mae:.2e} m²/s")
    else:
        logger.warning("No valid results for MAE calculation")
    
    return results

def generate_final_plots(results: List[Dict[str, Any]]):
    """
    Generate timescale-accuracy curves and multi-solvent comparison plots.
    
    Args:
        results: List of pipeline result dictionaries
    """
    logger = get_logger()
    logger.info("Generating final plots")
    
    if not results:
        logger.warning("No results to plot")
        return
    
    # Generate timescale-accuracy plot
    plot_config = PlotConfig(
        output_dir=FIGURES_DIR,
        style='seaborn-v0_8-whitegrid',
        dpi=300
    )
    
    try:
        generate_timescale_accuracy_plot(results, plot_config)
        logger.info("Timescale-accuracy plot generated")
    except Exception as e:
        logger.error(f"Failed to generate timescale-accuracy plot: {e}", exc_info=True)
    
    try:
        generate_multi_solvent_comparison(results, plot_config)
        logger.info("Multi-solvent comparison plot generated")
    except Exception as e:
        logger.error(f"Failed to generate multi-solvent comparison plot: {e}", exc_info=True)

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="MD Diffusion Predictive Power Pipeline"
    )
    parser.add_argument(
        "--solvents",
        type=str,
        nargs='+',
        default=['water', 'ethanol', 'acetone'],
        help="Solvents to simulate"
    )
    parser.add_argument(
        "--timescales",
        type=str,
        nargs='+',
        default=['1ns', '5ns', '10ns'],
        help="Simulation timescales"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = LOGS_DIR / f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_logger(
        level=args.log_level.upper(),
        log_file=log_file
    )
    
    logger.info("Starting MD Diffusion Predictive Power Pipeline")
    logger.info(f"Solvents: {args.solvents}")
    logger.info(f"Timescales: {args.timescales}")
    
    try:
        # Parse solvents
        solvent_map = {s.value.lower(): s for s in Solvent}
        selected_solvents = []
        for s_name in args.solvents:
            if s_name.lower() in solvent_map:
                selected_solvents.append(solvent_map[s_name.lower()])
            else:
                logger.warning(f"Unknown solvent {s_name}, skipping")
        
        if not selected_solvents:
            logger.error("No valid solvents specified")
            sys.exit(1)
        
        # Configuration
        simulation_config = SimulationConfig(
            force_field="MARTINI",
            temperature=300,
            pressure=1.0,
            time_step=0.02,  # 20 fs
            max_runtime=21600  # 6 hours in seconds
        )
        
        analysis_config = AnalysisConfig(
            r_squared_threshold=0.95,
            scaling_factors={
                "water": 1.0,
                "ethanol": 1.0,
                "acetone": 1.0
            }
        )
        
        # Run pipeline
        results = run_pipeline(
            solvents=selected_solvents,
            timescales=args.timescales,
            simulation_config=simulation_config,
            analysis_config=analysis_config
        )
        
        # Generate plots
        generate_final_plots(results)
        
        logger.info("Pipeline completed successfully")
        
        # Log summary
        logger.info(f"Total combinations processed: {len(results)}")
        valid_count = sum(1 for r in results if r['mae'] is not None)
        logger.info(f"Successful MAE calculations: {valid_count}/{len(results)}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()