"""
Convergence analysis module for MobileGym State-Guided Curriculum.

Calculates steps-to-target for different training runs and reports
absolute/percentage differences between baselines and experimental runs.

Reads success rate threshold from config file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

# Constants
DEFAULT_CONFIG_PATH = "data/processed/training_config.json"
DEFAULT_BASELINE_LOGS = "data/processed/baseline_logs.json"
DEFAULT_EXPERIMENTAL_LOGS = "data/processed/experimental_logs.json"
DEFAULT_OUTPUT_PATH = "data/processed/convergence_analysis.json"

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load training configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is malformed
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    logger.info(f"Loaded config from {config_path}")
    return config
    
def load_logs(logs_path: str) -> Dict[str, Any]:
    """
    Load training logs from JSON file.
    
    Args:
        logs_path: Path to logs file
        
    Returns:
        Logs dictionary
        
    Raises:
        FileNotFoundError: If logs file doesn't exist
        json.JSONDecodeError: If logs file is malformed
    """
    logs_file = Path(logs_path)
    if not logs_file.exists():
        raise FileNotFoundError(f"Logs file not found: {logs_path}")
        
    with open(logs_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
        
    logger.info(f"Loaded logs from {logs_path}")
    return logs
    
def calculate_steps_to_target(
    logs: Dict[str, Any], 
    target_success_rate: float
) -> Optional[int]:
    """
    Calculate the number of steps (rollouts) required to reach target success rate.
    
    Args:
        logs: Training logs dictionary containing step-by-step metrics
        target_success_rate: Target success rate threshold (0.0 to 1.0)
        
    Returns:
        Number of steps to reach target, or None if target never reached
    """
    if 'training_history' not in logs:
        logger.warning("No training_history found in logs")
        return None
        
    history = logs['training_history']
    
    for entry in history:
        step = entry.get('step')
        success_rate = entry.get('success_rate')
        
        if step is None or success_rate is None:
            continue
            
        if success_rate >= target_success_rate:
            logger.debug(f"Target {target_success_rate} reached at step {step}")
            return step
            
    logger.info(f"Target {target_success_rate} never reached in {len(history)} steps")
    return None
    
def analyze_convergence(
    baseline_logs_path: str,
    experimental_logs_path: str,
    config_path: str
) -> Dict[str, Any]:
    """
    Perform convergence analysis between baseline and experimental runs.
    
    Args:
        baseline_logs_path: Path to baseline (Static Random) logs
        experimental_logs_path: Path to experimental (State-Guided) logs
        config_path: Path to configuration file containing success rate threshold
        
    Returns:
        Dictionary containing convergence analysis results
    """
    # Load configuration
    config = load_config(config_path)
    target_success_rate = config.get('success_rate_threshold', 0.8)
    logger.info(f"Using target success rate threshold: {target_success_rate}")
    
    # Load logs
    baseline_logs = load_logs(baseline_logs_path)
    experimental_logs = load_logs(experimental_logs_path)
    
    # Calculate steps to target
    baseline_steps = calculate_steps_to_target(baseline_logs, target_success_rate)
    experimental_steps = calculate_steps_to_target(experimental_logs, target_success_rate)
    
    # Build result
    result = {
        'target_success_rate': target_success_rate,
        'baseline': {
            'run_id': baseline_logs.get('run_id', 'unknown'),
            'scheduler_type': baseline_logs.get('scheduler_type', 'Static Random'),
            'steps_to_target': baseline_steps
        },
        'experimental': {
            'run_id': experimental_logs.get('run_id', 'unknown'),
            'scheduler_type': experimental_logs.get('scheduler_type', 'State-Guided'),
            'steps_to_target': experimental_steps
        },
        'comparison': {}
    }
    
    # Calculate differences if both reached target
    if baseline_steps is not None and experimental_steps is not None:
        absolute_diff = baseline_steps - experimental_steps
        percentage_diff = (absolute_diff / baseline_steps) * 100 if baseline_steps > 0 else 0.0
        
        result['comparison'] = {
            'absolute_difference': absolute_diff,
            'percentage_difference': percentage_diff,
            'interpretation': 'faster' if absolute_diff > 0 else 'slower' if absolute_diff < 0 else 'equal'
        }
        
        if absolute_diff > 0:
            logger.info(f"State-Guided is {absolute_diff} steps ({percentage_diff:.2f}%) faster")
        elif absolute_diff < 0:
            logger.info(f"State-Guided is {abs(absolute_diff)} steps ({abs(percentage_diff):.2f}%) slower")
        else:
            logger.info("Both methods reached target in equal steps")
            
    elif baseline_steps is None and experimental_steps is None:
        result['comparison'] = {
            'absolute_difference': None,
            'percentage_difference': None,
            'interpretation': 'neither_reached_target'
        }
        logger.warning("Neither method reached the target success rate")
        
    elif baseline_steps is None:
        result['comparison'] = {
            'absolute_difference': None,
            'percentage_difference': None,
            'interpretation': 'baseline_failed_experimental_succeeded'
        }
        logger.info("Experimental method reached target while baseline did not")
        
    else:  # experimental_steps is None
        result['comparison'] = {
            'absolute_difference': None,
            'percentage_difference': None,
            'interpretation': 'baseline_succeeded_experimental_failed'
        }
        logger.warning("Baseline reached target while experimental method did not")
        
    return result
    
def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save convergence analysis results to JSON file.
    
    Args:
        results: Analysis results dictionary
        output_path: Path to output file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Saved convergence analysis to {output_path}")
    
def main():
    """
    Main entry point for convergence analysis.
    """
    logger.info("Starting convergence analysis")
    
    # Default paths
    config_path = os.environ.get('CONFIG_PATH', DEFAULT_CONFIG_PATH)
    baseline_logs_path = os.environ.get('BASELINE_LOGS_PATH', DEFAULT_BASELINE_LOGS)
    experimental_logs_path = os.environ.get('EXPERIMENTAL_LOGS_PATH', DEFAULT_EXPERIMENTAL_LOGS)
    output_path = os.environ.get('OUTPUT_PATH', DEFAULT_OUTPUT_PATH)
    
    try:
        # Perform analysis
        results = analyze_convergence(
            baseline_logs_path=baseline_logs_path,
            experimental_logs_path=experimental_logs_path,
            config_path=config_path
        )
        
        # Save results
        save_results(results, output_path)
        
        # Print summary
        print(f"\nConvergence Analysis Summary:")
        print(f"  Target Success Rate: {results['target_success_rate']}")
        print(f"  Baseline Steps: {results['baseline']['steps_to_target']}")
        print(f"  Experimental Steps: {results['experimental']['steps_to_target']}")
        
        if results['comparison'].get('absolute_difference') is not None:
            diff = results['comparison']['absolute_difference']
            pct = results['comparison']['percentage_difference']
            interp = results['comparison']['interpretation']
            print(f"  Difference: {diff} steps ({pct:.2f}%) - {interp}")
        else:
            print(f"  Comparison: {results['comparison']['interpretation']}")
            
        print(f"\nResults saved to: {output_path}")
        logger.info("Convergence analysis completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during convergence analysis: {e}")
        raise
        
if __name__ == '__main__':
    main()
