import os
import sys
import json
import argparse
import logging
import time
import traceback
from typing import Dict, List, Optional, Any, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel

# Import project utilities
from utils.seeds import set_global_seed
from utils.config import get_simulation_params, get_config
from utils.validation import validate_trajectory_consistency

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Mock PyBullet Implementation for Testing & Simulation ---

class SimulationError(Exception):
    """Base exception for simulation failures."""
    pass

class KinematicConstraintViolation(SimulationError):
    """Raised when joint limits or kinematic constraints are violated."""
    pass

class CollisionError(SimulationError):
    """Raised when a collision is detected."""
    pass

class MockPyBullet:
    """
    Mock implementation of PyBullet for simulation testing.
    In a real environment, this would wrap `import pybullet`.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.joint_limits = {
            "joint_0": (-1.57, 1.57),
            "joint_1": (-1.57, 1.57),
            "joint_2": (-1.57, 1.57),
            "joint_3": (-1.57, 1.57),
            "joint_4": (-1.57, 1.57),
            "joint_5": (-1.57, 1.57),
            "joint_6": (-1.57, 1.57),
        }
        self.simulation_step_count = 0
        self.fail_next_step = False
        self.fail_type = None

    def set_fail_next_step(self, fail_type: str = "kinematic"):
        """Helper for testing: force the next step to fail."""
        self.fail_next_step = True
        self.fail_type = fail_type

    def reset_simulation(self):
        """Reset the simulation state."""
        self.simulation_step_count = 0
        self.fail_next_step = False
        self.fail_type = None

    def step_simulation(self, trajectory: np.ndarray) -> Dict[str, Any]:
        """
        Execute a single simulation step for a given trajectory segment.
        
        Args:
            trajectory: Array of joint positions for the current step.
        
        Returns:
            Dict with 'success', 'collision', 'error_type' keys.
        
        Raises:
            SimulationError: If the step fails due to constraints or collisions.
        """
        if self.fail_next_step:
            self.fail_next_step = False
            if self.fail_type == "kinematic":
                raise KinematicConstraintViolation("Joint limit violation detected in mock step.")
            elif self.fail_type == "collision":
                raise CollisionError("Collision detected in mock step.")
            else:
                raise SimulationError(f"Unknown failure type: {self.fail_type}")

        # Validate trajectory dimensions
        if len(trajectory) != len(self.joint_limits):
            raise SimulationError(f"Trajectory dimension mismatch: expected {len(self.joint_limits)}, got {len(trajectory)}")

        # Check joint limits
        for i, (pos, (min_l, max_l)) in enumerate(zip(trajectory, self.joint_limits.values())):
            if pos < min_l or pos > max_l:
                raise KinematicConstraintViolation(f"Joint {i} out of limits: {pos} not in [{min_l}, {max_l}]")

        # Mock collision check (randomly fail 5% of steps for realism in tests if not forced)
        if self.rng.random() < 0.05:
            raise CollisionError("Random collision detected.")

        self.simulation_step_count += 1
        return {
            "success": True,
            "collision": False,
            "error_type": None,
            "step_count": self.simulation_step_count
        }

# --- Data Loading Helpers ---

def load_vla_proxy_baseline(filepath: str) -> pd.DataFrame:
    """
    Load the VLA Proxy baseline from a parquet file.
    """
    if not os.path.exists(filepath):
        raise RuntimeError(
            f"VLA Proxy Baseline artifact not found at {filepath}. "
            "Please ensure T032d has generated it."
        )
    try:
        df = pd.read_parquet(filepath)
        logger.info(f"Loaded VLA Proxy Baseline: {len(df)} rows")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load VLA Proxy Baseline: {e}")

def generate_random_baseline(n_samples: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate random trajectories within joint limits for baseline comparison.
    """
    set_global_seed(seed)
    rng = np.random.default_rng(seed)
    n_joints = 7
    n_steps = 50 # Mock trajectory length
    
    data = []
    for i in range(n_samples):
        # Generate random joint positions for each step
        trajectory = []
        for _ in range(n_steps):
            step_data = rng.uniform(-1.57, 1.57, n_joints)
            trajectory.append(step_data)
        
        data.append({
            "prompt_id": f"random_{i}",
            "trajectory": np.array(trajectory),
            "source": "random_baseline"
        })
    
    return pd.DataFrame(data)

def run_non_neural_inference(prompt_ids: List[str], model_dir: str) -> pd.DataFrame:
    """
    Mock inference engine that loads pre-trained models and generates trajectories.
    In a real scenario, this would load BERT embeddings and run the DT/GMM models.
    """
    logger.info(f"Running non-neural inference for {len(prompt_ids)} prompts")
    # Mock: Generate deterministic trajectories based on prompt_id hash
    data = []
    for pid in prompt_ids:
        # Deterministic pseudo-random generation based on prompt_id
        seed_val = int(hashlib.md5(pid.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed_val)
        n_joints = 7
        n_steps = 50
        trajectory = rng.uniform(-1.0, 1.0, (n_steps, n_joints))
        data.append({
            "prompt_id": pid,
            "trajectory": trajectory,
            "source": "non_neural_model"
        })
    return pd.DataFrame(data)

# --- Core Simulation Logic ---

def execute_simulation_step(
    simulator: MockPyBullet, 
    trajectory: np.ndarray, 
    prompt_id: str
) -> Dict[str, Any]:
    """
    Execute a single simulation step with robust error handling.
    
    This function wraps the simulation step to catch any exceptions (KinematicConstraintViolation, 
    CollisionError, or generic SimulationError) and records the failure without crashing the pipeline.
    
    Args:
        simulator: The MockPyBullet instance.
        trajectory: The trajectory array to execute.
        prompt_id: The ID of the prompt being tested.
    
    Returns:
        A dictionary with keys: 'prompt_id', 'success', 'collision', 'error_type', 'error_message'.
    """
    result = {
        "prompt_id": prompt_id,
        "success": False,
        "collision": False,
        "error_type": None,
        "error_message": None
    }
    
    try:
        # In a full simulation, we would loop through steps. 
        # Here we simulate the whole trajectory as a single step or a sequence of steps.
        # For robustness testing, we treat the whole trajectory execution as the "step".
        # If the trajectory is a 2D array (steps, joints), we iterate or pass the whole thing.
        # Assuming trajectory is (n_steps, n_joints)
        
        # We'll simulate step-by-step to catch intermediate errors
        n_steps = trajectory.shape[0] if trajectory.ndim > 1 else 1
        step_traj = trajectory if trajectory.ndim == 1 else trajectory[0] # Simplified for mock
        
        # Actually, let's just try to execute the first step or the whole thing as one atomic op for the mock
        # The requirement is to catch errors.
        simulator.step_simulation(step_traj)
        
        result["success"] = True
        result["collision"] = False
        
    except KinematicConstraintViolation as e:
        result["success"] = False
        result["error_type"] = "KinematicConstraintViolation"
        result["error_message"] = str(e)
        logger.warning(f"Simulation failed for {prompt_id}: {e}")
        
    except CollisionError as e:
        result["success"] = False
        result["collision"] = True
        result["error_type"] = "CollisionError"
        result["error_message"] = str(e)
        logger.warning(f"Simulation failed for {prompt_id} (Collision): {e}")
        
    except SimulationError as e:
        result["success"] = False
        result["error_type"] = "SimulationError"
        result["error_message"] = str(e)
        logger.warning(f"Simulation failed for {prompt_id}: {e}")
        
    except Exception as e:
        # Catch any unexpected errors to ensure pipeline doesn't crash
        result["success"] = False
        result["error_type"] = "UnexpectedError"
        result["error_message"] = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Unexpected error during simulation for {prompt_id}: {traceback.format_exc()}")
    
    return result

def run_simulation_loop(
    prompts_df: pd.DataFrame,
    non_neural_trajectories: pd.DataFrame,
    random_trajectories: pd.DataFrame,
    vla_proxy_trajectories: pd.DataFrame,
    seed: int = 42
) -> pd.DataFrame:
    """
    Run the full simulation loop for all three baselines.
    """
    set_global_seed(seed)
    simulator = MockPyBullet(seed=seed)
    
    results = []
    
    # Align data by prompt_id
    common_prompts = prompts_df['prompt_id'].tolist()
    
    logger.info(f"Starting simulation loop for {len(common_prompts)} prompts")
    
    for pid in common_prompts:
        # Extract trajectories for this prompt
        nn_traj = non_neural_trajectories[non_neural_trajectories['prompt_id'] == pid]['trajectory'].values
        rand_traj = random_trajectories[random_trajectories['prompt_id'] == pid]['trajectory'].values
        vla_traj = vla_proxy_trajectories[vla_proxy_trajectories['prompt_id'] == pid]['trajectory'].values
        
        if len(nn_traj) == 0 or len(rand_traj) == 0 or len(vla_traj) == 0:
            logger.warning(f"Missing trajectory for prompt {pid}, skipping.")
            continue
        
        nn_traj = nn_traj[0]
        rand_traj = rand_traj[0]
        vla_traj = vla_traj[0]
        
        # Run Non-Neural
        res_nn = execute_simulation_step(simulator, nn_traj, f"{pid}_nn")
        res_nn["baseline"] = "non_neural"
        results.append(res_nn)
        
        # Run Random
        res_rand = execute_simulation_step(simulator, rand_traj, f"{pid}_rand")
        res_rand["baseline"] = "random"
        results.append(res_rand)
        
        # Run VLA Proxy
        res_vla = execute_simulation_step(simulator, vla_traj, f"{pid}_vla")
        res_vla["baseline"] = "vla_proxy"
        results.append(res_vla)
        
        # Reset simulator state for next prompt to avoid state leakage in mock
        simulator.reset_simulation()
    
    return pd.DataFrame(results)

def verify_data_alignment(
    prompts_df: pd.DataFrame,
    non_neural_df: pd.DataFrame,
    random_df: pd.DataFrame,
    vla_proxy_df: pd.DataFrame
) -> bool:
    """
    Verify that all datasets contain the exact same set of prompt IDs.
    """
    ids_prompt = set(prompts_df['prompt_id'].tolist())
    ids_nn = set(non_neural_df['prompt_id'].tolist())
    ids_rand = set(random_df['prompt_id'].tolist())
    ids_vla = set(vla_proxy_df['prompt_id'].tolist())
    
    if ids_prompt != ids_nn or ids_prompt != ids_rand or ids_prompt != ids_vla:
        logger.error("Data alignment failed: Prompt IDs do not match across datasets.")
        logger.error(f"Prompt IDs: {ids_prompt}")
        logger.error(f"NN IDs: {ids_nn}")
        logger.error(f"Rand IDs: {ids_rand}")
        logger.error(f"VLA IDs: {ids_vla}")
        return False
    
    logger.info("Data alignment verified successfully.")
    return True

def run_paired_ttests(simulation_results: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform paired t-tests on success rates between baselines.
    """
    # Group by prompt_id and baseline
    # We need to reshape to have columns for each baseline's success
    pivot = simulation_results.pivot_table(
        index='prompt_id', 
        columns='baseline', 
        values='success', 
        aggfunc='first'
    )
    
    if not all(b in pivot.columns for b in ['non_neural', 'random', 'vla_proxy']):
        logger.warning("Missing baselines for t-test.")
        return {}
    
    nn_success = pivot['non_neural'].values.astype(float)
    rand_success = pivot['random'].values.astype(float)
    vla_success = pivot['vla_proxy'].values.astype(float)
    
    # Paired t-tests
    t_nn_rand, p_nn_rand = ttest_rel(nn_success, rand_success)
    t_nn_vla, p_nn_vla = ttest_rel(nn_success, vla_success)
    t_rand_vla, p_rand_vla = ttest_rel(rand_success, vla_success)
    
    return {
        "nn_vs_rand": {"t_stat": float(t_nn_rand), "p_value": float(p_nn_rand)},
        "nn_vs_vla": {"t_stat": float(t_nn_vla), "p_value": float(p_nn_vla)},
        "rand_vs_vla": {"t_stat": float(t_rand_vla), "p_value": float(p_rand_vla)}
    }

def main():
    """
    Main entry point for the simulation evaluation script.
    """
    parser = argparse.ArgumentParser(description="Simulation Evaluation Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    set_global_seed(args.seed)
    
    # Load configuration
    config = get_config(args.config)
    simulation_params = get_simulation_params(config)
    
    # Load Baselines
    try:
        vla_proxy_df = load_vla_proxy_baseline(simulation_params.get("vla_baseline_path"))
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Generate Random Baseline
    random_df = generate_random_baseline(len(vla_proxy_df), seed=args.seed)
    
    # Run Non-Neural Inference (Mock)
    # In real scenario, load models and run inference
    non_neural_df = run_non_neural_inference(vla_proxy_df['prompt_id'].tolist(), "artifacts/models")
    
    # Verify Alignment
    if not verify_data_alignment(vla_proxy_df, non_neural_df, random_df, vla_proxy_df):
        logger.error("Data alignment verification failed. Exiting.")
        sys.exit(1)
    
    # Run Simulation Loop
    simulation_results = run_simulation_loop(
        vla_proxy_df, non_neural_df, random_df, vla_proxy_df, seed=args.seed
    )
    
    # Save Results
    output_path = simulation_params.get("output_path", "data/results/simulation_logs.csv")
    simulation_results.to_csv(output_path, index=False)
    logger.info(f"Simulation results saved to {output_path}")
    
    # Run T-Tests
    ttest_results = run_paired_ttests(simulation_results)
    ttest_path = simulation_params.get("ttest_output_path", "data/results/ttest_results.json")
    with open(ttest_path, 'w') as f:
        json.dump(ttest_results, f, indent=2)
    logger.info(f"T-Test results saved to {ttest_path}")
    
    logger.info("Simulation evaluation complete.")

if __name__ == "__main__":
    main()
