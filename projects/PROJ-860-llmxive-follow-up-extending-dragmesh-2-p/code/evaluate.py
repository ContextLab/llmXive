import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Import from project API surface
from environment import PhysicsEnvironment, create_cpu_environment
from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from baseline_runner import StaticBaselinePolicy, run_baseline_episode
from seed_config import set_seeds, init_reproducibility

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/evaluation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def load_generated_objects(data_dir: str) -> List[str]:
    """
    Load list of generated object file paths from the data/generated directory.
    Expects .xml or .urdf files produced by generator.py (T007a).
    """
    gen_dir = Path(data_dir) / "generated"
    if not gen_dir.exists():
        raise FileNotFoundError(f"Generated data directory not found: {gen_dir}")
    
    # Support both .xml and .urdf
    files = list(gen_dir.glob("*.xml")) + list(gen_dir.glob("*.urdf"))
    if not files:
        raise FileNotFoundError(f"No geometry files found in {gen_dir}")
    
    return sorted([str(f) for f in files])

def run_adaptive_episode(
    env: PhysicsEnvironment,
    object_path: str,
    estimator: VirtualTactileEstimator,
    scheduler: AdaptiveRewardScheduler,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single episode using the adaptive policy.
    Returns success status and episode metrics.
    """
    set_seeds(seed)
    env.reset()
    
    # Load object with randomized friction (simulating novel object)
    # The generator already created these with varying friction, we just load them
    env.load_object(object_path)
    
    episode_success = False
    steps = 0
    max_steps = 500
    total_reward = 0.0
    k_est_history = []
    
    for _ in range(max_steps):
        # Get current state
        state = env.get_state()
        
        # Estimate virtual tactile stiffness
        k_est = estimator.update(state)
        k_est_history.append(k_est)
        
        # Get adaptive reward weights
        reward_weights = scheduler.get_weights(k_est)
        
        # Compute action (simplified policy for evaluation)
        # In a full RL setup, this would be a learned policy network
        action = env.compute_adaptive_action(state, reward_weights)
        
        # Step environment
        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        
        # Check success condition (object grasped/stable)
        if info.get('grasp_success', False):
            episode_success = True
            break
        
        if done:
            break
    
    return {
        'success': episode_success,
        'steps': steps,
        'total_reward': total_reward,
        'k_est_final': k_est_history[-1] if k_est_history else 0.0,
        'k_est_mean': float(np.mean(k_est_history)) if k_est_history else 0.0
    }

def run_static_episode(
    env: PhysicsEnvironment,
    object_path: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single episode using the static baseline policy.
    Returns success status and episode metrics.
    """
    set_seeds(seed)
    env.reset()
    
    env.load_object(object_path)
    
    # Use the static baseline policy from baseline_runner
    # We wrap it to match our return format
    baseline_policy = StaticBaselinePolicy()
    result = run_baseline_episode(env, baseline_policy, seed)
    
    return {
        'success': result.get('success', False),
        'steps': result.get('steps', 0),
        'total_reward': result.get('total_reward', 0.0),
        'k_est_final': result.get('k_est_final', 0.0),
        'k_est_mean': result.get('k_est_mean', 0.0)
    }

def evaluate_policy_pair(
    object_path: str,
    object_id: str,
    seed_base: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Evaluate both adaptive and static policies on the same object with paired seeds.
    Returns results for both policies.
    """
    # Create environment once per object (paired evaluation)
    env = create_cpu_environment()
    
    # Initialize components for adaptive policy
    estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
    scheduler = AdaptiveRewardScheduler()
    
    # Run adaptive episode
    seed_adaptive = seed_base
    adaptive_result = run_adaptive_episode(
        env, object_path, estimator, scheduler, seed_adaptive
    )
    
    # Reset environment for static episode (same object, different seed)
    env.reset()
    env.load_object(object_path)
    
    # Run static episode
    seed_static = seed_base + 1000  # Offset seed for static policy
    static_result = run_static_episode(env, object_path, seed_static)
    
    env.close()
    
    return adaptive_result, static_result

def main():
    parser = argparse.ArgumentParser(description='Evaluate adaptive vs static policies on novel objects')
    parser.add_argument('--data-dir', type=str, default='data',
                      help='Base directory for data (default: data)')
    parser.add_argument('--output-dir', type=str, default='data/results',
                      help='Directory for evaluation results (default: data/results)')
    parser.add_argument('--seed', type=int, default=42,
                      help='Base random seed for reproducibility')
    parser.add_argument('--num-objects', type=int, default=None,
                      help='Number of objects to evaluate (None = all)')
    
    args = parser.parse_args()
    
    # Initialize reproducibility
    init_reproducibility(args.seed)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading generated objects from {args.data_dir}/generated")
    object_files = load_generated_objects(args.data_dir)
    
    if args.num_objects:
        object_files = object_files[:args.num_objects]
    
    logger.info(f"Evaluating {len(object_files)} objects")
    
    results = []
    
    for idx, object_path in enumerate(object_files):
        object_id = Path(object_path).stem
        logger.info(f"Evaluating object {idx+1}/{len(object_files)}: {object_id}")
        
        try:
            adaptive_result, static_result = evaluate_policy_pair(
                object_path, object_id, args.seed + idx
            )
            
            result_record = {
                'object_id': object_id,
                'object_path': object_path,
                'policy_type': 'adaptive',
                'success': adaptive_result['success'],
                'steps': adaptive_result['steps'],
                'total_reward': adaptive_result['total_reward'],
                'k_est_final': adaptive_result['k_est_final'],
                'k_est_mean': adaptive_result['k_est_mean']
            }
            results.append(result_record)
            
            result_record = {
                'object_id': object_id,
                'object_path': object_path,
                'policy_type': 'static',
                'success': static_result['success'],
                'steps': static_result['steps'],
                'total_reward': static_result['total_reward'],
                'k_est_final': static_result['k_est_final'],
                'k_est_mean': static_result['k_est_mean']
            }
            results.append(result_record)
            
        except Exception as e:
            logger.error(f"Failed to evaluate object {object_id}: {str(e)}")
            # Log failure but continue with other objects
            results.append({
                'object_id': object_id,
                'policy_type': 'adaptive',
                'success': False,
                'error': str(e)
            })
            results.append({
                'object_id': object_id,
                'policy_type': 'static',
                'success': False,
                'error': str(e)
            })
    
    # Save results to JSON
    output_file = output_dir / "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation complete. Results saved to {output_file}")
    
    # Compute summary statistics
    adaptive_successes = [r for r in results if r['policy_type'] == 'adaptive' and r.get('success', False)]
    static_successes = [r for r in results if r['policy_type'] == 'static' and r.get('success', False)]
    
    adaptive_rate = len(adaptive_successes) / len([r for r in results if r['policy_type'] == 'adaptive']) if results else 0
    static_rate = len(static_successes) / len([r for r in results if r['policy_type'] == 'static']) if results else 0
    
    logger.info(f"Adaptive success rate: {adaptive_rate:.2%} ({len(adaptive_successes)}/{len([r for r in results if r['policy_type'] == 'adaptive'])})")
    logger.info(f"Static success rate: {static_rate:.2%} ({len(static_successes)}/{len([r for r in results if r['policy_type'] == 'static'])})")
    
    if static_rate > 0:
        improvement = ((adaptive_rate - static_rate) / static_rate) * 100
        logger.info(f"Improvement over static: {improvement:.2f}%")
    
    return results

if __name__ == '__main__':
    main()