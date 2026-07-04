import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import time

# Add project root to path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.generators import generate_lorenz_trajectory, generate_rossler_trajectory, validate_trajectory
from code.noise import add_noise_to_trajectory, NoiseType
from code.metrics import compute_all_metrics
from code.analysis import analyze_results_from_files, load_ground_truth_metrics
from code.visualize import run_visualization_pipeline
from code.utils.io import write_json_artifact, load_trajectory, compute_file_checksum
from code.config import LORENZ_PARAMS, ROSSLER_PARAMS, DT, T_MAX, SNR_LEVELS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_clean_trajectories(systems: List[str], seeds: List[int], output_dir: Path):
    """Generate clean trajectories for specified systems and seeds."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for system in systems:
        for seed in seeds:
            logger.info(f"Generating {system} trajectory with seed {seed}")
            
            if system == "lorenz":
                traj = generate_lorenz_trajectory(seed=seed)
            elif system == "rossler":
                traj = generate_rossler_trajectory(seed=seed)
            else:
                logger.error(f"Unknown system: {system}")
                continue
            
            if not validate_trajectory(traj):
                logger.warning(f"Validation failed for {system} seed {seed}, skipping.")
                continue
            
            # Save trajectory
            filename = f"{system}_clean_{seed}.csv"
            filepath = output_dir / filename
            traj.save_to_csv(filepath)
            
            # Save checksum
            checksum = compute_file_checksum(filepath)
            checksum_file = output_dir / f"{system}_clean_{seed}.sha256"
            with open(checksum_file, 'w') as f:
                f.write(checksum)
            
            generated_files.append(str(filepath))
            logger.info(f"Saved {filepath}")
            
    return generated_files

def inject_noise(traj_path: str, snr_db: float, noise_type: NoiseType, output_dir: Path):
    """Inject noise into a trajectory and save it."""
    traj = load_trajectory(traj_path)
    
    logger.info(f"Injecting {noise_type} noise at {snr_db}dB into {traj_path}")
    
    noisy_traj = add_noise_to_trajectory(traj, snr_db, noise_type)
    
    # Save noisy trajectory
    system_type = traj.system_type
    seed = traj.seed
    noise_suffix = "gaussian" if noise_type == NoiseType.GAUSSIAN else "quantization"
    filename = f"{system_type}_noisy_{noise_suffix}_{int(snr_db)}dB_{seed}.csv"
    filepath = output_dir / filename
    
    noisy_traj.save_to_csv(filepath)
    
    # Save metadata
    metadata = {
        "source_file": traj_path,
        "noise_type": noise_type.value,
        "target_snr_db": snr_db,
        "actual_snr_db": noisy_traj.actual_snr_db,
        "seed": seed,
        "system_type": system_type
    }
    metadata_path = output_dir / f"{filename.replace('.csv', '.json')}"
    write_json_artifact(metadata, str(metadata_path))
    
    logger.info(f"Saved noisy trajectory to {filepath}")
    return str(filepath)

def compute_metrics_for_all(noisy_files: List[str], ground_truth_dir: Path, metrics_dir: Path):
    """Compute metrics for all noisy trajectories and compare with ground truth."""
    metrics_dir = Path(metrics_dir)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    all_metrics = []
    
    for traj_file in noisy_files:
        logger.info(f"Computing metrics for {traj_file}")
        
        traj = load_trajectory(traj_file)
        metrics = compute_all_metrics(traj)
        
        # Load ground truth for comparison
        # Assuming ground truth is named based on seed
        seed = traj.seed
        gt_file = ground_truth_dir / f"ground_truth_metrics_{seed}.json"
        
        if gt_file.exists():
            gt_metrics = load_ground_truth_metrics(str(gt_file))
            # Add error calculation here if needed, or let analysis step handle it
            metrics["ground_truth"] = gt_metrics
        else:
            logger.warning(f"Ground truth not found for seed {seed}")
        
        # Save individual metrics
        output_name = Path(traj_file).stem + "_metrics.json"
        output_path = metrics_dir / output_name
        write_json_artifact(metrics, str(output_path))
        
        all_metrics.append(metrics)
        
    return all_metrics

def run_full_pipeline(systems: List[str], seeds: List[int], snr_levels: List[float], 
                     noise_types: List[NoiseType], output_root: Path, time_budget_seconds: int = 7200):
    """Run the full pipeline: generation -> noise -> metrics -> analysis -> export."""
    start_time = time.time()
    
    data_raw = output_root / "data" / "raw"
    data_processed = output_root / "data" / "processed"
    data_results = output_root / "data" / "results"
    
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    data_results.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate clean trajectories
    logger.info("=== Step 1: Generating Clean Trajectories ===")
    clean_files = generate_clean_trajectories(systems, seeds, data_raw)
    
    if not clean_files:
        logger.error("No clean trajectories generated. Aborting.")
        return
    
    # Step 2: Compute ground truth metrics (T017)
    logger.info("=== Step 2: Computing Ground Truth Metrics ===")
    for traj_file in clean_files:
        filename = Path(traj_file).name
        system, _, seed = filename.replace(".csv", "").split("_")
        metrics_file = data_processed / f"ground_truth_metrics_{seed}.json"
        
        # Compute and save
        compute_metrics_for_all([traj_file], data_raw, data_processed)
        # Rename to ground truth format
        src = data_processed / f"{filename.replace('.csv', '_metrics.json')}"
        if src.exists():
            src.rename(metrics_file)
            
    # Step 3: Inject noise
    logger.info("=== Step 3: Injecting Noise ===")
    noisy_files = []
    for traj_file in clean_files:
        for snr in snr_levels:
            for noise_type in noise_types:
                if time.time() - start_time > time_budget_seconds:
                    logger.warning("Time budget exceeded. Stopping noise injection.")
                    break
                
                noisy_path = inject_noise(traj_file, snr, noise_type, data_processed)
                noisy_files.append(noisy_path)
        if time.time() - start_time > time_budget_seconds:
            break
    
    # Step 4: Compute metrics for noisy data
    logger.info("=== Step 4: Computing Metrics for Noisy Data ===")
    noisy_metrics = compute_metrics_for_all(noisy_files, data_processed, data_processed)
    
    # Step 5: Analyze results
    logger.info("=== Step 5: Analyzing Results ===")
    analysis_results = analyze_results_from_files(data_processed, data_results)
    
    # Step 6: Visualization and Export
    logger.info("=== Step 6: Visualization and Export ===")
    run_visualization_pipeline(data_processed, data_results)
    
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")
    
    return analysis_results

def main():
    parser = argparse.ArgumentParser(description="Full Pipeline for Chaotic Time-Series Analysis")
    parser.add_argument("--systems", nargs='+', default=["lorenz", "rossler"], help="Systems to generate")
    parser.add_argument("--seeds", nargs='+', type=int, default=[42], help="Seeds to use")
    parser.add_argument("--snr-levels", nargs='+', type=float, default=[0, 10, 20, 30], help="SNR levels in dB")
    parser.add_argument("--noise-types", nargs='+', choices=["gaussian", "quantization"], default=["gaussian"], help="Noise types")
    parser.add_argument("--output-root", type=str, default=".", help="Project root directory")
    parser.add_argument("--time-budget", type=int, default=7200, help="Time budget in seconds (default 2h)")
    
    args = parser.parse_args()
    
    # Parse noise types
    noise_types = [NoiseType.GAUSSIAN if n == "gaussian" else NoiseType.QUANTIZATION for n in args.noise_types]
    
    output_root = Path(args.output_root)
    
    run_full_pipeline(
        systems=args.systems,
        seeds=args.seeds,
        snr_levels=args.snr_levels,
        noise_types=noise_types,
        output_root=output_root,
        time_budget_seconds=args.time_budget
    )

if __name__ == "__main__":
    main()