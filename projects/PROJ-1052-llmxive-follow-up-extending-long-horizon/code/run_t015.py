"""
T015: Execute agent on injected trajectories to measure recovery success.

This script reads injected trajectories from data/processed/injected_trajectories.jsonl,
maps recovery segment tags from the baseline data (T014), runs the agent on the
injected data, and outputs recovery success metrics to data/processed/injected_execution_logs.csv.
"""
import csv
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from agent_runner import AgentRunner
from utils.state_diff import process_baseline_logs_with_recovery_tags
from utils.logging_handler import setup_logger, log_metric, load_config

logger = setup_logger("t015_recovery")

def load_injected_trajectories(input_path: Path) -> List[Dict[str, Any]]:
    """Load injected trajectories from JSONL file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Injected trajectories file not found: {input_path}")
    
    trajectories = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                traj = json.loads(line)
                trajectories.append(traj)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON at line {line_num}: {e}")
                raise
    
    if not trajectories:
        raise ValueError("No valid trajectories found in input file")
    
    logger.info(f"Loaded {len(trajectories)} injected trajectories")
    return trajectories

def load_baseline_recovery_tags(baseline_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load baseline execution logs and extract recovery segment tags.
    
    Returns a dictionary mapping task_id -> list of recovery segments with their IDs.
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline execution logs not found: {baseline_path}")
    
    # Use the existing T014 function to process baseline logs
    # This function should have been run in T014 and produced the tagged baseline logs
    baseline_df = process_baseline_logs_with_recovery_tags(str(baseline_path))
    
    if baseline_df is None or baseline_df.empty:
        raise ValueError("Baseline logs could not be processed or are empty")
    
    # Extract recovery segment mapping
    recovery_map = {}
    for _, row in baseline_df.iterrows():
        task_id = row.get('task_id')
        if not task_id:
            continue
        
        recovery_segment_id = row.get('recovery_segment_id', '')
        if recovery_segment_id:
            if task_id not in recovery_map:
                recovery_map[task_id] = []
            
            recovery_map[task_id].append({
                'recovery_segment_id': recovery_segment_id,
                'segment_data': row.to_dict()
            })
    
    logger.info(f"Loaded recovery segment tags for {len(recovery_map)} tasks")
    return recovery_map

def map_recovery_segments(
    trajectory: Dict[str, Any],
    recovery_map: Dict[str, List[Dict[str, Any]]]
) -> List[str]:
    """
    Map recovery segment IDs from baseline data to the current injected trajectory.
    
    Args:
        trajectory: The injected trajectory data
        recovery_map: Pre-loaded recovery segment mapping from baseline data
        
    Returns:
        List of recovery segment IDs associated with this trajectory
    """
    task_id = trajectory.get('task_id')
    if not task_id or task_id not in recovery_map:
        logger.warning(f"No recovery segment tags found for task_id: {task_id}")
        return []
    
    # Extract recovery segment IDs
    segment_ids = [seg['recovery_segment_id'] for seg in recovery_map[task_id]]
    return segment_ids

def run_recovery_evaluation(
    trajectories: List[Dict[str, Any]],
    recovery_map: Dict[str, List[Dict[str, Any]]],
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Run agent on injected trajectories and record recovery success.
    
    Args:
        trajectories: List of injected trajectories to evaluate
        recovery_map: Recovery segment mapping from baseline data
        config: Optional configuration for agent runner
        
    Returns:
        List of evaluation results with recovery success metrics
    """
    results = []
    agent_runner = AgentRunner(config=config)
    
    for idx, trajectory in enumerate(trajectories):
        task_id = trajectory.get('task_id', f'unknown_task_{idx}')
        logger.info(f"Processing trajectory {idx + 1}/{len(trajectories)}: {task_id}")
        
        try:
            # Map recovery segments from baseline to this injected trajectory
            recovery_segment_ids = map_recovery_segments(trajectory, recovery_map)
            
            # Run the agent on the injected trajectory
            # The agent_runner should handle the injected error and attempt recovery
            success, metadata = agent_runner.run_trajectory(trajectory)
            
            # Record results
            result = {
                'task_id': task_id,
                'recovery_success': success,
                'recovery_segment_id': ','.join(recovery_segment_ids) if recovery_segment_ids else '',
                'metadata': json.dumps(metadata) if metadata else '{}'
            }
            
            # Log metrics
            log_metric('recovery_success', 1 if success else 0)
            if recovery_segment_ids:
                log_metric('recovery_segment_count', len(recovery_segment_ids))
            
            results.append(result)
            
            if success:
                logger.info(f"  ✓ Recovery successful for {task_id}")
            else:
                logger.warning(f"  ✗ Recovery failed for {task_id}")
                
        except Exception as e:
            logger.error(f"  ✗ Error processing {task_id}: {e}")
            # Record failure with error details
            results.append({
                'task_id': task_id,
                'recovery_success': False,
                'recovery_segment_id': '',
                'metadata': json.dumps({'error': str(e)})
            })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save evaluation results to CSV file."""
    if not results:
        raise ValueError("No results to save")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['task_id', 'recovery_success', 'recovery_segment_id', 'metadata']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for T015 execution."""
    # Configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path)) if config_path.exists() else {}
    
    # File paths
    injected_trajectories_path = Path(__file__).parent.parent / "data" / "processed" / "injected_trajectories.jsonl"
    baseline_execution_logs_path = Path(__file__).parent.parent / "data" / "processed" / "baseline_execution_logs.csv"
    output_path = Path(__file__).parent.parent / "data" / "processed" / "injected_execution_logs.csv"
    
    logger.info("Starting T015: Recovery success evaluation on injected trajectories")
    
    # Validate input files exist
    if not injected_trajectories_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {injected_trajectories_path}. "
            "Please ensure T013 (injected_trajectories.jsonl) has been completed."
        )
    
    if not baseline_execution_logs_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {baseline_execution_logs_path}. "
            "Please ensure T014 (baseline_execution_logs.csv with recovery tags) has been completed."
        )
    
    try:
        # Load injected trajectories
        trajectories = load_injected_trajectories(injected_trajectories_path)
        
        # Load baseline recovery segment tags
        recovery_map = load_baseline_recovery_tags(baseline_execution_logs_path)
        
        # Run recovery evaluation
        results = run_recovery_evaluation(trajectories, recovery_map, config)
        
        # Save results
        save_results(results, output_path)
        
        # Summary statistics
        total = len(results)
        successful = sum(1 for r in results if r['recovery_success'])
        failed = total - successful
        
        logger.info(f"Evaluation complete: {successful}/{total} successful recovery ({successful/total*100:.1f}%)")
        logger.info(f"Results saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"T015 execution failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
