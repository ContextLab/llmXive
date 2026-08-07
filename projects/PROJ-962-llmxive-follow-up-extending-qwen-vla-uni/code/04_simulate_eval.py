"""
04_simulate_eval.py - Simulation evaluation and statistical comparison.
Implements PyBullet simulation, baseline generation, and paired t-tests.
"""
import os
import sys
import json
import argparse
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from scipy import stats

# Import from project utils
from utils.seeds import set_global_seed, get_seed
from utils.config import get_simulation_params, get_config
from utils.validation import compute_file_checksum, validate_dataframe_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Mock PyBullet for CPU-only environment without heavy dependencies ---
# In a real environment, this would import pybullet
class MockPyBullet:
    """Mock PyBullet environment for simulation without actual physics engine."""
    
    def __init__(self, robot_type: str = "franka"):
        self.robot_type = robot_type
        self.joint_limits = {
            "joint_1": (-2.8973, 2.8973),
            "joint_2": (-1.7628, 1.7628),
            "joint_3": (-2.8973, 2.8973),
            "joint_4": (-3.0718, -0.0698),
            "joint_5": (-2.8973, 2.8973),
            "joint_6": (-0.0175, 3.7525),
            "joint_7": (-2.8973, 2.8973)
        }
        self.base_pos = [0.0, 0.0, 0.0]
        self.base_orientation = [0.0, 0.0, 0.0, 1.0]
        
    def loadRobot(self, urdf_file: str, base_position: List[float], base_orientation: List[float]):
        """Mock loading a robot."""
        return 1  # Return dummy robot ID
        
    def setJointMotorControl2(self, robot_id: int, joint_index: int, control_mode: int, 
                             force: float, targetVelocity: float = 0.0, 
                             positionGain: float = 0.1, velocityGain: float = 0.1):
        """Mock setting joint control."""
        pass
        
    def stepSimulation(self):
        """Mock simulation step."""
        pass
        
    def getJointState(self, robot_id: int, joint_index: int):
        """Mock getting joint state."""
        return [0.0, 0.0, 0.0, 0.0]  # [position, velocity, effort, reaction_forces]
        
    def resetSimulation(self):
        """Mock resetting simulation."""
        pass
        
    def disconnect(self):
        """Mock disconnecting."""
        pass

def load_vla_proxy_baseline(filepath: str) -> pd.DataFrame:
    """
    Load the VLA Proxy baseline artifact.
    
    Args:
        filepath: Path to the parquet file containing the baseline.
        
    Returns:
        DataFrame with prompt_id, task_type, and action_sequence.
        
    Raises:
        RuntimeError: If the file does not exist.
    """
    if not os.path.exists(filepath):
        raise RuntimeError(
            f"VLA Proxy Baseline artifact not found at {filepath}. "
            "Please ensure T032d has generated it."
        )
    
    logger.info(f"Loading VLA Proxy Baseline from {filepath}")
    df = pd.read_parquet(filepath)
    
    required_cols = ['prompt_id', 'task_type', 'action_sequence']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Baseline file missing required columns: {required_cols}")
        
    logger.info(f"Loaded {len(df)} baseline samples")
    return df

def generate_random_baseline(prompt_ids: List[str], task_types: List[str], 
                             seed: int, joint_limits: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
    """
    Generate random sampling baseline with fixed seed for reproducibility.
    
    This function generates random trajectories via uniform sampling within 
    joint limits, using a fixed seed to ensure byte-identical outputs 
    across runs with the same seed.
    
    Args:
        prompt_ids: List of prompt identifiers.
        task_types: List of task types corresponding to prompts.
        seed: Random seed for reproducibility.
        joint_limits: Dictionary of joint name to (min, max) limits.
        
    Returns:
        DataFrame with prompt_id, task_type, and action_sequence.
    """
    # Set seed for reproducibility (T059 requirement)
    set_global_seed(seed)
    
    logger.info(f"Generating Random Baseline with seed={seed} for {len(prompt_ids)} samples")
    
    # Extract all joint limits as a list of (min, max) tuples
    limits_list = [joint_limits[joint] for joint in sorted(joint_limits.keys())]
    num_joints = len(limits_list)
    
    # Define trajectory length (number of time steps)
    trajectory_length = 50  # Fixed length for all trajectories
    
    random_trajectories = []
    
    for i in range(len(prompt_ids)):
        # Generate random trajectory: uniform sampling within joint limits
        # Shape: (trajectory_length, num_joints)
        trajectory = np.zeros((trajectory_length, num_joints))
        
        for t in range(trajectory_length):
            for j, (min_val, max_val) in enumerate(limits_list):
                trajectory[t, j] = np.random.uniform(min_val, max_val)
        
        random_trajectories.append(trajectory)
    
    # Create DataFrame
    df = pd.DataFrame({
        'prompt_id': prompt_ids,
        'task_type': task_types,
        'action_sequence': random_trajectories
    })
    
    return df

def run_non_neural_inference(prompt_ids: List[str], task_types: List[str]) -> pd.DataFrame:
    """
    Run non-neural model inference (placeholder for actual implementation).
    
    In a full implementation, this would:
    1. Load trained models from artifacts/models/
    2. Generate BERT embeddings for prompts
    3. Find nearest cluster
    4. Sample trajectory from selected model
    
    For this task, we return a placeholder structure.
    """
    logger.info(f"Running Non-Neural Inference for {len(prompt_ids)} samples")
    
    # Placeholder: In real implementation, this would use trained models
    # For now, we return a structure similar to random baseline
    # but with "inference" logic that would be implemented in T022/T023
    
    # Simulate some deterministic output based on prompt_id hash
    trajectories = []
    for pid in prompt_ids:
        # Use hash of prompt_id to generate deterministic "inference" result
        hash_val = hash(pid) % 1000
        num_joints = 7
        traj_len = 50
        traj = np.random.RandomState(hash_val).rand(traj_len, num_joints) * 2 - 1
        trajectories.append(traj)
    
    return pd.DataFrame({
        'prompt_id': prompt_ids,
        'task_type': task_types,
        'action_sequence': trajectories
    })

def execute_simulation_step(robot: MockPyBullet, trajectory: np.ndarray, 
                            task_type: str) -> Dict[str, Any]:
    """
    Execute a single simulation step for a trajectory.
    
    Args:
        robot: MockPyBullet instance.
        trajectory: Numpy array of shape (num_steps, num_joints).
        task_type: Type of task being executed.
        
    Returns:
        Dictionary with success flag, collision count, and execution time.
    """
    start_time = time.time()
    success = True
    collision_count = 0
    
    try:
        for step_idx, joint_positions in enumerate(trajectory):
            # Check joint limits
            for j_idx, pos in enumerate(joint_positions):
                joint_name = f"joint_{j_idx+1}"
                min_lim, max_lim = robot.joint_limits[joint_name]
                
                if pos < min_lim or pos > max_lim:
                    collision_count += 1
                    success = False
                    # Continue simulation but mark as failure
            
            # Execute simulation step
            robot.stepSimulation()
            
    except Exception as e:
        logger.warning(f"Simulation error: {e}")
        success = False
    
    execution_time = time.time() - start_time
    
    return {
        'success': success,
        'collision_count': collision_count,
        'execution_time': execution_time
    }

def run_simulation_loop(robot: MockPyBullet, df: pd.DataFrame, 
                       task_types: List[str]) -> pd.DataFrame:
    """
    Run simulation loop for all samples in a DataFrame.
    
    Args:
        robot: MockPyBullet instance.
        df: DataFrame with prompt_id, task_type, action_sequence.
        task_types: List of task types.
        
    Returns:
        DataFrame with simulation results.
    """
    results = []
    
    for idx, row in df.iterrows():
        trajectory = row['action_sequence']
        task_type = row['task_type']
        prompt_id = row['prompt_id']
        
        sim_result = execute_simulation_step(robot, trajectory, task_type)
        
        results.append({
            'prompt_id': prompt_id,
            'task_type': task_type,
            'success': sim_result['success'],
            'collision_count': sim_result['collision_count'],
            'execution_time': sim_result['execution_time']
        })
    
    return pd.DataFrame(results)

def verify_data_alignment(df1: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame) -> bool:
    """
    Verify that prompt_id lists are identical across all three DataFrames.
    
    Args:
        df1: Non-neural inference results.
        df2: Random baseline results.
        df3: VLA proxy baseline results.
        
    Returns:
        True if all prompt_id lists are byte-identical.
        
    Raises:
        ValueError: If prompt_ids are not aligned.
    """
    ids1 = sorted(df1['prompt_id'].tolist())
    ids2 = sorted(df2['prompt_id'].tolist())
    ids3 = sorted(df3['prompt_id'].tolist())
    
    if ids1 != ids2 or ids2 != ids3:
        raise ValueError(
            "Prompt IDs are not aligned across all three datasets. "
            "Non-neural, Random, and VLA Proxy must use identical prompt sets."
        )
    
    logger.info("Data alignment verified: all prompt IDs match")
    return True

def run_paired_ttests(df_nn: pd.DataFrame, df_rand: pd.DataFrame, 
                     df_vla: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Perform paired t-tests for success rates.
    
    Compares:
    - Non-neural vs Random
    - Non-neural vs VLA Proxy
    - Random vs VLA Proxy
    
    Args:
        df_nn: Non-neural simulation results.
        df_rand: Random baseline results.
        df_vla: VLA proxy results.
        
    Returns:
        Dictionary with t-statistics and p-values for each comparison.
    """
    # Ensure alignment
    verify_data_alignment(df_nn, df_rand, df_vla)
    
    # Extract success arrays (binary: 1 for success, 0 for failure)
    success_nn = df_nn['success'].astype(int).values
    success_rand = df_rand['success'].astype(int).values
    success_vla = df_vla['success'].astype(int).values
    
    # Perform paired t-tests
    t_nn_rand, p_nn_rand = stats.ttest_rel(success_nn, success_rand)
    t_nn_vla, p_nn_vla = stats.ttest_rel(success_nn, success_vla)
    t_rand_vla, p_rand_vla = stats.ttest_rel(success_rand, success_vla)
    
    results = {
        'non_neural_vs_random': {
            't_statistic': float(t_nn_rand),
            'p_value': float(p_nn_rand),
            'mean_diff': float(np.mean(success_nn) - np.mean(success_rand))
        },
        'non_neural_vs_vla': {
            't_statistic': float(t_nn_vla),
            'p_value': float(p_nn_vla),
            'mean_diff': float(np.mean(success_nn) - np.mean(success_vla))
        },
        'random_vs_vla': {
            't_statistic': float(t_rand_vla),
            'p_value': float(p_rand_vla),
            'mean_diff': float(np.mean(success_rand) - np.mean(success_vla))
        }
    }
    
    logger.info(f"T-Test Results: {results}")
    return results

def main():
    """Main entry point for simulation evaluation."""
    parser = argparse.ArgumentParser(description="Simulation Evaluation Pipeline")
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--vla_baseline', type=str, 
                       default='data/processed/vla_proxy_baseline.parquet',
                       help='Path to VLA Proxy baseline')
    parser.add_argument('--output_dir', type=str, default='data/results',
                       help='Directory for output files')
    parser.add_argument('--num_samples', type=int, default=100,
                       help='Number of samples to process')
    args = parser.parse_args()
    
    # Set global seed for reproducibility (T059 requirement)
    set_global_seed(args.seed)
    logger.info(f"Global seed set to {get_seed()}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load VLA Proxy Baseline
    try:
        df_vla = load_vla_proxy_baseline(args.vla_baseline)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Limit to num_samples if specified
    if len(df_vla) > args.num_samples:
        df_vla = df_vla.head(args.num_samples)
    
    prompt_ids = df_vla['prompt_id'].tolist()
    task_types = df_vla['task_type'].tolist()
    
    # Get joint limits from config
    config = get_config()
    joint_limits = config.get('joint_limits', {
        "joint_1": (-2.8973, 2.8973),
        "joint_2": (-1.7628, 1.7628),
        "joint_3": (-2.8973, 2.8973),
        "joint_4": (-3.0718, -0.0698),
        "joint_5": (-2.8973, 2.8973),
        "joint_6": (-0.0175, 3.7525),
        "joint_7": (-2.8973, 2.8973)
    })
    
    # Generate Random Baseline (T059: Fixed seed for reproducibility)
    df_rand = generate_random_baseline(
        prompt_ids=prompt_ids,
        task_types=task_types,
        seed=args.seed,
        joint_limits=joint_limits
    )
    
    # Run Non-Neural Inference
    df_nn = run_non_neural_inference(prompt_ids, task_types)
    
    # Initialize Mock PyBullet
    robot = MockPyBullet()
    
    # Run simulation loop for all three baselines
    logger.info("Running simulation for VLA Proxy...")
    sim_vla = run_simulation_loop(robot, df_vla, task_types)
    
    logger.info("Running simulation for Random Baseline...")
    sim_rand = run_simulation_loop(robot, df_rand, task_types)
    
    logger.info("Running simulation for Non-Neural Model...")
    sim_nn = run_simulation_loop(robot, df_nn, task_types)
    
    # Save simulation results
    sim_vla.to_csv(os.path.join(args.output_dir, 'simulation_vla.csv'), index=False)
    sim_rand.to_csv(os.path.join(args.output_dir, 'simulation_random.csv'), index=False)
    sim_nn.to_csv(os.path.join(args.output_dir, 'simulation_non_neural.csv'), index=False)
    
    # Verify data alignment
    try:
        verify_data_alignment(sim_nn, sim_rand, sim_vla)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run paired t-tests
    ttest_results = run_paired_ttests(sim_nn, sim_rand, sim_vla)
    
    # Save t-test results
    with open(os.path.join(args.output_dir, 'ttest_results.json'), 'w') as f:
        json.dump(ttest_results, f, indent=2)
    
    # Log final summary
    logger.info("Simulation evaluation complete.")
    logger.info(f"VLA Success Rate: {sim_vla['success'].mean():.2%}")
    logger.info(f"Random Success Rate: {sim_rand['success'].mean():.2%}")
    logger.info(f"Non-Neural Success Rate: {sim_nn['success'].mean():.2%}")
    
    # T059 Verification: Run baseline generation twice with same seed
    # and assert byte-identical output
    logger.info("Verifying Random Baseline Reproducibility (T059)...")
    df_rand_2 = generate_random_baseline(
        prompt_ids=prompt_ids,
        task_types=task_types,
        seed=args.seed,
        joint_limits=joint_limits
    )
    
    # Compare action sequences
    is_identical = True
    for idx in range(len(df_rand)):
        traj1 = df_rand.iloc[idx]['action_sequence']
        traj2 = df_rand_2.iloc[idx]['action_sequence']
        if not np.array_equal(traj1, traj2):
            is_identical = False
            break
    
    if is_identical:
        logger.info("T059 VERIFIED: Random Baseline is reproducible with fixed seed.")
    else:
        logger.error("T059 FAILED: Random Baseline is NOT reproducible!")
        sys.exit(1)
    
    logger.info("Pipeline Complete. Exit Code: 0")

if __name__ == "__main__":
    main()
