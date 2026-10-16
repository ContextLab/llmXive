import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Local imports matching API surface
from config import get_full_config, set_simulation_seed
from data.generator import (
    generate_coupled_lorenz_trajectory,
    HighNoiseWarning,
    UnphysicalTrajectoryError,
)
from data.loader import save_trajectory, load_trajectory
from analysis.baseline import (
    compute_asymptotic_baseline,
    validate_clean_system_baseline,
    save_baseline_result,
    load_baseline_result,
    validate_and_gate_for_baseline,
    NonChaoticSystemError,
    BaselineConvergenceError,
    BaselineResult,
)
from analysis.shadowing import (
    validate_shadowing_lemma,
    run_shadowing_check_batch,
    gate_for_ftle_calculation,
    ShadowingCheckError,
)
from utils.stability import check_numerical_validity, detect_divergence_rate

# llmxive toolkit paths helper for writing .npz files
from llmxive_toolkit import paths

import numpy as np

# Configure logging
logging_config = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
logging.basicConfig(**logging_config)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantifying the Influence of Initial Conditions on Chaotic Systems"
    )
    parser.add_argument(
        '--mode',
        choices=['generate', 'analyze', 'validate', 'full'],
        default='full',
        help='Execution mode: generate data, run analysis, validate, or full pipeline'
    )
    # Existing single-value arguments (kept for backward compatibility)
    parser.add_argument('--N', type=int, default=3, help='Number of coupled Lorenz oscillators')
    parser.add_argument('--noise-level', type=float, default=0.01,
                        help='Noise level sigma')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-dir', type=str, default='data',
                        help='Output directory')
    parser.add_argument('--strict-gating', action='store_true', default=True,
                        help='Enforce strict gating based on baseline and shadowing checks')

    # New arguments required for T008
    parser.add_argument(
        '--N-values',
        type=str,
        default='3,5',
        help='Comma‑separated list of oscillator counts (e.g., "3,5")'
    )
    parser.add_argument(
        '--noise-levels',
        type=str,
        default='0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0',
        help='Comma‑separated list of σ_noise values (max 1.0)'
    )
    parser.add_argument(
        '--trials',
        type=int,
        default=None,
        help='Override automatic trial count (k). If omitted, k=50 for σ<0.01 else k=30.'
    )
    return parser.parse_args()


def _parse_comma_separated_ints(s: str) -> List[int]:
    return [int(item.strip()) for item in s.split(',') if item.strip()]


def _parse_comma_separated_floats(s: str) -> List[float]:
    return [float(item.strip()) for item in s.split(',') if item.strip()]


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
    """Run the data generation pipeline (legacy)."""
    logger.info(f"Starting generation pipeline with N={args.N}, noise={args.noise_level}, seed={args.seed}")
    set_simulation_seed(args.seed)
    config = get_full_config()

    # Override config with CLI args
    config['simulation']['N_oscillators'] = args.N

    try:
        trajectories = generate_batch_trajectories(
            n_trajectories=10,  # Small batch for legacy mode
            noise_level=args.noise_level,
            config=config
        )

        # Save trajectories using the existing JSON‑based saver
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


def run_generation_loop(args: argparse.Namespace) -> Dict[str, Any]:
    """
    T008 implementation: generate trajectories for multiple N and σ values.

    - Accepts --N-values and --noise-levels (comma‑separated lists).
    - For each (N, σ) generates k trials:
          k = 50 if σ < 0.01 else 30 (overridden by --trials if supplied).
    - Saves each trajectory as an immutable ``.npz`` file:
          data/raw/trajectory_N{N}_sigma{σ}_trial{t}.npz
    """
    logger.info("Running T008 generation loop")

    # Parse the comma‑separated lists
    N_list = _parse_comma_separated_ints(args.N_values)
    sigma_list = _parse_comma_separated_floats(args.noise_levels)

    # Enforce the specification maximum σ ≤ 1.0
    sigma_list = [s for s in sigma_list if s <= 1.0]

    base_seed = args.seed if args.seed is not None else 42

    generated_files = []
    failures = []

    for N in N_list:
        for sigma in sigma_list:
            # Determine number of trials
            if args.trials is not None:
                k = args.trials
            else:
                k = 50 if sigma < 0.01 else 30

            logger.info(f"Generating N={N}, sigma={sigma:.4f}, trials={k}")

            for trial in range(k):
                # Derive a reproducible seed per (N, sigma, trial)
                seed = base_seed + N * 1000 + int(sigma * 10000) + trial

                try:
                    traj = generate_coupled_lorenz_trajectory(
                        N=N,
                        t_start=0.0,
                        t_end=get_full_config()['simulation']['t_max'],
                        dt=get_full_config()['simulation']['dt_output'],
                        sigma_noise=sigma,
                        coupling_strength=get_full_config()['simulation']['coupling_strength'],
                        coupling_topology=get_full_config()['simulation']['coupling_topology'],
                        seed=seed
                    )

                    # Prepare output path using llmxive_toolkit.paths
                    out_path = paths.data('raw',
                                          f'trajectory_N{N}_sigma{sigma}_trial{trial}.npz')

                    # Save as .npz (time and state arrays)
                    np.savez_compressed(out_path,
                                        time=traj.time,
                                        state=traj.state,
                                        noise_level=traj.noise_level,
                                        N_oscillators=traj.N_oscillators,
                                        coupling_strength=traj.coupling_strength,
                                        seed=traj.seed,
                                        is_clean=traj.is_clean)

                    generated_files.append(str(out_path))

                except UnphysicalTrajectoryError as e:
                    # Log and continue – unphysical trajectories are simply skipped
                    logger.warning(f"Skipped unphysical trajectory (N={N}, sigma={sigma}, trial={trial}): {e}")
                    failures.append({'N': N, 'sigma': sigma, 'trial': trial, 'error': str(e)})
                except HighNoiseWarning as w:
                    # Record the warning but still keep the file (high‑noise is allowed)
                    logger.warning(f"High noise warning (N={N}, sigma={sigma}, trial={trial}): {w}")
                    # Save the trajectory despite the warning (already done above)
                except Exception as e:
                    logger.error(f"Unexpected error during generation (N={N}, sigma={sigma}, trial={trial}): {e}")
                    failures.append({'N': N, 'sigma': sigma, 'trial': trial, 'error': str(e)})

    summary = {
        'status': 'completed' if generated_files else 'failed',
        'generated_files': generated_files,
        'failures': failures,
        'total_generated': len(generated_files)
    }
    logger.info(f"Generation loop finished: {summary['total_generated']} files created.")
    return summary


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
    This function implements the gating mechanism for T011.
    """
    logger.info("Starting analysis pipeline with strict gating")

    # ----------------------------------------------------------------------
    # 1. Compute Asymptotic Baseline (if not already present)
    # ----------------------------------------------------------------------
    baseline_result: BaselineResult = None
    baseline_path: Path = None
    try:
        logger.info("Computing asymptotic baseline...")
        config = get_full_config()
        config['simulation']['N_oscillators'] = args.N

        # Compute baseline for clean system
        baseline_result = compute_asymptotic_baseline(
            N=args.N,
            config=config
        )

        # Save baseline
        baseline_dir = Path(args.output_dir) / 'processed'
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / f'baseline_N{args.N}.json'
        save_baseline_result(baseline_result, baseline_path, f'baseline_N{args.N}')

        logger.info(f"Baseline computed: lambda_max = {baseline_result.lambda_max}")
    except Exception as e:
        logger.error(f"Baseline computation failed: {e}")
        return {'status': 'failed', 'error': f"Baseline computation: {e}", 'gated': True}

    # ----------------------------------------------------------------------
    # 2. Load Baseline from Disk and Verify Status (T011 gating)
    # ----------------------------------------------------------------------
    try:
        logger.info(f"Loading baseline from {baseline_path} for gating check...")
        loaded_baseline = load_baseline_result(baseline_path)

        # The BaselineResult is expected to have a 'status' attribute.
        # If the attribute is missing, treat it as invalid.
        baseline_status = getattr(loaded_baseline, 'status', None)
        if baseline_status != "valid":
            raise BaselineConvergenceError(
                f"Baseline status invalid (status={baseline_status})"
            )

        # Verify chaotic regime (lambda_max > 0)
        if getattr(loaded_baseline, 'lambda_max', 0) <= 0:
            raise NonChaoticSystemError(
                f"Baseline lambda_max non‑positive ({loaded_baseline.lambda_max})"
            )
    except (BaselineConvergenceError, NonChaoticSystemError) as gate_err:
        logger.error(f"Gating failed: {gate_err}")
        return {
            'status': 'gated',
            'gated': True,
            'reasons': [str(gate_err)],
            'message': "Analysis pipeline halted due to baseline gating failure (T011)."
        }
    except Exception as e:
        logger.error(f"Unexpected error during baseline gating: {e}")
        return {
            'status': 'gated',
            'gated': True,
            'reasons': [str(e)],
            'message': "Analysis pipeline halted due to unexpected gating error."
        }

    # ----------------------------------------------------------------------
    # 3. Validate Baseline Convergence (previous T025 step)
    # ----------------------------------------------------------------------
    validation_status = 'passed'
    validation_error = None
    try:
        logger.info("Validating baseline convergence...")
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

    # ----------------------------------------------------------------------
    # 4. Check Non‑Chaotic Regime (T026) – already covered by gating but
    #    retained for backward compatibility.
    # ----------------------------------------------------------------------
    non_chaotic_status = 'passed'
    non_chaotic_error = None
    try:
        logger.info("Checking for non‑chaotic regime...")
        if baseline_result.lambda_max <= 0:
            non_chaotic_status = 'failed'
            non_chaotic_error = f"Non‑chaotic regime detected: lambda_max={baseline_result.lambda_max} <= 0"
            raise NonChaoticSystemError(non_chaotic_error)
    except NonChaoticSystemError as e:
        logger.error(f"Non‑chaotic check failed: {e}")
        non_chaotic_status = 'failed'
        non_chaotic_error = str(e)
    except Exception as e:
        logger.error(f"Non‑chaotic check error: {e}")
        non_chaotic_status = 'failed'
        non_chaotic_error = str(e)

    # ----------------------------------------------------------------------
    # 5. Shadowing Lemma Check (T043)
    # ----------------------------------------------------------------------
    shadowing_status = 'passed'
    shadowing_error = None
    try:
        logger.info("Running Shadowing Lemma Check...")
        input_dir = Path(args.output_dir) / 'raw'
        traj_files = list(input_dir.glob(f'traj_N{args.N}_sigma*'))

        if not traj_files:
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

    # ----------------------------------------------------------------------
    # 6. Aggregate gating results
    # ----------------------------------------------------------------------
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

    # Determine final gating outcome
    is_gated = any([
        validation_status == 'failed',
        non_chaotic_status == 'failed',
        shadowing_status == 'failed'
    ])

    if is_gated:
        logger.critical("EXECUTION HALTED: Gating conditions failed.")
        reasons = []
        if validation_status == 'failed':
            reasons.append(f"T025 Validation Failed: {validation_error}")
        if non_chaotic_status == 'failed':
            reasons.append(f"T026 Non‑Chaotic Check Failed: {non_chaotic_error}")
        if shadowing_status == 'failed':
            reasons.append(f"T043 Shadowing Check Failed: {shadowing_error}")

        return {
            'status': 'gated',
            'gated': True,
            'reasons': reasons,
            'baseline_results': baseline_results,
            'message': "Analysis pipeline halted due to failed validation checks (T025, T026, or T043)."
        }

    logger.info("All gating checks passed. Proceeding to FTLE calculation.")
    # Placeholder: FTLE computation would be invoked here in subsequent tasks.
    return {
        'status': 'success',
        'gated': False,
        'message': "Gating passed. Ready for FTLE calculation (T022/T023).",
        'baseline_results': baseline_results
    }


def main():
    args = parse_arguments()
    config = get_full_config()

    # Override N if provided via the legacy single‑value flag
    if args.N:
        config['simulation']['N_oscillators'] = args.N

    if not validate_configuration(config):
        sys.exit(1)

    if args.mode == 'generate':
        # Prefer the new multi‑value generation loop if the user supplied lists
        if args.N_values != '3,5' or args.noise_levels != '0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0':
            result = run_generation_loop(args)
        else:
            # Fall back to the legacy single‑value generator
            result = run_generation_pipeline(args)
    elif args.mode == 'validate':
        result = run_validation(args)
    elif args.mode == 'analyze':
        # This triggers the full gating logic (including the new T011 gate)
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