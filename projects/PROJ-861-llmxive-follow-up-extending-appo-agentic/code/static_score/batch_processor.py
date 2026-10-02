import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logger import get_logger
from utils.config import get_config
from static_score.compute import StaticScorer

logger = get_logger(__name__)

# Default configuration values
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes per task
DEFAULT_MAX_EXCLUSION_RATE = 0.10  # 10% exclusion threshold

def load_sampled_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load sampled tasks from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Sampled tasks file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'tasks' in data:
        return data['tasks']
    else:
        raise ValueError(f"Unexpected data format in {input_path}")

def process_single_task(
    task: Dict[str, Any], 
    scorer: StaticScorer, 
    timeout_seconds: float
) -> Optional[Dict[str, Any]]:
    """
    Process a single task with timeout monitoring.
    
    Returns:
        - Result dict if successful
        - None if task timed out (excluded)
    """
    task_id = task.get('task_id', 'unknown')
    start_time = time.time()
    
    try:
        result = scorer.score(task)
        elapsed = time.time() - start_time
        
        result['processing_time'] = elapsed
        result['status'] = 'SUCCESS'
        
        if elapsed > timeout_seconds:
            logger.warning(
                f"Task {task_id} exceeded timeout ({elapsed:.2f}s > {timeout_seconds}s) "
                f"but completed. Marking as TIMEOUT_EXCLUDED."
            )
            result['status'] = 'TIMEOUT_EXCLUDED'
            result['exclusion_reason'] = 'EXCEEDED_DURATION_THRESHOLD'
            return result
        
        return result
        
    except TimeoutError:
        elapsed = time.time() - start_time
        logger.error(
            f"Task {task_id} timed out after {elapsed:.2f}s. "
            "Excluding from dataset."
        )
        return {
            'task_id': task_id,
            'status': 'TIMEOUT_EXCLUDED',
            'exclusion_reason': 'EXECUTION_TIMEOUT',
            'processing_time': elapsed,
            'scores': None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"Task {task_id} failed after {elapsed:.2f}s: {str(e)}"
        )
        return {
            'task_id': task_id,
            'status': 'FAILED',
            'exclusion_reason': f'ERROR: {str(e)}',
            'processing_time': elapsed,
            'scores': None
        }

def run_batch_processing(
    tasks: List[Dict[str, Any]], 
    scorer: StaticScorer,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_exclusion_rate: float = DEFAULT_MAX_EXCLUSION_RATE
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process a batch of tasks with timeout monitoring and exclusion logic.
    
    Args:
        tasks: List of task dictionaries to process
        scorer: StaticScorer instance
        timeout_seconds: Maximum allowed time per task
        max_exclusion_rate: Threshold above which we exit with error
        
    Returns:
        Tuple of (results_list, stats_dict)
        
    Raises:
        SystemExit: If exclusion rate exceeds threshold
    """
    results = []
    excluded_count = 0
    total_count = len(tasks)
    
    logger.info(f"Starting batch processing of {total_count} tasks")
    logger.info(f"Timeout threshold: {timeout_seconds}s per task")
    logger.info(f"Max exclusion rate: {max_exclusion_rate:.2%}")
    
    for idx, task in enumerate(tasks, 1):
        task_id = task.get('task_id', f'task_{idx}')
        logger.info(f"Processing [{idx}/{total_count}] {task_id}")
        
        result = process_single_task(task, scorer, timeout_seconds)
        
        if result is not None:
            results.append(result)
            
            if result.get('status') == 'TIMEOUT_EXCLUDED':
                excluded_count += 1
                logger.warning(
                    f"Excluded {task_id} due to timeout. "
                    f"Current exclusion rate: {excluded_count}/{idx} = "
                    f"{excluded_count/max(1, idx):.2%}"
                )
    
    # Calculate exclusion statistics
    exclusion_rate = excluded_count / max(1, total_count)
    
    stats = {
        'total_tasks': total_count,
        'processed': len(results),
        'excluded': excluded_count,
        'exclusion_rate': exclusion_rate,
        'timeout_threshold': timeout_seconds,
        'max_allowed_rate': max_exclusion_rate
    }
    
    # Check if exclusion rate exceeds threshold
    if exclusion_rate > max_exclusion_rate:
        error_msg = (
            f"RESOURCE_LIMIT_EXCEEDED: "
            f"Exclusion rate ({exclusion_rate:.2%}) exceeds threshold "
            f"({max_exclusion_rate:.2%}). "
            f"Excluded {excluded_count}/{total_count} tasks due to timeouts."
        )
        logger.error(error_msg)
        logger.error("Aborting processing due to excessive timeout exclusions.")
        raise SystemExit(1)
    
    logger.info(
        f"Batch processing complete. "
        f"Exclusion rate: {exclusion_rate:.2%} ({excluded_count}/{total_count})"
    )
    
    return results, stats

def save_results(
    results: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    output_path: str
):
    """Save processing results and statistics to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'results': results,
        'statistics': stats,
        'metadata': {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tasks': stats['total_tasks'],
            'successful_tasks': stats['processed'] - stats['excluded'],
            'excluded_tasks': stats['excluded']
        }
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for batch processing with timeout monitoring."""
    config = get_config()
    
    # Get configuration values with defaults
    input_path = config.get('static_input_path', 'data/processed/sampled_tasks.json')
    output_path = config.get('static_output_path', 'data/processed/static_scores.json')
    timeout_seconds = config.get('task_timeout_seconds', DEFAULT_TIMEOUT_SECONDS)
    max_exclusion_rate = config.get('max_exclusion_rate', DEFAULT_EXCLUSION_RATE)
    
    logger.info(f"Loading tasks from {input_path}")
    tasks = load_sampled_tasks(input_path)
    
    logger.info("Initializing StaticScorer")
    scorer = StaticScorer(
        model_path=config.get('model_path', 'microsoft/phi-2'),
        device=config.get('device', 'cpu'),
        epsilon=config.get('epsilon', 1e-9)
    )
    
    try:
        results, stats = run_batch_processing(
            tasks=tasks,
            scorer=scorer,
            timeout_seconds=timeout_seconds,
            max_exclusion_rate=max_exclusion_rate
        )
        
        save_results(results, stats, output_path)
        
        logger.info("Batch processing completed successfully")
        return 0
        
    except SystemExit as e:
        if e.code == 1:
            logger.error("Processing aborted due to RESOURCE_LIMIT_EXCEEDED")
            return 1
        raise
    except Exception as e:
        logger.exception(f"Fatal error during batch processing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
