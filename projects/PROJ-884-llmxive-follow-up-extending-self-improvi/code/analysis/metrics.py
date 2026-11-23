"""
Metrics calculation for the BES experiments.
Calculates success rates, wall-clock time, energy consumption, and GPU hours estimates.
"""
import json
import os
import math
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExperimentMetrics:
    """Container for calculated experiment metrics."""
    total_puzzles: int = 0
    successful_puzzles: int = 0
    success_rate: float = 0.0
    total_wall_clock_seconds: float = 0.0
    avg_wall_clock_seconds: float = 0.0
    total_energy_joules: float = 0.0
    avg_energy_joules: float = 0.0
    estimated_gpu_hours: float = 0.0
    calibration_source: Optional[str] = None
    gpu_conversion_factor: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_puzzles": self.total_puzzles,
            "successful_puzzles": self.successful_puzzles,
            "success_rate": self.success_rate,
            "total_wall_clock_seconds": self.total_wall_clock_seconds,
            "avg_wall_clock_seconds": self.avg_wall_clock_seconds,
            "total_energy_joules": self.total_energy_joules,
            "avg_energy_joules": self.avg_energy_joules,
            "estimated_gpu_hours": self.estimated_gpu_hours,
            "calibration_source": self.calibration_source,
            "gpu_conversion_factor": self.gpu_conversion_factor
        }

def load_calibrated_tdp(file_path: str = "data/processed/calibrated_tdp.json") -> Dict[str, Any]:
    """Load the calibrated TDP data."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Calibrated TDP file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'tdp_watts' not in data:
        raise ValueError(f"Calibrated TDP file missing 'tdp_watts' field: {file_path}")
    
    return data

def load_experiment_logs(file_path: str) -> List[Dict[str, Any]]:
    """Load experiment logs from a JSONL or JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Experiment log file not found: {file_path}")
    
    logs = []
    if path.suffix == '.jsonl':
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    logs.append(json.loads(line))
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                logs = data
            elif isinstance(data, dict) and 'logs' in data:
                logs = data['logs']
            else:
                logs = [data]
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return logs

def load_gpu_conversion_factor(file_path: str = "data/processed/literature_gpu_factor.json") -> float:
    """
    Load the literature-based GPU conversion factor.
    
    Constraint: This script MUST read `data/processed/literature_gpu_factor.json` 
    and verify that it is not zero before use.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is missing the 'conversion_factor' field or if the factor is zero.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GPU conversion factor file not found: {file_path}. "
                                "Please ensure T040b has been executed to generate this file.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'conversion_factor' not in data:
        raise ValueError(f"GPU conversion factor file missing 'conversion_factor' field: {file_path}")
    
    factor = data['conversion_factor']
    
    if not isinstance(factor, (int, float)):
        raise ValueError(f"GPU conversion factor must be a number, got {type(factor)}")
    
    if factor == 0:
        raise ValueError(f"GPU conversion factor cannot be zero. "
                         "This would result in zero energy estimates. "
                         "Please check the source file: {file_path}")
    
    logger.info(f"Loaded GPU conversion factor: {factor} from {file_path}")
    return float(factor)

def calculate_metrics_from_logs(logs: List[Dict[str, Any]], 
                                tdp_watts: float, 
                                gpu_factor: Optional[float] = None) -> ExperimentMetrics:
    """
    Calculate metrics from experiment logs.
    
    Args:
        logs: List of log entries from the experiment.
        tdp_watts: The calibrated TDP in watts.
        gpu_factor: Optional GPU conversion factor for estimating GPU hours.
        
    Returns:
        ExperimentMetrics object with calculated values.
    """
    metrics = ExperimentMetrics()
    metrics.total_puzzles = len(logs)
    
    if metrics.total_puzzles == 0:
        logger.warning("No logs provided, returning empty metrics.")
        return metrics
    
    successful = 0
    total_time = 0.0
    total_energy = 0.0
    
    for log in logs:
        # Check success
        if log.get('status') == 'success' or log.get('success', False):
            successful += 1
        
        # Extract time
        duration = log.get('duration_seconds', log.get('wall_clock_seconds', 0.0))
        if not isinstance(duration, (int, float)):
            logger.warning(f"Invalid duration in log: {duration}")
            duration = 0.0
        total_time += duration
        
        # Calculate energy: Energy (J) = Power (W) * Time (s)
        # We use the TDP as the power draw estimate
        energy = tdp_watts * duration
        total_energy += energy
    
    metrics.successful_puzzles = successful
    metrics.success_rate = successful / metrics.total_puzzles
    metrics.total_wall_clock_seconds = total_time
    metrics.avg_wall_clock_seconds = total_time / metrics.total_puzzles
    metrics.total_energy_joules = total_energy
    metrics.avg_energy_joules = total_energy / metrics.total_puzzles
    
    # Estimate GPU hours if factor provided
    if gpu_factor is not None and gpu_factor > 0:
        # GPU hours estimated based on energy consumption and conversion factor
        # This is a rough estimate based on the literature factor
        # GPU_hours = (Energy_Joules / (TDP_Watts * 3600)) * conversion_factor
        # Or more simply: GPU_hours = (total_time_hours) * conversion_factor
        total_time_hours = total_time / 3600.0
        metrics.estimated_gpu_hours = total_time_hours * gpu_factor
        metrics.gpu_conversion_factor = gpu_factor
    
    return metrics

def calculate_gpu_hours_estimated(logs: List[Dict[str, Any]], 
                                  tdp_watts: float, 
                                  gpu_factor: float) -> float:
    """
    Calculate estimated GPU hours based on logs and conversion factor.
    
    Args:
        logs: List of log entries.
        tdp_watts: Calibrated TDP in watts.
        gpu_factor: GPU conversion factor.
        
    Returns:
        Estimated GPU hours.
    """
    metrics = calculate_metrics_from_logs(logs, tdp_watts, gpu_factor)
    return metrics.estimated_gpu_hours

def save_metrics_to_csv(metrics: ExperimentMetrics, output_path: str) -> None:
    """Save metrics to a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value', 'unit'])
        writer.writerow(['total_puzzles', metrics.total_puzzles, 'count'])
        writer.writerow(['successful_puzzles', metrics.successful_puzzles, 'count'])
        writer.writerow(['success_rate', metrics.success_rate, 'ratio'])
        writer.writerow(['total_wall_clock_seconds', metrics.total_wall_clock_seconds, 'seconds'])
        writer.writerow(['avg_wall_clock_seconds', metrics.avg_wall_clock_seconds, 'seconds'])
        writer.writerow(['total_energy_joules', metrics.total_energy_joules, 'joules'])
        writer.writerow(['avg_energy_joules', metrics.avg_energy_joules, 'joules'])
        if metrics.estimated_gpu_hours > 0:
            writer.writerow(['estimated_gpu_hours', metrics.estimated_gpu_hours, 'hours'])
            writer.writerow(['gpu_conversion_factor', metrics.gpu_conversion_factor, 'factor'])

def perform_scaling_analysis(logs_by_complexity: Dict[int, List[Dict[str, Any]]],
                             tdp_watts: float,
                             gpu_factor: Optional[float] = None) -> Dict[int, ExperimentMetrics]:
    """
    Perform scaling analysis across different complexity levels.
    
    Args:
        logs_by_complexity: Dictionary mapping complexity level to list of logs.
        tdp_watts: Calibrated TDP in watts.
        gpu_factor: Optional GPU conversion factor.
        
    Returns:
        Dictionary mapping complexity level to ExperimentMetrics.
    """
    results = {}
    for complexity, logs in logs_by_complexity.items():
        metrics = calculate_metrics_from_logs(logs, tdp_watts, gpu_factor)
        results[complexity] = metrics
        logger.info(f"Complexity {complexity}: success_rate={metrics.success_rate:.2f}, "
                    f"avg_time={metrics.avg_wall_clock_seconds:.2f}s")
    return results

def main():
    """
    Main entry point for metrics calculation.
    
    This function:
    1. Loads the calibrated TDP from data/processed/calibrated_tdp.json
    2. Loads the GPU conversion factor from data/processed/literature_gpu_factor.json
    3. Validates that the GPU conversion factor is not zero
    4. Calculates and outputs metrics for provided experiment logs
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate experiment metrics')
    parser.add_argument('--logs', type=str, required=True, 
                      help='Path to experiment logs (JSON or JSONL)')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output metrics file (JSON or CSV)')
    parser.add_argument('--tdp-file', type=str, 
                      default='data/processed/calibrated_tdp.json',
                      help='Path to calibrated TDP file')
    parser.add_argument('--gpu-factor-file', type=str,
                      default='data/processed/literature_gpu_factor.json',
                      help='Path to GPU conversion factor file')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], default='json',
                      help='Output format')
    
    args = parser.parse_args()
    
    try:
        # Load TDP
        tdp_data = load_calibrated_tdp(args.tdp_file)
        tdp_watts = tdp_data['tdp_watts']
        logger.info(f"Loaded TDP: {tdp_watts}W from {args.tdp_file}")
        
        # Load and validate GPU conversion factor
        gpu_factor = load_gpu_conversion_factor(args.gpu_factor_file)
        logger.info(f"GPU conversion factor validated: {gpu_factor}")
        
        # Load logs
        logs = load_experiment_logs(args.logs)
        logger.info(f"Loaded {len(logs)} log entries from {args.logs}")
        
        # Calculate metrics
        metrics = calculate_metrics_from_logs(logs, tdp_watts, gpu_factor)
        metrics.calibration_source = tdp_data.get('source', 'unknown')
        
        logger.info(f"Calculated metrics: success_rate={metrics.success_rate:.2%}, "
                    f"avg_time={metrics.avg_wall_clock_seconds:.2f}s, "
                    f"avg_energy={metrics.avg_energy_joules:.2f}J")
        
        if metrics.estimated_gpu_hours > 0:
            logger.info(f"Estimated GPU hours: {metrics.estimated_gpu_hours:.4f}")
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.format == 'json':
            with open(output_path, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2)
            logger.info(f"Saved metrics to {output_path}")
        elif args.format == 'csv':
            save_metrics_to_csv(metrics, str(output_path))
            logger.info(f"Saved metrics to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()