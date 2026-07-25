"""
Iterative agent loop implementation with deterministic loop detection and early exit.

Implements T047: Detects query loops and terminates early to prevent infinite cycles
before hitting the maximum turn limit.
"""
import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_config_summary, get_path
from agent.base import load_curated_dataset
from agent.static_analysis import run_static_analysis, format_analysis_report
from agent.prompts import format_reformulation_prompt, get_signal_summary


def compute_query_hash(query: str) -> str:
    """
    Compute a deterministic hash for a query string.
    
    Args:
        query: The query string to hash.
        
    Returns:
        A SHA256 hex digest of the query.
    """
    return hashlib.sha256(query.encode('utf-8')).hexdigest()


def detect_query_loop(
    current_query: str,
    query_history: List[str],
    similarity_threshold: float = 0.0,
    lookback_window: int = 3
) -> Tuple[bool, Optional[str]]:
    """
    Detect if the current query is a repeat of a previous query in the history.
    
    This function checks for exact string matches and optionally semantic similarity
    based on query hashes to detect loops in the agent's exploration.
    
    Args:
        current_query: The current query string being evaluated.
        query_history: List of previous query strings in the conversation.
        similarity_threshold: Threshold for semantic similarity (0.0 = exact match only).
        lookback_window: Number of most recent queries to check against.
        
    Returns:
        A tuple of (is_loop_detected, matched_query) where matched_query is the
        previous query that triggered the loop detection, or None if no loop.
    """
    if not query_history:
        return False, None
    
    # Check only the most recent queries within the lookback window
    recent_queries = query_history[-lookback_window:]
    
    current_hash = compute_query_hash(current_query)
    
    for prev_query in recent_queries:
        prev_hash = compute_query_hash(prev_query)
        
        # Exact hash match indicates identical query
        if current_hash == prev_hash:
            return True, prev_query
        
        # If threshold > 0, we could implement fuzzy matching here
        # For now, we stick to exact matches for deterministic behavior
        
    return False, None


def run_iterative_loop(
    issue: Dict[str, Any],
    max_turns: int = 3,
    loop_detection_window: int = 3
) -> Dict[str, Any]:
    """
    Run the iterative agent loop for a single issue with loop detection.
    
    Args:
        issue: The issue dictionary containing code, instructions, etc.
        max_turns: Maximum number of turns allowed.
        loop_detection_window: Number of recent queries to check for loops.
        
    Returns:
        A dictionary containing the execution results, including:
        - issue_id
        - query_history
        - coverage_score
        - turns_used
        - termination_reason (normal, loop_detected, max_turns_reached)
        - static_analysis_signals
        - error_signals
    """
    issue_id = issue.get('issue_id', 'unknown')
    instructions = issue.get('instructions', '')
    code = issue.get('code', '')
    
    query_history: List[str] = []
    static_analysis_signals: List[Dict[str, Any]] = []
    error_signals: List[str] = []
    coverage_score: float = 0.0
    turns_used: int = 0
    termination_reason: str = "normal"
    retrieved_context: List[str] = []
    
    # Initial query
    current_query = instructions
    
    for turn in range(1, max_turns + 1):
        turns_used = turn
        
        # Check for loop before executing the turn
        is_loop, matched_query = detect_query_loop(
            current_query,
            query_history,
            lookback_window=loop_detection_window
        )
        
        if is_loop:
            termination_reason = "loop_detected"
            # Log the loop detection event
            error_signals.append(
                f"Loop detected: Query '{current_query[:50]}...' "
                f"repeats previous query at turn {turn}"
            )
            break
        
        # Record the current query
        query_history.append(current_query)
        
        # Execute static analysis on the current code state
        try:
            analysis_result = run_static_analysis(code)
            formatted_report = format_analysis_report(analysis_result)
            static_analysis_signals.append({
                'turn': turn,
                'report': formatted_report,
                'raw': analysis_result
            })
        except Exception as e:
            # Handle static analysis errors gracefully (T050)
            static_analysis_signals.append({
                'turn': turn,
                'report': "neutral_anomaly",
                'raw': {'error': str(e)}
            })
            error_signals.append(f"Static analysis error: {str(e)}")
        
        # Simulate retrieval and coverage calculation
        # In a real implementation, this would call a retrieval system
        # For now, we simulate based on the presence of errors
        if analysis_result.get('errors', []):
            # If there are errors, we might not have full coverage yet
            coverage_score = 0.5  # Placeholder
        else:
            coverage_score = 1.0  # Placeholder for successful resolution
        
        # Check if we've achieved the goal (coverage == 1.0 or no errors)
        if coverage_score >= 1.0 and not analysis_result.get('errors', []):
            termination_reason = "goal_achieved"
            break
        
        # Reformulate query based on static analysis signals
        if analysis_result.get('errors', []):
            signal_summary = get_signal_summary(analysis_result)
            reformulated_query = format_reformulation_prompt(
                original_query=current_query,
                signal_summary=signal_summary,
                code_context=code[:500]  # Limit context size
            )
            current_query = reformulated_query
        else:
            # No errors, but coverage not 1.0 - might need more exploration
            current_query = f"{instructions} (Turn {turn}: Further exploration needed)"
    
    return {
        'issue_id': issue_id,
        'query_history': query_history,
        'static_analysis_signals': static_analysis_signals,
        'error_signals': error_signals,
        'coverage_score': coverage_score,
        'turns_used': turns_used,
        'termination_reason': termination_reason,
        'retrieved_context_ids': list(range(len(retrieved_context)))
    }


def run_iterative_on_dataset(
    dataset_path: str,
    output_path: str,
    max_turns: int = 3,
    loop_detection_window: int = 3
) -> None:
    """
    Run the iterative agent loop on a curated dataset.
    
    Args:
        dataset_path: Path to the input dataset JSONL file.
        output_path: Path to write the output logs JSONL file.
        max_turns: Maximum number of turns per issue.
        loop_detection_window: Number of recent queries to check for loops.
    """
    issues = load_curated_dataset(dataset_path)
    results = []
    
    for issue in issues:
        result = run_iterative_loop(
            issue,
            max_turns=max_turns,
            loop_detection_window=loop_detection_window
        )
        results.append(result)
        
        # Log progress
        print(f"Processed issue {result['issue_id']}: "
              f"turns={result['turns_used']}, "
              f"termination={result['termination_reason']}")
    
    # Write results to output file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    print(f"Results written to {output_path}")


def main() -> None:
    """Main entry point for the iterative agent script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run iterative agent loop with loop detection'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=str(get_path('curated_hard_subset')),
        help='Path to input dataset'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(get_path('iterative_logs')),
        help='Path to output logs'
    )
    parser.add_argument(
        '--max-turns',
        type=int,
        default=3,
        help='Maximum number of turns per issue'
    )
    parser.add_argument(
        '--loop-detection-window',
        type=int,
        default=3,
        help='Number of recent queries to check for loops'
    )
    
    args = parser.parse_args()
    
    config = get_config_summary()
    print(f"Running iterative agent with config: {config}")
    
    run_iterative_on_dataset(
        dataset_path=args.input,
        output_path=args.output,
        max_turns=args.max_turns,
        loop_detection_window=args.loop_detection_window
    )


if __name__ == '__main__':
    main()
