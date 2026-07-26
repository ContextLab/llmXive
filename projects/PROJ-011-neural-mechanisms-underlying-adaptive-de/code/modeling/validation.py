"""
Validation module for belief updating model convergence.

Checks R-hat and ESS metrics, handles non-convergence with multiple restart attempts,
and logs validation results for downstream processing.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pymc as pm
import arviz as az

from utils.io import ensure_dir, load_json, save_json
from utils.logger import get_logger
from utils.config import get_config
from modeling.belief_updater import run_mcmc_sampling, extract_posterior_samples, load_behavioral_data, prepare_model_data, build_hierarchical_model
from modeling.runtime_enforcer import RuntimeEnforcer, RuntimeLimitExceeded

# Constants for convergence criteria
DEFAULT_RHAT_THRESHOLD = 1.05
DEFAULT_ESS_MIN = 200
DEFAULT_MAX_RESTARTS = 3
DEFAULT_MIN_SAMPLES = 1000
DEFAULT_WARMUP = 1000

def check_convergence(
    idata: az.InferenceData,
    rhat_threshold: float = DEFAULT_RHAT_THRESHOLD,
    ess_min: int = DEFAULT_ESS_MIN,
    var_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Check convergence of MCMC sampling results.
    
    Args:
        idata: Arviz InferenceData object from PyMC sampling
        rhat_threshold: Maximum acceptable R-hat value (default 1.05)
        ess_min: Minimum acceptable effective sample size (default 200)
        var_names: List of variable names to check (None for all)
        
    Returns:
        Dictionary with convergence metrics and status
    """
    if var_names is None:
        var_names = list(idata.posterior.data_vars)
    
    convergence_results = {
        'converged': True,
        'rhat_values': {},
        'ess_values': {},
        'failures': [],
        'warnings': []
    }
    
    # Calculate R-hat
    rhat_data = az.rhat(idata, var_names=var_names)
    for var in var_names:
        if var in rhat_data.data_vars:
            rhat_val = float(rhat_data[var].values)
            convergence_results['rhat_values'][var] = rhat_val
            
            if rhat_val > rhat_threshold:
                convergence_results['converged'] = False
                convergence_results['failures'].append({
                    'variable': var,
                    'metric': 'rhat',
                    'value': rhat_val,
                    'threshold': rhat_threshold
                })
            elif rhat_val > 1.01:
                convergence_results['warnings'].append({
                    'variable': var,
                    'metric': 'rhat',
                    'value': rhat_val,
                    'note': 'Slightly elevated R-hat'
                })
    
    # Calculate ESS
    ess_data = az.ess(idata, var_names=var_names)
    for var in var_names:
        if var in ess_data.data_vars:
            ess_val = float(ess_data[var].values)
            convergence_results['ess_values'][var] = ess_val
            
            if ess_val < ess_min:
                convergence_results['converged'] = False
                convergence_results['failures'].append({
                    'variable': var,
                    'metric': 'ess',
                    'value': ess_val,
                    'threshold': ess_min
                })
            elif ess_val < ess_min * 2:
                convergence_results['warnings'].append({
                    'variable': var,
                    'metric': 'ess',
                    'value': ess_val,
                    'note': 'Low effective sample size'
                })
    
    return convergence_results

def validate_and_restart(
    participant_id: str,
    config: Dict[str, Any],
    behavioral_data: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
    max_restarts: int = DEFAULT_MAX_RESTARTS,
    runtime_enforcer: Optional[RuntimeEnforcer] = None
) -> Tuple[Optional[az.InferenceData], Dict[str, Any]]:
    """
    Run model with convergence validation and automatic restarts on failure.
    
    Args:
        participant_id: Unique identifier for the participant
        config: Model configuration dictionary
        behavioral_data: Preprocessed behavioral data for the participant
        logger: Logger instance
        max_restarts: Maximum number of restart attempts
        runtime_enforcer: Optional runtime enforcer for time limits
        
    Returns:
        Tuple of (InferenceData or None if failed, validation report)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    validation_report = {
        'participant_id': participant_id,
        'total_attempts': 0,
        'successful': False,
        'attempts': [],
        'final_status': 'failed',
        'error': None
    }
    
    for attempt in range(max_restarts + 1):
        validation_report['total_attempts'] = attempt + 1
        attempt_report = {
            'attempt_number': attempt + 1,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'running'
        }
        
        logger.info(f"Participant {participant_id}: Attempt {attempt + 1}/{max_restarts + 1}")
        
        try:
            # Check runtime before starting
            if runtime_enforcer:
                runtime_enforcer.check_time_remaining()
            
            # Prepare model data
            model_data = prepare_model_data(behavioral_data, config)
            
            # Build model
            model = build_hierarchical_model(model_data, config)
            
            # Run sampling
            logger.info(f"Participant {participant_id}: Starting MCMC sampling...")
            idata = run_mcmc_sampling(
                model,
                config.get('chains', 4),
                config.get('samples', DEFAULT_MIN_SAMPLES),
                config.get('warmup', DEFAULT_WARMUP),
                config.get('random_seed', None),
                logger=logger
            )
            
            # Check convergence
            logger.info(f"Participant {participant_id}: Checking convergence...")
            convergence_results = check_convergence(
                idata,
                rhat_threshold=config.get('rhat_threshold', DEFAULT_RHAT_THRESHOLD),
                ess_min=config.get('ess_min', DEFAULT_ESS_MIN)
            )
            
            attempt_report['convergence'] = convergence_results
            
            if convergence_results['converged']:
                attempt_report['status'] = 'converged'
                validation_report['attempts'].append(attempt_report)
                validation_report['successful'] = True
                validation_report['final_status'] = 'converged'
                validation_report['convergence_details'] = convergence_results
                logger.info(f"Participant {participant_id}: Successfully converged on attempt {attempt + 1}")
                return idata, validation_report
            else:
                attempt_report['status'] = 'non_converged'
                attempt_report['failures'] = convergence_results['failures']
                validation_report['attempts'].append(attempt_report)
                logger.warning(
                    f"Participant {participant_id}: Attempt {attempt + 1} failed convergence. "
                    f"Failures: {convergence_results['failures']}"
                )
                
                # If this was the last attempt, mark as failed
                if attempt == max_restarts:
                    validation_report['final_status'] = 'non_converged'
                    validation_report['error'] = 'Max restarts reached without convergence'
                    return None, validation_report
                
                # Prepare for next attempt with increased samples
                config['samples'] = int(config.get('samples', DEFAULT_MIN_SAMPLES) * 1.5)
                config['warmup'] = int(config.get('warmup', DEFAULT_WARMUP) * 1.5)
                logger.info(f"Participant {participant_id}: Increasing samples to {config['samples']} for next attempt")
                
        except RuntimeLimitExceeded as e:
            attempt_report['status'] = 'runtime_exceeded'
            attempt_report['error'] = str(e)
            validation_report['attempts'].append(attempt_report)
            validation_report['final_status'] = 'runtime_exceeded'
            validation_report['error'] = str(e)
            logger.error(f"Participant {participant_id}: Runtime limit exceeded - {e}")
            return None, validation_report
            
        except Exception as e:
            attempt_report['status'] = 'error'
            attempt_report['error'] = str(e)
            validation_report['attempts'].append(attempt_report)
            logger.error(f"Participant {participant_id}: Error during attempt {attempt + 1}: {e}")
            
            if attempt == max_restarts:
                validation_report['final_status'] = 'error'
                validation_report['error'] = str(e)
                return None, validation_report
            
            # Continue to next attempt
            continue
    
    # Should not reach here, but just in case
    validation_report['final_status'] = 'failed'
    validation_report['error'] = 'Unexpected termination'
    return None, validation_report

def save_validation_report(
    validation_report: Dict[str, Any],
    output_path: Path,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Save validation report to JSON file.
    
    Args:
        validation_report: Validation report dictionary
        output_path: Path to save the report
        logger: Logger instance
    """
    if logger is None:
        logger = get_logger(__name__)
    
    ensure_dir(output_path.parent)
    save_json(validation_report, output_path)
    logger.info(f"Validation report saved to {output_path}")

def main() -> None:
    """
    Main entry point for validation script.
    
    Processes all participants from behavioral data, validates model convergence,
    and saves results.
    """
    logger = get_logger(__name__)
    logger.info("Starting model validation for convergence...")
    
    # Load configuration
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data/processed'))
    output_dir = Path(config.get('model_output_dir', 'data/models'))
    reports_dir = output_dir / 'validation'
    
    ensure_dir(reports_dir)
    
    # Load behavioral data
    behavioral_file = data_dir / 'behavioral' / 'all_participants.json'
    if not behavioral_file.exists():
        logger.error(f"Behavioral data file not found: {behavioral_file}")
        sys.exit(1)
    
    all_data = load_json(behavioral_file)
    participants = all_data.get('participants', [])
    
    logger.info(f"Found {len(participants)} participants to validate")
    
    # Initialize runtime enforcer if configured
    runtime_enforcer = None
    if config.get('enable_runtime_limits', False):
        runtime_enforcer = RuntimeEnforcer(
            time_limit_seconds=config.get('runtime_limit_seconds', 21600),  # 6 hours
            logger=logger
        )
    
    validation_results = []
    converged_count = 0
    
    for participant in participants:
        participant_id = participant.get('participant_id')
        if not participant_id:
            logger.warning("Skipping participant without ID")
            continue
        
        logger.info(f"Processing participant: {participant_id}")
        
        # Run validation with restarts
        idata, report = validate_and_restart(
            participant_id=participant_id,
            config=config.get('model_config', {}),
            behavioral_data=participant,
            logger=logger,
            max_restarts=config.get('max_validation_restarts', DEFAULT_MAX_RESTARTS),
            runtime_enforcer=runtime_enforcer
        )
        
        # Save individual report
        report_path = reports_dir / f"{participant_id}_validation.json"
        save_validation_report(report, report_path, logger)
        
        validation_results.append(report)
        
        if report['successful']:
            converged_count += 1
            logger.info(f"Participant {participant_id}: Converged")
        else:
            logger.warning(f"Participant {participant_id}: Failed to converge - {report['final_status']}")
    
    # Save summary
    summary = {
        'total_participants': len(participants),
        'converged_count': converged_count,
        'convergence_rate': converged_count / len(participants) if participants else 0,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': config.get('model_config', {}),
        'individual_reports': validation_results
    }
    
    summary_path = reports_dir / 'validation_summary.json'
    save_json(summary, summary_path)
    logger.info(f"Validation complete. Summary saved to {summary_path}")
    logger.info(f"Convergence rate: {summary['convergence_rate']:.2%} ({converged_count}/{len(participants)})")

if __name__ == '__main__':
    main()
