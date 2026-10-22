"""
download_human.py
-----------------
Acquires human reference C++ solutions from the Codeforces benchmark
using the DeepMind CodeContests dataset from HuggingFace.

This script filters for problems that have at least one C++ solution,
extracts the source code, and writes it to a JSONL file.
"""

import argparse
import json
import random
from pathlib import Path
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def acquire_codeforces_cpp(output_path: Path, min_problems: int, seed: int):
    """
    Downloads the CodeContests dataset, extracts C++ solutions, and saves to JSONL.
    """
    log.info("Loading CodeContests dataset from HuggingFace...")
    
    # Use streaming=True to handle potentially large datasets efficiently
    # and avoid filling disk/RAM on the runner.
    ds = load_dataset("deepmind/code_contests", split="train", streaming=True)
    
    # Set seed for reproducibility when selecting solutions
    random.seed(seed)
    
    collected = []
    problem_ids = set()
    
    log.info(f"Filtering for at least {min_problems} C++ solutions...")
    
    for entry in ds:
        problem_id = entry.get("problem_id")
        solutions = entry.get("solutions", [])
        
        if not problem_id or not solutions:
            continue
        
        # Filter for C++ solutions
        cpp_solutions = [s for s in solutions if s.get("language") == "cpp"]
        
        if cpp_solutions:
            # Pick a random C++ solution from the available ones for this problem
            sol = random.choice(cpp_solutions)
            code = sol.get("code")
            
            if code:
                collected.append({
                    "problem_id": problem_id,
                    "human_code": code
                })
                problem_ids.add(problem_id)
        
        if len(collected) >= min_problems:
            break
    
    if len(collected) < min_problems:
        raise RuntimeError(
            f"Failed to acquire minimum {min_problems} C++ solutions. "
            f"Only found {len(collected)}."
        )
    
    # Write to JSONL
    with output_path.open("w", encoding="utf-8") as f:
        for item in collected:
            f.write(json.dumps(item) + "\n")
    
    log.info(f"Successfully wrote {len(collected)} distinct C++ solutions to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Download human reference C++ solutions.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSONL file.")
    parser.add_argument("--min-problems", type=int, default=50, help="Minimum number of problems to collect.")
    parser.add_argument("--seed", type=int, default=20231027, help="Random seed for solution selection.")
    
    args = parser.parse_args()
    
    # Use llmxive_toolkit.paths to resolve the output path relative to project root
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = paths.path(args.output)
    
    # Ensure directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    acquire_codeforces_cpp(out_path, args.min_problems, args.seed)

if __name__ == "__main__":
    main()