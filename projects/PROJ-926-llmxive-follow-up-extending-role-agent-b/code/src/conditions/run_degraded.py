"""
T022: Run Degraded Condition (WIA Horizon Zero)

Loads baseline failure trajectories and re-executes them in the ALFWorld simulator
with the WIA prediction horizon set to 0 (Degraded condition).
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path to allow imports from code/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.sim.alfworld_runner import run_episode
from src.conditions.degraded import configure_degraded_environment, get_degraded_prompt_template
from src.config.config import DATA_PATH

def load_baseline_failures(input_path: str) -> List[Dict[str, Any]]:
    """Load baseline failure trajectories from JSON."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Baseline failures file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'trajectories' in data:
        return data['trajectories']
    else:
        raise ValueError(f"Unexpected data format in {input_path}")

def run_degraded_simulation(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Re-run a specific trajectory in the ALFWorld simulator with WIA=0.
    
    Args:
        trajectory: Original baseline failure trajectory dict
        
    Returns:
        Dict containing the degraded trajectory result
    """
    original_id = trajectory.get('id')
    task_id = trajectory.get('task_id')
    
    if not task_id:
        raise ValueError(f"Missing task_id in trajectory {original_id}")
    
    # Configure degraded environment (WIA Horizon = 0)
    degraded_config = configure_degraded_environment()
    
    # Get the degraded prompt template
    prompt_template = get_degraded_prompt_template()
    
    # Run the episode with the degraded configuration
    # Note: We pass the original task_id but the environment is configured
    # to have WIA=0, which affects the agent's prediction horizon
    try:
        result = run_episode(
            task_id=task_id,
            seed=trajectory.get('seed', 42),
            config_override=degraded_config,
            prompt_template=prompt_template
        )
        
        # Determine failure description from the result
        # Since we are simulating WIA=0, we expect failures to be related
        # to lack of predictive capability
        if result.get('success', False):
            failure_description = "Unexpected success in degraded condition"
        else:
            failure_description = result.get('failure_reason', "Failed due to WIA=0 constraint")
        
        return {
            'id': str(uuid.uuid4()),
            'original_id': original_id,
            'task_id': task_id,
            'failure_description': failure_description,
            'context_type': 'WIA_ZERO',
            'action_log': result.get('action_log', []),
            'state_transitions': result.get('state_transitions', []),
            'timestamp': datetime.now().isoformat(),
            'config_used': degraded_config
        }
        
    except Exception as e:
        # Log the error but continue processing other trajectories
        return {
            'id': str(uuid.uuid4()),
            'original_id': original_id,
            'task_id': task_id,
            'failure_description': f"Simulation error: {str(e)}",
            'context_type': 'WIA_ZERO',
            'action_log': [],
            'state_transitions': [],
            'timestamp': datetime.now().isoformat(),
            'config_used': degraded_config,
            'error': str(e)
        }

def run(input_path: str, output_path: str) -> None:
    """
    Main function to process all baseline failures and generate degraded trajectories.
    
    Args:
        input_path: Path to baseline_failures.json
        output_path: Path to save degraded_failures.json
    """
    print(f"Loading baseline failures from {input_path}")
    baseline_trajectories = load_baseline_failures(input_path)
    print(f"Loaded {len(baseline_trajectories)} baseline trajectories")
    
    degraded_results = []
    
    for i, trajectory in enumerate(baseline_trajectories):
        print(f"Processing trajectory {i+1}/{len(baseline_trajectories)}: {trajectory.get('id', 'unknown')}")
        result = run_degraded_simulation(trajectory)
        degraded_results.append(result)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump({
            'metadata': {
                'total_trajectories': len(degraded_results),
                'condition': 'degraded',
                'wia_horizon': 0,
                'generated_at': datetime.now().isoformat()
            },
            'trajectories': degraded_results
        }, f, indent=2)
    
    print(f"Saved {len(degraded_results)} degraded trajectories to {output_path}")
    
    # Verification
    if len(degraded_results) != len(baseline_trajectories):
        print(f"WARNING: Mismatch in trajectory counts. Expected {len(baseline_trajectories)}, got {len(degraded_results)}")
    
    # Verify required keys
    required_keys = ['id', 'original_id', 'failure_description', 'context_type']
    for result in degraded_results:
        for key in required_keys:
            if key not in result:
                print(f"ERROR: Missing required key '{key}' in result {result.get('id', 'unknown')}")

def main():
    parser = argparse.ArgumentParser(description='Run degraded condition simulation')
    parser.add_argument('--input', type=str, default='data/raw/baseline_failures.json',
                      help='Path to baseline failures JSON')
    parser.add_argument('--output', type=str, default='data/raw/degraded_failures.json',
                      help='Path to save degraded failures JSON')
    
    args = parser.parse_args()
    
    run(args.input, args.output)

if __name__ == '__main__':
    main()
