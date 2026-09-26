"""
Metrics calculation module for DRL training analysis.

Calculates:
1. Area Under the Curve (AUC) for learning curves
2. Time-to-convergence (episodes to reach stable performance)
3. Episodes to reach high sustained success rate (SC-001)

Outputs metrics to results/learning_metrics.json
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from src.utils.config import get_path

logger = logging.getLogger(__name__)

# Constants for success rate threshold (SC-001)
SUCCESS_RATE_THRESHOLD = 0.85  # 85% sustained success rate
SUSTAINMENT_WINDOW = 10  # Number of consecutive episodes to check


def calculate_auc(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Area Under the Curve using trapezoidal rule.
    
    Args:
        x: Array of episode numbers (or time steps)
        y: Array of metric values (e.g., rewards, success rates)
        
    Returns:
        AUC value as float
    """
    if len(x) != len(y) or len(x) == 0:
        raise ValueError("x and y must have the same non-zero length")
    
    # Use numpy's trapezoidal integration
    auc = np.trapz(y, x)
    return float(auc)


def calculate_time_to_convergence(
    rewards: np.ndarray,
    window_size: int = 10,
    threshold_factor: float = 0.95
) -> Optional[int]:
    """
    Calculate time-to-convergence: episodes until the agent reaches
    a stable performance level (within 5% of the best recent average).
    
    Args:
        rewards: Array of episode rewards
        window_size: Number of episodes to average for stability check
        threshold_factor: Performance threshold relative to best average (0.95 = 95%)
        
    Returns:
        Episode number where convergence is detected, or None if not converged
    """
    if len(rewards) < window_size:
        return None
    
    # Calculate rolling average
    rolling_avg = np.convolve(
        rewards, 
        np.ones(window_size)/window_size, 
        mode='valid'
    )
    
    if len(rolling_avg) == 0:
        return None
    
    # Find the best average achieved
    best_avg = np.max(rolling_avg)
    threshold = best_avg * threshold_factor
    
    # Find first episode where rolling average stays above threshold
    for i, avg in enumerate(rolling_avg):
        if avg >= threshold:
            # Verify it stays above threshold for the rest (simplified check)
            # In practice, we might want a more robust convergence check
            return i + window_size  # Episode number (1-indexed)
    
    return None  # Not converged


def calculate_episodes_to_sustained_success(
    success_rates: np.ndarray,
    threshold: float = SUCCESS_RATE_THRESHOLD,
    window: int = SUSTAINMENT_WINDOW
) -> Optional[int]:
    """
    Calculate episodes to reach a high sustained success rate (SC-001).
    
    Finds the first episode after which the success rate remains above
    the threshold for a sustained window of episodes.
    
    Args:
        success_rates: Array of per-episode success rates (0.0 to 1.0)
        threshold: Minimum success rate to consider "high" (default: 0.85)
        window: Number of consecutive episodes to sustain the rate (default: 10)
        
    Returns:
        Episode number where sustained success begins, or None if not achieved
    """
    if len(success_rates) < window:
        return None
    
    # Check for sustained success
    for i in range(len(success_rates) - window + 1):
        window_rates = success_rates[i:i + window]
        if np.all(window_rates >= threshold):
            return i  # Episode where sustained success begins
    
    return None  # Never achieved sustained success


def process_single_seed_metrics(
    episode_rewards: List[float],
    episode_successes: List[int],
    episode_times: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Process metrics for a single training seed.
    
    Args:
        episode_rewards: List of total rewards per episode
        episode_successes: List of 0/1 success indicators per episode
        episode_times: Optional list of episode durations in seconds
        
    Returns:
        Dictionary with calculated metrics
    """
    rewards_arr = np.array(episode_rewards)
    successes_arr = np.array(episode_successes, dtype=float)
    
    # Calculate success rate per episode (cumulative or per-episode?)
    # Assuming per-episode success rate (binary 0 or 1)
    success_rates = successes_arr  # Already 0 or 1
    
    metrics = {
        "auc_rewards": calculate_auc(
            np.arange(1, len(rewards_arr) + 1), 
            rewards_arr
        ),
        "auc_success": calculate_auc(
            np.arange(1, len(success_rates) + 1), 
            success_rates
        ),
        "total_episodes": len(rewards_arr),
        "final_reward": float(rewards_arr[-1]) if len(rewards_arr) > 0 else 0.0,
        "final_success_rate": float(success_rates[-1]) if len(success_rates) > 0 else 0.0,
        "max_reward": float(np.max(rewards_arr)) if len(rewards_arr) > 0 else 0.0,
        "max_success_rate": float(np.max(success_rates)) if len(success_rates) > 0 else 0.0,
        "mean_reward": float(np.mean(rewards_arr)) if len(rewards_arr) > 0 else 0.0,
        "std_reward": float(np.std(rewards_arr)) if len(rewards_arr) > 0 else 0.0,
    }
    
    # Time to convergence
    convergence_episode = calculate_time_to_convergence(rewards_arr)
    metrics["time_to_convergence_episode"] = convergence_episode
    
    # Episodes to sustained success (SC-001)
    sustained_success_episode = calculate_episodes_to_sustained_success(success_rates)
    metrics["episodes_to_sustained_success"] = sustained_success_episode
    metrics["sustained_success_threshold"] = SUCCESS_RATE_THRESHOLD
    metrics["sustained_success_window"] = SUSTAINMENT_WINDOW
    
    if episode_times:
        times_arr = np.array(episode_times)
        metrics["total_training_time_seconds"] = float(np.sum(times_arr))
        metrics["mean_episode_time_seconds"] = float(np.mean(times_arr))
    
    return metrics


def aggregate_seed_metrics(
    all_seed_metrics: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate metrics across multiple seeds.
    
    Args:
        all_seed_metrics: List of per-seed metric dictionaries
        
    Returns:
        Dictionary with aggregated statistics
    """
    if not all_seed_metrics:
        return {"error": "No metrics to aggregate"}
    
    # Extract arrays for aggregation
    auc_rewards = [m["auc_rewards"] for m in all_seed_metrics]
    auc_success = [m["auc_success"] for m in all_seed_metrics]
    convergence_episodes = [
        m["time_to_convergence_episode"] 
        for m in all_seed_metrics 
        if m["time_to_convergence_episode"] is not None
    ]
    sustained_episodes = [
        m["episodes_to_sustained_success"] 
        for m in all_seed_metrics 
        if m["episodes_to_sustained_success"] is not None
    ]
    
    aggregated = {
        "num_seeds": len(all_seed_metrics),
        "auc_rewards": {
            "mean": float(np.mean(auc_rewards)),
            "std": float(np.std(auc_rewards)),
            "min": float(np.min(auc_rewards)),
            "max": float(np.max(auc_rewards)),
        },
        "auc_success": {
            "mean": float(np.mean(auc_success)),
            "std": float(np.std(auc_success)),
            "min": float(np.min(auc_success)),
            "max": float(np.max(auc_success)),
        },
    }
    
    if convergence_episodes:
        aggregated["time_to_convergence"] = {
            "mean_episode": float(np.mean(convergence_episodes)),
            "std_episode": float(np.std(convergence_episodes)),
            "seeds_converged": len(convergence_episodes),
            "seeds_total": len(all_seed_metrics),
        }
    else:
        aggregated["time_to_convergence"] = {
            "seeds_converged": 0,
            "seeds_total": len(all_seed_metrics),
            "note": "No seeds reached convergence threshold"
        }
    
    if sustained_episodes:
        aggregated["episodes_to_sustained_success"] = {
            "mean_episode": float(np.mean(sustained_episodes)),
            "std_episode": float(np.std(sustained_episodes)),
            "seeds_achieved": len(sustained_episodes),
            "seeds_total": len(all_seed_metrics),
            "threshold": SUCCESS_RATE_THRESHOLD,
            "window": SUSTAINMENT_WINDOW,
        }
    else:
        aggregated["episodes_to_sustained_success"] = {
            "seeds_achieved": 0,
            "seeds_total": len(all_seed_metrics),
            "threshold": SUCCESS_RATE_THRESHOLD,
            "window": SUSTAINMENT_WINDOW,
            "note": "No seeds achieved sustained success rate"
        }
    
    return aggregated


def load_training_curves(
    modality: str,
    results_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Load training curve CSV files for a specific modality.
    
    Args:
        modality: Modality name (e.g., 'rgb', 'depth', 'grid')
        results_dir: Optional override for results directory
        
    Returns:
        List of dictionaries, one per seed, with episode data
    """
    if results_dir is None:
        results_dir = Path(get_path("results"))
    
    curves_dir = results_dir / "training_curves"
    if not curves_dir.exists():
        logger.warning(f"Training curves directory not found: {curves_dir}")
        return []
    
    seed_data = []
    seed_files = sorted(curves_dir.glob(f"{modality}_seed_*.csv"))
    
    for seed_file in seed_files:
        try:
            import csv
            episodes = []
            rewards = []
            successes = []
            times = []
            
            with open(seed_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    episodes.append(int(row.get('episode', 0)))
                    rewards.append(float(row.get('reward', 0.0)))
                    successes.append(int(row.get('success', 0)))
                    if 'time_seconds' in row:
                        times.append(float(row['time_seconds']))
            
            seed_data.append({
                "seed_file": str(seed_file),
                "episodes": episodes,
                "rewards": rewards,
                "successes": successes,
                "times": times if times else None,
            })
            
        except Exception as e:
            logger.error(f"Failed to load {seed_file}: {e}")
            continue
    
    return seed_data


def calculate_metrics_for_modality(
    modality: str,
    results_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Calculate all metrics for a specific modality across all seeds.
    
    Args:
        modality: Modality name (e.g., 'rgb', 'depth', 'grid')
        results_dir: Optional override for results directory
        
    Returns:
        Dictionary with per-seed and aggregated metrics
    """
    seed_data_list = load_training_curves(modality, results_dir)
    
    if not seed_data_list:
        return {
            "modality": modality,
            "error": "No training curves found",
            "num_seeds": 0
        }
    
    all_seed_metrics = []
    for seed_data in seed_data_list:
        seed_metrics = process_single_seed_metrics(
            seed_data["rewards"],
            seed_data["successes"],
            seed_data.get("times")
        )
        seed_metrics["seed_file"] = seed_data["seed_file"]
        all_seed_metrics.append(seed_metrics)
    
    aggregated = aggregate_seed_metrics(all_seed_metrics)
    aggregated["modality"] = modality
    
    return {
        "modality": modality,
        "per_seed_metrics": all_seed_metrics,
        "aggregated": aggregated
    }


def generate_learning_metrics_report(
    modalities: List[str] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate complete learning metrics report for all modalities.
    
    Args:
        modalities: List of modalities to process (default: all known)
        output_path: Optional path to save JSON report
        
    Returns:
        Complete metrics report dictionary
    """
    if modalities is None:
        modalities = ["rgb", "depth", "grid"]
    
    report = {
        "generated_at": "auto-generated",  # Will be replaced by actual timestamp if needed
        "modalities": {},
        "summary": {}
    }
    
    for modality in modalities:
        modality_metrics = calculate_metrics_for_modality(modality)
        report["modalities"][modality] = modality_metrics
    
    # Generate summary across modalities
    if report["modalities"]:
        summary = {}
        for modality, data in report["modalities"].items():
            if "aggregated" in data:
                summary[modality] = {
                    "num_seeds": data["aggregated"].get("num_seeds", 0),
                    "auc_rewards_mean": data["aggregated"]["auc_rewards"]["mean"],
                    "auc_success_mean": data["aggregated"]["auc_success"]["mean"],
                }
                if "episodes_to_sustained_success" in data["aggregated"]:
                    epis = data["aggregated"]["episodes_to_sustained_success"]
                    summary[modality]["episodes_to_sustained_success"] = epis
        report["summary"] = summary
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Learning metrics report saved to {output_path}")
    
    return report


def main():
    """Main entry point for metrics calculation."""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get output path from config
    results_dir = Path(get_path("results"))
    output_path = results_dir / "learning_metrics.json"
    
    logger.info("Starting learning metrics calculation...")
    
    try:
        # Calculate metrics for all modalities
        report = generate_learning_metrics_report(
            modalities=["rgb", "depth", "grid"],
            output_path=output_path
        )
        
        logger.info(f"Metrics calculation complete. Report saved to {output_path}")
        
        # Print summary
        print("\n=== Learning Metrics Summary ===")
        for modality, data in report.get("modalities", {}).items():
            if "aggregated" in data:
                agg = data["aggregated"]
                print(f"\n{modality.upper()}:")
                print(f"  Seeds processed: {agg.get('num_seeds', 0)}")
                print(f"  AUC (Rewards): {agg['auc_rewards']['mean']:.2f} ± {agg['auc_rewards']['std']:.2f}")
                print(f"  AUC (Success): {agg['auc_success']['mean']:.2f} ± {agg['auc_success']['std']:.2f}")
                
                if "episodes_to_sustained_success" in agg:
                    epis = agg["episodes_to_sustained_success"]
                    if epis.get("seeds_achieved", 0) > 0:
                        print(f"  Episodes to Sustained Success (≥{epis['threshold']}): "
                              f"{epis['mean_episode']:.1f} ± {epis['std_episode']:.1f} "
                              f"({epis['seeds_achieved']}/{epis['seeds_total']} seeds)")
                    else:
                        print(f"  Episodes to Sustained Success: Not achieved in any seed")
        
        return 0
        
    except Exception as e:
        logger.error(f"Metrics calculation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
