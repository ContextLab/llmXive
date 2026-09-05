"""
Sensitivity analysis for diffusion coefficient estimation.

Implements a sweep of regression start times to verify robustness of 
diffusion coefficient calculations against trajectory length variations.

Per T008c and US2: Uses concrete start times {0.1, 0.2, 0.3} of total 
trajectory length (replacing [deferred] placeholders).
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from datetime import datetime
import numpy as np

from config import Solvent, SimulationConfig, AnalysisConfig
from data_models.sensitivity_report import SensitivityPoint, SensitivityReport
from analysis.msd import analyze_msd, load_trajectory_timeseries
from utils.logging import get_logger

logger = get_logger(__name__)

# Concrete start time fractions as per T008c implementation
SENSITIVITY_START_FRACTIONS = [0.1, 0.2, 0.3]
VARIANCE_THRESHOLD = 0.05  # 5% variance threshold

def calculate_diffusion_at_start_time(
    trajectory_path: Path,
    total_length: float,
    start_fraction: float,
    config: AnalysisConfig
) -> Optional[float]:
    """
    Calculate diffusion coefficient starting from a specific fraction of the trajectory.
    
    Args:
        trajectory_path: Path to the trajectory file
        total_length: Total length of the trajectory in ns
        start_fraction: Fraction of trajectory to start analysis from (0.0-1.0)
        config: Analysis configuration parameters
        
    Returns:
        Diffusion coefficient in Å²/ns, or None if analysis fails
    """
    start_time = total_length * start_fraction
    logger.debug(f"Analyzing MSD from {start_time:.2f}ns ({start_fraction*100:.0f}% of trajectory)")
    
    try:
        # Load trajectory timeseries starting from the specified fraction
        timeseries = load_trajectory_timeseries(
            trajectory_path=trajectory_path,
            start_time=start_time,
            end_time=total_length
        )
        
        if timeseries is None or len(timeseries['times']) < 10:
            logger.warning(f"Insufficient data points for start fraction {start_fraction}")
            return None
        
        # Perform MSD analysis
        result = analyze_msd(
            times=timeseries['times'],
            msd_values=timeseries['msd_values'],
            config=config
        )
        
        if result is None or result.diffusion_coefficient is None:
            logger.warning(f"MSD analysis failed for start fraction {start_fraction}")
            return None
        
        return result.diffusion_coefficient
        
    except Exception as e:
        logger.error(f"Error calculating diffusion at {start_fraction*100:.0f}%: {e}")
        return None

def run_sensitivity_sweep(
    trajectory_path: Path,
    total_length: float,
    solvent: Solvent,
    timescale: str,
    config: AnalysisConfig
) -> SensitivityReport:
    """
    Run sensitivity analysis by sweeping regression start times.
    
    Args:
        trajectory_path: Path to the trajectory file
        total_length: Total trajectory length in ns
        solvent: Solvent type being analyzed
        timescale: Simulation timescale (e.g., '1ns', '5ns', '10ns')
        config: Analysis configuration
        
    Returns:
        SensitivityReport containing all sweep results
    """
    logger.info(f"Starting sensitivity sweep for {solvent.value} at {timescale}")
    
    points: List[SensitivityPoint] = []
    diffusion_values: List[float] = []
    
    for fraction in SENSITIVITY_START_FRACTIONS:
        d_value = calculate_diffusion_at_start_time(
            trajectory_path=trajectory_path,
            total_length=total_length,
            start_fraction=fraction,
            config=config
        )
        
        point = SensitivityPoint(
            start_fraction=fraction,
            start_time_ns=total_length * fraction,
            diffusion_coefficient=d_value,
            timestamp=datetime.now().isoformat()
        )
        points.append(point)
        
        if d_value is not None:
            diffusion_values.append(d_value)
    
    # Calculate variance if we have enough data points
    variance = None
    is_stable = False
    
    if len(diffusion_values) >= 2:
        mean_d = np.mean(diffusion_values)
        if mean_d > 0:
            variance = np.var(diffusion_values) / (mean_d ** 2)
            is_stable = variance <= VARIANCE_THRESHOLD
            logger.info(f"Sensitivity variance: {variance:.4f} (threshold: {VARIANCE_THRESHOLD})")
        else:
            logger.warning("Mean diffusion coefficient is zero, cannot calculate variance")
    else:
        logger.warning("Insufficient valid diffusion values to calculate variance")
    
    report = SensitivityReport(
        solvent=solvent.value,
        timescale=timescale,
        total_length_ns=total_length,
        sensitivity_points=points,
        variance=variance,
        is_stable=is_stable,
        threshold=VARIANCE_THRESHOLD,
        generated_at=datetime.now().isoformat()
    )
    
    logger.info(f"Sensitivity sweep complete for {solvent.value}: stable={is_stable}")
    return report

def save_sensitivity_report(
    report: SensitivityReport,
    output_path: Path
) -> None:
    """
    Save sensitivity report to JSON file.
    
    Args:
        report: SensitivityReport object to save
        output_path: Path for the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_dict = asdict(report)
    # Convert any non-serializable types
    for point in report_dict['sensitivity_points']:
        if point['diffusion_coefficient'] is not None:
            point['diffusion_coefficient'] = float(point['diffusion_coefficient'])
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")

def batch_sensitivity_analysis(
    trajectory_map: Dict[str, Path],
    config: AnalysisConfig
) -> List[SensitivityReport]:
    """
    Run sensitivity analysis on multiple trajectories.
    
    Args:
        trajectory_map: Dictionary mapping 'solvent_timescale' to trajectory path
        config: Analysis configuration
        
    Returns:
        List of SensitivityReport objects
    """
    reports = []
    
    for key, trajectory_path in trajectory_map.items():
        if not trajectory_path.exists():
            logger.warning(f"Trajectory not found: {trajectory_path}, skipping")
            continue
        
        # Parse key format: 'solvent_timescale' (e.g., 'water_1ns')
        parts = key.rsplit('_', 1)
        if len(parts) != 2:
            logger.error(f"Invalid key format: {key}, expected 'solvent_timescale'")
            continue
        
        solvent_str, timescale = parts
        
        try:
            solvent = Solvent(solvent_str)
        except ValueError:
            logger.error(f"Unknown solvent: {solvent_str}")
            continue
        
        # Extract total length from timescale (e.g., '10ns' -> 10.0)
        try:
            total_length = float(timescale.replace('ns', ''))
        except ValueError:
            logger.error(f"Invalid timescale format: {timescale}")
            continue
        
        report = run_sensitivity_sweep(
            trajectory_path=trajectory_path,
            total_length=total_length,
            solvent=solvent,
            timescale=timescale,
            config=config
        )
        
        reports.append(report)
        
        # Save individual report
        output_file = Path('data/processed') / f"sensitivity_{solvent_str}_{timescale}.json"
        save_sensitivity_report(report, output_file)
    
    return reports

def main():
    """Main entry point for sensitivity analysis."""
    logging.basicConfig(level=logging.INFO)
    
    from config import SimulationConfig, AnalysisConfig
    
    # Load configuration
    sim_config = SimulationConfig()
    analysis_config = AnalysisConfig()
    
    # Example usage - in production, this would load actual trajectory paths
    # from simulation outputs
    logger.info("Sensitivity analysis module loaded successfully")
    logger.info(f"Start fractions: {SENSITIVITY_START_FRACTIONS}")
    logger.info(f"Variance threshold: {VARIANCE_THRESHOLD}")
    
    # Note: This function is typically called from main.py pipeline
    # with actual trajectory paths from completed simulations

if __name__ == "__main__":
    main()