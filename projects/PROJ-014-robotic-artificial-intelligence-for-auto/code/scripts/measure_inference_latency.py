"""
Script to measure inference latency (ms/step) on CPU for trained DQN agents.

This script loads trained agents for each modality (RGB, Depth, Occupancy Grid),
runs inference on a fixed set of test steps, and reports the average, min, max,
and standard deviation of inference latency in milliseconds.

Output: results/latency_report.json
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from src.utils.config import get_path, get_hyperparameter, init_config
from src.agents.dqn_agent import create_dqn_agent, DQNConfig
from src.agents.memory import create_replay_buffer
from src.data.pipeline import create_rgb_preprocessor, create_depth_downsampler, create_occupancy_grid_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_trained_agent(modality: str, seed: int = 0) -> Any:
    """
    Load a trained DQN agent for the specified modality.
    
    Args:
        modality: One of 'rgb', 'depth', 'grid'
        seed: Training seed (default 0 for baseline measurement)
    
    Returns:
        DQNAgent instance
    """
    # Get config paths
    agent_path = get_path("agent_checkpoint", modality=modality, seed=seed)
    
    if not os.path.exists(agent_path):
        # Try to find any checkpoint for this modality
        base_dir = get_path("agent_dir", modality=modality)
        if os.path.exists(base_dir):
            checkpoints = list(Path(base_dir).glob("checkpoint_*.pt"))
            if checkpoints:
                agent_path = str(checkpoints[0])
                logger.info(f"Using alternative checkpoint: {agent_path}")
            else:
                raise FileNotFoundError(
                    f"No trained agent found for modality '{modality}'. "
                    f"Expected at: {agent_path}"
                )
        else:
            raise FileNotFoundError(
                f"Agent directory not found for modality '{modality}'. "
                f"Please run training first (T031)."
            )
    
    # Load agent from checkpoint
    # Note: This assumes the checkpoint contains the full agent state
    agent = create_dqn_agent(
        modality=modality,
        config=DQNConfig(
            observation_shape=(3, 84, 84) if modality == 'rgb' else 
                               (1, 42, 42) if modality == 'depth' else 
                               (1, 42, 42),
            action_dim=4,
            learning_rate=1e-4,
            gamma=0.99
        )
    )
    
    try:
        agent.load(agent_path)
        logger.info(f"Successfully loaded agent from {agent_path}")
    except Exception as e:
        logger.error(f"Failed to load agent: {e}")
        raise
    
    # Set to evaluation mode
    agent.policy.eval()
    return agent

def generate_test_observation(modality: str, device: str = 'cpu') -> torch.Tensor:
    """
    Generate a synthetic test observation matching the modality's expected shape.
    
    Note: This is ONLY for latency measurement. The actual values don't matter
    for timing inference, only the tensor shape and device.
    
    Args:
        modality: One of 'rgb', 'depth', 'grid'
        device: Target device ('cpu' or 'cuda')
    
    Returns:
        Tensor of shape (1, channels, height, width)
    """
    if modality == 'rgb':
        shape = (1, 3, 84, 84)
    elif modality == 'depth':
        shape = (1, 1, 42, 42)
    elif modality == 'grid':
        shape = (1, 1, 42, 42)
    else:
        raise ValueError(f"Unknown modality: {modality}")
    
    # Create random tensor - values don't matter for timing
    obs = torch.randn(shape, dtype=torch.float32, device=device)
    return obs

def measure_inference_latency(
    agent: Any,
    modality: str,
    num_steps: int = 100,
    warmup_steps: int = 10,
    device: str = 'cpu'
) -> Dict[str, float]:
    """
    Measure inference latency for a given agent.
    
    Args:
        agent: Trained DQNAgent
        modality: The modality type ('rgb', 'depth', 'grid')
        num_steps: Number of inference steps to measure
        warmup_steps: Number of warmup steps before timing starts
        device: Device to run inference on ('cpu' or 'cuda')
    
    Returns:
        Dictionary with latency statistics (ms)
    """
    # Ensure agent is in eval mode
    agent.policy.eval()
    
    # Move agent to device
    agent.policy.to(device)
    
    latencies = []
    
    # Warmup phase
    logger.info(f"Warming up for {warmup_steps} steps...")
    for _ in range(warmup_steps):
        obs = generate_test_observation(modality, device)
        with torch.no_grad():
            action = agent.act(obs, deterministic=True)
    
    # Measurement phase
    logger.info(f"Measuring inference latency for {num_steps} steps...")
    for i in range(num_steps):
        obs = generate_test_observation(modality, device)
        
        start_time = time.perf_counter()
        with torch.no_grad():
            action = agent.act(obs, deterministic=True)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
        
        if (i + 1) % 20 == 0:
            logger.debug(f"Completed {i + 1}/{num_steps} steps")
    
    # Calculate statistics
    latencies_np = np.array(latencies)
    
    stats = {
        "mean_ms": float(np.mean(latencies_np)),
        "median_ms": float(np.median(latencies_np)),
        "min_ms": float(np.min(latencies_np)),
        "max_ms": float(np.max(latencies_np)),
        "std_ms": float(np.std(latencies_np)),
        "p95_ms": float(np.percentile(latencies_np, 95)),
        "p99_ms": float(np.percentile(latencies_np, 99)),
        "num_steps": num_steps,
        "device": device
    }
    
    return stats

def run_latency_benchmark(
    modalities: List[str] = None,
    num_steps: int = 100,
    warmup_steps: int = 10,
    device: str = 'cpu'
) -> Dict[str, Dict[str, float]]:
    """
    Run latency benchmark for all modalities.
    
    Args:
        modalities: List of modalities to benchmark (default: all)
        num_steps: Number of inference steps per modality
        warmup_steps: Number of warmup steps
        device: Device to run on ('cpu' or 'cuda')
    
    Returns:
        Dictionary mapping modality to latency statistics
    """
    if modalities is None:
        modalities = ['rgb', 'depth', 'grid']
    
    results = {}
    
    for modality in modalities:
        logger.info(f"{'='*50}")
        logger.info(f"Benchmarking modality: {modality}")
        logger.info(f"{'='*50}")
        
        try:
            # Load agent
            agent = load_trained_agent(modality, seed=0)
            
            # Measure latency
            stats = measure_inference_latency(
                agent=agent,
                modality=modality,
                num_steps=num_steps,
                warmup_steps=warmup_steps,
                device=device
            )
            
            results[modality] = stats
            logger.info(f"  Mean latency: {stats['mean_ms']:.2f} ms")
            logger.info(f"  Median latency: {stats['median_ms']:.2f} ms")
            logger.info(f"  Std dev: {stats['std_ms']:.2f} ms")
            
        except FileNotFoundError as e:
            logger.warning(f"Skipping {modality}: {e}")
            results[modality] = {"error": str(e)}
        except Exception as e:
            logger.error(f"Error benchmarking {modality}: {e}")
            results[modality] = {"error": str(e)}
    
    return results

def save_latency_report(results: Dict[str, Dict[str, float]], output_path: str = None):
    """
    Save latency report to JSON file.
    
    Args:
        results: Dictionary of latency statistics
        output_path: Path to save the report (default: results/latency_report.json)
    """
    if output_path is None:
        output_path = get_path("latency_report")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": "Inference latency measurements (ms/step) on CPU for DQN agents",
        "note": "Latency measured on synthetic observations; actual inference may vary with real sensor data",
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Latency report saved to: {output_path}")
    return output_path

def main():
    """Main entry point for latency measurement script."""
    parser = argparse.ArgumentParser(
        description="Measure DQN inference latency on CPU"
    )
    parser.add_argument(
        "--modalities",
        nargs="+",
        default=None,
        choices=['rgb', 'depth', 'grid'],
        help="Modalities to benchmark (default: all)"
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=100,
        help="Number of inference steps to measure (default: 100)"
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=10,
        help="Number of warmup steps (default: 10)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default='cpu',
        choices=['cpu', 'cuda'],
        help="Device to run inference on (default: cpu)"
    )
    
    args = parser.parse_args()
    
    # Initialize config
    init_config()
    
    logger.info("Starting inference latency measurement...")
    logger.info(f"Modalities: {args.modalities or 'all'}")
    logger.info(f"Steps: {args.num_steps}")
    logger.info(f"Device: {args.device}")
    
    # Run benchmark
    results = run_latency_benchmark(
        modalities=args.modalities,
        num_steps=args.num_steps,
        warmup_steps=args.warmup_steps,
        device=args.device
    )
    
    # Save report
    output_path = save_latency_report(results)
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("LATENCY REPORT SUMMARY")
    logger.info("="*50)
    for modality, stats in results.items():
        if "error" in stats:
            logger.info(f"{modality}: ERROR - {stats['error']}")
        else:
            logger.info(f"{modality}:")
            logger.info(f"  Mean: {stats['mean_ms']:.2f} ms")
            logger.info(f"  Median: {stats['median_ms']:.2f} ms")
            logger.info(f"  Std: {stats['std_ms']:.2f} ms")
            logger.info(f"  Max: {stats['max_ms']:.2f} ms")
    
    logger.info(f"\nFull report saved to: {output_path}")
    return results

if __name__ == "__main__":
    main()
