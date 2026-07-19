"""
Trajectory Generator for llmXive Follow-up Study.

Generates and validates agent trajectories in ALFWorld environment.
Implements strict validation against ground-truth data before saving.
"""
import argparse
import json
import os
import re
import uuid
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Configuration imports
from src.config.config import SEED, DATA_PATH, MODEL_ID, CPU_DEVICE
from src.sim.alfworld_runner import run_episode, verify_alfworld_health
from src.sim.validation import validate_trajectory, load_ground_truth_raw
from src.sim.exclusion_logger import set_exclusion_path, log_excluded_trajectory, log_excluded_trajectories
from src.data.stream_utils import load_trajectory_dataset

# Set float32 precision for CPU execution as per spec
import torch
if CPU_DEVICE:
    torch.set_float32_matmul_precision('high')

# Constants
MAX_ATTEMPTS = 1000
TARGET_FAILURES = 500
VALIDATION_TIMEOUT = 300  # seconds

def load_model_and_tokenizer():
    """
    Load the Mistral-7B model and tokenizer in float32 CPU mode.
    Raises OSError if model is not accessible.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            local_files_only=False
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            use_cache=False,
            device_map="cpu" if CPU_DEVICE else None,
            trust_remote_code=True,
            local_files_only=False
        )
        
        return model, tokenizer
    except Exception as e:
        raise OSError(f"Failed to load model {MODEL_ID}: {str(e)}")

def extract_failure_reason(action_log: List[Dict]) -> str:
    """
    Extract failure reason from action log.
    """
    if not action_log:
        return "Unknown: Empty action log"
    
    # Look for common failure patterns
    failure_patterns = [
        r"failed to pick up (object|item) (.*?) after (\d+) steps",
        r"cannot (open|close|put|take) (.*?)",
        r"task (?:failed|terminated|aborted)",
        r"invalid action: (.*?)",
        r"timeout: (.*?)"
    ]
    
    combined_text = " ".join(str(step) for step in action_log)
    
    for pattern in failure_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            return f"Pattern match: {match.group(0)[:100]}"
    
    # Return last few steps if no pattern found
    if len(action_log) >= 3:
        return f"Last actions: {action_log[-3:]}"
    return f"Last actions: {action_log}"

def validate_and_filter_trajectories(
    trajectories: List[Dict],
    ground_truth_data: Dict
) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate trajectories against ground-truth and filter out invalid ones.
    
    Args:
        trajectories: List of trajectory dictionaries to validate
        ground_truth_data: Ground-truth validation data from T007a/T007b
        
    Returns:
        Tuple of (valid_trajectories, excluded_trajectories)
    """
    valid_trajectories = []
    excluded_trajectories = []
    
    for trajectory in trajectories:
        traj_id = trajectory.get('trajectory_id', str(uuid.uuid4()))
        action_log = trajectory.get('action_log', [])
        
        # Validate against ground-truth
        validation_result = validate_trajectory(action_log, ground_truth_data)
        
        if validation_result.get('status') == 'PASS':
            # Add validation metadata to trajectory
            trajectory['validation_status'] = 'PASS'
            trajectory['validation_timestamp'] = datetime.now().isoformat()
            trajectory['failure_reason'] = extract_failure_reason(action_log)
            valid_trajectories.append(trajectory)
        else:
            # Log excluded trajectory with reason
            exclusion_entry = {
                'trajectory_id': traj_id,
                'exclusion_reason': validation_result.get('reason', 'Validation failed'),
                'validation_status': validation_result.get('status', 'UNKNOWN'),
                'timestamp': datetime.now().isoformat()
            }
            excluded_trajectories.append(exclusion_entry)
    
    return valid_trajectories, excluded_trajectories

def generate_trajectory_batch(
    model,
    tokenizer,
    task_bank,
    n_trajectories: int,
    condition: str = 'baseline'
) -> List[Dict]:
    """
    Generate a batch of trajectories for the specified condition.
    
    Args:
        model: Pre-loaded LLM model
        tokenizer: Pre-loaded tokenizer
        task_bank: Task bank definitions
        n_trajectories: Number of trajectories to generate
        condition: Condition type (baseline, degraded, intervention)
        
    Returns:
        List of generated trajectory dictionaries
    """
    trajectories = []
    attempts = 0
    
    print(f"Starting trajectory generation for {n_trajectories} {condition} trajectories...")
    
    while len(trajectories) < n_trajectories and attempts < MAX_ATTEMPTS:
        attempts += 1
        
        # Select random task from task bank
        task_id = f"task_{attempts % len(task_bank)}"
        task_def = task_bank.get(task_id, {})
        
        if not task_def:
            continue
        
        try:
            # Run episode in ALFWorld
            episode_result = run_episode(
                task_id=task_id,
                seed=SEED + attempts,
                condition=condition
            )
            
            if episode_result and episode_result.get('success') == False:
                # This is a failure trajectory - keep it
                trajectory = {
                    'trajectory_id': str(uuid.uuid4()),
                    'task_id': task_id,
                    'condition': condition,
                    'action_log': episode_result.get('action_log', []),
                    'state_transitions': episode_result.get('state_transitions', []),
                    'generation_timestamp': datetime.now().isoformat(),
                    'attempts': attempts
                }
                trajectories.append(trajectory)
                
                if len(trajectories) % 50 == 0:
                    print(f"Generated {len(trajectories)} failure trajectories...")
            else:
                # Success trajectory - discard for failure generation
                pass
                
        except Exception as e:
            print(f"Error generating trajectory {attempts}: {str(e)}")
            continue
    
    return trajectories

def run(args: argparse.Namespace) -> None:
    """
    Main execution function for trajectory generation.
    
    Args:
        args: Command line arguments
    """
    # Verify ALFWorld environment health
    print("Verifying ALFWorld environment health...")
    verify_alfworld_health()
    
    # Load ground-truth data for validation
    print("Loading ground-truth data...")
    ground_truth_data = load_ground_truth_raw()
    
    if not ground_truth_data:
        raise RuntimeError("Failed to load ground-truth data. Ensure T007a has completed.")
    
    # Load task bank
    from src.retrieval.task_bank import get_task_definition
    task_bank = {}
    for i in range(100):  # Load sample task bank
        task_def = get_task_definition(f"task_{i}")
        if task_def:
            task_bank[f"task_{i}"] = task_def
    
    if not task_bank:
        raise RuntimeError("Failed to load task bank. Ensure T008 has completed.")
    
    # Load model
    print(f"Loading model {MODEL_ID}...")
    model, tokenizer = load_model_and_tokenizer()
    
    # Generate trajectories
    trajectories = generate_trajectory_batch(
        model=model,
        tokenizer=tokenizer,
        task_bank=task_bank,
        n_trajectories=args.n,
        condition=args.condition
    )
    
    # Validate and filter trajectories
    print(f"Validating {len(trajectories)} trajectories...")
    valid_trajectories, excluded_trajectories = validate_and_filter_trajectories(
        trajectories,
        ground_truth_data
    )
    
    # Log excluded trajectories
    if excluded_trajectories:
        exclusion_path = os.path.join(DATA_PATH, 'raw', 'excluded_log.json')
        set_exclusion_path(exclusion_path)
        log_excluded_trajectories(excluded_trajectories)
        print(f"Logged {len(excluded_trajectories)} excluded trajectories to {exclusion_path}")
    
    # Save validated trajectories
    output_path = args.output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for traj in valid_trajectories:
            f.write(json.dumps(traj) + '\n')
    
    print(f"Saved {len(valid_trajectories)} validated trajectories to {output_path}")
    
    # Verify count
    if len(valid_trajectories) < args.n:
        raise RuntimeError(
            f"Generated only {len(valid_trajectories)} valid trajectories, "
            f"but {args.n} were requested. Check ground-truth validation and ALFWorld configuration."
        )

def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description='Generate and validate ALFWorld trajectories')
    parser.add_argument('--n', type=int, default=500, help='Number of trajectories to generate')
    parser.add_argument('--condition', type=str, default='baseline', 
                      choices=['baseline', 'degraded', 'intervention'],
                      help='Condition type')
    parser.add_argument('--output', type=str, required=True, 
                      help='Output file path for trajectories')
    
    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    main()
