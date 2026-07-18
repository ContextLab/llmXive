"""
Implement the iterative agent loop with static analysis feedback.
Enforces turn limits and detects query loops.
"""
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from config import get_config_summary
from agent.static_analysis import run_static_analysis, format_analysis_report
from agent.prompts import format_reformulation_prompt, get_signal_summary
from utils.memory_manager import get_global_monitor


def load_curated_dataset() -> List[Dict[str, Any]]:
    """Load the curated dataset from hard_subset.jsonl."""
    from config import get_path
    path = get_path("curated", "hard_subset.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Curated dataset not found at {path}")
    
    dataset = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    return dataset


def execute_static_query(issue: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Execute a static query against the issue code.
    Returns retrieved context and analysis signals.
    """
    # Simulate retrieval based on query keywords (simplified for CPU tractability)
    # In a real implementation, this would use an embedding model or code search
    retrieved_context = []
    
    code = issue.get("code", "")
    lines = code.split('\n')
    
    # Simple keyword-based retrieval for demonstration
    query_lower = query.lower()
    for i, line in enumerate(lines):
        if any(word in line.lower() for word in query_lower.split()):
            retrieved_context.append({
                "line_number": i + 1,
                "content": line,
                "relevance_score": 0.8
            })
    
    return {
        "retrieved_context": retrieved_context,
        "query": query
    }


def detect_query_loop(history: List[str], current_query: str, threshold: int = 2) -> bool:
    """
    Detect if the current query is a repeat of previous queries.
    Returns True if a loop is detected.
    """
    if len(history) < threshold:
        return False
    
    # Check for exact matches in recent history
    recent = history[-threshold:]
    return current_query in recent


def run_iterative_loop(
    issue: Dict[str, Any],
    max_turns: int = 3,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the iterative agent loop with static analysis feedback.
    
    Args:
        issue: The issue dictionary containing code and metadata.
        max_turns: Maximum number of turns (default 3, overridden by sweep).
        seed: Random seed for reproducibility.
    
    Returns:
        Log entry with query history, analysis signals, and final status.
    """
    import random
    random.seed(seed)
    
    query_history: List[str] = []
    static_analysis_signals: List[Dict[str, Any]] = []
    turn_reasons: List[str] = []
    retrieved_contexts: List[Dict[str, Any]] = []
    
    # Initial query from issue description
    initial_query = issue.get("description", "Fix this issue")
    current_query = initial_query
    
    turn = 0
    status = "completed"
    final_error = None
    
    while turn < max_turns:
        turn += 1
        print(f"[Iterative] Turn {turn}/{max_turns} for {issue.get('issue_id')}")
        
        # Check for query loop
        if detect_query_loop(query_history, current_query):
            status = "loop_detected"
            turn_reasons.append(f"Query loop detected at turn {turn}")
            break
        
        # Execute query
        query_result = execute_static_query(issue, current_query)
        retrieved_contexts.append(query_result["retrieved_context"])
        query_history.append(current_query)
        
        # Run static analysis on retrieved context
        analysis = run_static_analysis(query_result["retrieved_context"])
        static_analysis_signals.append(analysis)
        
        # Check if analysis found issues
        if analysis.get("has_errors", False):
            signal_summary = get_signal_summary(analysis)
            turn_reasons.append(f"Static analysis found errors: {signal_summary}")
            
            # Reformulate query based on errors
            reformulation_prompt = format_reformulation_prompt(
                original_query=current_query,
                analysis_report=analysis,
                context=query_result["retrieved_context"]
            )
            
            # In a real implementation, this would call an LLM
            # For CPU tractability, we simulate a reformulation
            current_query = f"Fix error: {signal_summary} in {current_query}"
        else:
            turn_reasons.append("No errors found, proceeding")
            break
    
    # Compile log entry
    log_entry = {
        "issue_id": issue.get("issue_id"),
        "turns_executed": turn,
        "max_turns_allowed": max_turns,
        "query_history": query_history,
        "static_analysis_signals": static_analysis_signals,
        "turn_reasons": turn_reasons,
        "retrieved_context": [item for ctx in retrieved_contexts for item in ctx],
        "status": status,
        "final_error": final_error,
        "timestamp": time.time()
    }
    
    return log_entry


def run_iterative_on_dataset(
    dataset: List[Dict[str, Any]],
    max_turns: int = 3
) -> List[Dict[str, Any]]:
    """
    Run iterative loop on a full dataset.
    
    Args:
        dataset: List of issue dictionaries.
        max_turns: Maximum turns per issue.
    
    Returns:
        List of log entries.
    """
    results = []
    for issue in dataset:
        try:
            log = run_iterative_loop(issue, max_turns=max_turns)
            results.append(log)
        except Exception as e:
            results.append({
                "issue_id": issue.get("issue_id"),
                "status": "error",
                "error": str(e)
            })
    return results


def main():
    """Main entry point for testing the iterative loop."""
    print("Running Iterative Agent Loop...")
    config = get_config_summary()
    print(f"Config: {config}")
    
    try:
        dataset = load_curated_dataset()
        print(f"Loaded {len(dataset)} issues.")
        
        results = run_iterative_on_dataset(dataset, max_turns=3)
        
        # Save results
        from config import get_path
        output_path = get_path("results", "iterative_logs.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {output_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
