"""
Metrics calculation module for the llmXive research pipeline.

Calculates success rates, wall-clock time, and energy consumption from execution logs.
"""
import json
import os
import math
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Import config to access DEFAULT_TDP_WATTS
# We use a dynamic import pattern to avoid circular imports if config imports metrics
# However, based on the API surface, config.py is a standalone module.
try:
    from code.config import load_config, DEFAULT_TDP_WATTS
except ImportError:
    # Fallback if direct import fails, we will load from the JSON calibration file directly
    DEFAULT_TDP_WATTS = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExperimentMetrics:
    """Container for calculated experiment metrics."""
    puzzle_id: str
    success: bool
    wall_clock_seconds: float
    energy_joules: float
    cpu_percent: float
    complexity_n: int
    timestamp: str

def load_calibrated_tdp() -> float:
    """
    Load the TDP value from the calibration output file.
    
    Returns:
        float: The TDP in Watts.
        
    Raises:
        FileNotFoundError: If the calibration file is missing.
        ValueError: If the file exists but contains invalid data.
    """
    calibration_path = Path("data/processed/calibrated_tdp.json")
    
    if not calibration_path.exists():
        raise FileNotFoundError(
            f"Calibration file not found: {calibration_path}. "
            "Please run T007c (calibrate_tdp.py) to generate this file before running metrics analysis."
        )
    
    try:
        with open(calibration_path, 'r') as f:
            data = json.load(f)
        
        if 'tdp_watts' not in data:
            raise ValueError("Calibration file missing 'tdp_watts' field.")
        
        tdp = float(data['tdp_watts'])
        if tdp <= 0:
            raise ValueError(f"TDP value must be positive, got {tdp}")
        
        logger.info(f"Loaded TDP: {tdp} W from {calibration_path}")
        return tdp
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in calibration file: {e}")

def load_experiment_logs(log_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load experiment logs from the specified path or default location.
    
    Args:
        log_path: Path to the log file. Defaults to data/processed/experiment.log
        
    Returns:
        List of log entries.
    """
    if log_path is None:
        log_path = Path("data/processed/experiment.log")
        
    if not log_path.exists():
        raise FileNotFoundError(f"Experiment log not found: {log_path}")
        
    logs = []
    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                logs.append(entry)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                
    return logs

def load_gpu_conversion_factor() -> float:
    """
    Load the GPU conversion factor for estimating GPU-hours.
    
    Returns:
        float: The conversion factor.
    """
    factor_path = Path("data/processed/literature_gpu_factor.json")
    if factor_path.exists():
        with open(factor_path, 'r') as f:
            data = json.load(f)
            return float(data.get('factor', 0.0015))
    else:
        # Fallback to hardcoded value with warning as per T040a
        logger.warning("literature_gpu_factor.json not found. Using default 0.0015.")
        return 0.0015

def calculate_metrics_from_logs(logs: List[Dict[str, Any]]) -> List[ExperimentMetrics]:
    """
    Calculate metrics from raw experiment logs.
    
    Args:
        logs: List of log entries from load_experiment_logs.
        
    Returns:
        List of ExperimentMetrics objects.
        
    Note:
        This function implements the energy formula:
        E = DEFAULT_TDP_WATTS * (cpu_percent / 100) * wall_clock
        
        It strictly fails if calibrated_tdp.json is missing (handled by load_calibrated_tdp).
    """
    # Load TDP first to ensure we fail loudly if missing
    tdp_watts = load_calibrated_tdp()
    
    metrics = []
    
    for entry in logs:
        # Extract fields
        puzzle_id = entry.get('puzzle_id', 'unknown')
        success = entry.get('success', False)
        wall_clock = float(entry.get('wall_clock_seconds', 0.0))
        cpu_percent = float(entry.get('cpu_percent', 0.0))
        complexity_n = int(entry.get('complexity_n', 0))
        timestamp = entry.get('timestamp', '')
        
        # Calculate Energy
        # Formula: E = TDP * (cpu_percent / 100) * wall_clock
        energy_joules = tdp_watts * (cpu_percent / 100.0) * wall_clock
        
        metric = ExperimentMetrics(
            puzzle_id=puzzle_id,
            success=success,
            wall_clock_seconds=wall_clock,
            energy_joules=energy_joules,
            cpu_percent=cpu_percent,
            complexity_n=complexity_n,
            timestamp=timestamp
        )
        metrics.append(metric)
        
    return metrics

def calculate_gpu_hours_estimated(energy_joules: float) -> float:
    """
    Estimate GPU-hours based on energy consumption and a conversion factor.
    
    Args:
        energy_joules: Energy consumed in Joules.
        
    Returns:
        float: Estimated GPU-hours.
    """
    factor = load_gpu_conversion_factor()
    # Conversion: Joules -> kWh -> GPU-hours (approximate based on factor)
    # factor is typically derived from literature (e.g., Green500)
    # Assuming factor represents Joules per GPU-hour or similar scaling
    # The exact formula depends on the factor definition in literature_gpu_factor.json
    # Assuming factor is a multiplier to convert Joules to GPU-hours
    return energy_joules * factor

def save_metrics_to_csv(metrics: List[ExperimentMetrics], output_path: Path) -> None:
    """
    Save calculated metrics to a CSV file.
    
    Args:
        metrics: List of ExperimentMetrics objects.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'puzzle_id', 'success', 'wall_clock_seconds', 'energy_joules',
            'cpu_percent', 'complexity_n', 'timestamp'
        ])
        
        for m in metrics:
            writer.writerow([
                m.puzzle_id, m.success, m.wall_clock_seconds, m.energy_joules,
                m.cpu_percent, m.complexity_n, m.timestamp
            ])
    
    logger.info(f"Saved metrics to {output_path}")

def perform_scaling_analysis(metrics: List[ExperimentMetrics]) -> Dict[str, Any]:
    """
    Perform simple scaling analysis on the metrics.
    
    Args:
        metrics: List of ExperimentMetrics.
        
    Returns:
        Dict containing scaling statistics.
    """
    if not metrics:
        return {"error": "No metrics provided"}
        
    # Group by complexity_n
    complexity_data = {}
    for m in metrics:
        n = m.complexity_n
        if n not in complexity_data:
            complexity_data[n] = {'times': [], 'energies': []}
        complexity_data[n]['times'].append(m.wall_clock_seconds)
        complexity_data[n]['energies'].append(m.energy_joules)
        
    # Calculate averages
    summary = []
    for n in sorted(complexity_data.keys()):
        data = complexity_data[n]
        avg_time = sum(data['times']) / len(data['times'])
        avg_energy = sum(data['energies']) / len(data['energies'])
        summary.append({
            'n': n,
            'avg_time': avg_time,
            'avg_energy': avg_energy,
            'count': len(data['times'])
        })
        
    return {
        'scaling_summary': summary,
        'total_puzzles': len(metrics),
        'success_rate': sum(1 for m in metrics if m.success) / len(metrics)
    }

def main():
    """Main entry point for the metrics calculation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate metrics from experiment logs")
    parser.add_argument(
        "--log-path", 
        type=str, 
        default="data/processed/experiment.log",
        help="Path to the experiment log file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/metrics.csv",
        help="Path to the output CSV file"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Loading logs from {args.log_path}")
        logs = load_experiment_logs(Path(args.log_path))
        
        logger.info(f"Processing {len(logs)} log entries")
        metrics = calculate_metrics_from_logs(logs)
        
        logger.info(f"Saving metrics to {args.output}")
        save_metrics_to_csv(metrics, Path(args.output))
        
        # Also print summary to stdout
        analysis = perform_scaling_analysis(metrics)
        print(json.dumps(analysis, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()