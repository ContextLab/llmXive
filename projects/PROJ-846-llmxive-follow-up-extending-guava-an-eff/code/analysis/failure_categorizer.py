"""
Failure Categorizer for Symbolic-Guava Evaluation.

This module implements the logic to categorize evaluation failures into
geometric, semantic, perception, and latency categories using the
PerceptionLog and TaskOutcome data.

Dependencies:
- T034 (Latency flagging) must be completed before this script runs.
- T016 (PerceptionLog generation) must be completed.
- T031/T032 (Evaluation execution) must be completed.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_path, get_hyperparameter
from utils.exceptions import LlmXiveError
from data.models import TaskOutcome, FailureType


# Constants for categorization logic
LATENCY_THRESHOLD_MS = 150  # FR-008 threshold


def load_task_outcomes(outcome_path: Path) -> List[Dict[str, Any]]:
    """
    Load evaluation outcomes from the processed data file.

    Args:
        outcome_path: Path to the evaluation_outcomes.json file.

    Returns:
        List of outcome dictionaries.

    Raises:
        LlmXiveError: If file not found or invalid JSON.
    """
    if not outcome_path.exists():
        raise LlmXiveError(f"Task outcomes file not found: {outcome_path}")

    with open(outcome_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict with 'outcomes' key
    if isinstance(data, dict) and 'outcomes' in data:
        return data['outcomes']
    elif isinstance(data, list):
        return data
    else:
        raise LlmXiveError(f"Invalid format in {outcome_path}: expected list or dict with 'outcomes' key")


def load_perception_log(log_path: Path) -> Dict[str, Any]:
    """
    Load the PerceptionLog from the artifacts directory.

    Args:
        log_path: Path to perception_log.json.

    Returns:
        PerceptionLog dictionary.

    Raises:
        LlmXiveError: If file not found or invalid JSON.
    """
    if not log_path.exists():
        raise LlmXiveError(f"Perception log not found: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def categorize_failure(
    outcome: Dict[str, Any],
    perception_log: Optional[Dict[str, Any]] = None
) -> str:
    """
    Categorize a single task failure into one of four categories.

    Priority order (first match wins):
    1. Latency-induced (if latency > 150ms and failure is latency-induced)
    2. Perception (if perception quality is low or object missing)
    3. Geometric (if action involves spatial reasoning errors)
    4. Semantic (if action involves object identification or task understanding errors)

    Args:
        outcome: TaskOutcome dictionary.
        perception_log: Optional PerceptionLog for detailed analysis.

    Returns:
        One of: 'latency', 'perception', 'geometric', 'semantic'
    """
    # Check if task succeeded
    if outcome.get('success', False):
        return 'success'

    # 1. Check for latency-induced failures (T034 dependency)
    # Look for explicit latency flag in outcome
    if outcome.get('failure_category') == 'latency':
        return 'latency'

    # Also check latency field directly if category not set
    latency_ms = outcome.get('latency_ms', 0)
    if outcome.get('failure_reason', '').lower().find('latency') != -1:
        return 'latency'

    # 2. Check for perception-related failures
    # Use perception log if available and linked to this task
    task_id = outcome.get('task_id', '')
    if perception_log and task_id:
        # Find corresponding perception entries for this task
        perception_entries = perception_log.get('entries', [])
        for entry in perception_entries:
            if entry.get('task_id') == task_id:
                # Check for low perception quality
                if entry.get('object_missing_if_visible', False):
                    return 'perception'

                # Check confidence scores
                confidence_scores = entry.get('confidence_scores', [])
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    if avg_confidence < 0.5:  # Threshold for low confidence
                        return 'perception'

    # Check outcome-specific perception indicators
    failure_reason = outcome.get('failure_reason', '').lower()
    if any(term in failure_reason for term in ['perception', 'detection', 'vision', 'object missing']):
        return 'perception'

    # 3. Check for geometric failures
    if any(term in failure_reason for term in ['geometry', 'spatial', 'position', 'collision', 'alignment', 'trajectory']):
        return 'geometric'

    # 4. Check for semantic failures
    if any(term in failure_reason for term in ['semantic', 'object', 'task', 'instruction', 'understanding', 'meaning']):
        return 'semantic'

    # Default fallback: check action type or error message patterns
    action_type = outcome.get('action_type', '').lower()
    if 'navigate' in action_type or 'move' in action_type:
        return 'geometric'
    elif 'pick' in action_type or 'place' in action_type:
        # Could be either geometric or semantic - default to semantic for object interaction
        return 'semantic'

    # Ultimate fallback: semantic (most common for LLM reasoning errors)
    return 'semantic'


def categorize_all_failures(
    outcomes_path: Path,
    perception_log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Categorize all task failures and generate summary statistics.

    Args:
        outcomes_path: Path to evaluation_outcomes.json.
        perception_log_path: Optional path to perception_log.json.

    Returns:
        Dictionary with categorized failures and statistics.
    """
    # Load data
    outcomes = load_task_outcomes(outcomes_path)

    perception_log = None
    if perception_log_path and perception_log_path.exists():
        perception_log = load_perception_log(perception_log_path)

    # Categorize each outcome
    categorized = []
    failure_counts = {
        'success': 0,
        'latency': 0,
        'perception': 0,
        'geometric': 0,
        'semantic': 0,
        'unknown': 0
    }

    for outcome in outcomes:
        category = categorize_failure(outcome, perception_log)
        outcome['categorized_failure'] = category
        categorized.append(outcome)

        if category in failure_counts:
            failure_counts[category] += 1
        else:
            failure_counts['unknown'] += 1

    # Calculate statistics
    total_tasks = len(outcomes)
    total_failures = total_tasks - failure_counts['success']

    stats = {
        'total_tasks': total_tasks,
        'total_failures': total_failures,
        'success_rate': failure_counts['success'] / total_tasks if total_tasks > 0 else 0,
        'failure_distribution': failure_counts,
        'failure_rates': {
            cat: count / total_tasks if total_tasks > 0 else 0
            for cat, count in failure_counts.items()
        }
    }

    return {
        'categorized_outcomes': categorized,
        'statistics': stats,
        'timestamp': datetime.utcnow().isoformat(),
        'config': {
            'latency_threshold_ms': LATENCY_THRESHOLD_MS,
            'outcomes_path': str(outcomes_path),
            'perception_log_path': str(perception_log_path) if perception_log_path else None
        }
    }


def write_categorized_outcomes(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write categorized outcomes and statistics to JSON file.

    Args:
        result: Dictionary from categorize_all_failures.
        output_path: Path to output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)


def main():
    """
    Main entry point for failure categorization.
    """
    print("Starting failure categorization...")

    # Define paths
    outcomes_path = get_path('data/processed/evaluation_outcomes.json')
    perception_log_path = get_path('data/artifacts/perception_log.json')
    output_path = get_path('data/artifacts/failure_categorization.json')

    # Validate dependencies
    if not outcomes_path.exists():
        print(f"ERROR: Evaluation outcomes not found at {outcomes_path}")
        print("Please ensure T031/T032 (evaluation execution) is completed.")
        sys.exit(1)

    if not perception_log_path.exists():
        print(f"WARNING: Perception log not found at {perception_log_path}")
        print("Categorization will proceed without perception log analysis.")

    # Perform categorization
    try:
        result = categorize_all_failures(outcomes_path, perception_log_path)
    except LlmXiveError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Write results
    try:
        write_categorized_outcomes(result, output_path)
        print(f"Successfully wrote failure categorization to {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to write output: {e}")
        sys.exit(1)

    # Print summary
    stats = result['statistics']
    print("\n=== Failure Categorization Summary ===")
    print(f"Total Tasks: {stats['total_tasks']}")
    print(f"Total Failures: {stats['total_failures']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print("\nFailure Distribution:")
    for category, count in stats['failure_distribution'].items():
        if count > 0:
            rate = stats['failure_rates'][category]
            print(f"  {category.capitalize()}: {count} ({rate:.2%})")

    print("\nResults saved to:", output_path)


if __name__ == '__main__':
    main()
