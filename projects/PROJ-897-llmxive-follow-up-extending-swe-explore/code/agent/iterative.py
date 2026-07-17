"""
Iterative Agent Loop Implementation (T023)

Implements a CPU-tractable iterative agent loop with:
- 3-turn limit (FR-003)
- Turn logic: Query -> Retrieve -> Static Analysis -> Reformulate
- Loop detection (repeated queries)
- Comprehensive logging for pairing with baseline results
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Import from project API surface
from config import get_config_summary
from agent.static_analysis import run_static_analysis, format_analysis_report
from agent.prompts import format_reformulation_prompt, get_signal_summary
from utils.memory_manager import get_global_monitor, clean_up_large_objects

# Constants
MAX_TURNS = 3
QUERY_HISTORY_WINDOW = 3  # Check last N queries for loop detection

def load_curated_dataset(data_path: Path) -> List[Dict[str, Any]]:
    """Load the curated hard subset dataset."""
    if not data_path.exists():
        raise FileNotFoundError(f"Curated dataset not found at {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def execute_static_query(issue: Dict[str, Any], turn: int, query: str) -> Dict[str, Any]:
    """
    Simulate a static query execution.
    In a real implementation, this would call an LLM or retrieval system.
    For this benchmark, we simulate the retrieval based on static analysis.
    """
    # Simulate retrieval context (in real scenario, this would be LLM output)
    context = {
        "query": query,
        "turn": turn,
        "retrieved_files": [issue.get("file_path", "unknown.py")],
        "simulated_coverage": 0.0,  # Placeholder - real implementation would calculate
        "context_lines": []
    }
    return context

def detect_query_loop(query_history: List[str], new_query: str) -> bool:
    """Detect if the new query is a repeat of recent queries."""
    recent_queries = query_history[-QUERY_HISTORY_WINDOW:]
    return new_query in recent_queries

def run_iterative_loop(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the iterative agent loop for a single issue.
    
    Args:
        issue: Dictionary containing issue data from curated dataset
    
    Returns:
        Dictionary containing the complete agent log for this issue
    """
    issue_id = issue.get("issue_id", "unknown")
    file_path = issue.get("file_path", "")
    initial_code = issue.get("code", "")
    ground_truth_lines = issue.get("ground_truth_lines", [])
    initial_coverage = issue.get("initial_coverage", 0.0)
    
    log_entry = {
        "issue_id": issue_id,
        "file_path": file_path,
        "initial_coverage": initial_coverage,
        "turns": [],
        "query_history": [],
        "static_analysis_signals": [],
        "turn_reasons": [],
        "final_status": "incomplete",
        "total_turns": 0,
        "loop_detected": False,
        "execution_time": 0.0
    }
    
    start_time = time.time()
    query_history: List[str] = []
    turn_count = 0
    
    # Initial query formulation
    current_query = f"Analyze the following issue: {issue.get('description', 'No description')}"
    
    while turn_count < MAX_TURNS:
        turn_count += 1
        turn_start = time.time()
        
        # Step 1: Execute query (simulated retrieval)
        context = execute_static_query(issue, turn_count, current_query)
        log_entry["query_history"].append(current_query)
        
        # Step 2: Run static analysis on retrieved context
        analysis_result = run_static_analysis(initial_code)
        analysis_report = format_analysis_report(analysis_result)
        
        log_entry["static_analysis_signals"].append(analysis_result)
        
        # Step 3: Determine if reformulation is needed
        has_errors = any(
            signal.get("error_type") in ["syntax_error", "undefined_variable", "missing_import"]
            for signal in analysis_result.get("errors", [])
        )
        
        # Step 4: Check for loop detection
        if detect_query_loop(query_history, current_query):
            log_entry["loop_detected"] = True
            log_entry["final_status"] = "loop_detected"
            log_entry["turn_reasons"].append(f"Loop detected at turn {turn_count}")
            break
        
        # Step 5: Reformulate query if needed
        if has_errors and turn_count < MAX_TURNS:
            signal_summary = get_signal_summary(analysis_result)
            reformulation_prompt = format_reformulation_prompt(
                current_query, 
                signal_summary, 
                issue.get("description", "")
            )
            # In real implementation, this would call an LLM
            # For now, we simulate a reformulated query
            current_query = f"Reformulated query (turn {turn_count + 1}): Address {signal_summary}"
            log_entry["turn_reasons"].append(f"Reformulated due to errors: {signal_summary}")
        else:
            current_query = f"Final query (turn {turn_count}): {issue.get('description', '')}"
            log_entry["turn_reasons"].append("Completed analysis cycle")
            break
        
        # Clean up memory for next iteration
        clean_up_large_objects()
        
        turn_duration = time.time() - turn_start
        log_entry["turns"].append({
            "turn_number": turn_count,
            "query": current_query if has_errors else "Final query",
            "analysis_signals": analysis_result,
            "duration_seconds": turn_duration,
            "reformulated": has_errors
        })
    
    # Finalize log entry
    log_entry["total_turns"] = turn_count
    log_entry["execution_time"] = time.time() - start_time
    
    if log_entry["final_status"] == "incomplete":
        if turn_count >= MAX_TURNS:
            log_entry["final_status"] = "max_turns_reached"
        elif log_entry["loop_detected"]:
            log_entry["final_status"] = "loop_detected"
        else:
            log_entry["final_status"] = "completed"
    
    return log_entry

def run_iterative_on_dataset(
    input_path: Path, 
    output_dir: Path, 
    sample_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run the iterative agent loop on a dataset.
    
    Args:
        input_path: Path to the curated dataset JSONL file
        output_dir: Directory to save individual agent logs
        sample_size: Optional limit on number of issues to process
    
    Returns:
        List of all agent logs
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset = load_curated_dataset(input_path)
    
    if sample_size:
        dataset = dataset[:sample_size]
    
    all_logs = []
    
    for issue in dataset:
        issue_id = issue.get("issue_id", "unknown")
        print(f"Processing issue: {issue_id}")
        
        try:
            log_entry = run_iterative_loop(issue)
            all_logs.append(log_entry)
            
            # Save individual log
            log_path = output_dir / f"iterative_{issue_id}.json"
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2)
            
            # Clean up between issues
            clean_up_large_objects()
            
        except Exception as e:
            print(f"Error processing issue {issue_id}: {e}")
            # Continue with next issue
            continue
    
    return all_logs

def main():
    """Main entry point for the iterative agent loop."""
    config = get_config_summary()
    print(f"Starting iterative agent loop with config: {config}")
    
    # Define paths
    curated_path = Path("data/curated/hard_subset.jsonl")
    output_dir = Path("data/results/agent_logs")
    
    if not curated_path.exists():
        print(f"Error: Curated dataset not found at {curated_path}")
        sys.exit(1)
    
    # Run on full dataset
    logs = run_iterative_on_dataset(curated_path, output_dir)
    
    # Save combined results
    combined_path = output_dir / "iterative_all_logs.json"
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    print(f"Completed processing {len(logs)} issues")
    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    main()