import argparse
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports matching API surface
from config import get_full_config, set_simulation_seed
from data.generator import generate_batch_trajectories, HighNoiseWarning, UnphysicalTrajectoryError
from data.loader import save_trajectory, load_trajectory
from analysis.baseline import (
    compute_asymptotic_baseline,
    validate_clean_system_baseline,
    save_baseline_result,
    load_baseline_result,
    validate_and_gate_for_baseline,
    NonChaoticSystemError,
    BaselineConvergenceError
)
from analysis.shadowing import (
    validate_shadowing_lemma,
    run_shadowing_check_batch,
    gate_for_ftle_calculation,
    ShadowingCheckError
)
from utils.stability import check_numerical_validity, detect_divergence_rate

# Configure logging
logging_config = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
import logging
logging.basicConfig(**logging_config)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantifying the Influence of Initial Conditions on Chaotic Systems"
    )
    parser.add_argument('--mode', choices=['generate', 'analyze', 'validate', 'full'], default='full',
                        help='Execution mode: generate data, run analysis, validate, or full pipeline')
    parser.add_argument('--N', type=int, default=3, help='Number of coupled Lorenz oscillators')
    parser.add_argument('--noise-level', type=float, default=0.01, help='Noise level sigma')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-dir', type=str, default='data', help='Output directory')
    parser.add_argument('--strict-gating', action='store_true', default=True,
                        help='Enforce strict gating based on baseline and shadowing checks')
    return parser.parse_args()

def validate_configuration(config: Dict[str, Any]) -> bool:
    """Validate the configuration parameters."""
    if config.get('N', 0) < 1:
        logger.error("Number of oscillators N must be >= 1")
        return False
    if config.get('noise_level', 0) < 0:
        logger.error("Noise level must be non-negative")
        return False
    return True

def run_generation_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the data generation pipeline."""
    logger.info(f"Starting generation pipeline with N={args.N}, noise={args.noise_level}, seed={args.seed}")
    set_simulation_seed(args.seed)
    config = get_full_config()
    
    # Override config with CLI args
    config.simulation.N_oscillators = args.N
    # Note: Noise levels are usually a list in config, but we use the specific arg for generation
    
    try:
        trajectories = generate_batch_trajectories(
            n_trajectories=10, # Generate a small batch for initial validation
            noise_level=args.noise_level,
            config=config
        )
        
        # Save trajectories
        output_dir = Path(args.output_dir) / 'raw'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for i, traj in enumerate(trajectories):
            filename = save_trajectory(traj, output_dir, f'traj_N{args.N}_sigma{args.noise_level}_{i}')
            saved_files.append(filename)
        
        return {
            'status': 'success',
            'files': saved_files,
            'count': len(saved_files)
        }
    except (HighNoiseWarning, UnphysicalTrajectoryError) as e:
        logger.warning(f"Generation warning/error: {e}")
        return {
            'status': 'warning',
            'error': str(e),
            'files': []
        }
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'files': []
        }

def run_validation(args: argparse.Namespace) -> Dict[str, Any]:
    """Run validation checks on generated data."""
    logger.info("Starting validation pipeline")
    
    # Load a sample trajectory
    input_dir = Path(args.output_dir) / 'raw'
    # Find the first available file
    traj_files = list(input_dir.glob(f'traj_N{args.N}_sigma*'))
    if not traj_files:
        logger.error("No trajectory files found. Run generation first.")
        return {'status': 'failed', 'error': 'No trajectory files found'}
    
    traj_file = traj_files[0]
    try:
        traj_data = load_trajectory(traj_file)
        # Run stability checks
        stability_report = check_numerical_validity(traj_data['state'])
        
        # Compute divergence rate if needed
        div_rate = detect_divergence_rate(traj_data['state'])
        
        return {
            'status': 'success',
            'stability': stability_report,
            'divergence_rate': div_rate
        }
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {'status': 'failed', 'error': str(e)}

def run_analysis_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the full analysis pipeline with strict gating.
    This function implements the gating mechanism for T028.
    """
    logger.info("Starting analysis pipeline with strict gating")
    
    # 1. Compute Asymptotic Baseline (T024)
    baseline_result = None
    try:
        logger.info("Computing asymptotic baseline...")
        config = get_full_config()
        config.simulation.N_oscillators = args.N
        
        # Compute baseline for clean system
        baseline_result = compute_asymptotic_baseline(
            N=args.N,
            config=config
        )
        
        # Save baseline
        baseline_dir = Path(args.output_dir) / 'processed'
        baseline_dir.mkdir(parents=True, exist_ok=True)
        save_baseline_result(baseline_result, baseline_dir, f'baseline_N{args.N}')
        
        logger.info(f"Baseline computed: lambda_max = {baseline_result.lambda_max}")
    except Exception as e:
        logger.error(f"Baseline computation failed: {e}")
        return {'status': 'failed', 'error': f"Baseline computation: {e}", 'gated': True}

    # 2. Validate Baseline (T025)
    validation_status = 'passed'
    validation_error = None
    try:
        logger.info("Validating baseline convergence...")
        # This checks if the baseline converged properly
        if not validate_clean_system_baseline(baseline_result):
            validation_status = 'failed'
            validation_error = "Baseline did not converge"
            raise BaselineConvergenceError("Baseline did not converge")
    except BaselineConvergenceError as e:
        logger.error(f"Baseline validation failed: {e}")
        validation_status = 'failed'
        validation_error = str(e)
    except Exception as e:
        logger.error(f"Baseline validation error: {e}")
        validation_status = 'failed'
        validation_error = str(e)

    # 3. Check Non-Chaotic Regime (T026)
    non_chaotic_status = 'passed'
    non_chaotic_error = None
    try:
        logger.info("Checking for non-chaotic regime...")
        if baseline_result.lambda_max <= 0:
            non_chaotic_status = 'failed'
            non_chaotic_error = f"Non-chaotic regime detected: lambda_max={baseline_result.lambda_max} <= 0"
            raise NonChaoticSystemError(non_chaotic_error)
    except NonChaoticSystemError as e:
        logger.error(f"Non-chaotic check failed: {e}")
        non_chaotic_status = 'failed'
        non_chaotic_error = str(e)
    except Exception as e:
        logger.error(f"Non-chaotic check error: {e}")
        non_chaotic_status = 'failed'
        non_chaotic_error = str(e)

    # 4. Shadowing Lemma Check (T043)
    shadowing_status = 'passed'
    shadowing_error = None
    try:
        logger.info("Running Shadowing Lemma Check...")
        # Load a noisy trajectory to check shadowing
        input_dir = Path(args.output_dir) / 'raw'
        traj_files = list(input_dir.glob(f'traj_N{args.N}_sigma*'))
        
        if not traj_files:
            # Generate one if missing for the check
            logger.warning("No trajectory found for shadowing check, generating one...")
            run_generation_pipeline(args)
            traj_files = list(input_dir.glob(f'traj_N{args.N}_sigma*'))
        
        if traj_files:
            traj_data = load_trajectory(traj_files[0])
            shadowing_result = validate_shadowing_lemma(
                noisy_state=traj_data['state'],
                clean_baseline=baseline_result,
                config=get_full_config()
            )
            
            if not shadowing_result.is_valid:
                shadowing_status = 'failed'
                shadowing_error = f"Shadowing check failed: {shadowing_result.reason}"
                raise ShadowingCheckError(shadowing_error)
        else:
            shadowing_status = 'failed'
            shadowing_error = "No trajectory available for shadowing check"
            raise ShadowingCheckError(shadowing_error)
            
    except ShadowingCheckError as e:
        logger.error(f"Shadowing check failed: {e}")
        shadowing_status = 'failed'
        shadowing_error = str(e)
    except Exception as e:
        logger.error(f"Shadowing check error: {e}")
        shadowing_status = 'failed'
        shadowing_error = str(e)

    # 5. Gate Execution (T028 - The core requirement)
    # Collect all results for the gating function
    baseline_results = {
        'validation': validation_status,
        'non_chaotic': non_chaotic_status,
        'shadowing': shadowing_status,
        'errors': {
            'validation': validation_error,
            'non_chaotic': non_chaotic_error,
            'shadowing': shadowing_error
        }
    }

    # Use the gating function from baseline.py which encapsulates the logic
    # or implement the specific gating logic here if the imported function is insufficient
    is_gated = False
    gate_reason = []

    # T025 Validation Check
    if validation_status == 'failed':
        is_gated = True
        gate_reason.append(f"T025 Validation Failed: {validation_error}")

    # T026 Non-Chaotic Check
    if non_chaotic_status == 'failed':
        is_gated = True
        gate_reason.append(f"T026 Non-Chaotic Check Failed: {non_chaotic_error}")

    # T043 Shadowing Check
    if shadowing_status == 'failed':
        is_gated = True
        gate_reason.append(f"T043 Shadowing Check Failed: {shadowing_error}")

    if is_gated:
        logger.critical("EXECUTION HALTED: Gating conditions failed.")
        logger.critical(f"Reasons: {'; '.join(gate_reason)}")
        return {
            'status': 'gated',
            'gated': True,
            'reasons': gate_reason,
            'baseline_results': baseline_results,
            'message': "Analysis pipeline halted due to failed validation checks (T025, T026, or T043)."
        }

    logger.info("All gating checks passed. Proceeding to FTLE calculation.")
    
    # If we reach here, the gate is open. The next steps (T022/T023) would run here.
    # Since T022/T023 are separate tasks, we return success indicating the gate is open.
    return {
        'status': 'success',
        'gated': False,
        'message': "Gating passed. Ready for FTLE calculation (T022/T023).",
        'baseline_results': baseline_results
    }

def main():
    args = parse_arguments()
    config = get_full_config()
    
    # Override N if provided
    if args.N:
        config.simulation.N_oscillators = args.N
    
    if not validate_configuration(config):
        sys.exit(1)

    if args.mode == 'generate':
        result = run_generation_pipeline(args)
    elif args.mode == 'validate':
        result = run_validation(args)
    elif args.mode == 'analyze':
        # This triggers the full gating logic
        result = run_analysis_pipeline(args)
    elif args.mode == 'full':
        # Run generation first if needed
        gen_result = run_generation_pipeline(args)
        if gen_result['status'] == 'failed':
            print("Generation failed. Exiting.")
            sys.exit(1)
        
        # Then run analysis with gating
        result = run_analysis_pipeline(args)
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)

    # Print result summary
    print(json.dumps(result, indent=2, default=str))
    
    if result.get('status') in ['failed', 'gated']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()