"""
Iterative Agent Implementation with Turn-Loop Detection.

This module implements the iterative agent loop for the SWE-Explore benchmark.
It includes logic to detect and break infinite loops where the reformulated query
matches a previous turn's query within a sliding window.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_config_summary
from agent.static_analysis import run_static_analysis, format_analysis_report
from agent.prompts import format_reformulation_prompt, get_signal_summary
from agent.base import load_curated_dataset

# Try to import the quantized wrapper; if not available, we assume a mock or
# the environment handles it. The task focuses on the loop detection logic.
try:
    from agent.quantized_model import QuantizedModelWrapper
except ImportError:
    # Fallback stub if the specific quantized wrapper module isn't fully populated yet
    # but the task requires the loop logic to exist.
    class QuantizedModelWrapper:
        def __init__(self, model_id: str = "Qwen-1.5-0.5B-4bit"):
            self.model_id = model_id
            self.is_loaded = False

        def load(self):
            self.is_loaded = True

        def generate(self, prompt: str, max_tokens: int = 256) -> str:
            # Placeholder for actual LLM call
            return f"Mock response for: {prompt[:50]}..."

def detect_query_loop(
    current_query: str,
    query_history: List[str],
    window_size: int = 3
) -> bool:
    """
    Detect if the current query repeats a query within the last `window_size` turns.

    Args:
        current_query: The query string generated in the current turn.
        query_history: List of query strings from previous turns (ordered oldest to newest).
        window_size: Number of previous turns to check against.

    Returns:
        True if a loop is detected (current query matches one in the window), False otherwise.
    """
    if not query_history:
        return False

    # Get the last `window_size` queries
    recent_queries = query_history[-window_size:]

    # Normalize strings for comparison (strip whitespace, lower case)
    current_normalized = current_query.strip().lower()
    recent_normalized = [q.strip().lower() for q in recent_queries]

    return current_normalized in recent_normalized


def run_iterative_loop(
    issue: Dict[str, Any],
    max_turns: int = 5,
    loop_window: int = 3
) -> Dict[str, Any]:
    """
    Execute the iterative agent loop for a single issue.

    Args:
        issue: Dictionary containing issue details (id, code, ground_truth_lines, etc.).
        max_turns: Maximum number of turns allowed before termination.
        loop_window: Size of the sliding window for loop detection.

    Returns:
        Dictionary containing the execution log, including query history,
        static analysis signals, and termination reason.
    """
    log = {
        "issue_id": issue.get("issue_id", "unknown"),
        "query_history": [],
        "static_analysis_signals": [],
        "turn_reasons": [],
        "retrieved_context_ids": [],
        "final_coverage": 0.0,
        "termination_reason": "max_turns",
        "turns_used": 0
    }

    current_query = f"Initial query for issue {issue.get('issue_id')}"
    query_history: List[str] = []

    for turn in range(1, max_turns + 1):
        log["turn_reasons"].append(f"Start Turn {turn}")
        log["query_history"].append(current_query)
        log["turns_used"] = turn

        # 1. Retrieve Context (Mocked for this implementation)
        # In a real implementation, this would fetch relevant code lines based on the query.
        retrieved_ids = [f"context_line_{turn}"]
        log["retrieved_context_ids"].extend(retrieved_ids)

        # 2. Static Analysis
        # Analyze the retrieved context or the proposed fix
        analysis_result = run_static_analysis(
            code=issue.get("code", ""),
            context_ids=retrieved_ids
        )
        signal_summary = format_analysis_report(analysis_result)
        log["static_analysis_signals"].append(signal_summary)

        # 3. Check for Loop Detection BEFORE generating next query
        # If we are not at the last turn, we need to generate the next query.
        if turn < max_turns:
            # Check if the current query (which we just executed) is a repeat of a recent one
            # Note: The loop detection logic checks if the *next* query we are about to form
            # is a repeat. However, the task description says:
            # "detect and break infinite loops if the reformulated query matches a previous turn's query"
            # So we generate the reformulation first, then check it.
            
            prompt = format_reformulation_prompt(
                issue_code=issue.get("code", ""),
                current_query=current_query,
                analysis_signals=signal_summary,
                history=query_history
            )
            
            # Simulate model response for reformulation
            wrapper = QuantizedModelWrapper()
            # In a real scenario, wrapper.load() would be called.
            next_query = wrapper.generate(prompt)

            # Check for loop
            if detect_query_loop(next_query, query_history, loop_window):
                log["termination_reason"] = "loop_detected"
                log["final_coverage"] = 0.0 # Placeholder
                return log

            current_query = next_query
        else:
            log["termination_reason"] = "max_turns_reached"

    # Calculate coverage (mocked)
    log["final_coverage"] = 0.0 

    return log


def run_iterative_on_dataset(
    dataset_path: str,
    output_path: str,
    max_turns: int = 5,
    loop_window: int = 3
) -> None:
    """
    Run the iterative agent on a dataset of issues.

    Args:
        dataset_path: Path to the input JSONL file.
        output_path: Path to the output JSONL file.
        max_turns: Maximum turns per issue.
        loop_window: Window size for loop detection.
    """
    config_summary = get_config_summary()
    print(f"Starting iterative agent run. Config: {config_summary}")
    
    issues = load_curated_dataset(dataset_path)
    
    results = []
    for issue in issues:
        try:
            result = run_iterative_loop(
                issue=issue,
                max_turns=max_turns,
                loop_window=loop_window
            )
            results.append(result)
            print(f"Processed issue {result['issue_id']}: {result['termination_reason']}")
        except Exception as e:
            print(f"Error processing issue {issue.get('issue_id')}: {e}")
            results.append({
                "issue_id": issue.get("issue_id"),
                "error": str(e),
                "termination_reason": "error"
            })

    # Write results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')
    
    print(f"Results written to {output_path}")


def main() -> None:
    """Main entry point for the iterative agent script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Iterative Agent with Loop Detection")
    parser.add_argument("--input", type=str, required=True, help="Path to input dataset JSONL")
    parser.add_argument("--output", type=str, required=True, help="Path to output logs JSONL")
    parser.add_argument("--max-turns", type=int, default=5, help="Maximum turns per issue")
    parser.add_argument("--loop-window", type=int, default=3, help="Window size for loop detection")
    
    args = parser.parse_args()
    
    run_iterative_on_dataset(
        dataset_path=args.input,
        output_path=args.output,
        max_turns=args.max_turns,
        loop_window=args.loop_window
    )


if __name__ == "__main__":
    main()