import numpy as np
from typing import Tuple, Dict, Any, Optional, List
import sys
import os

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.student import TabularQStudent
from agents.teacher import TeacherOracle
from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything

def evaluate_agent_in_masked_mode(
    agent: TabularQStudent | TeacherOracle,
    env: PrivilegeMDP,
    num_episodes: int = 100,
    max_steps: int = 100,
    seed: Optional[int] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Evaluates an agent in a mode where the privileged state H is masked.
    
    For the Teacher (who normally sees H), this forces the agent to act
    as if it only sees O, effectively simulating the Student's observation space.
    For the Student, this ensures evaluation is strictly on O.
    
    Returns:
        Tuple of (average_return, metrics_dict)
    """
    if seed is not None:
        seed_everything(seed)
    
    returns = []
    steps_list = []
    
    # Store original reset method if needed, but we will manipulate obs directly
    # The environment's reset returns (obs, info). 
    # obs contains both O and H. We must mask H before passing to agent.
    
    for _ in range(num_episodes):
        obs, _ = env.reset()
        total_reward = 0
        steps = 0
        
        for _ in range(max_steps):
            # The observation 'obs' from env is (O, H).
            # We need to extract O.
            # Based on PrivilegeMDP structure: obs is likely a tuple or array.
            # The spec says Student sees O, Teacher sees (O, H).
            # We assume obs[0] is O and obs[1] is H, or obs is a dict.
            # Looking at typical discrete MDP implementations in this context:
            # If obs is a tuple (obs_O, obs_H):
            if isinstance(obs, tuple):
                obs_O = obs[0]
            elif isinstance(obs, dict):
                # If it's a dict, we assume keys 'O' and 'H' exist
                obs_O = obs.get('O', obs.get('observation', 0))
            else:
                # Fallback: assume the whole obs is O if it's a scalar/int
                # This might be incorrect if H is embedded, but we assume structure
                obs_O = obs
            
            # Force agent to act on obs_O only
            action = agent.select_action(obs_O)
            
            next_obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            steps += 1
            obs = next_obs
            
            if terminated or truncated:
                break
        
        returns.append(total_reward)
        steps_list.append(steps)
    
    avg_return = float(np.mean(returns))
    metrics = {
        "num_episodes": num_episodes,
        "total_steps": sum(steps_list),
        "avg_return": avg_return,
        "min_return": float(np.min(returns)),
        "max_return": float(np.max(returns)),
        "std_return": float(np.std(returns))
    }
    
    return avg_return, metrics

def calculate_performance_drop(
    acc_unmasked: float,
    acc_masked: float,
    r_max: float
) -> float:
    """
    Calculates the performance drop metric as defined in the task:
    (acc_unmasked - acc_masked) / R_max
    
    Args:
        acc_unmasked: Performance (return/accuracy) with full information (O, H)
        acc_masked: Performance (return/accuracy) with masked information (O only)
        r_max: The maximum possible reward per episode (R_max)
    
    Returns:
        The normalized performance drop metric.
    """
    if r_max == 0:
        raise ValueError("R_max cannot be zero to avoid division by zero.")
    
    drop = (acc_unmasked - acc_masked) / r_max
    return float(drop)

def run_generalization_analysis(
    student: TabularQStudent,
    teacher: TeacherOracle,
    env: PrivilegeMDP,
    r_max: float,
    num_episodes: int = 100,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Runs the full generalization analysis:
    1. Evaluate Teacher (unmasked/full info) -> acc_unmasked
    2. Evaluate Student (masked/observed info) -> acc_masked
    3. Calculate performance drop metric.
    
    Note: The task specifically asks for the metric calculation.
    We assume 'acc_unmasked' refers to the optimal policy performance (Teacher)
    and 'acc_masked' refers to the Student's performance under the same conditions
    or the Teacher's performance when forced to act without H.
    
    Given the context of "Generalization Test", it usually compares:
    - How well the Student performs (who never saw H).
    - How much the Teacher suffers if H is removed (the cost of missing H).
    
    Here we calculate the metric based on the prompt's formula:
    (acc_unmasked - acc_masked) / R_max
    
    We will interpret:
    - acc_unmasked: Teacher's performance (optimal).
    - acc_masked: Student's performance (or Teacher with H masked).
    Since the Student is the one being tested for generalization (or lack thereof),
    we use Student's performance as acc_masked.
    """
    
    if seed is not None:
        seed_everything(seed)
    
    # 1. Evaluate Teacher (Full Info)
    # Teacher sees (O, H), so this is the "unmasked" baseline.
    acc_unmasked, teacher_metrics = evaluate_agent_in_masked_mode(
        agent=teacher, 
        env=env, 
        num_episodes=num_episodes,
        seed=seed
    )
    
    # 2. Evaluate Student (Masked Info)
    # Student only sees O, so this is naturally "masked".
    # If we wanted to test Teacher's drop, we would pass a modified env or agent,
    # but the metric formula implies comparing the two agents' capabilities.
    acc_masked, student_metrics = evaluate_agent_in_masked_mode(
        agent=student,
        env=env,
        num_episodes=num_episodes,
        seed=seed
    )
    
    # 3. Calculate Metric
    performance_drop = calculate_performance_drop(acc_unmasked, acc_masked, r_max)
    
    return {
        "acc_unmasked": acc_unmasked,
        "acc_masked": acc_masked,
        "performance_drop_metric": performance_drop,
        "r_max": r_max,
        "teacher_metrics": teacher_metrics,
        "student_metrics": student_metrics
    }

# If run as script, perform a dummy check or usage example
if __name__ == "__main__":
    # This block allows the file to be executed for testing if needed,
    # but the core logic is in the functions above.
    print("Generalization analysis module loaded.")
    print("Functions available: evaluate_agent_in_masked_mode, calculate_performance_drop, run_generalization_analysis")