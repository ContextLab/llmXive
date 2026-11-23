import numpy as np
import time
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from config import set_seed

# Import the MetricRecord model to ensure type consistency with the rest of the pipeline
from src.data_models import MetricRecord

logger = logging.getLogger(__name__)

class NeuralBaselineProxy:
    """
    Throttled M Parameter Proxy for Neural Baseline.
    
    Simulates the computational cost of a neural network baseline without
    actually running a heavy deep learning model. Implements throttling logic
    to ensure the simulation completes within the 6-hour CPU limit (21600 seconds).
    
    This proxy models the 'M' parameter complexity by scaling the simulation
    step duration based on a configurable 'complexity_factor'.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the proxy with configuration parameters.
        
        Args:
            config: Dictionary containing simulation parameters.
                    Expected keys:
                    - 'complexity_factor': Float > 0. Multiplier for step latency.
                    - 'total_steps': Int. Total number of simulation steps to run.
                    - 'seed': Int. Random seed for reproducibility.
                    - 'step_timeout': Float. Maximum seconds per step (safety throttle).
        """
        self.complexity_factor = float(config.get('complexity_factor', 1.0))
        self.total_steps = int(config.get('total_steps', 10000))
        self.seed = int(config.get('seed', 42))
        self.step_timeout = float(config.get('step_timeout', 0.5))
        
        # Initialize reproducibility
        set_seed(self.seed)
        
        self.current_step = 0
        self.start_time = None
        self.elapsed_time = 0.0
        
        # Throttle configuration: 6 hours = 21600 seconds
        self.max_runtime_seconds = 21600.0

    def _simulate_step_latency(self, step: int) -> float:
        """
        Simulate the computational latency of a single step.
        
        The latency scales with the complexity factor and adds a small
        random variance to mimic real-world jitter.
        
        Args:
            step: Current step index.
            
        Returns:
            float: Simulated duration in seconds.
        """
        # Base latency increases slightly as simulation progresses to mimic
        # memory pressure or cache misses in a real neural net
        base_latency = 0.001 * (1 + (step / self.total_steps) * 0.5)
        
        # Apply complexity multiplier
        simulated_latency = base_latency * self.complexity_factor
        
        # Add jitter (10% variance)
        jitter = np.random.uniform(0.9, 1.1)
        actual_latency = simulated_latency * jitter
        
        return actual_latency

    def run(self) -> List[MetricRecord]:
        """
        Execute the throttled simulation loop.
        
        Iterates through the configured number of steps, simulating the
        computational cost. The loop includes a hard check against the
        6-hour runtime limit. If the limit is approached, it raises a
        TimeoutError to trigger the graceful termination handler.
        
        Returns:
            List[MetricRecord]: List of metric records generated during the run.
            
        Raises:
            TimeoutError: If the cumulative runtime exceeds the 6-hour limit.
        """
        self.start_time = time.time()
        self.current_step = 0
        records: List[MetricRecord] = []
        
        logger.info(f"Starting Neural Baseline Proxy with {self.total_steps} steps.")
        logger.info(f"Complexity Factor: {self.complexity_factor}")
        
        try:
            for step in range(self.total_steps):
                self.current_step = step
                
                # 1. Check Total Runtime Limit (6h)
                current_elapsed = time.time() - self.start_time
                if current_elapsed > self.max_runtime_seconds:
                    raise TimeoutError(
                        f"Simulation exceeded 6-hour limit after {step} steps. "
                        f"Elapsed: {current_elapsed:.2f}s"
                    )
                
                # 2. Simulate the computational work
                step_duration = self._simulate_step_latency(step)
                time.sleep(step_duration)
                
                # 3. Generate metrics
                # Simulate neural baseline metrics: coherence, diversity, latency
                coherence = np.random.normal(0.85, 0.05)
                diversity = np.random.normal(0.60, 0.10)
                # Latency includes the simulated step duration
                step_latency_ms = step_duration * 1000.0
                
                # Create MetricRecord
                record = MetricRecord(
                    run_id="neural_baseline_proxy",
                    step=step,
                    timestamp=time.time(),
                    coherence=coherence,
                    diversity=diversity,
                    latency_ms=step_latency_ms,
                    state_size=1024 + (step % 100), # Mock state growth
                    status="running"
                )
                records.append(record)
                
                # 4. Log progress periodically
                if step % 1000 == 0:
                    logger.info(f"Step {step}/{self.total_steps} completed. "
                                f"Elapsed: {current_elapsed:.2f}s")
                    
        except TimeoutError:
            logger.warning(f"Neural Baseline Proxy terminated early due to timeout at step {step}.")
            # Re-raise to be caught by the termination handler in run_simulation
            raise
        except Exception as e:
            logger.error(f"Neural Baseline Proxy failed at step {step}: {e}")
            raise
        
        final_elapsed = time.time() - self.start_time
        logger.info(f"Neural Baseline Proxy finished. Steps: {self.current_step}, "
                    f"Total Time: {final_elapsed:.2f}s")
        
        return records

def run_neural_baseline_proxy(config: Dict[str, Any]) -> List[MetricRecord]:
    """
    Entry point for running the neural baseline proxy simulation.
    
    Args:
        config: Configuration dictionary.
                
    Returns:
        List[MetricRecord]: List of metric records from the simulation.
    """
    proxy = NeuralBaselineProxy(config)
    return proxy.run()

def main():
    """
    CLI entry point for standalone testing of the neural baseline proxy.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Run Neural Baseline Proxy")
    parser.add_argument('--steps', type=int, default=10000, help='Number of steps')
    parser.add_argument('--complexity', type=float, default=1.0, help='Complexity factor')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default=None, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    config = {
        'total_steps': args.steps,
        'complexity_factor': args.complexity,
        'seed': args.seed
    }
    
    try:
        records = run_neural_baseline_proxy(config)
        print(f"Successfully generated {len(records)} records.")
        
        if args.output:
            # Simple JSON dump for verification
            import json
            with open(args.output, 'w') as f:
                json.dump([asdict(r) for r in records], f, indent=2)
            print(f"Results written to {args.output}")
            
    except TimeoutError as e:
        print(f"TIMEOUT: {e}")
        # Exit with specific code to signal timeout to the runner
        os._exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        os._exit(1)

if __name__ == "__main__":
    main()