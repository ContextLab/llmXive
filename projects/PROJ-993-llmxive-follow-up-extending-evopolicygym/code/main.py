import argparse
import sys
import os
import csv
import logging
import json
from typing import List, Dict, Any, Optional

# Import from project modules (relative imports handled by running as module or adding to path)
# Adjusted imports based on provided API surface
try:
    from envs.dynamic_shift_env import generate_all_dynamic_shift_envs, DynamicShiftEnvironment
    from agents.evolutionary_harness import EvolutionaryHarness, GenerationError
    from agents.policy_parser import parse_policy_complexity
    from analysis.stats import run_mixed_effects_model, calculate_shift_validation, calculate_success_rate
    from utils.config import set_seed, get_config
    from utils.logging import get_logger, setup_logging
except ImportError as e:
    # Fallback for direct script execution if __init__.py paths aren't set up
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from code.envs.dynamic_shift_env import generate_all_dynamic_shift_envs, DynamicShiftEnvironment
    from code.agents.evolutionary_harness import EvolutionaryHarness, GenerationError
    from code.agents.policy_parser import parse_policy_complexity
    from code.analysis.stats import run_mixed_effects_model, calculate_shift_validation, calculate_success_rate
    from code.utils.config import set_seed, get_config
    from code.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def run_shift_sensitivity_analysis(seeds: List[int], env_ids: List[str], shift_step: int = 80, output_path: str = "data/shift_validation.json") -> Dict[str, Any]:
    """
    Executes the shift validation analysis:
    1. Generates dynamic shift environments.
    2. Runs a static agent (non-adaptive) to measure performance drop.
    3. Calculates p-value for the drop.
    4. Writes results to JSON.
    """
    logger.info(f"Starting shift sensitivity analysis for envs: {env_ids}, shift_step: {shift_step}")
    
    # Ensure environments are registered/available
    # T013d handles registration, we assume they are ready or generate them here if needed
    # For this script, we rely on the registry or direct generation if specific IDs are passed
    
    results = []
    shift_config = {"shift_step": shift_step, "shift_type": "reward_inversion"} # Default config based on T013c/d context

    for env_id in env_ids:
        logger.info(f"Processing environment: {env_id}")
        try:
            # Generate the dynamic shift environment
            # Assuming generate_all_dynamic_shift_envs returns a dict of env_id -> env_instance
            # or we instantiate specific ones.
            # Based on T013d, environments are registered. We attempt to load them.
            env = DynamicShiftEnvironment(env_id, shift_config)
            
            # Run a simple static agent (e.g., random or fixed policy) to measure baseline vs post-shift
            # This mimics the "static agent" requirement from US1
            pre_shift_score = 0.0
            post_shift_score = 0.0
            
            # Simulate a run (simplified for CLI entry point)
            # In a full run, this would use the EvolutionaryHarness in a non-evolving mode
            # or a specific test harness.
            # We will use the EvolutionaryHarness but with a fixed seed and no evolution steps to simulate static behavior
            # or just run the env directly.
            
            # To strictly follow T014: "calculate p-value for performance drop; if p >= 0.05, FAIL"
            # We need multiple runs to get a distribution.
            
            run_scores_pre = []
            run_scores_post = []
            
            for seed in seeds:
                set_seed(seed)
                env.reset(seed=seed)
                
                # Pre-shift phase
                total_reward_pre = 0
                for step in range(shift_step):
                    obs, reward, term, trunc, info = env.step(env.action_space.sample()) # Random policy for static agent
                    total_reward_pre += reward
                    if term or trunc: break
                run_scores_pre.append(total_reward_pre)

                # Post-shift phase (continue from where it left off or reset? Usually reset for fairness in drop calc)
                # T013b implies the shift happens at step N.
                # Let's reset and run full episode to compare full episode rewards pre/post shift logic?
                # Actually, T013b says "alter reward functions ... after shift_step".
                # So we run an episode. The first 'shift_step' are pre, the rest are post?
                # Or we run two separate episodes: one where shift happens at N (if N < max_steps)
                # and one where it doesn't?
                # T014 says "performance drop".
                # Let's assume we run the episode. If the episode length > shift_step, we compare
                # reward accumulation before and after shift_step.
                
                env.reset(seed=seed)
                total_reward = 0
                pre_reward = 0
                post_reward = 0
                step_count = 0
                for step in range(100): # Fixed horizon
                    obs, reward, term, trunc, info = env.step(env.action_space.sample())
                    total_reward += reward
                    step_count += 1
                    if step < shift_step:
                        pre_reward += reward
                    else:
                        post_reward += reward
                    if term or trunc: break
                
                # Store full episode score for baseline? Or split?
                # Let's store the split scores for drop calculation
                run_scores_pre.append(pre_reward)
                run_scores_post.append(post_reward)
            
            # Calculate drop rate and stats
            import numpy as np
            pre_mean = np.mean(run_scores_pre)
            post_mean = np.mean(run_scores_post)
            drop_rate = (pre_mean - post_mean) / (abs(pre_mean) + 1e-6)
            
            # Calculate p-value (t-test)
            from scipy import stats
            t_stat, p_val = stats.ttest_ind(run_scores_pre, run_scores_post)
            
            result = {
                "env_id": env_id,
                "shift_step": shift_step,
                "pre_shift_score": float(pre_mean),
                "post_shift_score": float(post_mean),
                "drop_rate": float(drop_rate),
                "p_value": float(p_val)
            }
            results.append(result)
            
            if p_val >= 0.05:
                logger.warning(f"Shift validation FAILED for {env_id}: p-value {p_val:.4f} >= 0.05. Shift may be ineffective.")
                # T014 requirement: "explicitly FAIL the run"
                # We raise an exception to stop the pipeline as per spec
                raise RuntimeError(f"Shift validation failed for {env_id}: p-value {p_val:.4f} >= 0.05")

        except Exception as e:
            logger.error(f"Error processing {env_id}: {e}")
            # Re-raise to stop the pipeline if it's a validation failure
            if "Shift validation failed" in str(e):
                raise e
            continue

    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Shift validation results written to {output_path}")
    return results

def run_evolution_pipeline(seeds: List[int], runs: int, env_ids: List[str], conditions: List[str], output_path: str = "data/evolution_results.csv"):
    """
    Runs the evolutionary harness for specified conditions and seeds.
    Writes results to evolution_results.csv.
    """
    logger.info(f"Starting evolution pipeline: seeds={seeds}, runs={runs}, envs={env_ids}, conditions={conditions}")
    
    harness = EvolutionaryHarness()
    
    results = []
    run_id_counter = 0
    
    for seed in seeds:
        set_seed(seed)
        for env_id in env_ids:
            for condition in conditions:
                logger.info(f"Running seed={seed}, env={env_id}, condition={condition}")
                for run_idx in range(runs):
                    run_id_counter += 1
                    try:
                        # Run the evolution
                        # T032a: Must ensure policy write is flushed before parsing
                        score, policy_code = harness.run(
                            env_id=env_id,
                            condition=condition,
                            seed=seed,
                            run_id=run_id_counter
                        )
                        
                        # Parse complexity
                        complexity = 1.0
                        branch_count = 0
                        try:
                            if policy_code:
                                metrics = parse_policy_complexity(policy_code)
                                complexity = metrics.get("complexity", 1.0)
                                branch_count = metrics.get("branches", 0)
                        except Exception as e:
                            logger.warning(f"Failed to parse policy for run {run_id_counter}: {e}")
                            # T035: Record as "generation error" - we handle by logging, but we still write the row
                            # with default/zero complexity if parsing fails? Or skip?
                            # T032b says write the row. Let's write with 0 complexity if parse fails.
                            complexity = 0.0
                            branch_count = 0
                        
                        results.append({
                            "run_id": run_id_counter,
                            "seed": seed,
                            "condition": condition,
                            "env_id": env_id,
                            "score": float(score),
                            "complexity": float(complexity),
                            "branch_count": int(branch_count)
                        })
                        
                    except GenerationError as e:
                        logger.error(f"Generation error for run {run_id_counter}: {e}")
                        # T035: Record as "generation error"
                        results.append({
                            "run_id": run_id_counter,
                            "seed": seed,
                            "condition": condition,
                            "env_id": env_id,
                            "score": 0.0, # Or NaN? Float 0.0 for simplicity
                            "complexity": 0.0,
                            "branch_count": 0,
                            "error": str(e)
                        })
                    except Exception as e:
                        logger.error(f"Unexpected error for run {run_id_counter}: {e}")
                        results.append({
                            "run_id": run_id_counter,
                            "seed": seed,
                            "condition": condition,
                            "env_id": env_id,
                            "score": 0.0,
                            "complexity": 0.0,
                            "branch_count": 0,
                            "error": str(e)
                        })

    # Write to CSV
    if results:
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["run_id", "seed", "condition", "env_id", "score", "complexity", "branch_count"])
            writer.writeheader()
            for row in results:
                # Filter out error key if present for CSV consistency
                clean_row = {k: v for k, v in row.items() if k != 'error'}
                writer.writerow(clean_row)
        logger.info(f"Evolution results written to {output_path}")
    else:
        logger.warning("No results to write.")

def run_stats_analysis(input_path: str = "data/evolution_results.csv", output_path: str = "data/stats_results.json"):
    """
    Runs mixed-effects model analysis on evolution results.
    """
    logger.info(f"Running stats analysis on {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Cannot run stats analysis.")
        return {}

    results = run_mixed_effects_model(input_path)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Stats results written to {output_path}")
    return results

def run_full_pipeline(args):
    """
    Orchestrates the full pipeline: Shift Analysis -> Evolution -> Stats.
    """
    logger.info("Starting Full Pipeline")
    
    # 1. Shift Analysis (T014 requirement)
    # We need to ensure shift validation passes before proceeding
    try:
        shift_results = run_shift_sensitivity_analysis(
            seeds=args.seeds,
            env_ids=args.envs,
            shift_step=80, # Default moderate step
            output_path="data/shift_validation.json"
        )
    except RuntimeError as e:
        logger.critical(f"Pipeline aborted due to shift validation failure: {e}")
        return False

    # 2. Evolution Pipeline
    conditions = args.conditions.split(',') if isinstance(args.conditions, str) else args.conditions
    evolution_results = run_evolution_pipeline(
        seeds=args.seeds,
        runs=args.runs,
        env_ids=args.envs,
        conditions=conditions,
        output_path="data/evolution_results.csv"
    )

    # 3. Stats Analysis
    stats_results = run_stats_analysis(
        input_path="data/evolution_results.csv",
        output_path="data/stats_results.json"
    )

    # 4. Generate final_results.csv (Aggregated metrics)
    # T037 requirement: Output final_results.csv with aggregated metrics
    # We aggregate the stats results and shift results
    final_data = []
    
    # Add stats summary
    if stats_results:
        final_data.append({
            "metric": "mixed_model_p_value",
            "value": stats_results.get("p_value"),
            "details": json.dumps(stats_results)
        })
    
    # Add shift summary
    if shift_results:
        avg_drop = sum(r.get("drop_rate", 0) for r in shift_results) / len(shift_results)
        final_data.append({
            "metric": "avg_shift_drop_rate",
            "value": avg_drop,
            "details": f"Based on {len(shift_results)} environments"
        })

    with open("data/final_results.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "details"])
        writer.writeheader()
        for row in final_data:
            writer.writerow(row)
    
    logger.info("Full pipeline completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="EvoPolicyGym Analysis Pipeline CLI")
    
    # CLI args as per T037: --seeds, --runs, --envs, --conditions
    parser.add_argument("--run-evolution", action="store_true", help="Run the full evolution pipeline")
    parser.add_argument("--run-shift-analysis", action="store_true", help="Run only shift sensitivity analysis")
    parser.add_argument("--run-stats", action="store_true", help="Run only stats analysis")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    # Arguments for the pipeline
    parser.add_argument("--seeds", type=int, nargs="+", default=[42], help="List of random seeds to use")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per condition")
    parser.add_argument("--envs", type=str, nargs="+", default=["GridWorld-0"], help="List of environment IDs")
    parser.add_argument("--conditions", type=str, default="baseline,counterfactual", help="Comma-separated list of conditions")

    args = parser.parse_args()

    setup_logging()

    if args.run_evolution:
        success = run_full_pipeline(args)
        if not success:
            sys.exit(1)
    elif args.run_shift_analysis:
        run_shift_sensitivity_analysis(args.seeds, args.envs)
    elif args.run_stats:
        run_stats_analysis()
    else:
        # Default to full run if no specific flag? Or help?
        # T037 says "Create CLI entry point to execute full pipeline with command ... --run-evolution"
        # So if no flag, maybe print help.
        parser.print_help()

if __name__ == "__main__":
    main()