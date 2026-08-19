"""
Metrics calculation module for llmXive BES pipeline.

Calculates success rates, wall-clock time, and energy consumption (Joules)
from execution logs, using calibrated TDP values.

Constraint: Must fail loudly if calibration data is missing or invalid.
"""
import json
import os
import math
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
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
    tdp_watts: float
    timestamp: str
    complexity_n: int
    puzzle_type: str

def load_calibrated_tdp() -> Dict[str, Any]:
    """
    Load calibrated TDP data from the calibration run.
    
    Constraint: Must fail loudly if file is missing or invalid.
    """
    calibration_path = Path("data/processed/calibrated_tdp.json")
    
    if not calibration_path.exists():
        raise FileNotFoundError(
            f"Calibration data not found at {calibration_path}. "
            "Run T008a (calibrate_tdp.py) and T008c (generate_tdp_constant.py) first."
        )
    
    try:
        with open(calibration_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in calibration file: {e}")
    
    # Validate required fields
    required_fields = ['tdp_watts', 'source', 'error_margin', 'confidence_interval']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(
            f"Calibration data missing required fields: {missing_fields}. "
            "Ensure T008c has been run successfully."
        )
    
    # Validate TDP value
    tdp_watts = data.get('tdp_watts')
    if tdp_watts is None or not isinstance(tdp_watts, (int, float)) or tdp_watts <= 0:
        raise ValueError(
            f"Invalid TDP value: {tdp_watts}. Must be a positive number."
        )
    
    logger.info(f"Loaded calibrated TDP: {tdp_watts}W (source: {data['source']})")
    return data

def load_experiment_logs(log_dir: str = "data/processed") -> List[Dict[str, Any]]:
    """
    Load experiment logs from the processed directory.
    
    Looks for experiment.log files containing CPU percent and timing data.
    """
    log_path = Path(log_dir) / "experiment.log"
    
    if not log_path.exists():
        # Try to find any .log file in the directory
        log_files = list(Path(log_dir).glob("*.log"))
        if not log_files:
            raise FileNotFoundError(
                f"No experiment logs found in {log_dir}. "
                "Run the BES loop (T024) to generate logs first."
            )
        log_path = log_files[0]
    
    logs = []
    try:
        with open(log_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    logs.append(entry)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed log entry at line {line_num}: {e}")
                    continue
    except IOError as e:
        raise IOError(f"Failed to read log file {log_path}: {e}")
    
    if not logs:
        raise ValueError("No valid log entries found in experiment log")
    
    logger.info(f"Loaded {len(logs)} log entries from {log_path}")
    return logs

def load_gpu_conversion_factor() -> Dict[str, Any]:
    """
    Load GPU conversion factor from literature-based calibration.
    
    Returns the conversion factor and metadata.
    """
    factor_path = Path("data/processed/literature_gpu_factor.json")
    
    if not factor_path.exists():
        # Return default if not found, but log warning
        logger.warning("GPU conversion factor not found, using default 1.0")
        return {"conversion_factor": 1.0, "source": "default", "estimated": True}
    
    try:
        with open(factor_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in GPU factor file: {e}")
    
    if 'conversion_factor' not in data:
        raise ValueError("GPU conversion factor file missing 'conversion_factor' field")
    
    factor = data['conversion_factor']
    if not isinstance(factor, (int, float)) or factor <= 0:
        raise ValueError(f"Invalid GPU conversion factor: {factor}")
    
    logger.info(f"Loaded GPU conversion factor: {factor}")
    return data

def calculate_metrics_from_logs(
    logs: List[Dict[str, Any]],
    tdp_data: Dict[str, Any]
) -> List[ExperimentMetrics]:
    """
    Calculate metrics from experiment logs using calibrated TDP.
    
    Energy calculation: E = TDP * (cpu_percent/100) * wall_clock_seconds
    
    Constraint: Must fail loudly if required fields are missing.
    """
    tdp_watts = tdp_data['tdp_watts']
    metrics_list = []
    
    for log_entry in logs:
        # Extract required fields
        puzzle_id = log_entry.get('puzzle_id')
        success = log_entry.get('success')
        wall_clock = log_entry.get('wall_clock_seconds')
        cpu_percent = log_entry.get('cpu_percent')
        timestamp = log_entry.get('timestamp')
        complexity_n = log_entry.get('complexity_n', 0)
        puzzle_type = log_entry.get('puzzle_type', 'unknown')
        
        # Validate required fields
        missing_fields = []
        if puzzle_id is None:
            missing_fields.append('puzzle_id')
        if success is None:
            missing_fields.append('success')
        if wall_clock is None:
            missing_fields.append('wall_clock_seconds')
        if cpu_percent is None:
            missing_fields.append('cpu_percent')
        if timestamp is None:
            missing_fields.append('timestamp')
        
        if missing_fields:
            logger.warning(
                f"Skipping log entry for puzzle {puzzle_id}: "
                f"missing fields {missing_fields}"
            )
            continue
        
        # Validate numeric fields
        try:
            wall_clock = float(wall_clock)
            cpu_percent = float(cpu_percent)
            complexity_n = int(complexity_n)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping log entry for puzzle {puzzle_id}: invalid numeric field - {e}")
            continue
        
        if wall_clock < 0 or cpu_percent < 0 or cpu_percent > 100:
            logger.warning(
                f"Skipping log entry for puzzle {puzzle_id}: "
                f"invalid values (wall_clock={wall_clock}, cpu_percent={cpu_percent})"
            )
            continue
        
        # Calculate energy consumption
        energy_joules = tdp_watts * (cpu_percent / 100.0) * wall_clock
        
        # Create metrics object
        metrics = ExperimentMetrics(
            puzzle_id=str(puzzle_id),
            success=bool(success),
            wall_clock_seconds=round(wall_clock, 6),
            energy_joules=round(energy_joules, 6),
            cpu_percent=round(cpu_percent, 2),
            tdp_watts=round(tdp_watts, 2),
            timestamp=timestamp,
            complexity_n=complexity_n,
            puzzle_type=puzzle_type
        )
        metrics_list.append(metrics)
    
    logger.info(f"Calculated metrics for {len(metrics_list)} puzzles")
    return metrics_list

def calculate_gpu_hours_estimated(
    metrics_list: List[ExperimentMetrics],
    gpu_factor_data: Dict[str, Any]
) -> float:
    """
    Calculate estimated GPU hours based on CPU runtime and conversion factor.
    
    Returns total estimated GPU hours.
    """
    conversion_factor = gpu_factor_data['conversion_factor']
    total_cpu_hours = sum(m.wall_clock_seconds for m in metrics_list) / 3600.0
    estimated_gpu_hours = total_cpu_hours * conversion_factor
    
    logger.info(
        f"Estimated GPU hours: {estimated_gpu_hours:.4f} "
        f"(CPU hours: {total_cpu_hours:.4f}, factor: {conversion_factor})"
    )
    return estimated_gpu_hours

def save_metrics_to_csv(
    metrics_list: List[ExperimentMetrics],
    output_path: str = "data/processed/metrics.csv"
) -> None:
    """
    Save calculated metrics to a CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'puzzle_id', 'success', 'wall_clock_seconds', 'energy_joules',
        'cpu_percent', 'tdp_watts', 'timestamp', 'complexity_n', 'puzzle_type'
    ]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for metrics in metrics_list:
            writer.writerow(asdict(metrics))
    
    logger.info(f"Saved metrics to {output_file}")

def perform_scaling_analysis(
    metrics_list: List[ExperimentMetrics]
) -> Dict[str, Any]:
    """
    Perform basic scaling analysis on the metrics.
    
    Returns summary statistics by complexity level.
    """
    if not metrics_list:
        return {"error": "No metrics provided"}
    
    # Group by complexity
    complexity_groups = {}
    for metrics in metrics_list:
        n = metrics.complexity_n
        if n not in complexity_groups:
            complexity_groups[n] = []
        complexity_groups[n].append(metrics)
    
    # Calculate statistics for each complexity level
    scaling_stats = []
    for n in sorted(complexity_groups.keys()):
        group = complexity_groups[n]
        
        avg_time = sum(m.wall_clock_seconds for m in group) / len(group)
        avg_energy = sum(m.energy_joules for m in group) / len(group)
        success_rate = sum(1 for m in group if m.success) / len(group)
        
        scaling_stats.append({
            'complexity_n': n,
            'count': len(group),
            'avg_wall_clock_seconds': round(avg_time, 6),
            'avg_energy_joules': round(avg_energy, 6),
            'success_rate': round(success_rate, 4)
        })
    
    return {
        'scaling_stats': scaling_stats,
        'total_puzzles': len(metrics_list),
        'complexity_levels': len(complexity_groups)
    }

def main():
    """
    Main entry point for metrics calculation.
    
    Reads experiment logs, calculates metrics using calibrated TDP,
    and saves results to CSV.
    """
    try:
        # Load calibrated TDP (fails loudly if missing)
        logger.info("Loading calibrated TDP...")
        tdp_data = load_calibrated_tdp()
        
        # Load experiment logs
        logger.info("Loading experiment logs...")
        logs = load_experiment_logs()
        
        # Calculate metrics
        logger.info("Calculating metrics...")
        metrics_list = calculate_metrics_from_logs(logs, tdp_data)
        
        if not metrics_list:
            raise ValueError("No valid metrics could be calculated from logs")
        
        # Save metrics to CSV
        output_path = "data/processed/metrics.csv"
        save_metrics_to_csv(metrics_list, output_path)
        
        # Perform scaling analysis
        scaling_stats = perform_scaling_analysis(metrics_list)
        scaling_path = "data/processed/scaling_summary.json"
        with open(scaling_path, 'w') as f:
            json.dump(scaling_stats, f, indent=2)
        logger.info(f"Saved scaling summary to {scaling_path}")
        
        # Calculate GPU hours estimate
        gpu_factor_data = load_gpu_conversion_factor()
        gpu_hours = calculate_gpu_hours_estimated(metrics_list, gpu_factor_data)
        
        # Print summary
        total_success = sum(1 for m in metrics_list if m.success)
        total_attempts = len(metrics_list)
        success_rate = total_success / total_attempts if total_attempts > 0 else 0
        
        total_energy = sum(m.energy_joules for m in metrics_list)
        total_time = sum(m.wall_clock_seconds for m in metrics_list)
        
        print(f"\n=== Metrics Summary ===")
        print(f"Total puzzles: {total_attempts}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Total wall-clock time: {total_time:.2f} seconds")
        print(f"Total energy consumption: {total_energy:.2f} Joules")
        print(f"Estimated GPU hours: {gpu_hours:.4f}")
        print(f"Metrics saved to: {output_path}")
        print(f"Scaling summary saved to: {scaling_path}")
        
        return metrics_list, scaling_stats, gpu_hours
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()