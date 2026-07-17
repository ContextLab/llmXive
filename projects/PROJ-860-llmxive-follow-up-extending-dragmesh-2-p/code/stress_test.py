"""
Stress test script for VirtualTactileEstimator with noise injection.

This script validates the robustness of the VirtualTactileEstimator under
varying noise conditions, simulating real-world sensor imperfections.

It tests:
1. Moving average filter smoothing under high-frequency noise
2. Epsilon clamping stability near zero velocity
3. Linear correlation between k_est and ground-truth friction
4. Division-by-zero protection
"""
import os
import sys
import json
import logging
import argparse
import time
import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional, Any

# Import the estimator from the existing API surface
from estimator import VirtualTactileEstimator
from logging_config import get_logger, setup_all_loggers

# Constants for stress testing
DEFAULT_NOISE_LEVELS = [0.0, 0.1, 0.2, 0.5, 1.0]
DEFAULT_VELOCITY_RANGE = (0.01, 2.0)
DEFAULT_FRICTION_VALUES = [0.1, 0.3, 0.5, 0.7, 0.9]
DEFAULT_NUM_SAMPLES = 1000
DEFAULT_WINDOW_SIZE = 5
DEFAULT_EPSILON = 0.001

def generate_noisy_torque_velocity_pairs(
    friction_values: List[float],
    num_samples: int,
    noise_levels: List[float],
    velocity_range: Tuple[float, float],
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate synthetic torque/velocity pairs with controlled noise.
    
    Ground truth: torque = friction * velocity (simplified linear model)
    """
    if seed is not None:
        np.random.seed(seed)
    
    data = []
    for friction in friction_values:
        for noise_level in noise_levels:
            for _ in range(num_samples):
                # Generate ground truth velocity
                velocity = np.random.uniform(velocity_range[0], velocity_range[1])
                
                # Ground truth torque (linear relationship with friction)
                true_torque = friction * velocity
                
                # Add noise to both measurements
                noisy_velocity = velocity + np.random.normal(0, noise_level)
                noisy_torque = true_torque + np.random.normal(0, noise_level * 10)  # Torque noise scaled
                
                # Ensure velocity doesn't go negative (physical constraint)
                noisy_velocity = max(noisy_velocity, 0.0001)
                
                data.append({
                    'friction': friction,
                    'noise_level': noise_level,
                    'true_velocity': velocity,
                    'true_torque': true_torque,
                    'noisy_velocity': noisy_velocity,
                    'noisy_torque': noisy_torque
                })
    
    return data

def run_stress_test(
    noise_levels: List[float],
    friction_values: List[float],
    num_samples: int,
    window_size: int,
    epsilon: float,
    seed: Optional[int] = None,
    output_dir: str = "data/stress_test_results"
) -> Dict[str, Any]:
    """
    Run the full stress test suite on the VirtualTactileEstimator.
    
    Returns a dictionary containing test results and statistics.
    """
    # Setup logging
    logger = get_logger("stress_test")
    logger.info(f"Starting stress test with {len(noise_levels)} noise levels, "
               f"{len(friction_values)} friction values, {num_samples} samples each")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate test data
    test_data = generate_noisy_torque_velocity_pairs(
        friction_values=friction_values,
        num_samples=num_samples,
        noise_levels=noise_levels,
        velocity_range=DEFAULT_VELOCITY_RANGE,
        seed=seed
    )
    
    logger.info(f"Generated {len(test_data)} test samples")
    
    # Initialize estimator
    estimator = VirtualTactileEstimator(
        window_size=window_size,
        epsilon=epsilon
    )
    
    # Results storage
    results = {
        'test_parameters': {
            'noise_levels': noise_levels,
            'friction_values': friction_values,
            'num_samples': num_samples,
            'window_size': window_size,
            'epsilon': epsilon,
            'seed': seed
        },
        'per_condition_results': [],
        'overall_statistics': {}
    }
    
    # Track all k_est values for correlation analysis
    all_true_frictions = []
    all_estimated_k = []
    
    # Process each sample
    for i, sample in enumerate(test_data):
        # Reset estimator for each friction condition to avoid cross-contamination
        if i > 0 and (sample['friction'] != test_data[i-1]['friction'] or 
                     sample['noise_level'] != test_data[i-1]['noise_level']):
            estimator.reset()
        
        # Feed data to estimator
        k_est = estimator.update(
            torque=sample['noisy_torque'],
            velocity=sample['noisy_velocity']
        )
        
        # Store results
        result_entry = {
            'sample_id': i,
            'friction': sample['friction'],
            'noise_level': sample['noise_level'],
            'true_velocity': sample['true_velocity'],
            'true_torque': sample['true_torque'],
            'noisy_velocity': sample['noisy_velocity'],
            'noisy_torque': sample['noisy_torque'],
            'estimated_k': k_est,
            'is_clamped': estimator.is_clamped,
            'window_count': len(estimator.velocity_history)
        }
        
        results['per_condition_results'].append(result_entry)
        
        # Collect for correlation analysis (only after warm-up period)
        if len(estimator.velocity_history) >= window_size:
            all_true_frictions.append(sample['friction'])
            all_estimated_k.append(k_est)
        
        # Progress logging
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1}/{len(test_data)} samples")
    
    # Calculate overall statistics
    if all_true_frictions:
        correlation = np.corrcoef(all_true_frictions, all_estimated_k)[0, 1]
        mse = np.mean((np.array(all_true_frictions) - np.array(all_estimated_k)) ** 2)
        rmse = np.sqrt(mse)
        
        results['overall_statistics'] = {
            'correlation_coefficient': float(correlation),
            'mean_squared_error': float(mse),
            'root_mean_squared_error': float(rmse),
            'total_samples_processed': len(all_true_frictions),
            'warmup_samples_skipped': len(test_data) - len(all_true_frictions)
        }
        
        logger.info(f"Correlation (k_est vs friction): {correlation:.4f}")
        logger.info(f"RMSE: {rmse:.4f}")
    else:
        logger.warning("No samples passed warm-up period for correlation analysis")
        results['overall_statistics'] = {
            'error': 'Insufficient data for correlation analysis'
        }
    
    # Check for division-by-zero protection
    clamped_count = sum(1 for r in results['per_condition_results'] if r['is_clamped'])
    results['overall_statistics']['clamped_samples'] = clamped_count
    results['overall_statistics']['clamping_rate'] = clamped_count / len(results['per_condition_results'])
    
    logger.info(f"Clamping rate: {results['overall_statistics']['clamping_rate']:.4f}")
    
    # Write results to JSON
    output_file = os.path.join(output_dir, "stress_test_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")
    
    # Write summary CSV for quick analysis
    summary_file = os.path.join(output_dir, "stress_test_summary.csv")
    with open(summary_file, 'w') as f:
        f.write("friction,noise_level,count,mean_k_est,std_k_est\n")
        
        # Aggregate by condition
        condition_stats = {}
        for r in results['per_condition_results']:
            key = (r['friction'], r['noise_level'])
            if key not in condition_stats:
                condition_stats[key] = {'k_est': [], 'count': 0}
            condition_stats[key]['k_est'].append(r['estimated_k'])
            condition_stats[key]['count'] += 1
        
        for (friction, noise), stats in condition_stats.items():
            k_est_array = np.array(stats['k_est'])
            mean_k = np.mean(k_est_array)
            std_k = np.std(k_est_array)
            f.write(f"{friction},{noise},{stats['count']},{mean_k:.6f},{std_k:.6f}\n")
    
    logger.info(f"Summary written to {summary_file}")
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Stress test VirtualTactileEstimator with noise injection"
    )
    parser.add_argument(
        '--noise-levels',
        type=float,
        nargs='+',
        default=DEFAULT_NOISE_LEVELS,
        help='Noise levels to test (default: {})'.format(DEFAULT_NOISE_LEVELS)
    )
    parser.add_argument(
        '--friction-values',
        type=float,
        nargs='+',
        default=DEFAULT_FRICTION_VALUES,
        help='Friction values to test (default: {})'.format(DEFAULT_FRICTION_VALUES)
    )
    parser.add_argument(
        '--num-samples',
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help='Number of samples per condition (default: {})'.format(DEFAULT_NUM_SAMPLES)
    )
    parser.add_argument(
        '--window-size',
        type=int,
        default=DEFAULT_WINDOW_SIZE,
        help='Moving average window size (default: {})'.format(DEFAULT_WINDOW_SIZE)
    )
    parser.add_argument(
        '--epsilon',
        type=float,
        default=DEFAULT_EPSILON,
        help='Epsilon for clamping (default: {})'.format(DEFAULT_EPSILON)
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default="data/stress_test_results",
        help='Output directory for results (default: data/stress_test_results)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file path (default: None)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.log_file:
        setup_all_loggers(log_file=args.log_file)
    
    logger = get_logger("stress_test")
    logger.info("Starting VirtualTactileEstimator stress test")
    
    start_time = time.time()
    
    try:
        results = run_stress_test(
            noise_levels=args.noise_levels,
            friction_values=args.friction_values,
            num_samples=args.num_samples,
            window_size=args.window_size,
            epsilon=args.epsilon,
            seed=args.seed,
            output_dir=args.output_dir
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Stress test completed in {elapsed_time:.2f} seconds")
        
        # Print summary
        print("\n" + "="*60)
        print("STRESS TEST SUMMARY")
        print("="*60)
        print(f"Noise levels tested: {args.noise_levels}")
        print(f"Friction values tested: {args.friction_values}")
        print(f"Total samples: {args.num_samples * len(args.noise_levels) * len(args.friction_values)}")
        print(f"Window size: {args.window_size}")
        print(f"Epsilon: {args.epsilon}")
        print(f"Seed: {args.seed}")
        print(f"Time elapsed: {elapsed_time:.2f}s")
        
        if 'correlation_coefficient' in results['overall_statistics']:
            print(f"\nCorrelation (k_est vs friction): {results['overall_statistics']['correlation_coefficient']:.4f}")
            print(f"RMSE: {results['overall_statistics']['root_mean_squared_error']:.4f}")
            print(f"Clamping rate: {results['overall_statistics']['clamping_rate']:.4f}")
        
        print(f"\nResults saved to: {args.output_dir}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Stress test failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()